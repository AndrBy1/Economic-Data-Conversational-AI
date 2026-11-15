"""Streamlit entry point for the GDP/Core CPI analytics foundation."""

from datetime import date, timedelta

import matplotlib.pyplot as plt
import streamlit as st

from src.analytics import align_growth_series, latest, trend_summary, yoy_growth
from src.conversation import OllamaClient, answer_question
from src.demo_data import load_demo_data
from src.fred_client import CORE_CPI, GDP, FredAPIError, FredClient


st.set_page_config(page_title="Economic Data AI", page_icon="📈", layout="wide")
st.title("U.S. GDP & Core CPI Explorer")
st.caption("Foundation release: verified FRED data retrieval and deterministic economic metrics")

with st.sidebar:
    st.header("Data window")
    years = st.slider("Years of history", min_value=1, max_value=20, value=10)
    load = st.button("Load FRED data", type="primary")
    use_ollama = st.checkbox("Use Ollama to explain answers", value=True)

if load or "data" not in st.session_state:
    client = FredClient()
    start = date.today() - timedelta(days=365 * years + 400)
    try:
        with st.spinner("Loading GDP and Core CPI from FRED..."):
            if client.api_key:
                st.session_state.data = {
                    "gdp": client.get_observations(GDP, start=start),
                    "cpi": client.get_observations(CORE_CPI, start=start),
                }
                st.session_state.source_label = "Live FRED API data"
            else:
                st.session_state.data = {
                    "gdp": client.get_public_csv_observations(GDP, start=start),
                    "cpi": client.get_public_csv_observations(CORE_CPI, start=start),
                }
                st.session_state.source_label = "Live public FRED CSV data (no API key)"
    except FredAPIError as exc:
        st.session_state.data = load_demo_data()
        st.session_state.source_label = "Synthetic demo data — not current FRED data"
        st.warning(f"FRED could not be reached ({exc}). Using clearly labelled demo data.")

data = st.session_state.data
st.info(f"Data source: {st.session_state.source_label}")
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

st.subheader("Ask the economic data assistant")
for message in st.session_state.get("messages", []):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask about GDP, Core CPI, trends, or their relationship")
if question:
    st.session_state.setdefault("messages", []).append({"role": "user", "content": question})
    result = answer_question(question, data, st.session_state.source_label)
    response = result["answer"]
    if use_ollama:
        explained = OllamaClient().explain(question, response, st.session_state.source_label)
        if explained:
            response = explained
    response += f"\n\n_Source: {st.session_state.source_label}._"
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

with st.expander("What is implemented in this first slice?"):
    st.markdown(
        """
        - FRED API client with typed, validated observations.
        - Latest-value retrieval and year-over-year GDP/Core CPI calculations.
        - A common quarterly timeline for comparison and visualization.
        - A Streamlit chat router for the required question types.
        - Optional Ollama explanations grounded in deterministic calculations.
        - Public FRED CSV fallback and labelled synthetic demo data when FRED is unavailable.
        """
    )
