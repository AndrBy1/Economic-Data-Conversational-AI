"""Streamlit entry point for the GDP/Core CPI analytics foundation."""

from datetime import date, timedelta
from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
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
    demo = st.checkbox("Use synthetic demo data", value=False)

if load or "data" not in st.session_state or st.session_state.get("settings") != (years, demo):
    st.session_state.settings = (years, demo)
    st.session_state.messages = []
    client = FredClient()
    start = date.today() - timedelta(days=365 * years + 400)
    try:
        with st.spinner("Loading GDP and Core CPI from FRED..."):
            if demo:
                raise FredAPIError("Demo mode selected")
            if client.api_key:
                try:
                    st.session_state.data = {
                        "gdp": client.get_observations(GDP, start=start),
                        "cpi": client.get_observations(CORE_CPI, start=start),
                    }
                    st.session_state.source_label = "Live FRED API data"
                except FredAPIError:
                    client.api_key = None
            if not client.api_key:
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
st.caption("GDP is nominal (current dollars), seasonally adjusted at an annual rate. Growth is year over year. Core CPI is seasonally adjusted; quarterly comparisons average monthly YoY rates. Observation dates are period dates, not release dates.")
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
if not comparison.empty:
    comparison = comparison[comparison.period >= comparison.period.max() - pd.DateOffset(years=years)]
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
    chart_bytes = BytesIO()
    fig.savefig(chart_bytes, format="png", bbox_inches="tight")
    st.download_button("Download comparison chart", chart_bytes.getvalue(), "comparison.png", "image/png")
    st.download_button("Download comparison data", comparison.to_csv(index=False), "comparison.csv", "text/csv")
    plt.close(fig)
    st.write(trend_summary(comparison, "gdp_growth"))

st.subheader("Ask the economic data assistant")
for message in st.session_state.get("messages", []):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("chart") is not None:
            st.line_chart(message["chart"].set_index("period"))

question = st.chat_input("Ask about GDP, Core CPI, trends, or their relationship")
if question:
    st.session_state.setdefault("messages", []).append({"role": "user", "content": question})
    result = answer_question(question, data, st.session_state.source_label)
    response = result["answer"]
    if use_ollama:
        explained = OllamaClient().explain(question, response, st.session_state.source_label)
        if explained:
            response += "\n\nOllama interpretation (generated):\n\n" + explained
        else:
            response += "\n\nOllama is unavailable; showing the calculated answer."
    response += f"\n\n_Source: {st.session_state.source_label}._"
    st.session_state.messages.append({"role": "assistant", "content": response, "chart": comparison.copy() if result['chart'] else None})
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
