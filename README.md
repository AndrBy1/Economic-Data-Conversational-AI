# Economic Data Conversational AI

This repository is being developed in increments for the GDP/Core CPI conversational-AI assignment.

## Current implementation

The current release provides the reliable data and analytics foundation:

- `src/fred_client.py` retrieves and validates GDP (`GDP`) and core CPI (`CPILFESL`) observations from FRED.
- `src/analytics.py` calculates latest values, year-over-year rates, and a common quarterly comparison frame.
- `app.py` displays the two latest observations and a GDP-growth/core-inflation chart in Streamlit.
- `src/conversation.py` routes supported natural-language questions to verified calculations and optionally asks Ollama to explain them.
- `src/demo_data.py` provides clearly labelled synthetic data when neither FRED endpoint is reachable.
- `tests/test_analytics.py` covers the calculation boundary.

## Run locally

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Optionally copy `.env.example` to `.env` and add a FRED API key. If no key is available, the app first tries FRED's public graph CSV endpoint and then falls back to labelled demo data.

3. Start the app:

   ```bash
   streamlit run app.py
   ```

To enable local LLM explanations, install Ollama separately, start it, and pull the configured model:

```bash
ollama pull llama3.1:8b
```

The app remains usable when Ollama is not running; it will show the deterministic, data-grounded answer instead.

4. Run tests with `pytest`.

## Planned next slices

1. Add architecture diagram, sample conversations, findings report, and packaging/deployment guidance.
2. Improve intent handling and add richer chart responses.

The LLM will explain results returned by deterministic tools; it will not be trusted to invent or calculate economic values from memory.
