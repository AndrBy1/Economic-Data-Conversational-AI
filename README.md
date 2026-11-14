# Economic Data Conversational AI

This repository is being developed in increments for the GDP/Core CPI conversational-AI assignment.

## First implementation slice

The current release provides the reliable data and analytics foundation:

- `src/fred_client.py` retrieves and validates GDP (`GDP`) and core CPI (`CPILFESL`) observations from FRED.
- `src/analytics.py` calculates latest values, year-over-year rates, and a common quarterly comparison frame.
- `app.py` displays the two latest observations and a GDP-growth/core-inflation chart in Streamlit.
- `tests/test_analytics.py` covers the calculation boundary.

## Run locally

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and add a FRED API key.

3. Start the app:

   ```bash
   streamlit run app.py
   ```

4. Run tests with `pytest`.

## Planned next slices

1. Add an Ollama adapter and a small intent/tool router for the required questions.
2. Add conversational state, citations/data dates, and chart requests from chat.
3. Add architecture diagram, sample conversations, findings report, and packaging/deployment guidance.

The LLM will explain results returned by deterministic tools; it will not be trusted to invent or calculate economic values from memory.
