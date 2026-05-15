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
)
from parameters import DEFAULT_PARAMS, BUILDING_TYPES


class WoodConstructionLockInModel(MesaModel):
    """Agent-based model of wood construction lock-in and transition.

    Version 0.3:
    - One step = one year.
    - Projects have building types.
    - Market shares are tracked both overall and by building type.
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

        # System state variables
        self.trust_in_wood = self.params["initial_trust_in_wood"]
        self.design_competence = self.params["initial_design_competence"]
        self.contractor_competence = self.params["initial_contractor_competence"]
        self.supplier_capacity = self.params["initial_supplier_capacity"]
        self.standardization = self.params["initial_standardization"]
        self.regulatory_routine = self.params["initial_regulatory_routine"]
        self.education_capacity = self.params["initial_education_capacity"]
        self.workforce = self.params["initial_workforce"]
        self.attractiveness = self.params["initial_attractiveness"]
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

    def _initial_weighted_market_shares(self):
        total_weight = sum(v["project_share"] for v in self.building_types.values())
        wood = sum(v["project_share"] * v["initial_wood_share"] for v in self.building_types.values()) / total_weight
        hybrid = sum(v["project_share"] * v["initial_hybrid_share"] for v in self.building_types.values()) / total_weight
        return wood, hybrid

    def _create_developers(self):
        n = max(30, int(self.params["projects_per_year"] * 0.75))
        developers = []
        for i in range(n):
            # Developer type is now mainly determined at project level, but
            # agent-level type still captures organizational disposition.
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
        """Choose project-level developer type using the building type's public share."""
        bt = self.building_types[building_type]
        public_share = bt.get("public_share", self.params["share_public_developers"])
        r = self.random.random()
        if r < public_share:
            return "public"
        # Within the non-public part, split pioneers and conservatives.
        if self.random.random() < self.params["share_pioneer_developers"]:
            return "pioneer"
        return "conservative"

    def _get_developer(self, developer_type):
        # Prefer matching organizational type if possible.
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

        if material == "wood":
            return max(
                -0.05,
                bt.get("wood_base_cost_premium", p["wood_base_cost_premium"])
                + p["capacity_shortage_penalty"] * shortage * intensity
                - 0.10 * self.standardization
                - 0.06 * self.design_competence
                - 0.05 * self.contractor_competence,
            )
        if material == "hybrid":
            return max(
                -0.03,
                p["hybrid_base_cost_premium"]
                + 0.45 * p["capacity_shortage_penalty"] * shortage * intensity
                - 0.06 * self.standardization
                - 0.03 * self.design_competence,
            )
        return 0.0

    def _estimate_perceived_risk(self, material: str, building_type: str) -> float:
        bt = self.building_types[building_type]
        risk_multiplier = bt.get("risk_multiplier", 1.0)
        if material == "wood":
            return clamp(
                risk_multiplier * (
                    0.48
                    - 0.20 * self.trust_in_wood
                    - 0.17 * self.design_competence
                    - 0.14 * self.contractor_competence
                    - 0.12 * self.standardization
                    - 0.08 * self.regulatory_routine
                )
            )
        if material == "hybrid":
            return clamp(
                risk_multiplier * (
                    0.31
                    - 0.12 * self.trust_in_wood
                    - 0.09 * self.design_competence
                    - 0.07 * self.contractor_competence
                    - 0.06 * self.standardization
                    - 0.04 * self.regulatory_routine
                )
            )
        return 0.10

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

        # Trust dynamics:
        # Version 0.3 allowed trust to saturate at 1.0 too easily.
        # In reality, even a mature wood-construction market retains
        # residual distrust, material preferences and institutional inertia.
        #
        # Therefore:
        # - successful projects have diminishing returns as trust approaches a ceiling,
        # - failures hurt more when trust is high,
        # - policy/cluster effects also have diminishing returns,
        # - trust slowly drifts back toward a baseline if it is not reinforced.
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
            (0.01 * p["cluster_strength"] + 0.004 * p["carbon_policy_strength"])
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

        competence_learning = p["learning_rate"] * wood_like_share
        self.design_competence = clamp(
            self.design_competence
            + competence_learning
            + 0.4 * competence_learning * self.workforce
            - p["competence_decay"]
        )
        self.contractor_competence = clamp(
            self.contractor_competence
            + 0.85 * competence_learning
            + 0.3 * competence_learning * self.workforce
            - p["competence_decay"]
        )

        self.standardization = clamp(
            self.standardization
            + p["standardization_learning_rate"] * wood_like_share
            + 0.04 * p["standardization_investment"]
            + 0.03 * p["cluster_strength"]
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
            + 0.01 * p["carbon_policy_strength"]
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

            rows.append({
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
            })
        return rows

    def step(self):
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

            result = ProjectResult(
                material=material,
                success=success,
                cost_premium=self._estimate_cost_premium(material, building_type),
                perceived_risk=self._estimate_perceived_risk(material, building_type),
                developer_type=developer_type,
                building_type=building_type,
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

        self._update_system_learning(results)
        self.supplier.step()
        self.education.step()
        self.regulator.step()

        avg_cost_wood = self._mean([r.cost_premium for r in results if r.material == "wood"])
        avg_risk_wood = self._mean([r.perceived_risk for r in results if r.material == "wood"])
        failure_rate_wood = self._mean([0 if r.success else 1 for r in results if r.material == "wood"])

        self.history.append({
            "year": self.year,
            "projects": total,
            "wood_share": self.wood_market_share,
            "hybrid_share": self.hybrid_market_share,
            "concrete_share": self.concrete_market_share,
            "wood_like_share": self.wood_demand_pressure,
            "trust_in_wood": self.trust_in_wood,
            "design_competence": self.design_competence,
            "contractor_competence": self.contractor_competence,
            "supplier_capacity": self.supplier_capacity,
            "standardization": self.standardization,
            "regulatory_routine": self.regulatory_routine,
            "education_capacity": self.education_capacity,
            "workforce": self.workforce,
            "attractiveness": self.attractiveness,
            "concrete_lock_in": self.concrete_lock_in,
            "reference_stock": self.reference_stock,
            "avg_wood_cost_premium": avg_cost_wood,
            "avg_wood_perceived_risk": avg_risk_wood,
            "wood_failure_rate": failure_rate_wood,
        })

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
