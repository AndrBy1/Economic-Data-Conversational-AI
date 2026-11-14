"""Small, testable client for the FRED observations API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()


class FredAPIError(RuntimeError):
    """Raised when FRED cannot return a usable response."""


@dataclass(frozen=True)
class SeriesConfig:
    series_id: str
    name: str
    units: str


GDP = SeriesConfig("GDP", "Gross Domestic Product", "Billions of dollars")
CORE_CPI = SeriesConfig(
    "CPILFESL", "Consumer Price Index less Food and Energy", "Index 1982-84=100"
)


class FredClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("FRED_API_KEY")
        self.base_url = (base_url or os.getenv("FRED_API_URL", "https://api.stlouisfed.org/fred")).rstrip("/")

    def get_observations(
        self,
        series: SeriesConfig,
        start: date | None = None,
        end: date | None = None,
    ) -> pd.DataFrame:
        """Fetch observations and return a typed date/value DataFrame."""
        if not self.api_key:
            raise FredAPIError("FRED_API_KEY is not configured. Copy .env.example to .env and add your key.")

        params = {
            "api_key": self.api_key,
            "file_type": "json",
            "series_id": series.series_id,
            "sort_order": "asc",
        }
        if start:
            params["observation_start"] = start.isoformat()
        if end:
            params["observation_end"] = end.isoformat()

        try:
            response = requests.get(f"{self.base_url}/series/observations", params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            raise FredAPIError(f"Could not reach FRED: {exc}") from exc
        except ValueError as exc:
            raise FredAPIError("FRED returned an invalid JSON response.") from exc

        if "error_code" in payload:
            raise FredAPIError(f"FRED API error {payload.get('error_code')}: {payload.get('error_message', 'Unknown error')}")

        frame = pd.DataFrame(payload.get("observations", []))
        if frame.empty:
            raise FredAPIError(f"FRED returned no observations for {series.series_id}.")

        frame = frame[["date", "value"]].copy()
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
        frame = frame.dropna().sort_values("date").reset_index(drop=True)
        if frame.empty:
            raise FredAPIError(f"FRED returned no numeric observations for {series.series_id}.")
        return frame
