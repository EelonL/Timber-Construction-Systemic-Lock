import math
import random
from dataclasses import asdict
import pandas as pd

try:
    from mesa import Model as MesaModel
except Exception:
    class MesaModel:
        def __init__(self, *args, **kwargs):
            pass

from agents import (
    DeveloperAgent,
    SupplierAgent,
    EducationAgent,
    RegulatorAgent,
    ProjectResult,
    clamp,
    calculate_risk_components,
    composite_risk,
    RISK_COMPONENTS,
)
from parameters import DEFAULT_PARAMS, BUILDING_TYPES


class WoodConstructionLockInModel(MesaModel):
    """Agent-based model of wood construction lock-in and transition.

    Version 0.5:
    - One step = one year.
    - Projects have building types.
    - Perceived risk is decomposed into six components.
    """

    def __init__(self, params=None, building_types=None):
        try:
            super().__init__()
        except TypeError:
            pass

        self.params = dict(DEFAULT_PARAMS)
        if params:
            self.params.update(params)

        self.building_types = building_types or BUILDING_TYPES

        self.random = random.Random(self.params["random_seed"])
        self.year = 0
        self.effective_carbon_policy_strength = self._effective_carbon_policy_strength()

        # System state variables
        self.trust_in_wood = self.params["initial_trust_in_wood"]
        self.design_competence = self.params["initial_design_competence"]
        self.contractor_competence = self.params["initial_contractor_competence"]
        self.supplier_capacity = self.params["initial_supplier_capacity"]

        # Material-flow subsystem.
        # supplier_capacity = delivery capability of the ecosystem
        # material_capacity = available construction-grade wood product/system capacity
        self.material_capacity = self.params.get("initial_material_capacity", 0.35)
        self.wood_material_demand = 0.0
        self.material_bottleneck = 0.0
        self.material_capacity_utilization = 0.0
        self.material_price_pressure = 0.0
        self.material_risk_pressure = 0.0
        self.domestic_allocation_factor = 0.0
        self.effective_material_capacity_limit = min(
            self.params.get("max_material_capacity", 0.75),
            self.params.get("raw_material_limit", 0.90),
        )

        self.standardization = self.params["initial_standardization"]
        self.regulatory_routine = self.params["initial_regulatory_routine"]
        self.education_capacity = self.params["initial_education_capacity"]
        self.workforce = self.params["initial_workforce"]
        self.attractiveness = self.params["initial_attractiveness"]

        # Education and workforce pipeline, v0.8.
        self.youth_attractiveness = self.params.get("initial_youth_attractiveness", 0.18)
        self.adult_attractiveness = self.params.get("initial_adult_attractiveness", 0.32)
        self.vocational_education_capacity = self.params.get("initial_vocational_education_capacity", 0.28)
        self.he_education_capacity = self.params.get("initial_he_education_capacity", 0.12)
        self.vocational_workforce = self.params.get("initial_vocational_workforce", 0.26)
        self.engineering_workforce = self.params.get("initial_engineering_workforce", 0.14)
        self.concrete_lock_in = self.params["initial_concrete_lock_in"]

        # Overall initial shares are weighted averages from building types.
        self.wood_market_share, self.hybrid_market_share = self._initial_weighted_market_shares()
        self.concrete_market_share = 1 - self.wood_market_share - self.hybrid_market_share

        self.reference_stock = self.wood_market_share + 0.5 * self.hybrid_market_share
        self.wood_demand_pressure = self.wood_market_share + 0.5 * self.hybrid_market_share
        self.previous_wood_demand_pressure = self.wood_demand_pressure

        self.segment_reference_stock = {
            bt: data["initial_wood_share"] + 0.5 * data["initial_hybrid_share"]
            for bt, data in self.building_types.items()
        }

        self.developers = self._create_developers()
        self.supplier = SupplierAgent("supplier_ecosystem", self)
        self.education = EducationAgent("education_system", self)
        self.regulator = RegulatorAgent("regulatory_system", self)

        self.history = []
        self.segment_history = []
        self.project_log = []

    def _effective_carbon_policy_strength(self):
        """Return year-specific carbon policy strength.

        Version 0.9 models carbon policy as tightening over time:
        an initial, relatively mild phase and a later, stronger phase.
        """
        p = self.params
        if not p.get("use_dynamic_carbon_policy", True):
            return p.get("carbon_policy_strength", 0.25)

        tightening_year = int(p.get("carbon_policy_tightening_year", 3))
        if self.year >= tightening_year:
            return p.get("carbon_policy_tightened_strength", p.get("carbon_policy_strength", 0.25))
        return p.get("carbon_policy_initial_strength", p.get("carbon_policy_strength", 0.25))

    def _initial_weighted_market_shares(self):
        total_weight = sum(v["project_share"] for v in self.building_types.values())
        wood = sum(v["project_share"] * v["initial_wood_share"] for v in self.building_types.values()) / total_weight
        hybrid = sum(v["project_share"] * v["initial_hybrid_share"] for v in self.building_types.values()) / total_weight
        return wood, hybrid

    def _create_developers(self):
        n = max(30, int(self.params["projects_per_year"] * 0.75))
        developers = []
        for i in range(n):
            r = self.random.random()
            if r < self.params["share_public_developers"]:
                t = "public"
            elif r < self.params["share_public_developers"] + self.params["share_pioneer_developers"]:
                t = "pioneer"
            else:
                t = "conservative"
            developers.append(DeveloperAgent(f"developer_{i}", self, t))
        return developers

    def _choose_building_type(self):
        names = list(self.building_types.keys())
        weights = [self.building_types[name]["project_share"] for name in names]
        total = sum(weights)
        r = self.random.random() * total
        cumulative = 0.0
        for name, weight in zip(names, weights):
            cumulative += weight
            if r <= cumulative:
                return name
        return names[-1]

    def _developer_type_for_building_type(self, building_type):
        bt = self.building_types[building_type]
        public_share = bt.get("public_share", self.params["share_public_developers"])
        r = self.random.random()
        if r < public_share:
            return "public"
        if self.random.random() < self.params["share_pioneer_developers"]:
            return "pioneer"
        return "conservative"

    def _get_developer(self, developer_type):
        candidates = [d for d in self.developers if d.developer_type == developer_type]
        if candidates:
            return self.random.choice(candidates)
        return self.random.choice(self.developers)

    def _business_cycle_multiplier(self):
        amp = self.params["cycle_amplitude"]
        period = self.params["cycle_period_years"]
        return 1.0 + amp * math.sin(2 * math.pi * self.year / max(1, period))

    def _project_failure_probability(self, material: str, building_type: str) -> float:
        p = self.params
        bt = self.building_types[building_type]

        if material == "wood":
            base = bt.get("base_failure_probability_wood", p["base_failure_probability_wood"])
        elif material == "hybrid":
            base = bt.get("base_failure_probability_hybrid", p["base_failure_probability_hybrid"])
        else:
            return 0.03

        competence = 0.5 * self.design_competence + 0.5 * self.contractor_competence
        failure_prob = (
            base
            - p["failure_reduction_from_competence"] * competence
            - p["failure_reduction_from_standardization"] * self.standardization
            - 0.03 * self.regulatory_routine
        )
        return clamp(failure_prob, 0.01, 0.35)

    def _estimate_cost_premium(self, material: str, building_type: str) -> float:
        p = self.params
        bt = self.building_types[building_type]
        shortage = max(0.0, self.wood_demand_pressure - self.supplier_capacity)
        intensity = bt.get("capacity_intensity", 1.0)

        material_price_pressure = getattr(self, "material_price_pressure", 0.0)

        if material == "wood":
            return max(
                -0.05,
                bt.get("wood_base_cost_premium", p["wood_base_cost_premium"])
                + p["capacity_shortage_penalty"] * shortage * intensity
                + material_price_pressure
                - 0.10 * self.standardization
                - 0.06 * self.design_competence
                - 0.05 * self.contractor_competence,
            )
        if material == "hybrid":
            return max(
                -0.03,
                p["hybrid_base_cost_premium"]
                + 0.45 * p["capacity_shortage_penalty"] * shortage * intensity
                + 0.55 * material_price_pressure
                - 0.06 * self.standardization
                - 0.03 * self.design_competence,
            )
        return 0.0

    def _estimate_perceived_risk(self, material: str, building_type: str, developer_type: str) -> tuple[float, dict]:
        cost = self._estimate_cost_premium(material, building_type)
        components = calculate_risk_components(
            self,
            building_type,
            material,
            cost,
            developer_type=developer_type,
        )
        risk = composite_risk(
            components,
            self.params,
            self.building_types[building_type].get("risk_multiplier", 1.0)
        )
        return risk, components


    def _update_material_constraints(self):
        """Update material-flow constraints after yearly material demand is known.

        This subsystem separates:
        - supplier_capacity: project-delivery capability of the wood-construction ecosystem
        - material_capacity: construction-grade wood product/system availability

        Material capacity is constrained by industrial expansion potential,
        raw-material/sustainability boundaries and export/domestic allocation.
        """
        p = self.params

        allocation_signal = (
            p.get("domestic_demand_stability", 0.30)
            + p.get("domestic_construction_price_premium", 0.00)
            - 0.5 * p.get("export_market_attractiveness", 0.70)
        )

        domestic_allocation_gain = p.get("export_reallocation_sensitivity", 0.25) * allocation_signal
        self.domestic_allocation_factor = clamp(0.30 + domestic_allocation_gain, 0.05, 0.75)

        industrial_limit = p.get("max_material_capacity", 0.75) + self.domestic_allocation_factor * 0.20
        raw_limit = p.get("raw_material_limit", 0.90)
        self.effective_material_capacity_limit = clamp(min(industrial_limit, raw_limit), 0.05, 1.0)

        # projects_per_year is only a Monte Carlo sample size.
        # Material demand is scaled separately by annual_market_volume_index.
        demand = (
            p.get("annual_market_volume_index", 1.0)
            * (
                self.wood_market_share * p.get("wood_project_material_intensity", 1.0)
                + self.hybrid_market_share * p.get("hybrid_project_material_intensity", 0.5)
            )
        )
        self.wood_material_demand = demand
        self.material_capacity_utilization = demand / max(0.01, self.material_capacity)
        self.material_bottleneck = max(0.0, demand - self.material_capacity)

        self.material_price_pressure = (
            self.material_bottleneck
            * p.get("material_bottleneck_cost_impact", 0.20)
        )
        self.material_risk_pressure = (
            self.material_bottleneck
            * p.get("material_bottleneck_risk_impact", 0.25)
        )

        growth_signal = (
            0.65 * self.material_bottleneck
            + 0.25 * p.get("supplier_investment_support", 0.20)
            + 0.20 * p.get("cluster_strength", 0.10)
            + 0.15 * p.get("domestic_demand_stability", 0.30)
        )
        growth = p.get("material_capacity_growth_rate", 0.04) * max(0.0, growth_signal)
        depreciation = p.get("material_capacity_depreciation", 0.005)

        self.material_capacity = clamp(
            self.material_capacity + growth - depreciation,
            0.01,
            self.effective_material_capacity_limit,
        )

    def _update_system_learning(self, results):
        p = self.params
        total = max(1, len(results))
        wood_count = sum(1 for r in results if r.material == "wood")
        hybrid_count = sum(1 for r in results if r.material == "hybrid")
        wood_like_share = (wood_count + 0.5 * hybrid_count) / total

        wood_success = sum(1 for r in results if r.material == "wood" and r.success)
        hybrid_success = sum(1 for r in results if r.material == "hybrid" and r.success)
        wood_failures = sum(1 for r in results if r.material == "wood" and not r.success)
        hybrid_failures = sum(1 for r in results if r.material == "hybrid" and not r.success)

        success_signal = (wood_success + 0.5 * hybrid_success) / total
        failure_signal = (wood_failures + 0.5 * hybrid_failures) / total

        # Shock scenario: visible failure in one year
        if self.params.get("shock_year") == self.year:
            failure_signal += self.params.get("shock_strength", 0.20)

        # Trust dynamics from v0.4
        trust_ceiling = p.get("trust_ceiling", 0.82)
        trust_baseline = p.get("trust_baseline", 0.28)
        trust_decay = p.get("trust_decay", 0.012)

        trust_headroom = max(0.0, trust_ceiling - self.trust_in_wood)

        success_gain = (
            p["trust_success_impact"]
            * success_signal
            * 10
            * trust_headroom
        )

        failure_loss = (
            p["trust_failure_impact"]
            * failure_signal
            * 5
            * (0.5 + self.trust_in_wood)
        )

        policy_gain = (
            (0.005 * p["cluster_strength"] + 0.004 * self.effective_carbon_policy_strength)
            * trust_headroom
        )

        mean_reversion = trust_decay * max(0.0, self.trust_in_wood - trust_baseline)

        self.trust_in_wood = clamp(
            self.trust_in_wood
            + success_gain
            - failure_loss
            + policy_gain
            - mean_reversion,
            0.0,
            trust_ceiling
        )

        effective_learning_rate = p["learning_rate"] * (1 + 0.25 * p.get("cluster_strength", 0.10))
        competence_learning = effective_learning_rate * wood_like_share

        # Engineering workforce supports design/system competence.
        # Vocational workforce supports contractor/site/factory competence.
        self.design_competence = clamp(
            self.design_competence
            + competence_learning
            + 0.45 * competence_learning * self.engineering_workforce
            + 0.15 * p.get("industry_training_strength", 0.25) * wood_like_share
            - p["competence_decay"]
        )
        self.contractor_competence = clamp(
            self.contractor_competence
            + 0.85 * competence_learning
            + 0.40 * competence_learning * self.vocational_workforce
            + 0.18 * p.get("industry_training_strength", 0.25) * wood_like_share
            - p["competence_decay"]
        )

        self.standardization = clamp(
            self.standardization
            + p["standardization_learning_rate"] * wood_like_share
            + 0.04 * p["standardization_investment"]
            + 0.015 * p["cluster_strength"]
            - 0.008
        )

        self.reference_stock = clamp(
            0.88 * self.reference_stock
            + 0.12 * wood_like_share
        )

        self.attractiveness = clamp(
            self.attractiveness
            + p["attractiveness_success_impact"] * success_signal * 10
            - p["attractiveness_failure_impact"] * failure_signal * 5
            + 0.01 * self.effective_carbon_policy_strength
            + 0.01 * self.standardization
        )

        self.concrete_lock_in = clamp(
            self.concrete_lock_in
            - p["lock_in_decay_from_wood"] * wood_like_share
            + 0.004 * (1 - wood_like_share)
        )

        # Segment-level references update by building type.
        for bt_name in self.building_types:
            bt_results = [r for r in results if r.building_type == bt_name]
            if not bt_results:
                continue
            n = len(bt_results)
            bt_wood = sum(1 for r in bt_results if r.material == "wood")
            bt_hybrid = sum(1 for r in bt_results if r.material == "hybrid")
            bt_wood_like = (bt_wood + 0.5 * bt_hybrid) / n
            self.segment_reference_stock[bt_name] = clamp(
                0.86 * self.segment_reference_stock[bt_name]
                + 0.14 * bt_wood_like
            )

    def _risk_component_means(self, results, prefix=""):
        rows = {}
        relevant = [r for r in results if r.material in ("wood", "hybrid")]
        for comp in RISK_COMPONENTS:
            attr = f"risk_{comp}"
            values = [getattr(r, attr) for r in relevant]
            rows[f"{prefix}risk_{comp}"] = self._mean(values)
        return rows

    def _segment_summary_rows(self, results):
        rows = []
        for bt_name in self.building_types:
            bt_results = [r for r in results if r.building_type == bt_name]
            n = len(bt_results)
            if n == 0:
                continue
            wood = sum(1 for r in bt_results if r.material == "wood")
            hybrid = sum(1 for r in bt_results if r.material == "hybrid")
            concrete = n - wood - hybrid
            failures = sum(1 for r in bt_results if not r.success and r.material in ("wood", "hybrid"))
            wood_costs = [r.cost_premium for r in bt_results if r.material == "wood"]
            wood_risks = [r.perceived_risk for r in bt_results if r.material == "wood"]

            row = {
                "year": self.year,
                "building_type": bt_name,
                "projects": n,
                "wood_share": wood / n,
                "hybrid_share": hybrid / n,
                "concrete_share": concrete / n,
                "wood_like_share": (wood + 0.5 * hybrid) / n,
                "segment_reference_stock": self.segment_reference_stock.get(bt_name, 0.0),
                "wood_failure_rate": failures / max(1, wood + hybrid),
                "avg_wood_cost_premium": self._mean(wood_costs),
                "avg_wood_perceived_risk": self._mean(wood_risks),
            }
            row.update(self._risk_component_means(bt_results))
            rows.append(row)
        return rows

    def step(self):
        self.effective_carbon_policy_strength = self._effective_carbon_policy_strength()

        projects_this_year = max(
            1,
            int(self.params["projects_per_year"] * self._business_cycle_multiplier())
        )

        results = []
        self.previous_wood_demand_pressure = self.wood_demand_pressure

        for i in range(projects_this_year):
            building_type = self._choose_building_type()
            developer_type = self._developer_type_for_building_type(building_type)
            developer = self._get_developer(developer_type)
            material = developer.choose_material(building_type)

            failure_prob = self._project_failure_probability(material, building_type)
            success = self.random.random() > failure_prob

            developer.update_experience(material, success)

            cost_premium = self._estimate_cost_premium(material, building_type)
            perceived_risk, risk_components = self._estimate_perceived_risk(material, building_type, developer_type)

            result = ProjectResult(
                material=material,
                success=success,
                cost_premium=cost_premium,
                perceived_risk=perceived_risk,
                developer_type=developer_type,
                building_type=building_type,
                risk_competence=risk_components["competence"],
                risk_regulatory_fire=risk_components["regulatory_fire"],
                risk_cost_uncertainty=risk_components["cost_uncertainty"],
                risk_supply_chain=risk_components["supply_chain"],
                risk_moisture_technical=risk_components["moisture_technical"],
                risk_market_acceptance=risk_components["market_acceptance"],
            )
            results.append(result)
            self.project_log.append({"year": self.year, **asdict(result)})

        total = len(results)
        wood_count = sum(1 for r in results if r.material == "wood")
        hybrid_count = sum(1 for r in results if r.material == "hybrid")
        concrete_count = total - wood_count - hybrid_count

        self.wood_market_share = wood_count / total
        self.hybrid_market_share = hybrid_count / total
        self.concrete_market_share = concrete_count / total
        self.wood_demand_pressure = self.wood_market_share + 0.5 * self.hybrid_market_share

        self._update_material_constraints()
        self._update_system_learning(results)
        self.supplier.step()
        self.education.step()
        self.regulator.step()

        avg_cost_wood = self._mean([r.cost_premium for r in results if r.material == "wood"])
        avg_risk_wood = self._mean([r.perceived_risk for r in results if r.material == "wood"])
        failure_rate_wood = self._mean([0 if r.success else 1 for r in results if r.material == "wood"])

        history_row = {
            "year": self.year,
            "projects": total,
            "wood_share": self.wood_market_share,
            "hybrid_share": self.hybrid_market_share,
            "concrete_share": self.concrete_market_share,
            "wood_like_share": self.wood_demand_pressure,
            "wood_demand_pressure": self.wood_demand_pressure,
            "wood_material_demand": self.wood_material_demand,
            "effective_carbon_policy_strength": self.effective_carbon_policy_strength,
            "trust_in_wood": self.trust_in_wood,
            "design_competence": self.design_competence,
            "contractor_competence": self.contractor_competence,
            "supplier_capacity": self.supplier_capacity,
            "material_capacity": self.material_capacity,
            "material_capacity_utilization": self.material_capacity_utilization,
            "material_bottleneck": self.material_bottleneck,
            "material_price_pressure": self.material_price_pressure,
            "material_risk_pressure": self.material_risk_pressure,
            "domestic_allocation_factor": self.domestic_allocation_factor,
            "effective_material_capacity_limit": self.effective_material_capacity_limit,
            "standardization": self.standardization,
            "regulatory_routine": self.regulatory_routine,
            "education_capacity": self.education_capacity,
            "workforce": self.workforce,
            "attractiveness": self.attractiveness,
            "youth_attractiveness": self.youth_attractiveness,
            "adult_attractiveness": self.adult_attractiveness,
            "vocational_education_capacity": self.vocational_education_capacity,
            "he_education_capacity": self.he_education_capacity,
            "vocational_workforce": self.vocational_workforce,
            "engineering_workforce": self.engineering_workforce,
            "concrete_lock_in": self.concrete_lock_in,
            "reference_stock": self.reference_stock,
            "avg_wood_cost_premium": avg_cost_wood,
            "avg_wood_perceived_risk": avg_risk_wood,
            "wood_failure_rate": failure_rate_wood,
        }
        history_row.update(self._risk_component_means(results))
        self.history.append(history_row)

        self.segment_history.extend(self._segment_summary_rows(results))
        self.year += 1

    @staticmethod
    def _mean(values):
        values = list(values)
        if not values:
            return 0.0
        return sum(values) / len(values)

    def run(self, years=None) -> pd.DataFrame:
        years = years or self.params["years"]
        for _ in range(years):
            self.step()
        return pd.DataFrame(self.history)

    def project_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.project_log)

    def segment_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.segment_history)
