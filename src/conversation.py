"""Question router and optional Ollama explanation layer."""

from __future__ import annotations

import os
import re

import pandas as pd
import requests

from src.analytics import align_growth_series, latest, trend_summary, yoy_growth


def _years(question: str, default: int) -> int:
    match = re.search(r"(\d+)\s*years?", question.lower())
    return int(match.group(1)) if match else default


def _since(frame: pd.DataFrame, years: int) -> pd.DataFrame:
    cutoff = frame["date"].max() - pd.DateOffset(years=years)
    return frame[frame["date"] >= cutoff].copy()


def answer_question(question: str, data: dict[str, pd.DataFrame], source_label: str) -> dict:
    """Answer supported questions with computed values, not LLM guesses."""
    text = question.lower()
    gdp, cpi = data["gdp"], data["cpi"]
    if "latest" in text and "gdp" in text:
        item = latest(gdp)
        answer = f"The latest GDP observation is ${item['value']:,.1f} billion, reported for {item['date']:%Y-%m-%d}."
        return {"answer": answer, "chart": False}
    if ("inflation" in text or "rate" in text) and ("cpi" in text or "core" in text):
        inflation = yoy_growth(cpi, 12)
        item = inflation.iloc[-1]
        answer = f"The latest Core CPI inflation rate is {item['growth_rate']:.2f}% year over year, based on {item['date']:%Y-%m-%d}."
        return {"answer": answer, "chart": False}
    if "relationship" in text or "correlat" in text:
        comparison = align_growth_series(gdp, cpi)
        correlation = comparison["gdp_growth"].corr(comparison["core_cpi_inflation"])
        answer = f"Across {len(comparison)} overlapping quarters, the Pearson correlation is {correlation:.2f}. This describes association, not causation."
        return {"answer": answer, "chart": True}
    if "visual" in text or "chart" in text or "plot" in text or "graph" in text:
        return {"answer": "I generated a quarterly comparison of GDP growth and Core CPI inflation below.", "chart": True}
    if "summar" in text or "trend" in text:
        comparison = align_growth_series(gdp, cpi)
        answer = f"GDP growth {trend_summary(comparison, 'gdp_growth').lower()} Core CPI inflation {trend_summary(comparison, 'core_cpi_inflation').lower()}"
        return {"answer": answer, "chart": True}
    if "gdp" in text and ("changed" in text or "past" in text or "last" in text):
        window = _since(gdp, _years(text, 10))
        change = (window.iloc[-1]["value"] / window.iloc[0]["value"] - 1) * 100
        answer = f"GDP changed from ${window.iloc[0]['value']:,.1f}B to ${window.iloc[-1]['value']:,.1f}B, a {change:.1f}% change over the selected period."
        return {"answer": answer, "chart": False}
    if "cpi" in text and ("changed" in text or "past" in text or "last" in text):
        window = _since(cpi, _years(text, 5))
        inflation = yoy_growth(window, 12)
        answer = f"Over the selected period, the Core CPI index moved from {window.iloc[0]['value']:.1f} to {window.iloc[-1]['value']:.1f}. The latest year-over-year rate in that window is {inflation.iloc[-1]['growth_rate']:.2f}%."
        return {"answer": answer, "chart": False}
    return {"answer": "I can answer questions about latest GDP, GDP changes, Core CPI inflation, trends, relationships, and comparison charts.", "chart": False}


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    def explain(self, question: str, grounded_answer: str, source_label: str) -> str | None:
        prompt = f"""You are an economics teaching assistant. Explain the verified answer below in plain language.
Do not change any numbers, invent data, or claim causation. Mention the source label when useful.
Question: {question}
Verified answer: {grounded_answer}
Source label: {source_label}
"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            response.raise_for_status()
            result = response.json().get("response", "").strip()
            return result or None
        except (requests.RequestException, ValueError):
            return None
