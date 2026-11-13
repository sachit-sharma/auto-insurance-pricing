"""Gross-premium estimator dashboard.

Launch with: streamlit run app/streamlit_app.py  (from the project root,
after `pip install streamlit` into the env that has pandas — see
docs/streamlit_dashboard.md)
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import premium_calculator as pc

st.set_page_config(page_title="Auto Insurance Pricing", page_icon="🚗")
st.title("Auto Insurance Pricing — Gross Premium Estimator")


@st.cache_resource
def get_artifacts():
    return pc.load_artifacts()


try:
    config, freq_rating, sev_rating = get_artifacts()
except FileNotFoundError:
    st.error(
        "Rating-table artifacts not found under `data/processed/`. Run the notebook's "
        "export cells (see docs/streamlit_dashboard.md) before launching this app."
    )
    st.stop()

territory_options = list(config["territory_labels"].values())

st.sidebar.header("Policy characteristics")
age = st.sidebar.slider("Policyholder age", 18, 95, 40)
bonus_malus = st.sidebar.slider("Bonus-malus level", 0, 22, 5)
horsepower = st.sidebar.slider("Horsepower (kW)", 10, 243, 60)
vehicle_age = st.sidebar.slider("Vehicle age (years)", 0, 48, 3)
territory_label = st.sidebar.selectbox("Territory", territory_options)
fuel = st.sidebar.selectbox("Fuel", ["gasoline", "diesel"])
use = st.sidebar.selectbox("Use", ["private", "work"])

result = pc.calculate_premium(
    age=age,
    bonus_malus=bonus_malus,
    horsepower=horsepower,
    vehicle_age=vehicle_age,
    territory_label=territory_label,
    fuel=fuel,
    use=use,
    config=config,
    freq_rating=freq_rating,
    sev_rating=sev_rating,
)

if result["inputs_clipped"]:
    st.warning(f"Some inputs were outside the training range and clipped: {result['inputs_clipped']}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Frequency", f"{result['pred_frequency']:.3f}")
col2.metric("Severity", f"€{result['pred_severity']:,.2f}")
col3.metric("Pure Premium", f"€{result['pred_pure_premium']:,.2f}")
col4.metric("Gross Premium", f"€{result['pred_gross_premium']:,.2f}")

st.caption(
    f"Gross = (Pure Premium + €{config['expense_loadings']['fixed_expense']:.0f}) / "
    f"(1 - {config['expense_loadings']['variable_expense_ratio']:.0%} - "
    f"{config['expense_loadings']['profit_contingency_loading']:.0%})"
)

with st.expander("Matched rating-table rows for this policy"):
    st.write("Frequency model")
    st.dataframe(result["freq_rows"], hide_index=True)
    st.write("Severity model")
    st.dataframe(result["sev_rows"], hide_index=True)

with st.expander("Full rating tables"):
    st.write("Frequency (final Poisson model)")
    st.dataframe(freq_rating, hide_index=True)
    st.write("Severity (Gamma model)")
    st.dataframe(sev_rating, hide_index=True)
