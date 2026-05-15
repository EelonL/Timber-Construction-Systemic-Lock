from copy import deepcopy
from parameters import DEFAULT_PARAMS

SCENARIOS = {
    "Nykykehitys": {
        "description": "Pehmeää ohjelmaohjausta, satunnaisia pilotteja ja maltillista koulutuskehitystä.",
        "updates": {},
    },
    "Koulutuspanostus": {
        "description": "Lisätään koulutusta, opettajien osaamista ja työvoimavirtaa, mutta kysyntä ja kapasiteetti muuttuvat vain hitaasti.",
        "updates": {
            "education_investment": 0.80,
            "education_response_rate": 0.08,
            "initial_education_capacity": 0.40,
            "initial_workforce": 0.35,
        },
    },
    "Julkinen kysyntäveturi": {
        "description": "Julkiset tilaajat painottavat puuta ja hybridiratkaisuja erityisesti kouluissa, päiväkodeissa ja muissa julkisissa hankkeissa.",
        "updates": {
            "public_procurement_strength": 0.65,
            "share_public_developers": 0.45,
            "wood_experiment_floor": 0.015,
            "hybrid_experiment_floor": 0.025,
        },
    },
    "Kysyntä + kapasiteettituki": {
        "description": "Julkinen kysyntä yhdistyy teollisen kapasiteetin ja standardoinnin tukeen.",
        "updates": {
            "public_procurement_strength": 0.65,
            "supplier_investment_support": 0.75,
            "standardization_investment": 0.70,
            "cluster_strength": 0.30,
            "wood_experiment_floor": 0.015,
            "hybrid_experiment_floor": 0.025,
        },
    },
    "Hiiliohjaus": {
        "description": "Vähähiilisyys vaikuttaa aidosti tarjousvertailuun ja materiaalivalintoihin.",
        "updates": {
            "carbon_policy_initial_strength": 0.30,
            "carbon_policy_tightened_strength": 0.60,
            "carbon_policy_tightening_year": 3,
            "climate_sensitivity": 0.40,
            "wood_experiment_floor": 0.012,
            "hybrid_experiment_floor": 0.022,
        },
    },
    "Alueellinen klusteri": {
        "description": "Tilaajat, viranomaiset, oppilaitokset, suunnittelijat ja toimittajat oppivat samassa ekosysteemissä.",
        "updates": {
            "cluster_strength": 0.50,
            "standardization_investment": 0.65,
            "supplier_investment_support": 0.55,
            "education_investment": 0.65,
            "public_procurement_strength": 0.50,
            "choice_temperature": 0.24,
            "wood_experiment_floor": 0.020,
            "hybrid_experiment_floor": 0.030,
        },
    },
    "Negatiivinen shokki": {
        "description": "Yksi näkyvä epäonnistuminen heikentää luottamusta ja alan mainetta simulaation keskivaiheilla.",
        "updates": {
            "shock_year": 8,
            "shock_strength": 0.25,
        },
    },
}


def get_params_for_scenario(name: str) -> dict:
    params = deepcopy(DEFAULT_PARAMS)
    params.update(SCENARIOS[name]["updates"])
    return params
