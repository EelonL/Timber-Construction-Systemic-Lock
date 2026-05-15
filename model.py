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
from parameters import DEFAULT_PARAMS


class WoodConstructionLockInModel(MesaModel):
    """Agent-based model of wood construction lock-in and transition.

    One step = one year.
    """

    def __init__(self, params=None):
        try:
            super().__init__()
        except TypeError:
            pass

        self.params = dict(DEFAULT_PARAMS)
        if params:
            self.params.update(params)

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

        self.wood_market_share = self.params["initial_wood_share"]
        self.hybrid_market_share = self.params["initial_hybrid_share"]
        self.concrete_market_share = 1 - self.wood_market_share - self.hybrid_market_share

        self.reference_stock = self.wood_market_share + 0.5 * self.hybrid_market_share
        self.wood_demand_pressure = self.wood_market_share + 0.5 * self.hybrid_market_share
        self.previous_wood_demand_pressure = self.wood_demand_pressure

        self.developers = self._create_developers()
        self.supplier = SupplierAgent("supplier_ecosystem", self)
        self.education = EducationAgent("education_system", self)
        self.regulator = RegulatorAgent("regulatory_system", self)

        self.history = []
        self.project_log = []

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

    def _business_cycle_multiplier(self):
        amp = self.params["cycle_amplitude"]
        period = self.params["cycle_period_years"]
        return 1.0 + amp * math.sin(2 * math.pi * self.year / max(1, period))

    def _project_failure_probability(self, material: str) -> float:
        p = self.params
        if material == "wood":
            base = p["base_failure_probability_wood"]
        elif material == "hybrid":
            base = p["base_failure_probability_hybrid"]
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

    def _estimate_cost_premium(self, material: str) -> float:
        p = self.params
        shortage = max(0.0, self.wood_demand_pressure - self.supplier_capacity)

        if material == "wood":
            return max(
                -0.05,
                p["wood_base_cost_premium"]
                + p["capacity_shortage_penalty"] * shortage
                - 0.10 * self.standardization
                - 0.06 * self.design_competence
                - 0.05 * self.contractor_competence,
            )
        if material == "hybrid":
            return max(
                -0.03,
                p["hybrid_base_cost_premium"]
                + 0.45 * p["capacity_shortage_penalty"] * shortage
                - 0.06 * self.standardization
                - 0.03 * self.design_competence,
            )
        return 0.0

    def _estimate_perceived_risk(self, material: str) -> float:
        if material == "wood":
            return clamp(
                0.48
                - 0.20 * self.trust_in_wood
                - 0.17 * self.design_competence
                - 0.14 * self.contractor_competence
                - 0.12 * self.standardization
                - 0.08 * self.regulatory_routine
            )
        if material == "hybrid":
            return clamp(
                0.31
                - 0.12 * self.trust_in_wood
                - 0.09 * self.design_competence
                - 0.07 * self.contractor_competence
                - 0.06 * self.standardization
                - 0.04 * self.regulatory_routine
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

        self.trust_in_wood = clamp(
            self.trust_in_wood
            + p["trust_success_impact"] * success_signal * 10
            - p["trust_failure_impact"] * failure_signal * 5
            + 0.01 * p["cluster_strength"]
            + 0.004 * p["carbon_policy_strength"]
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

    def step(self):
        projects_this_year = max(
            1,
            int(self.params["projects_per_year"] * self._business_cycle_multiplier())
        )

        results = []
        self.previous_wood_demand_pressure = self.wood_demand_pressure

        for i in range(projects_this_year):
            developer = self.random.choice(self.developers)
            material = developer.choose_material()

            failure_prob = self._project_failure_probability(material)
            success = self.random.random() > failure_prob

            developer.update_experience(material, success)

            result = ProjectResult(
                material=material,
                success=success,
                cost_premium=self._estimate_cost_premium(material),
                perceived_risk=self._estimate_perceived_risk(material),
                developer_type=developer.developer_type,
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
