"""Deterministic economic calculations used by the UI and future LLM tools."""

from __future__ import annotations

import pandas as pd


def latest(frame: pd.DataFrame) -> dict:
    row = frame.iloc[-1]
    return {"date": row["date"], "value": float(row["value"])}


def percent_change(frame: pd.DataFrame, periods: int = 1, column_name: str = "rate") -> pd.DataFrame:
    result = frame.copy()
    result[column_name] = result["value"].pct_change(periods=periods) * 100
    return result.dropna(subset=[column_name]).reset_index(drop=True)


def annual_growth(frame: pd.DataFrame) -> pd.DataFrame:
    """Compute year-over-year growth using the closest observation 12 months earlier."""
    result = frame.set_index("date").sort_index()[["value"]].copy()
    result["growth_rate"] = result["value"].pct_change(freq="12MS") * 100
    # FRED series have different frequencies; a 12-month calendar shift is safer
    # for CPI, while GDP is quarterly and is handled with a four-observation lag.
    result["growth_rate"] = result["value"].pct_change(4) * 100 if len(result) < 100 else result["growth_rate"]
    return result.reset_index().dropna(subset=["growth_rate"])


def yoy_growth(frame: pd.DataFrame, periods: int) -> pd.DataFrame:
    result = frame.copy()
    result["growth_rate"] = result["value"].pct_change(periods=periods) * 100
    return result.dropna(subset=["growth_rate"]).reset_index(drop=True)


def align_growth_series(gdp: pd.DataFrame, cpi: pd.DataFrame) -> pd.DataFrame:
    """Return quarterly GDP growth and monthly CPI YoY inflation on common dates."""
    gdp_growth = yoy_growth(gdp, 4).rename(columns={"growth_rate": "gdp_growth"})
    cpi_growth = yoy_growth(cpi, 12).rename(columns={"growth_rate": "core_cpi_inflation"})
    gdp_growth["period"] = gdp_growth["date"].dt.to_period("Q").dt.to_timestamp()
    cpi_growth["period"] = cpi_growth["date"].dt.to_period("Q").dt.to_timestamp()
    gdp_growth = gdp_growth.groupby("period", as_index=False)["gdp_growth"].last()
    cpi_growth = cpi_growth.groupby("period").filter(lambda group: len(group) == 3)
    cpi_growth = cpi_growth.groupby("period", as_index=False)["core_cpi_inflation"].mean()
    return pd.merge(gdp_growth, cpi_growth, on="period", how="inner").sort_values("period")


def trend_summary(frame: pd.DataFrame, value_column: str) -> str:
    if frame.empty:
        return "No overlapping observations are available."
    values = frame[value_column].dropna()
    direction = "increased" if values.iloc[-1] > values.iloc[0] else "decreased"
    return f"The series {direction} from {values.iloc[0]:.2f}% to {values.iloc[-1]:.2f}% over the selected period."
