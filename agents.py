import math
from dataclasses import dataclass

try:
    from mesa import Agent as MesaAgent
except Exception:
    class MesaAgent:
        def __init__(self, *args, **kwargs):
            pass


RISK_COMPONENTS = [
    "competence",
    "regulatory_fire",
    "cost_uncertainty",
    "supply_chain",
    "moisture_technical",
    "market_acceptance",
]


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def component_weights(params: dict) -> dict:
    return {
        "competence": params.get("risk_weight_competence", 0.25),
        "regulatory_fire": params.get("risk_weight_regulatory_fire", 0.22),
        "cost_uncertainty": params.get("risk_weight_cost_uncertainty", 0.18),
        "supply_chain": params.get("risk_weight_supply_chain", 0.14),
        "moisture_technical": params.get("risk_weight_moisture_technical", 0.11),
        "market_acceptance": params.get("risk_weight_market_acceptance", 0.10),
    }


def composite_risk(components: dict, params: dict, risk_multiplier: float = 1.0) -> float:
    weights = component_weights(params)
    total_w = sum(weights.values())
    if total_w <= 0:
        return clamp(sum(components.values()) / max(1, len(components)))
    value = sum(weights[k] * components.get(k, 0.0) for k in weights) / total_w
    return clamp(value * risk_multiplier)


def calculate_risk_components(
    model,
    building_type: str,
    material: str,
    cost_premium: float,
    developer_type: str = "conservative",
    wood_experience: float = 0.0,
    hybrid_experience: float = 0.0,
) -> dict:
    """Calculate perceived risk as six subcomponents.

    The components are deliberately stylized. They are calibrated as normalized
    0..1 risk indicators, not as probabilities.

    Components:
    - competence: lack of design/contractor/workforce competence
    - regulatory_fire: regulation, permitting and fire-safety uncertainty
    - cost_uncertainty: cost-estimate uncertainty and risk premium
    - supply_chain: supplier availability and capacity risk
    - moisture_technical: moisture, durability and technical execution risk
    - market_acceptance: residual client/user/investor acceptance risk
    """
    p = model.params
    bt = model.building_types[building_type]
    base = bt.get("risk_components", {})
    segment_ref = model.segment_reference_stock.get(building_type, 0.0)
    shortage = max(0.0, model.wood_demand_pressure - model.supplier_capacity)

    material_bottleneck = getattr(model, "material_bottleneck", 0.0)
    material_price_pressure = getattr(model, "material_price_pressure", 0.0)
    material_risk_pressure = getattr(model, "material_risk_pressure", 0.0)

    # Hybrid is treated as a transitional solution: lower risk than pure wood,
    # but still affected by the same system variables.
    if material == "hybrid":
        material_factor = 0.68
        experience = hybrid_experience
    elif material == "wood":
        material_factor = 1.00
        experience = wood_experience
    else:
        material_factor = 0.25
        experience = 0.0

    conservative_extra = p.get("conservative_risk_extra", 0.15) if developer_type == "conservative" else 0.0
    pioneer_reduction = 0.05 if developer_type == "pioneer" else 0.0
    public_reduction = 0.03 if developer_type == "public" else 0.0

    avg_competence = 0.5 * model.design_competence + 0.5 * model.contractor_competence

    components = {
        "competence": (
            base.get("competence", 0.50)
            * (1 - 0.55 * avg_competence - 0.15 * model.workforce - 0.10 * experience)
        ),
        "regulatory_fire": (
            base.get("regulatory_fire", 0.50)
            * (1 - 0.60 * model.regulatory_routine - 0.20 * model.standardization)
        ),
        "cost_uncertainty": (
            base.get("cost_uncertainty", 0.50)
            * (1 - 0.40 * model.standardization - 0.15 * model.trust_in_wood)
            + max(0.0, cost_premium) * 1.15
            + material_price_pressure
        ),
        "supply_chain": (
            base.get("supply_chain", 0.50)
            * (1 - 0.60 * model.supplier_capacity)
            + shortage * bt.get("capacity_intensity", 1.0) * 0.65
            + material_risk_pressure
            + material_bottleneck * 0.35
        ),
        "moisture_technical": (
            base.get("moisture_technical", 0.50)
            * (1 - 0.45 * model.contractor_competence - 0.35 * model.standardization)
        ),
        "market_acceptance": (
            base.get("market_acceptance", 0.50)
            * (1 - 0.45 * model.trust_in_wood - 0.25 * segment_ref)
            + 0.5 * conservative_extra
            - pioneer_reduction
            - public_reduction
        ),
    }

    # Apply material factor and final clamp.
    return {k: clamp(v * material_factor) for k, v in components.items()}


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
    building_type: str
    risk_competence: float
    risk_regulatory_fire: float
    risk_cost_uncertainty: float
    risk_supply_chain: float
    risk_moisture_technical: float
    risk_market_acceptance: float


class DeveloperAgent(BaseAgent):
    """A developer/client that chooses concrete, wood, or hybrid for one project."""

    def __init__(self, unique_id, model, developer_type: str):
        super().__init__(unique_id, model)
        self.developer_type = developer_type
        self.wood_experience = 0.0
        self.hybrid_experience = 0.0

    def _softmax_choice(self, scores: dict) -> str:
        """Probabilistic material choice."""
        m = self.model
        p = m.params
        temperature = max(0.05, p.get("choice_temperature", 0.35))

        max_score = max(scores.values())
        weights = {
            k: math.exp((v - max_score) / temperature)
            for k, v in scores.items()
        }

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

    def _cost_premium_for_material(self, building_type: str, material: str) -> float:
        m = self.model
        p = m.params
        bt = m.building_types[building_type]
        shortage = max(0.0, m.wood_demand_pressure - m.supplier_capacity)
        intensity = bt.get("capacity_intensity", 1.0)

        material_price_pressure = getattr(m, "material_price_pressure", 0.0)

        if material == "wood":
            return max(
                -0.05,
                bt.get("wood_base_cost_premium", p["wood_base_cost_premium"])
                + p["capacity_shortage_penalty"] * shortage * intensity
                + material_price_pressure
                - 0.10 * m.standardization
                - 0.06 * m.design_competence
                - 0.05 * m.contractor_competence,
            )
        if material == "hybrid":
            return max(
                -0.03,
                p["hybrid_base_cost_premium"]
                + 0.45 * p["capacity_shortage_penalty"] * shortage * intensity
                + 0.55 * material_price_pressure
                - 0.06 * m.standardization
                - 0.03 * m.design_competence,
            )
        return 0.0

    def choose_material(self, building_type: str) -> str:
        m = self.model
        p = m.params
        bt = m.building_types[building_type]

        climate_weight = p["private_climate_weight"]
        policy_bonus = 0.0
        pioneer_bonus = 0.0

        if self.developer_type == "public":
            climate_weight = p["public_climate_weight"]
            policy_bonus = p["public_procurement_strength"] * 0.40 * bt["policy_relevance"]
        elif self.developer_type == "pioneer":
            pioneer_bonus = p["pioneer_bonus"]

        wood_cost = self._cost_premium_for_material(building_type, "wood")
        hybrid_cost = self._cost_premium_for_material(building_type, "hybrid")

        wood_components = calculate_risk_components(
            m, building_type, "wood", wood_cost, self.developer_type,
            self.wood_experience, self.hybrid_experience
        )
        hybrid_components = calculate_risk_components(
            m, building_type, "hybrid", hybrid_cost, self.developer_type,
            self.wood_experience, self.hybrid_experience
        )

        wood_risk = composite_risk(wood_components, p, bt.get("risk_multiplier", 1.0))
        hybrid_risk = composite_risk(hybrid_components, p, bt.get("risk_multiplier", 1.0))

        carbon_benefit_wood = (
            p["carbon_policy_strength"]
            * climate_weight
            * p["climate_sensitivity"]
            * bt.get("climate_relevance", 1.0)
        )
        carbon_benefit_hybrid = 0.55 * carbon_benefit_wood

        segment_ref = m.segment_reference_stock.get(building_type, 0.0)
        reference_bonus = 0.14 * m.reference_stock + 0.12 * segment_ref
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
            - p["risk_sensitivity"] * wood_risk
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
            - 0.65 * p["risk_sensitivity"] * hybrid_risk
            - 0.04 * m.concrete_lock_in
        )

        concrete_score = (
            0.10
            + 0.13 * m.concrete_lock_in
            - 0.12 * p["carbon_policy_strength"] * climate_weight * bt.get("climate_relevance", 1.0)
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
    """Education and workforce pipeline with vocational and higher-education channels.

    Version 0.8 separates:
    - youth attractiveness and adult attractiveness,
    - vocational education capacity and HE/engineering education capacity,
    - vocational workforce and engineering workforce.

    The old aggregate variables `workforce`, `education_capacity` and `attractiveness`
    are still updated as weighted summaries for compatibility with the rest of the model.
    """

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

        p = model.params
        self.vocational_pipeline = [
            0.0 for _ in range(p.get("vocational_education_delay_years", 3))
        ]
        self.he_pipeline = [
            0.0 for _ in range(p.get("he_education_delay_years", 4))
        ]

    def step(self):
        m = self.model
        p = m.params

        market_signal = 0.55 * m.wood_market_share + 0.30 * m.hybrid_market_share + 0.15 * m.reference_stock
        success_signal = max(0.0, m.trust_in_wood - p.get("trust_baseline", 0.28))
        training = p.get("industry_training_strength", 0.25)

        # Attractiveness: youth pipeline is more inert and starts lower;
        # adult pipeline reacts somewhat more to visible demand and reskilling opportunities.
        m.youth_attractiveness = clamp(
            m.youth_attractiveness
            + p.get("youth_attractiveness_success_impact", 0.020) * success_signal
            + 0.010 * p.get("education_investment", 0.30)
            + 0.006 * p.get("cluster_strength", 0.10)
            - p.get("attractiveness_decline_pressure", 0.010)
        )
        m.adult_attractiveness = clamp(
            m.adult_attractiveness
            + p.get("adult_attractiveness_success_impact", 0.030) * success_signal
            + 0.012 * p.get("education_investment", 0.30)
            + 0.008 * p.get("cluster_strength", 0.10)
            - 0.6 * p.get("attractiveness_decline_pressure", 0.010)
        )

        # Capacity responds slowly; weak attractiveness prevents full utilization.
        vocational_demand = (
            0.45 * m.youth_attractiveness
            + 0.35 * m.adult_attractiveness
            + 0.20 * market_signal
        )
        he_demand = (
            0.35 * m.youth_attractiveness
            + 0.35 * m.adult_attractiveness
            + 0.30 * market_signal
        )

        new_vocational_students = clamp(
            m.vocational_education_capacity
            * vocational_demand
            * (0.60 + 0.40 * p.get("education_investment", 0.30))
        )
        new_he_students = clamp(
            m.he_education_capacity
            * he_demand
            * (0.55 + 0.45 * p.get("education_investment", 0.30))
        )

        vocational_graduating = self.vocational_pipeline.pop(0) if self.vocational_pipeline else new_vocational_students
        he_graduating = self.he_pipeline.pop(0) if self.he_pipeline else new_he_students
        self.vocational_pipeline.append(new_vocational_students)
        self.he_pipeline.append(new_he_students)

        m.vocational_workforce = clamp(
            m.vocational_workforce
            + vocational_graduating
            + 0.025 * training * market_signal
            - p.get("retirement_pressure_vocational", 0.025)
        )
        m.engineering_workforce = clamp(
            m.engineering_workforce
            + he_graduating
            + 0.015 * training * market_signal
            - p.get("retirement_pressure_engineering", 0.030)
        )

        m.vocational_education_capacity = clamp(
            m.vocational_education_capacity
            + p.get("vocational_capacity_response_rate", 0.030)
            * (p.get("education_investment", 0.30) + 0.5 * market_signal + 0.3 * training)
            - 0.010 * (1 - m.youth_attractiveness)
        )
        m.he_education_capacity = clamp(
            m.he_education_capacity
            + p.get("he_capacity_response_rate", 0.020)
            * (p.get("education_investment", 0.30) + 0.5 * market_signal + 0.3 * training)
            - 0.012 * (1 - m.youth_attractiveness)
        )

        # Compatibility summaries.
        m.workforce = clamp(0.55 * m.vocational_workforce + 0.45 * m.engineering_workforce)
        m.education_capacity = clamp(0.60 * m.vocational_education_capacity + 0.40 * m.he_education_capacity)
        m.attractiveness = clamp(0.45 * m.youth_attractiveness + 0.55 * m.adult_attractiveness)


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
