import math
from dataclasses import dataclass

try:
    from mesa import Agent as MesaAgent
except Exception:
    class MesaAgent:
        def __init__(self, *args, **kwargs):
            pass


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


class BaseAgent(MesaAgent):
    """Compatibility wrapper for Mesa 2.x and 3.x style Agent initialization."""

    def __init__(self, unique_id, model):
        self.unique_id = unique_id
        self.model = model
        try:
            super().__init__(unique_id, model)  # Mesa 2.x
        except TypeError:
            try:
                super().__init__(model)  # Mesa 3.x
            except TypeError:
                super().__init__()


@dataclass
class ProjectResult:
    material: str
    success: bool
    cost_premium: float
    perceived_risk: float
    developer_type: str


class DeveloperAgent(BaseAgent):
    """A developer/client that chooses concrete, wood, or hybrid for one project."""

    def __init__(self, unique_id, model, developer_type: str):
        super().__init__(unique_id, model)
        self.developer_type = developer_type
        self.wood_experience = 0.0
        self.hybrid_experience = 0.0

    def _softmax_choice(self, scores: dict) -> str:
        """Probabilistic material choice.

        Version 0.1 used deterministic argmax. That made concrete dominate completely
        under default parameters. This version uses a softmax choice with small
        experiment floors for wood and hybrid.
        """
        m = self.model
        p = m.params
        temperature = max(0.05, p.get("choice_temperature", 0.35))

        max_score = max(scores.values())
        weights = {
            k: math.exp((v - max_score) / temperature)
            for k, v in scores.items()
        }

        # Add minimum experimentation probabilities.
        weights["wood"] += p.get("wood_experiment_floor", 0.025)
        weights["hybrid"] += p.get("hybrid_experiment_floor", 0.04)

        total = sum(weights.values())
        r = m.random.random() * total
        cumulative = 0.0
        for material, weight in weights.items():
            cumulative += weight
            if r <= cumulative:
                return material
        return "concrete"

    def choose_material(self) -> str:
        m = self.model
        p = m.params

        climate_weight = p["private_climate_weight"]
        policy_bonus = 0.0
        pioneer_bonus = 0.0
        conservative_risk_extra = 0.0

        if self.developer_type == "public":
            climate_weight = p["public_climate_weight"]
            policy_bonus = p["public_procurement_strength"] * 0.40
        elif self.developer_type == "pioneer":
            pioneer_bonus = p["pioneer_bonus"]
        elif self.developer_type == "conservative":
            conservative_risk_extra = p["conservative_risk_extra"]

        shortage = max(0.0, m.wood_demand_pressure - m.supplier_capacity)
        wood_cost = (
            p["wood_base_cost_premium"]
            + p["capacity_shortage_penalty"] * shortage
            - 0.10 * m.standardization
            - 0.06 * m.design_competence
            - 0.05 * m.contractor_competence
        )
        hybrid_cost = (
            p["hybrid_base_cost_premium"]
            + 0.45 * p["capacity_shortage_penalty"] * shortage
            - 0.06 * m.standardization
            - 0.03 * m.design_competence
        )

        wood_risk = (
            0.48
            - 0.20 * m.trust_in_wood
            - 0.17 * m.design_competence
            - 0.14 * m.contractor_competence
            - 0.11 * m.regulatory_routine
            - 0.12 * m.standardization
            - 0.10 * self.wood_experience
            + conservative_risk_extra
        )
        hybrid_risk = (
            0.31
            - 0.12 * m.trust_in_wood
            - 0.09 * m.design_competence
            - 0.07 * m.contractor_competence
            - 0.07 * m.regulatory_routine
            - 0.05 * self.hybrid_experience
            + 0.5 * conservative_risk_extra
        )

        carbon_benefit_wood = p["carbon_policy_strength"] * climate_weight * p["climate_sensitivity"]
        carbon_benefit_hybrid = 0.55 * carbon_benefit_wood

        reference_bonus = 0.22 * m.reference_stock
        cluster_bonus = 0.12 * p["cluster_strength"]

        wood_score = (
            carbon_benefit_wood
            + policy_bonus
            + pioneer_bonus
            + reference_bonus
            + cluster_bonus
            + 0.12 * self.wood_experience
            + 0.06 * m.attractiveness
            - p["cost_sensitivity"] * wood_cost
            - p["risk_sensitivity"] * clamp(wood_risk)
            - 0.08 * m.concrete_lock_in
        )

        hybrid_score = (
            carbon_benefit_hybrid
            + 0.60 * policy_bonus
            + 0.55 * pioneer_bonus
            + 0.55 * reference_bonus
            + 0.06 * self.hybrid_experience
            + 0.04 * m.attractiveness
            - 0.75 * p["cost_sensitivity"] * hybrid_cost
            - 0.65 * p["risk_sensitivity"] * clamp(hybrid_risk)
            - 0.04 * m.concrete_lock_in
        )

        concrete_score = (
            0.10
            + 0.13 * m.concrete_lock_in
            - 0.12 * p["carbon_policy_strength"] * climate_weight
        )

        # Noise captures project-specific variation.
        wood_score += m.random.normalvariate(0, 0.035)
        hybrid_score += m.random.normalvariate(0, 0.030)
        concrete_score += m.random.normalvariate(0, 0.025)

        return self._softmax_choice({
            "wood": wood_score,
            "hybrid": hybrid_score,
            "concrete": concrete_score,
        })

    def update_experience(self, material: str, success: bool):
        delta = 0.06 if success else 0.02
        if material == "wood":
            self.wood_experience = clamp(self.wood_experience + delta)
        elif material == "hybrid":
            self.hybrid_experience = clamp(self.hybrid_experience + delta)


class SupplierAgent(BaseAgent):
    """Aggregated wood-product supplier ecosystem."""

    def step(self):
        m = self.model
        p = m.params

        utilization = m.wood_demand_pressure / max(0.01, m.supplier_capacity)
        expected_demand = 0.65 * m.wood_demand_pressure + 0.35 * m.previous_wood_demand_pressure

        investment_signal = (
            0.45 * expected_demand
            + 0.25 * p["supplier_investment_support"]
            + 0.20 * p["cluster_strength"]
            + 0.10 * m.trust_in_wood
        )

        if utilization > p["capacity_investment_threshold"] or investment_signal > p["capacity_investment_threshold"]:
            growth = min(
                p["max_capacity_growth_per_year"],
                p["capacity_learning_rate"] * (utilization + p["supplier_investment_support"] + p["cluster_strength"]) / 3,
            )
        else:
            growth = 0.0

        min_capacity = p.get("min_supplier_capacity", 0.05)
        m.supplier_capacity = clamp(m.supplier_capacity + growth - p["capacity_depreciation"], min_capacity, 1.0)


class EducationAgent(BaseAgent):
    """Aggregated education and workforce pipeline with a delay."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.pipeline = [0.0 for _ in range(model.params["education_delay_years"])]

    def step(self):
        m = self.model
        p = m.params

        demand_signal = 0.5 * m.wood_market_share + 0.3 * m.hybrid_market_share + 0.2 * m.attractiveness
        new_students = clamp(
            p["education_investment"] * p["education_response_rate"]
            + demand_signal * 0.04
            + p["cluster_strength"] * 0.03
        )

        graduating = self.pipeline.pop(0) if self.pipeline else new_students
        self.pipeline.append(new_students)

        m.workforce = clamp(
            m.workforce
            + graduating
            - 0.012
        )

        m.education_capacity = clamp(
            m.education_capacity
            + 0.04 * p["education_investment"]
            + 0.02 * p["cluster_strength"]
            - 0.008
        )


class RegulatorAgent(BaseAgent):
    """Aggregated regulatory and permitting routine."""

    def step(self):
        m = self.model
        p = m.params
        learning = 0.03 * (m.wood_market_share + 0.5 * m.hybrid_market_share)
        m.regulatory_routine = clamp(
            m.regulatory_routine
            + learning
            + 0.015 * p["cluster_strength"]
            - 0.004
        )
