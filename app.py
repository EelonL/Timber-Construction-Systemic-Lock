import copy
import pandas as pd
import streamlit as st

from model import WoodConstructionLockInModel
from scenarios import SCENARIOS, get_params_for_scenario
from parameters import BUILDING_TYPES


st.set_page_config(
    page_title="TTS PuuSiirtymä",
    page_icon="🌲",
    layout="wide",
)

st.title("🌲 TTS PuuSiirtymä")
st.caption(
    "Agenttipohjainen demonstraatiomalli puurakentamisen lukkiutumisesta ja mahdollisesta siirtymästä. "
    "Versio 0.3 erottaa rakennustyypit, jotta siirtymää voidaan tarkastella segmenteittäin."
)

with st.sidebar:
    st.header("Skenaario")
    scenario_name = st.selectbox("Valitse skenaario", list(SCENARIOS.keys()))
    st.write(SCENARIOS[scenario_name]["description"])

    st.divider()
    st.header("Perusasetukset")

    params = get_params_for_scenario(scenario_name)
    building_types = copy.deepcopy(BUILDING_TYPES)

    params["years"] = st.slider("Simulaation pituus, vuotta", 5, 50, int(params["years"]))
    params["projects_per_year"] = st.slider("Simuloituja rakennushankkeita vuodessa", 20, 500, int(params["projects_per_year"]), step=10)
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

    params["initial_supplier_capacity"] = st.slider(
        "Puutuoteteollinen kapasiteetti alussa",
        0.01, 1.0, float(params["initial_supplier_capacity"]), 0.01
    )
    params["initial_concrete_lock_in"] = st.slider(
        "Betonijärjestelmän lukkiutuminen alussa",
        0.0, 1.0, float(params["initial_concrete_lock_in"]), 0.05
    )

    with st.expander("Rakennustyyppien lähtöosuudet"):
        st.caption(
            "Nämä ovat alustavia malliarvoja. Ne kannattaa myöhemmin kalibroida tilastoilla."
        )
        for bt_name, bt in building_types.items():
            st.markdown(f"**{bt_name}**")
            bt["initial_wood_share"] = st.slider(
                f"Puun lähtöosuus: {bt_name}",
                0.0, 1.0, float(bt["initial_wood_share"]), 0.01,
                key=f"{bt_name}_wood"
            )
            bt["initial_hybrid_share"] = st.slider(
                f"Hybridin lähtöosuus: {bt_name}",
                0.0, 1.0, float(bt["initial_hybrid_share"]), 0.01,
                key=f"{bt_name}_hybrid"
            )
            bt["project_share"] = st.slider(
                f"Hanketyypin osuus simuloidusta markkinasta: {bt_name}",
                0.01, 0.60, float(bt["project_share"]), 0.01,
                key=f"{bt_name}_project_share"
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
def run_model_cached(params_tuple, building_types_tuple):
    params = dict(params_tuple)
    building_types = {k: dict(v) for k, v in building_types_tuple}
    model = WoodConstructionLockInModel(params=params, building_types=building_types)
    history = model.run(params["years"])
    projects = model.project_dataframe()
    segments = model.segment_dataframe()
    return history, projects, segments


params_tuple = tuple(sorted(params.items()))
building_types_tuple = tuple(
    (name, tuple(sorted(data.items())))
    for name, data in sorted(building_types.items())
)
# Convert nested tuple back-friendly before caching call
building_types_for_cache = tuple(
    (name, dict(items))
    for name, items in building_types_tuple
)

history, projects, segments = run_model_cached(params_tuple, building_types_for_cache)

latest = history.iloc[-1]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Puun osuus lopussa", f"{latest['wood_share']*100:.1f} %")
c2.metric("Puu + hybridi lopussa", f"{latest['wood_like_share']*100:.1f} %")
c3.metric("Luottamus puuhun", f"{latest['trust_in_wood']:.2f}")
c4.metric("Puutuoteteollinen kapasiteetti", f"{latest['supplier_capacity']:.2f}")

st.subheader("Koko simuloidun markkinan markkinaosuudet")
market_df = history.set_index("year")[["wood_share", "hybrid_share", "concrete_share"]]
market_df = market_df.rename(columns={
    "wood_share": "Puu",
    "hybrid_share": "Hybridi",
    "concrete_share": "Betoni"
})
st.line_chart(market_df)

st.subheader("Puun osuus rakennustyypeittäin")
wood_pivot = segments.pivot(index="year", columns="building_type", values="wood_share")
st.line_chart(wood_pivot)

st.subheader("Puu + hybridi rakennustyypeittäin")
wood_like_pivot = segments.pivot(index="year", columns="building_type", values="wood_like_share")
st.line_chart(wood_like_pivot)

st.subheader("Rakennustyyppien lopputilanne")
last_year = segments["year"].max()
last_segments = segments[segments["year"] == last_year].copy()
last_segments["Puu %"] = last_segments["wood_share"] * 100
last_segments["Hybridi %"] = last_segments["hybrid_share"] * 100
last_segments["Puu + 0.5 × hybridi %"] = last_segments["wood_like_share"] * 100
last_segments["Betoni %"] = last_segments["concrete_share"] * 100

display_cols = [
    "building_type",
    "projects",
    "Puu %",
    "Hybridi %",
    "Puu + 0.5 × hybridi %",
    "Betoni %",
    "segment_reference_stock",
    "avg_wood_cost_premium",
    "avg_wood_perceived_risk",
]
st.dataframe(
    last_segments[display_cols].rename(columns={
        "building_type": "Rakennustyyppi",
        "projects": "Hankkeita",
        "segment_reference_stock": "Segmentin referenssivaranto",
        "avg_wood_cost_premium": "Puun kustannuslisä",
        "avg_wood_perceived_risk": "Puun koettu riski",
    }),
    use_container_width=True,
)

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

with st.expander("Näytä rakennustyyppikohtainen data"):
    st.dataframe(segments, use_container_width=True)

with st.expander("Näytä hankeloki"):
    st.dataframe(projects, use_container_width=True)

st.subheader("Tulkinta")
st.markdown(
    """
Versio 0.3 erottaa rakennustyypit. Tämä on tärkeää, koska puurakentaminen ei ole samassa asemassa eri segmenteissä:

- pienkerrostaloissa puu voi olla jo varsin vahva,
- opetusrakennuksissa ja julkisissa hankkeissa poliittinen ohjaus voi vaikuttaa paljon,
- kerrostaloissa betonijärjestelmän lukkiutuminen, riskit ja kustannuspaineet ovat vahvempia,
- toimitila- ja teollisuusrakentamisessa päätöksenteko voi olla enemmän kustannus- ja toimivuusperusteista.

Mallin tarkoitus ei ole ennustaa todellisia markkinaosuuksia, vaan tutkia, missä segmenteissä siirtymä voisi syntyä ja missä lukkiutuminen säilyy.
"""
)

st.info(
    "Version 0.3: rakennustyyppien lähtöarvot ovat alustavia ja kannattaa kalibroida tilastoilla. "
    "Seuraava askel voisi olla todellisen markkinaosuusdatan ja hankemäärien lisääminen rakennustyypeittäin."
)
