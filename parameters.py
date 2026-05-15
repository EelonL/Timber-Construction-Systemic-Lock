"""
Default parameters for TTS PuuSiirtymä.

All values are intentionally approximate and normalized.
The model is meant for exploring mechanisms and scenarios, not forecasting.
"""

DEFAULT_PARAMS = {
    # Simulation
    "years": 25,
    "random_seed": 42,
    "projects_per_year": 120,

    # Initial market shares
    "initial_wood_share": 0.05,
    "initial_hybrid_share": 0.10,

    # Initial system states, 0..1
    "initial_trust_in_wood": 0.30,
    "initial_design_competence": 0.28,
    "initial_contractor_competence": 0.25,
    "initial_supplier_capacity": 0.15,
    "initial_standardization": 0.22,
    "initial_regulatory_routine": 0.22,
    "initial_education_capacity": 0.25,
    "initial_workforce": 0.25,
    "initial_attractiveness": 0.28,
    "initial_concrete_lock_in": 0.80,

    # Cost and risk
    "wood_base_cost_premium": 0.08,
    "hybrid_base_cost_premium": 0.035,
    "capacity_shortage_penalty": 0.18,
    "risk_sensitivity": 0.55,
    "cost_sensitivity": 0.60,
    "climate_sensitivity": 0.45,

    # Choice model
    # Larger temperature = more exploration / less deterministic choice.
    "choice_temperature": 0.35,
    "wood_experiment_floor": 0.025,
    "hybrid_experiment_floor": 0.04,
    "min_supplier_capacity": 0.05,

    # Policy levers, 0..1
    "public_procurement_strength": 0.25,
    "carbon_policy_strength": 0.20,
    "education_investment": 0.30,
    "standardization_investment": 0.25,
    "supplier_investment_support": 0.20,
    "cluster_strength": 0.10,

    # Learning and forgetting
    "learning_rate": 0.08,
    "standardization_learning_rate": 0.06,
    "trust_success_impact": 0.04,
    "trust_failure_impact": 0.14,
    "competence_decay": 0.006,
    "lock_in_decay_from_wood": 0.025,

    # Project outcome probabilities
    "base_failure_probability_wood": 0.10,
    "base_failure_probability_hybrid": 0.07,
    "failure_reduction_from_competence": 0.07,
    "failure_reduction_from_standardization": 0.05,

    # Supplier dynamics
    "capacity_investment_threshold": 0.55,
    "capacity_learning_rate": 0.07,
    "capacity_depreciation": 0.007,
    "max_capacity_growth_per_year": 0.09,

    # Education dynamics
    "education_delay_years": 3,
    "education_response_rate": 0.05,
    "attractiveness_success_impact": 0.03,
    "attractiveness_failure_impact": 0.06,

    # Developer mix
    "share_public_developers": 0.35,
    "share_pioneer_developers": 0.15,
    "share_conservative_developers": 0.50,

    # Developer preference baselines
    "public_climate_weight": 0.55,
    "private_climate_weight": 0.25,
    "pioneer_bonus": 0.18,
    "conservative_risk_extra": 0.12,

    # Business cycle
    "cycle_amplitude": 0.15,
    "cycle_period_years": 8,
}
