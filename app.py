"""Streamlit entry point for the GDP/Core CPI analytics foundation."""

from datetime import date, timedelta

import matplotlib.pyplot as plt
import streamlit as st

from src.analytics import align_growth_series, latest, trend_summary, yoy_growth
from src.fred_client import CORE_CPI, GDP, FredAPIError, FredClient


st.set_page_config(page_title="Economic Data AI", page_icon="📈", layout="wide")
st.title("U.S. GDP & Core CPI Explorer")
st.caption("Foundation release: verified FRED data retrieval and deterministic economic metrics")

with st.sidebar:
    st.header("Data window")
    years = st.slider("Years of history", min_value=1, max_value=20, value=10)
    load = st.button("Load FRED data", type="primary")

if load or "data" not in st.session_state:
    client = FredClient()
    start = date.today() - timedelta(days=365 * years + 400)
    try:
        with st.spinner("Loading GDP and Core CPI from FRED..."):
            st.session_state.data = {
                "gdp": client.get_observations(GDP, start=start),
                "cpi": client.get_observations(CORE_CPI, start=start),
            }
    except FredAPIError as exc:
        st.error(str(exc))
        st.info("Set FRED_API_KEY in a local .env file, then reload the app.")
        st.stop()

data = st.session_state.data
gdp_latest = latest(data["gdp"])
cpi_latest = latest(data["cpi"])
gdp_growth = yoy_growth(data["gdp"], 4)
cpi_inflation = yoy_growth(data["cpi"], 12)

metric_1, metric_2 = st.columns(2)
metric_1.metric("Latest GDP", f"${gdp_latest['value']:,.1f}B", gdp_latest["date"].strftime("%Y-%m-%d"))
if cpi_inflation.empty:
    metric_2.metric("Latest Core CPI index", f"{cpi_latest['value']:,.1f}", cpi_latest["date"].strftime("%Y-%m-%d"))
else:
    latest_inflation = cpi_inflation.iloc[-1]
    metric_2.metric(
        "Latest Core CPI inflation (YoY)",
        f"{latest_inflation['growth_rate']:.2f}%",
        latest_inflation["date"].strftime("%Y-%m-%d"),
    )

st.subheader("Growth and inflation")
comparison = align_growth_series(data["gdp"], data["cpi"])
if comparison.empty:
    st.warning("There are not yet enough overlapping observations to compare the series.")
else:
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(comparison["period"], comparison["gdp_growth"], label="GDP growth (YoY)", linewidth=2)
    ax.plot(comparison["period"], comparison["core_cpi_inflation"], label="Core CPI inflation (YoY)", linewidth=2)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Percent")
    ax.set_xlabel("Quarter")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)
    st.write(trend_summary(comparison, "gdp_growth"))

with st.expander("What is implemented in this first slice?"):
    st.markdown(
        """
        - FRED API client with typed, validated observations.
        - Latest-value retrieval and year-over-year GDP/Core CPI calculations.
        - A common quarterly timeline for comparison and visualization.
        - A Streamlit UI with explicit data loading and clear API-key errors.

        The conversational Ollama layer will call these calculations as tools in the next slice, so generated answers are grounded in the same numbers shown here.
        """
    )
