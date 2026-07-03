"""
"""
import io
import pathlib
from typing import Optional
import requests
import pandas as pd


# LMP data
EIA_URL = "https://www.eia.gov/electricity/wholesalemarkets/csv/pjm_lmp_da_hr_zones_{year}.csv"

# Philadelphia — representative PJM load center
_WEATHER_LAT = 39.95
_WEATHER_LON = -75.16
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

    # Drop rows with remaining NaN (longer gaps are reliable inputs)
    df = df.dropna(subset=["lmp_usd_mwh"])

    missing_pct = df["lmp_usd_mwh"].isna().mean()
    assert missing_pct < 0.01, f"Price data has {missing_pct:.1%} missing - check source"

    return df[["lmp_usd_mwh"]]


def fetch_weather(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch hourly temperature from Open-Meteo for Philadelphia.

    Returns a DataFrame indexed by timestamps in the specified time zone
    with one column: temperature_2m.
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": _WEATHER_LAT,
        "longitude": _WEATHER_LON,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m",
        "timezone": "America/New_York",
        "temperature_unit": "fahrenheit",
    }
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    # Open-Meteo returns local time strings
    # There can be Daylight Savings Problems here
    times = pd.to_datetime(data["hourly"]["time"])
    temps = data["hourly"]["temperature_2m"]

    weather = pd.DataFrame({"temperature_2m": temps}, index=times)

    # ambiguous='NaT' marks the duplicated fall-back hour as NaT; drop it
    # This handles the Daylight Savings Problems
    # tz_localize() assigns the local timezone while explicitly handling DST
    # edge cases by marking ambiguous (repeated) times as NaT
    # then shifts nonexistent (skipped) times forward
    # This prevents errors and ensures the time series remains valid across
    # daylight saving time transitions.
    weather.index = weather.index.tz_localize(_TZ, ambiguous="NaT", nonexistent="shift_forward")
    weather = weather[weather.index.notna()].sort_index()
    weather.index.name = "datetime_et"

    return weather[["temperature_2m"]]


def merge_price_and_weather(price_df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    Left-join price and weather on their shared Eastern-time DatetimeIndex.

    Forward-fills up to 2 hours of missing weather (brief API gaps).
    Asserts that weather coverage is above 95%.
    """
    merged = price_df.join(weather_df, how="left")
    merged["temperature_2m"] = merged["temperature_2m"].ffill(limit=2)

    weather_missing = merged["temperature_2m"].isna().mean()
    assert weather_missing < 0.05, (
        f"Weather data has {weather_missing:.1%} missing after merge - check date ranges"
    )

    return merged
