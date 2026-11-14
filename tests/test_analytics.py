import pandas as pd

from src.analytics import align_growth_series, latest, yoy_growth


def sample_frame(periods=16):
    return pd.DataFrame({
        "date": pd.date_range("2020-01-01", periods=periods, freq="QS"),
        "value": [100 + i * 2 for i in range(periods)],
    })


def test_latest_returns_last_observation():
    result = latest(sample_frame(2))
    assert result["value"] == 102.0


def test_yoy_growth_uses_requested_lag():
    result = yoy_growth(sample_frame(), 4)
    assert len(result) == 12
    assert round(result.iloc[0]["growth_rate"], 2) == 8.0


def test_alignment_returns_common_quarterly_periods():
    gdp = sample_frame(16)
    cpi = pd.DataFrame({
        "date": pd.date_range("2020-01-01", periods=48, freq="MS"),
        "value": [100 + i for i in range(48)],
    })
    result = align_growth_series(gdp, cpi)
    assert {"period", "gdp_growth", "core_cpi_inflation"} <= set(result.columns)
    assert not result.empty
