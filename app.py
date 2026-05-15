import pandas as pd
import streamlit as st

from model import WoodConstructionLockInModel
from scenarios import SCENARIOS, get_params_for_scenario


st.set_page_config(
    page_title="TTS PuuSiirtymä",
    page_icon="🌲",
    layout="wide",
)

st.title("🌲 TTS PuuSiirtymä")
st.caption(
    "Agenttipohjainen demonstraatiomalli puurakentamisen lukkiutumisesta ja mahdollisesta siirtymästä. "
    "Malli ei ennusta todellista markkinaosuutta, vaan tekee näkyväksi systeemisiä takaisinkytkentöjä."
)

with st.sidebar:
    st.header("Skenaario")
    scenario_name = st.selectbox("Valitse skenaario", list(SCENARIOS.keys()))
    st.write(SCENARIOS[scenario_name]["description"])

    st.divider()
    st.header("Perusasetukset")

    params = get_params_for_scenario(scenario_name)

    params["years"] = st.slider("Simulaation pituus, vuotta", 5, 50, int(params["years"]))
    params["projects_per_year"] = st.slider("Hankkeita vuodessa", 20, 500, int(params["projects_per_year"]), step=10)
    params["random_seed"] = st.number_input("Satunnaissiemen", value=int(params["random_seed"]), step=1)

    st.divider()
    st.header("Politiikka- ja kehitysvivut")

    params["public_procurement_strength"] = st.slider(
        "Julkinen kysyntä / hankintapaine",
        0.0, 1.0, float(params["public_procurement_strength"]), 0.05
    )
    params["carbon_policy_strength"] = st.slider(
        "Hiiliohjauksen voimakkuus",
        0.0, 1.0, float(params["carbon_policy_strength"]), 0.05
    )
    params["education_investment"] = st.slider(
        "Koulutuspanostus",
        0.0, 1.0, float(params["education_investment"]), 0.05
    )
    params["standardization_investment"] = st.slider(
        "Standardointi ja vakioratkaisut",
        0.0, 1.0, float(params["standardization_investment"]), 0.05
    )
    params["supplier_investment_support"] = st.slider(
        "Teollisen kapasiteetin tuki",
        0.0, 1.0, float(params["supplier_investment_support"]), 0.05
    )
    params["cluster_strength"] = st.slider(
        "Alueellinen klusteri / yhteisoppiminen",
        0.0, 1.0, float(params["cluster_strength"]), 0.05
    )

    st.divider()
    st.header("Lähtötilanne")

    params["initial_wood_share"] = st.slider(
        "Puun lähtöosuus",
        0.0, 0.50, float(params["initial_wood_share"]), 0.01
    )
    params["initial_hybrid_share"] = st.slider(
        "Hybridien lähtöosuus",
        0.0, 0.50, float(params["initial_hybrid_share"]), 0.01
    )
    params["wood_base_cost_premium"] = st.slider(
        "Puun lähtökustannuslisä",
        -0.10, 0.30, float(params["wood_base_cost_premium"]), 0.01
    )
    params["initial_supplier_capacity"] = st.slider(
        "Puutuoteteollinen kapasiteetti alussa",
        0.01, 1.0, float(params["initial_supplier_capacity"]), 0.01
    )
    params["initial_concrete_lock_in"] = st.slider(
        "Betonijärjestelmän lukkiutuminen alussa",
        0.0, 1.0, float(params["initial_concrete_lock_in"]), 0.05
    )

    with st.expander("Lisäasetukset"):
        params["choice_temperature"] = st.slider(
            "Materiaalivalinnan satunnaisuus / kokeiluhalukkuus",
            0.05, 0.80, float(params["choice_temperature"]), 0.05
        )
        params["wood_experiment_floor"] = st.slider(
            "Puun minimikokeiluosuus",
            0.0, 0.15, float(params["wood_experiment_floor"]), 0.005
        )
        params["hybrid_experiment_floor"] = st.slider(
            "Hybridin minimikokeiluosuus",
            0.0, 0.20, float(params["hybrid_experiment_floor"]), 0.005
        )


@st.cache_data(show_spinner=False)
def run_model_cached(params_tuple):
    params = dict(params_tuple)
    model = WoodConstructionLockInModel(params=params)
    history = model.run(params["years"])
    projects = model.project_dataframe()
    return history, projects


params_tuple = tuple(sorted(params.items()))
history, projects = run_model_cached(params_tuple)

latest = history.iloc[-1]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Puun osuus lopussa", f"{latest['wood_share']*100:.1f} %")
c2.metric("Puu + hybridi lopussa", f"{latest['wood_like_share']*100:.1f} %")
c3.metric("Luottamus puuhun", f"{latest['trust_in_wood']:.2f}")
c4.metric("Puutuoteteollinen kapasiteetti", f"{latest['supplier_capacity']:.2f}")

st.subheader("Markkinaosuudet ajan yli")
market_df = history.set_index("year")[["wood_share", "hybrid_share", "concrete_share"]]
market_df = market_df.rename(columns={
    "wood_share": "Puu",
    "hybrid_share": "Hybridi",
    "concrete_share": "Betoni"
})
st.line_chart(market_df)

st.subheader("Systeemin tilamuuttujat")
state_df = history.set_index("year")[[
    "trust_in_wood",
    "supplier_capacity",
    "design_competence",
    "contractor_competence",
    "standardization",
    "regulatory_routine",
    "workforce",
    "concrete_lock_in",
]]
state_df = state_df.rename(columns={
    "trust_in_wood": "Luottamus puuhun",
    "supplier_capacity": "Puutuoteteollinen kapasiteetti",
    "design_competence": "Suunnitteluosaaminen",
    "contractor_competence": "Urakointi-/työmaaosaaminen",
    "standardization": "Standardointi",
    "regulatory_routine": "Viranomaisrutiini",
    "workforce": "Osaajapohja",
    "concrete_lock_in": "Betonijärjestelmän lukkiutuminen",
})
st.line_chart(state_df)

st.subheader("Puun kustannus-, riski- ja epäonnistumissignaalit")
risk_df = history.set_index("year")[[
    "avg_wood_cost_premium",
    "avg_wood_perceived_risk",
    "wood_failure_rate",
]]
risk_df = risk_df.rename(columns={
    "avg_wood_cost_premium": "Puun keskim. kustannuslisä",
    "avg_wood_perceived_risk": "Koettu riski",
    "wood_failure_rate": "Epäonnistumisaste",
})
st.line_chart(risk_df)

with st.expander("Näytä vuosittainen data"):
    st.dataframe(history, use_container_width=True)

with st.expander("Näytä hankeloki"):
    st.dataframe(projects, use_container_width=True)

st.subheader("Tulkinta")
st.markdown(
    """
Tässä mallissa puurakentaminen pääsee kasvu-uralle vain, jos useampi mekanismi vahvistuu samaan aikaan:

- kysyntä tuottaa referenssejä ja oppimista,
- oppiminen pienentää koettua riskiä,
- standardointi pienentää kustannuslisää,
- kapasiteetti kasvaa, kun kysyntä on riittävän ennustettavaa,
- koulutus tuottaa osaajia viiveellä,
- julkinen kysyntä ja hiiliohjaus voivat siirtää rakennuttajien päätöskynnystä.

Version 0.2 muutos: materiaalivalinta on todennäköisyyspohjainen, ei puhdas voittaja-vie-kaiken-valinta. 
Siksi myös lukkiutuneessa järjestelmässä voi syntyä pieni määrä puu- ja hybridirakentamisen kokeiluja.
"""
)

st.info(
    "Version 0.2: parametrien arvot ovat edelleen alustavia. Seuraava askel olisi validoida parametreja asiantuntijahaastatteluilla "
    "ja lisätä erilliset rakennustyypit, esimerkiksi koulut, päiväkodit, kerrostalot ja toimitilat."
)
