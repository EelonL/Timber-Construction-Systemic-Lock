"""
Default parameters for TTS PuuSiirtymä.

Version 0.5 adds explicit perceived-risk components.
All values are intentionally approximate and normalized.
The model is meant for exploring mechanisms and scenarios, not forecasting.
"""

BUILDING_TYPES = {
    "Kerrostalot": {
        "project_share": 0.28,
        "initial_wood_share": 0.02,
        "initial_hybrid_share": 0.05,
        "wood_base_cost_premium": 0.06,
        "base_failure_probability_wood": 0.12,
        "base_failure_probability_hybrid": 0.08,
        "risk_multiplier": 1.25,
        "public_share": 0.15,
        "climate_relevance": 1.00,
        "policy_relevance": 0.60,
        "capacity_intensity": 1.25,
        "risk_components": {
            "competence": 0.68,
            "regulatory_fire": 0.72,
            "cost_uncertainty": 0.58,
            "supply_chain": 0.56,
            "moisture_technical": 0.48,
            "market_acceptance": 0.62,
        },
    },
    "Pienkerrostalot": {
        "project_share": 0.10,
        "initial_wood_share": 0.45,
        "initial_hybrid_share": 0.10,
        "wood_base_cost_premium": 0.02,
        "base_failure_probability_wood": 0.07,
        "base_failure_probability_hybrid": 0.05,
        "risk_multiplier": 0.75,
        "public_share": 0.20,
        "climate_relevance": 0.80,
        "policy_relevance": 0.50,
        "capacity_intensity": 0.70,
        "risk_components": {
            "competence": 0.32,
            "regulatory_fire": 0.30,
            "cost_uncertainty": 0.30,
            "supply_chain": 0.34,
            "moisture_technical": 0.34,
            "market_acceptance": 0.28,
        },
    },
    "Opetusrakennukset": {
        "project_share": 0.14,
        "initial_wood_share": 0.28,
        "initial_hybrid_share": 0.10,
        "wood_base_cost_premium": 0.04,
        "base_failure_probability_wood": 0.08,
        "base_failure_probability_hybrid": 0.06,
        "risk_multiplier": 0.90,
        "public_share": 0.85,
        "climate_relevance": 1.00,
        "policy_relevance": 1.00,
        "capacity_intensity": 0.90,
        "risk_components": {
            "competence": 0.46,
            "regulatory_fire": 0.50,
            "cost_uncertainty": 0.42,
            "supply_chain": 0.40,
            "moisture_technical": 0.45,
            "market_acceptance": 0.34,
        },
    },
    "Julkiset rakennukset muut": {
        "project_share": 0.16,
        "initial_wood_share": 0.16,
        "initial_hybrid_share": 0.10,
        "wood_base_cost_premium": 0.05,
        "base_failure_probability_wood": 0.09,
        "base_failure_probability_hybrid": 0.06,
        "risk_multiplier": 0.95,
        "public_share": 0.90,
        "climate_relevance": 0.95,
        "policy_relevance": 1.00,
        "capacity_intensity": 0.90,
        "risk_components": {
            "competence": 0.50,
            "regulatory_fire": 0.52,
            "cost_uncertainty": 0.46,
            "supply_chain": 0.42,
            "moisture_technical": 0.46,
            "market_acceptance": 0.38,
        },
    },
    "Teollisuusrakennukset": {
        "project_share": 0.16,
        "initial_wood_share": 0.08,
        "initial_hybrid_share": 0.10,
        "wood_base_cost_premium": 0.04,
        "base_failure_probability_wood": 0.07,
        "base_failure_probability_hybrid": 0.05,
        "risk_multiplier": 0.85,
        "public_share": 0.10,
        "climate_relevance": 0.70,
        "policy_relevance": 0.40,
        "capacity_intensity": 0.75,
        "risk_components": {
            "competence": 0.40,
            "regulatory_fire": 0.38,
            "cost_uncertainty": 0.42,
            "supply_chain": 0.45,
            "moisture_technical": 0.36,
            "market_acceptance": 0.34,
        },
    },
    "Toimitilat": {
        "project_share": 0.16,
        "initial_wood_share": 0.08,
        "initial_hybrid_share": 0.15,
        "wood_base_cost_premium": 0.06,
        "base_failure_probability_wood": 0.09,
        "base_failure_probability_hybrid": 0.06,
        "risk_multiplier": 1.00,
        "public_share": 0.20,
        "climate_relevance": 0.90,
        "policy_relevance": 0.50,
        "capacity_intensity": 1.00,
        "risk_components": {
            "competence": 0.50,
            "regulatory_fire": 0.48,
            "cost_uncertainty": 0.52,
            "supply_chain": 0.48,
            "moisture_technical": 0.42,
            "market_acceptance": 0.52,
        },
    },
}


DEFAULT_PARAMS = {
    # Simulation
    "years": 25,
    "random_seed": 42,
    "projects_per_year": 120,

    # Initial system states, 0..1
    "initial_trust_in_wood": 0.30,
    "initial_design_competence": 0.28,
    "initial_contractor_competence": 0.25,
    "initial_supplier_capacity": 0.15,
    "initial_standardization": 0.22,
    "initial_regulatory_routine": 0.22,
    "initial_education_capacity": 0.20,
    "initial_workforce": 0.20,
    "initial_attractiveness": 0.25,
    "initial_concrete_lock_in": 0.80,

    # Trust dynamics
    "trust_ceiling": 0.82,
    "trust_baseline": 0.28,
    "trust_decay": 0.012,

    # Risk component weights.
    # These weights are derived from the literature logic:
    # competence and regulation/fire are usually the most prominent perceived risks.
    "risk_weight_competence": 0.25,
    "risk_weight_regulatory_fire": 0.22,
    "risk_weight_cost_uncertainty": 0.18,
    "risk_weight_supply_chain": 0.14,
    "risk_weight_moisture_technical": 0.11,
    "risk_weight_market_acceptance": 0.10,

    # Cost and risk; can be modified by building type
    "wood_base_cost_premium": 0.08,
    "hybrid_base_cost_premium": 0.035,
    "capacity_shortage_penalty": 0.18,
    "risk_sensitivity": 0.65,
    "cost_sensitivity": 0.60,
    "climate_sensitivity": 0.40,

    # Choice model
    "choice_temperature": 0.18,
    "wood_experiment_floor": 0.005,
    "hybrid_experiment_floor": 0.010,
    "min_supplier_capacity": 0.05,

    # Policy levers, 0..1
    "public_procurement_strength": 0.25,

    # Carbon policy, v0.9.
    # One simulation step is interpreted as one year.
    # If year 0 is 2026, tightening_year=3 roughly corresponds to 2029.
    "carbon_policy_strength": 0.25,  # legacy / UI fallback
    "carbon_policy_initial_strength": 0.25,
    "carbon_policy_tightened_strength": 0.55,
    "carbon_policy_tightening_year": 3,
    "use_dynamic_carbon_policy": True,

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

    # Project outcome probabilities; can be modified by building type
    "base_failure_probability_wood": 0.10,
    "base_failure_probability_hybrid": 0.07,
    "failure_reduction_from_competence": 0.07,
    "failure_reduction_from_standardization": 0.05,

    # Supplier dynamics
    "capacity_investment_threshold": 0.55,
    "capacity_learning_rate": 0.07,
    "capacity_depreciation": 0.007,
    "max_capacity_growth_per_year": 0.09,

    # Material flow and production constraints.
    # These are normalized 0..1 indicators, not physical cubic-metre values yet.
    "initial_material_capacity": 0.35,
    "max_material_capacity": 0.75,
    "raw_material_limit": 0.90,
    "material_capacity_growth_rate": 0.04,
    "material_capacity_depreciation": 0.005,
    "material_bottleneck_cost_impact": 0.20,
    "material_bottleneck_risk_impact": 0.25,

    # Market-volume scaling, v1.0.
    # projects_per_year is a simulation sample size.
    # annual_market_volume_index scales the real market volume represented by the sample.
    "annual_market_volume_index": 1.00,
    "wood_project_material_intensity": 1.00,
    "hybrid_project_material_intensity": 0.40,

    # Export/domestic allocation logic.
    "export_market_attractiveness": 0.70,
    "domestic_construction_price_premium": 0.00,
    "export_reallocation_sensitivity": 0.25,
    "domestic_demand_stability": 0.30,

    # Education dynamics: legacy aggregate values kept for compatibility.
    "education_delay_years": 3,
    "education_response_rate": 0.05,
    "attractiveness_success_impact": 0.03,
    "attractiveness_failure_impact": 0.06,

    # Education and workforce pipeline, v0.8.
    # These reflect a long-term declining attractiveness and narrowed education pipeline.
    "initial_youth_attractiveness": 0.18,
    "initial_adult_attractiveness": 0.32,
    "initial_vocational_education_capacity": 0.28,
    "initial_he_education_capacity": 0.12,
    "initial_vocational_workforce": 0.26,
    "initial_engineering_workforce": 0.14,

    "vocational_education_delay_years": 3,
    "he_education_delay_years": 4,
    "retirement_pressure_vocational": 0.025,
    "retirement_pressure_engineering": 0.030,
    "industry_training_strength": 0.25,

    # How strongly market success and visible career prospects affect attractiveness.
    "youth_attractiveness_success_impact": 0.020,
    "adult_attractiveness_success_impact": 0.030,
    "attractiveness_decline_pressure": 0.010,

    # How strongly education capacity can respond to demand and investment.
    "vocational_capacity_response_rate": 0.030,
    "he_capacity_response_rate": 0.020,

    # Developer mix. In v0.3+ building types also have public_share, so this is a fallback.
    "share_public_developers": 0.35,
    "share_pioneer_developers": 0.15,
    "share_conservative_developers": 0.50,

    # Developer preference baselines
    "public_climate_weight": 0.55,
    "private_climate_weight": 0.20,
    "pioneer_bonus": 0.18,
    "conservative_risk_extra": 0.15,

    # Business cycle
    "cycle_amplitude": 0.15,
    "cycle_period_years": 8,
}
