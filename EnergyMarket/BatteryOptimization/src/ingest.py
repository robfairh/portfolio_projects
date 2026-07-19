"""
"""
import io
import pathlib
from typing import Optional
import requests
import numpy as np
import pandas as pd


_ROOT = pathlib.Path(__file__).parent.parent


EIA_URL = "https://www.eia.gov/electricity/wholesalemarkets/csv/pjm_lmp_da_hr_zones_{year}.csv"
DEFAULT_CSV = _ROOT / "data" / "sample_pjm_lmp.csv"
_TZ = "America/New_York"


def download_price_data_by_year(year: int) -> pd.DataFrame:
    """
    Downloads data from EIA Website and creates a .csv for the specified year.
    """
    url = EIA_URL.format(year=year)
    print(f"Downloading {url} ...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    raw = pd.read_csv(io.BytesIO(resp.content), skiprows=3)

    utc_col = [c for c in raw.columns if "UTC" in c][0]
    lmp_col = [c for c in raw.columns if "Allegheny Power System LMP" == c][0]

    return raw[[utc_col, lmp_col]].rename(
        columns={utc_col: "utc_timestamp", lmp_col: "lmp_usd_mwh"}
    )


def load_price_data(csv_path: str) -> pd.DataFrame:
    """
    Load hourly PJM day-ahead LMP prices from a CSV file.

    Returns a DataFrame indexed by timestamps in the specified time zone
    with one column: lmp_usd_mwh.
    """
    df = pd.read_csv(csv_path, parse_dates=["utc_timestamp"])

    # Localize to UTC then convert to specified time zone
    # No Daylight Savings Problems here
    df["datetime_et"] = (
        df["utc_timestamp"]
        .dt.tz_localize("UTC")
        .dt.tz_convert(_TZ)
    )
    df = df.set_index("datetime_et").drop(columns=["utc_timestamp"])
    df = df.sort_index()

    # Fill isolated gaps (outages, data feed blips) with last valid value up
    # to 2 consecutive hours
    df["lmp_usd_mwh"] = df["lmp_usd_mwh"].ffill(limit=2)

    # Drop rows with remaining NaN (longer gaps are not reliable inputs)
    df = df.dropna(subset=["lmp_usd_mwh"])

    missing_pct = df["lmp_usd_mwh"].isna().mean()
    assert missing_pct < 0.01, f"Price data has {missing_pct:.1%} missing - check source"

    return df[["lmp_usd_mwh"]]


def prices_by_day(df: pd.DataFrame) -> dict:
    """
    Split the price series into a dict keyed by date.

    Each value is a 24-element Series of hourly prices ($/MWh).
    Days with fewer than 23 hours are excluded (Daylight Savings transitions).
    """
    days = {}
    for date, group in df.groupby(df.index.date):
        if len(group) >= 23:
            days[date] = group["lmp_usd_mwh"].values
    return days


def get_sample_day(days: dict, percentile: float = 75) -> tuple:
    """
    Return (date, prices) for the day whose total price spread is at the
    given percentile — useful for picking a representative plot day.
    """
    spreads = {d: p.max() - p.min() for d, p in days.items()}
    threshold = np.percentile(list(spreads.values()), percentile)
    date = min(spreads, key=lambda d: abs(spreads[d] - threshold))
    return date, days[date]
