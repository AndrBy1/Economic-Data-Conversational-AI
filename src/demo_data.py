"""Deterministic demo observations used when FRED is unreachable.

The demo path makes the application usable without credentials, but is clearly
labelled in the UI and must not be presented as current economic data.
"""

import numpy as np
import pandas as pd


def load_demo_data() -> dict[str, pd.DataFrame]:
    monthly = pd.date_range("2010-01-01", "2025-12-01", freq="MS")
    month_number = np.arange(len(monthly))
    cpi = 217 + month_number * 0.22 + 1.5 * np.sin(month_number / 9)
    cpi += np.where((monthly >= "2021-01-01") & (monthly <= "2022-12-01"), (month_number - 132) * 0.045, 0)
    cpi_frame = pd.DataFrame({"date": monthly, "value": cpi})

    quarterly = pd.date_range("2010-01-01", "2025-10-01", freq="QS")
    quarter_number = np.arange(len(quarterly))
    gdp = 15000 + quarter_number * 175 + 120 * np.sin(quarter_number / 4)
    gdp += np.where(quarterly == "2020-04-01", -1800, 0)
    gdp += np.where(quarterly == "2020-07-01", -650, 0)
    gdp_frame = pd.DataFrame({"date": quarterly, "value": gdp})
    return {"gdp": gdp_frame, "cpi": cpi_frame}
