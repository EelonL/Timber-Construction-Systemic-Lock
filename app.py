import copy
import pandas as pd
import streamlit as st
import altair as alt

from model import WoodConstructionLockInModel
from scenarios import SCENARIOS, get_params_for_scenario
from parameters import BUILDING_TYPES


st.set_page_config(
    page_title="TTS PuuSiirtymä",
    page_icon="🌲",
    layout="wide",
)

# --- TTS visual theme extracted from "TTS PowerPoint 2026.potx" ---
TTS_COLORS = {
    "blue": "#1973FF",
    "light_blue": "#8CB9FF",
    "turquoise": "#00E1BE",
    "light_turquoise": "#80F0DF",
    "pink": "#FF75E6",
    "dark_blue": "#0C397F",
    "orange": "#FF9533",
    "light_gray": "#EEEEEE",
    "white": "#FFFFFF",
}
TTS_CHART_COLORS = [
    TTS_COLORS["blue"],
    TTS_COLORS["turquoise"],
    TTS_COLORS["orange"],
    TTS_COLORS["pink"],
    TTS_COLORS["dark_blue"],
    TTS_COLORS["light_blue"],
    TTS_COLORS["light_turquoise"],
]

st.markdown(
    f"""
    <style>
    :root {{
        --tts-blue: {TTS_COLORS["blue"]};
        --tts-light-blue: {TTS_COLORS["light_blue"]};
        --tts-turquoise: {TTS_COLORS["turquoise"]};
        --tts-light-turquoise: {TTS_COLORS["light_turquoise"]};
        --tts-pink: {TTS_COLORS["pink"]};
        --tts-dark-blue: {TTS_COLORS["dark_blue"]};
        --tts-orange: {TTS_COLORS["orange"]};
        --tts-light-gray: {TTS_COLORS["light_gray"]};
    }}

    html, body, [class*="css"] {{
        font-family: "Satoshi", "Satoshi Medium", "Aptos", "Segoe UI", Arial, sans-serif;
        color: var(--tts-dark-blue);
    }}

    .stApp {{
        background: linear-gradient(180deg, #FFFFFF 0%, #F7FAFF 100%);
    }}

    h1, h2, h3 {{
        color: var(--tts-dark-blue);
        letter-spacing: -0.02em;
    }}

    h1 {{
        font-family: "Satoshi Medium", "Satoshi", "Aptos Display", "Segoe UI", Arial, sans-serif;
        font-weight: 700;
    }}

    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #F3F7FF 0%, #FFFFFF 100%);
        border-right: 1px solid #DDE9FF;
    }}

    div[data-testid="stMetric"] {{
        background: #FFFFFF;
        border: 1px solid #DDE9FF;
        border-left: 5px solid var(--tts-blue);
        border-radius: 16px;
        padding: 14px 16px;
        box-shadow: 0 6px 18px rgba(12, 57, 127, 0.06);
    }}

    div[data-testid="stMetricValue"] {{
        color: var(--tts-blue);
        font-weight: 700;
    }}

    div[data-testid="stExpander"] {{
        border: 1px solid #DDE9FF;
        border-radius: 14px;
        overflow: hidden;
        background: #FFFFFF;
    }}

    .stButton > button {{
        background: var(--tts-blue);
        color: white;
        border: 0;
        border-radius: 999px;
        font-weight: 700;
    }}

    .stButton > button:hover {{
        background: var(--tts-dark-blue);
        color: white;
    }}

    .stSlider [data-baseweb="slider"] > div {{
        color: var(--tts-blue);
    }}

    .stDataFrame {{
        border-radius: 14px;
        overflow: hidden;
    }}

    a {{
        color: var(--tts-blue);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def tts_line_chart(data: pd.DataFrame, height: int = 340):
    """Render a TTS-themed multi-line chart.

    Accepts the same wide dataframe format used by st.line_chart:
    index = x-axis, columns = series.
    """
    if data is None or data.empty:
        st.info("Ei näytettävää dataa.")
        return

    chart_data = data.copy()
    x_name = chart_data.index.name or "index"
    chart_data = chart_data.reset_index().rename(columns={chart_data.index.name or "index": x_name})
    long_df = chart_data.melt(id_vars=[x_name], var_name="Muuttuja", value_name="Arvo")

    chart = (
        alt.Chart(long_df)
        .mark_line(strokeWidth=3)
        .encode(
            x=alt.X(f"{x_name}:Q", title="Vuosi"),
            y=alt.Y("Arvo:Q", title=None),
            color=alt.Color(
                "Muuttuja:N",
                scale=alt.Scale(range=TTS_CHART_COLORS),
                legend=alt.Legend(title=None, orient="bottom"),
            ),
            tooltip=[
                alt.Tooltip(f"{x_name}:Q", title="Vuosi"),
                alt.Tooltip("Muuttuja:N", title="Muuttuja"),
                alt.Tooltip("Arvo:Q", title="Arvo", format=".3f"),
            ],
        )
        .properties(height=height)
        .configure_axis(
            labelColor=TTS_COLORS["dark_blue"],
            titleColor=TTS_COLORS["dark_blue"],
            gridColor="#E8EEF9",
        )
        .configure_view(strokeWidth=0)
        .configure_legend(labelColor=TTS_COLORS["dark_blue"])
    )
    st.altair_chart(chart, use_container_width=True)


st.title("🌲 TTS PuuSiirtymä")
st.caption(
    "Agenttipohjainen demonstraatiomalli puurakentamisen lukkiutumisesta ja mahdollisesta siirtymästä. "
    "Versio 0.9.1 käyttää TTS:n teemavärejä ja Satoshi-fonttiperhettä, jos fontti on saatavilla selaimessa."
)

RISK_LABELS = {
    "risk_competence": "Osaamisriski",
    "risk_regulatory_fire": "Sääntely- ja paloturvallisuusriski",
    "risk_cost_uncertainty": "Kustannusepävarmuus",
    "risk_supply_chain": "Toimitusketjuriski",
    "risk_moisture_technical": "Kosteus- ja tekninen riski",
    "risk_market_acceptance": "Markkina-/hyväksyttävyysriski",
}

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
    params["use_dynamic_carbon_policy"] = st.checkbox(
        "Käytä ajassa kiristyvää hiiliohjausta",
        value=bool(params.get("use_dynamic_carbon_policy", True))
    )
    if params["use_dynamic_carbon_policy"]:
        params["carbon_policy_initial_strength"] = st.slider(
            "Hiiliohjauksen alkuvaiheen voimakkuus",
            0.0, 1.0, float(params.get("carbon_policy_initial_strength", 0.25)), 0.05
        )
        params["carbon_policy_tightened_strength"] = st.slider(
            "Hiiliohjauksen kiristynyt voimakkuus",
            0.0, 1.0, float(params.get("carbon_policy_tightened_strength", 0.55)), 0.05
        )
        params["carbon_policy_tightening_year"] = st.slider(
            "Hiiliohjauksen kiristymisvuosi simulaatiossa",
            0, 20, int(params.get("carbon_policy_tightening_year", 3)), 1
        )
        params["carbon_policy_strength"] = params["carbon_policy_initial_strength"]
    else:
        params["carbon_policy_strength"] = st.slider(
            "Hiiliohjauksen voimakkuus",
            0.0, 1.0, float(params.get("carbon_policy_strength", 0.25)), 0.05
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
        "Puutuoteteollinen toimituskyvykkyys alussa",
        0.01, 1.0, float(params["initial_supplier_capacity"]), 0.01
    )
    params["initial_material_capacity"] = st.slider(
        "Rakentamiseen soveltuva puutuotekapasiteetti alussa",
        0.01, 1.0, float(params.get("initial_material_capacity", 0.35)), 0.01
    )
    params["initial_concrete_lock_in"] = st.slider(
        "Betonijärjestelmän lukkiutuminen alussa",
        0.0, 1.0, float(params["initial_concrete_lock_in"]), 0.05
    )

    with st.expander("Luottamuksen dynamiikka"):
        params["trust_ceiling"] = st.slider(
            "Luottamuksen yläraja",
            0.50, 0.95, float(params.get("trust_ceiling", 0.82)), 0.01
        )
        params["trust_baseline"] = st.slider(
            "Luottamuksen perustaso",
            0.00, 0.60, float(params.get("trust_baseline", 0.28)), 0.01
        )
        params["trust_decay"] = st.slider(
            "Luottamuksen palautuminen perustasoa kohti",
            0.000, 0.050, float(params.get("trust_decay", 0.012)), 0.001
        )

    with st.expander("Materiaalivirrat ja viennin houkuttelevuus"):
        st.caption("Nämä kuvaavat, kuinka paljon kotimainen puurakentaminen saa käyttöönsä rakentamiseen soveltuvaa puutuotekapasiteettia suhteessa vientiin, investointeihin ja kestävään raaka-ainerajaan.")
        params["max_material_capacity"] = st.slider(
            "Teollisen puutuotekapasiteetin realistinen yläraja",
            0.10, 1.00, float(params.get("max_material_capacity", 0.75)), 0.01
        )
        params["raw_material_limit"] = st.slider(
            "Raaka-aineen / kestävän puunkäytön yläraja",
            0.10, 1.00, float(params.get("raw_material_limit", 0.90)), 0.01
        )
        params["material_capacity_growth_rate"] = st.slider(
            "Puutuotekapasiteetin kasvunopeus",
            0.00, 0.15, float(params.get("material_capacity_growth_rate", 0.04)), 0.005
        )
        params["material_bottleneck_cost_impact"] = st.slider(
            "Pullonkaulan vaikutus kustannuksiin",
            0.00, 0.60, float(params.get("material_bottleneck_cost_impact", 0.20)), 0.01
        )
        params["material_bottleneck_risk_impact"] = st.slider(
            "Pullonkaulan vaikutus toimitusketjuriskiin",
            0.00, 0.60, float(params.get("material_bottleneck_risk_impact", 0.25)), 0.01
        )
        params["export_market_attractiveness"] = st.slider(
            "Vientimarkkinan houkuttelevuus",
            0.00, 1.00, float(params.get("export_market_attractiveness", 0.70)), 0.01
        )
        params["domestic_construction_price_premium"] = st.slider(
            "Kotimaisen rakentamisen maksama lisäarvo / hintapreemio",
            -0.20, 0.40, float(params.get("domestic_construction_price_premium", 0.00)), 0.01
        )
        params["domestic_demand_stability"] = st.slider(
            "Kotimaisen puurakentamiskysynnän ennustettavuus",
            0.00, 1.00, float(params.get("domestic_demand_stability", 0.30)), 0.01
        )
        params["export_reallocation_sensitivity"] = st.slider(
            "Viennistä kotimaahan allokoinnin herkkyys",
            0.00, 1.00, float(params.get("export_reallocation_sensitivity", 0.25)), 0.01
        )

    with st.expander("Koulutuksen vetovoima ja osaajaputki"):
        st.caption("Nämä kuvaavat puutuotealan koulutuksen pitkään kaventunutta vetovoimaa ja erillisiä ammatillisia sekä korkeakoulutason osaajaputkia.")
        params["initial_youth_attractiveness"] = st.slider(
            "Nuorten vetovoima alussa",
            0.00, 1.00, float(params.get("initial_youth_attractiveness", 0.18)), 0.01
        )
        params["initial_adult_attractiveness"] = st.slider(
            "Aikuisten / alanvaihtajien vetovoima alussa",
            0.00, 1.00, float(params.get("initial_adult_attractiveness", 0.32)), 0.01
        )
        params["initial_vocational_education_capacity"] = st.slider(
            "Ammatillisen koulutuksen kapasiteetti alussa",
            0.00, 1.00, float(params.get("initial_vocational_education_capacity", 0.28)), 0.01
        )
        params["initial_he_education_capacity"] = st.slider(
            "Korkeakoulu-/insinöörikoulutuksen kapasiteetti alussa",
            0.00, 1.00, float(params.get("initial_he_education_capacity", 0.12)), 0.01
        )
        params["initial_vocational_workforce"] = st.slider(
            "Ammatillinen osaajapohja alussa",
            0.00, 1.00, float(params.get("initial_vocational_workforce", 0.26)), 0.01
        )
        params["initial_engineering_workforce"] = st.slider(
            "Insinööri-/suunnitteluosaajapohja alussa",
            0.00, 1.00, float(params.get("initial_engineering_workforce", 0.14)), 0.01
        )
        params["industry_training_strength"] = st.slider(
            "Yritys–oppilaitosyhteistyö ja työelämäkoulutus",
            0.00, 1.00, float(params.get("industry_training_strength", 0.25)), 0.01
        )
        params["retirement_pressure_vocational"] = st.slider(
            "Ammatillisen osaajapohjan poistuma",
            0.00, 0.08, float(params.get("retirement_pressure_vocational", 0.025)), 0.001
        )
        params["retirement_pressure_engineering"] = st.slider(
            "Insinööriosaajapohjan poistuma",
            0.00, 0.08, float(params.get("retirement_pressure_engineering", 0.030)), 0.001
        )

    with st.expander("Riskikomponenttien painot"):
        st.caption("Painot määräävät, kuinka paljon kukin riskikomponentti vaikuttaa materiaalivalintaan.")
        params["risk_weight_competence"] = st.slider(
            "Osaamisriski", 0.0, 0.50, float(params["risk_weight_competence"]), 0.01
        )
        params["risk_weight_regulatory_fire"] = st.slider(
            "Sääntely- ja paloturvallisuusriski", 0.0, 0.50, float(params["risk_weight_regulatory_fire"]), 0.01
        )
        params["risk_weight_cost_uncertainty"] = st.slider(
            "Kustannusepävarmuus", 0.0, 0.50, float(params["risk_weight_cost_uncertainty"]), 0.01
        )
        params["risk_weight_supply_chain"] = st.slider(
            "Toimitusketjuriski", 0.0, 0.50, float(params["risk_weight_supply_chain"]), 0.01
        )
        params["risk_weight_moisture_technical"] = st.slider(
            "Kosteus- ja tekninen riski", 0.0, 0.50, float(params["risk_weight_moisture_technical"]), 0.01
        )
        params["risk_weight_market_acceptance"] = st.slider(
            "Markkina-/hyväksyttävyysriski", 0.0, 0.50, float(params["risk_weight_market_acceptance"]), 0.01
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
            bt["risk_multiplier"] = st.slider(
                f"Kokonaisriskikerroin: {bt_name}",
                0.40, 1.80, float(bt["risk_multiplier"]), 0.05,
                key=f"{bt_name}_risk_multiplier"
            )

    with st.expander("Lisäasetukset"):
        st.caption("Nämä kuvaavat päätöksenteon hajontaa ja satunnaisia kokeiluja. Niiden kannattaa olla pieniä, jotta ne eivät ohita kustannus-, riski- ja kapasiteettimekanismeja.")
        params["choice_temperature"] = st.slider(
            "Päätöksenteon hajonta",
            0.05, 0.40, float(params["choice_temperature"]), 0.01
        )
        params["wood_experiment_floor"] = st.slider(
            "Puun minimikokeiluosuus",
            0.0, 0.05, float(params["wood_experiment_floor"]), 0.001
        )
        params["hybrid_experiment_floor"] = st.slider(
            "Hybridin minimikokeiluosuus",
            0.0, 0.07, float(params["hybrid_experiment_floor"]), 0.001
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
    (name, tuple(sorted(data.items(), key=lambda x: x[0])))
    for name, data in sorted(building_types.items())
)
building_types_for_cache = tuple(
    (name, dict(items))
    for name, items in building_types_tuple
)

history, projects, segments = run_model_cached(params_tuple, building_types_for_cache)

latest = history.iloc[-1]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Puun osuus lopussa", f"{latest['wood_share']*100:.1f} %")
c2.metric("Puu + hybridi lopussa", f"{latest['wood_like_share']*100:.1f} %")
c3.metric("Luottamus puuhun", f"{latest['trust_in_wood']:.2f}")
c4.metric("Puutuoteteollinen toimituskyvykkyys", f"{latest['supplier_capacity']:.2f}")
c5.metric("Materiaalipullonkaula", f"{latest['material_bottleneck']:.2f}")

st.subheader("Koko simuloidun markkinan markkinaosuudet")
market_df = history.set_index("year")[["wood_share", "hybrid_share", "concrete_share"]]
market_df = market_df.rename(columns={
    "wood_share": "Puu",
    "hybrid_share": "Hybridi",
    "concrete_share": "Betoni"
})
tts_line_chart(market_df)

st.subheader("Hiiliohjauksen ja julkisen hankinnan ohjaus")
policy_df = history.set_index("year")[[
    "effective_carbon_policy_strength",
]]
policy_df = policy_df.rename(columns={
    "effective_carbon_policy_strength": "Efektiivinen hiiliohjauksen voimakkuus",
})
tts_line_chart(policy_df, height=220)

st.subheader("Materiaalivirrat ja puutuotekapasiteetin rajoite")
material_df = history.set_index("year")[[
    "wood_demand_pressure",
    "material_capacity",
    "effective_material_capacity_limit",
    "material_bottleneck",
    "material_capacity_utilization",
    "domestic_allocation_factor",
]]
material_df = material_df.rename(columns={
    "wood_demand_pressure": "Puutuotekysyntäpaine",
    "material_capacity": "Rakentamiseen soveltuva puutuotekapasiteetti",
    "effective_material_capacity_limit": "Efektiivinen kapasiteetin yläraja",
    "material_bottleneck": "Materiaalipullonkaula",
    "material_capacity_utilization": "Materiaalikapasiteetin käyttöaste",
    "domestic_allocation_factor": "Kotimaan allokaatiokerroin",
})
tts_line_chart(material_df)

st.subheader("Koulutuksen vetovoima ja osaajaputki")
education_df = history.set_index("year")[[
    "youth_attractiveness",
    "adult_attractiveness",
    "vocational_education_capacity",
    "he_education_capacity",
    "vocational_workforce",
    "engineering_workforce",
]]
education_df = education_df.rename(columns={
    "youth_attractiveness": "Nuorten vetovoima",
    "adult_attractiveness": "Aikuisten / alanvaihtajien vetovoima",
    "vocational_education_capacity": "Ammatillisen koulutuksen kapasiteetti",
    "he_education_capacity": "Korkeakoulu-/insinöörikoulutuksen kapasiteetti",
    "vocational_workforce": "Ammatillinen osaajapohja",
    "engineering_workforce": "Insinööri-/suunnitteluosaajapohja",
})
tts_line_chart(education_df)

st.subheader("Puun osuus rakennustyypeittäin")
wood_pivot = segments.pivot(index="year", columns="building_type", values="wood_share")
tts_line_chart(wood_pivot)

st.subheader("Puu + hybridi rakennustyypeittäin")
wood_like_pivot = segments.pivot(index="year", columns="building_type", values="wood_like_share")
tts_line_chart(wood_like_pivot)

st.subheader("Riskikomponentit koko markkinassa")
risk_cols = list(RISK_LABELS.keys())
risk_df = history.set_index("year")[risk_cols].rename(columns=RISK_LABELS)
tts_line_chart(risk_df)

st.subheader("Riskikomponentit rakennustyypeittäin")
selected_bt = st.selectbox(
    "Valitse rakennustyyppi riskikomponenttien tarkasteluun",
    sorted(segments["building_type"].unique())
)
seg_risk = segments[segments["building_type"] == selected_bt].set_index("year")[risk_cols].rename(columns=RISK_LABELS)
tts_line_chart(seg_risk)

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
    "risk_competence",
    "risk_regulatory_fire",
    "risk_cost_uncertainty",
    "risk_supply_chain",
    "risk_moisture_technical",
    "risk_market_acceptance",
]
st.dataframe(
    last_segments[display_cols].rename(columns={
        "building_type": "Rakennustyyppi",
        "projects": "Hankkeita",
        "segment_reference_stock": "Segmentin referenssivaranto",
        "avg_wood_cost_premium": "Puun kustannuslisä",
        "avg_wood_perceived_risk": "Puun koettu kokonaisriski",
        **RISK_LABELS,
    }),
    use_container_width=True,
)

st.subheader("Systeemin tilamuuttujat")
state_df = history.set_index("year")[[
    "trust_in_wood",
    "supplier_capacity",
    "material_capacity",
    "design_competence",
    "contractor_competence",
    "standardization",
    "regulatory_routine",
    "vocational_workforce",
    "engineering_workforce",
    "workforce",
    "concrete_lock_in",
]]
state_df = state_df.rename(columns={
    "trust_in_wood": "Luottamus puuhun",
    "supplier_capacity": "Puutuoteteollinen toimituskyvykkyys",
    "material_capacity": "Rakentamiseen soveltuva puutuotekapasiteetti",
    "design_competence": "Suunnitteluosaaminen",
    "contractor_competence": "Urakointi-/työmaaosaaminen",
    "standardization": "Standardointi",
    "regulatory_routine": "Viranomaisrutiini",
    "vocational_workforce": "Ammatillinen osaajapohja",
    "engineering_workforce": "Insinööri-/suunnitteluosaajapohja",
    "workforce": "Osaajapohja yhteensä",
    "concrete_lock_in": "Betonijärjestelmän lukkiutuminen",
})
tts_line_chart(state_df)

st.subheader("Puun kustannus-, riski- ja epäonnistumissignaalit")
basic_risk_df = history.set_index("year")[[
    "avg_wood_cost_premium",
    "avg_wood_perceived_risk",
    "wood_failure_rate",
]]
basic_risk_df = basic_risk_df.rename(columns={
    "avg_wood_cost_premium": "Puun keskim. kustannuslisä",
    "avg_wood_perceived_risk": "Koettu kokonaisriski",
    "wood_failure_rate": "Epäonnistumisaste",
})
tts_line_chart(basic_risk_df)

with st.expander("Näytä vuosittainen data"):
    st.dataframe(history, use_container_width=True)

with st.expander("Näytä rakennustyyppikohtainen data"):
    st.dataframe(segments, use_container_width=True)

with st.expander("Näytä hankeloki"):
    st.dataframe(projects, use_container_width=True)

st.subheader("Tulkinta")
st.markdown(
    """
Versio 0.5 jakaa tilaajien riskikokemuksen kuuteen osaan:

- **osaamisriski**: onko suunnittelijoilla, urakoitsijoilla ja työvoimalla riittävä osaaminen,
- **sääntely- ja paloturvallisuusriski**: ovatko lupakäytännöt, paloturvallisuus ja hyväksyntäprosessi ennakoitavia,
- **kustannusepävarmuus**: kuinka paljon hinta- ja riskipreemioita liittyy puuhun,
- **toimitusketjuriski**: riittääkö kapasiteetti ja onko toimittajakenttä luotettava,
- **kosteus- ja tekninen riski**: teknisen toteutuksen, kosteudenhallinnan ja kestävyyden epävarmuus,
- **markkina-/hyväksyttävyysriski**: tilaajien, käyttäjien, sijoittajien ja markkinan hyväksyntä.

Tämä tekee näkyväksi, että puurakentamisen jarru ei ole vain yksi 'riski', vaan useiden riskien yhdistelmä. Eri skenaariot voivat pienentää eri riskikomponentteja eri tahtiin.

Versio 0.7 lisää tähän materiaalivirran rajoitteen: jos puutuotekysyntä kasvaa nopeammin kuin rakentamiseen soveltuva kapasiteetti, kustannusepävarmuus ja toimitusketjuriski kasvavat. Vientimarkkinan houkuttelevuus voi hidastaa kapasiteetin ohjautumista kotimaiseen rakentamiseen.
"""
)

st.info(
    "Version 0.9: malliin lisättiin ajassa kiristyvä hiiliohjaus ja tarkennettiin julkisen hankinnan rakennustyyppikohtaista vaikutusta.  Riskikomponenttien lähtöarvot ja painot ovat tutkimuksella perusteltuja alustavia malliarvoja. "
    "Ne kannattaa kalibroida asiantuntijahaastatteluilla ja rakennustyyppikohtaisella evidenssillä."
)
