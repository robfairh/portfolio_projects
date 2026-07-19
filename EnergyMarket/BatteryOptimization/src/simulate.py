"""
"""
import datetime
from typing import Optional
import numpy as np
import pandas as pd
from src.optimize import build_and_solve
from src.constants import *


def run_simulation(
    days: dict,
    power_mw: float = POWER_MW,
    capacity_mwh: float = CAPACITY_MWH,
    rte: float = RTE,
    soc_init_frac: float = 0.50,
) -> pd.DataFrame:
    """
    Optimize each day independently and return a per-day results DataFrame.

    Each day starts at soc_init_frac * capacity_mwh.

    Parameters
    ----------
    days          : {date: np.ndarray of hourly prices} from ingest.prices_by_day
    power_mw      : rated power (MW)
    capacity_mwh  : energy capacity (MWh)
    rte           : round-trip efficiency
    soc_init_frac : starting SOC as fraction of capacity

    Returns
    -------
    DataFrame indexed by date with columns:
      profit_usd, charge_mwh, discharge_mwh, cycles, status
    """
    soc_init = soc_init_frac * capacity_mwh
    records = []

    for date, prices in sorted(days.items()):
        result = build_and_solve(
            prices=prices,
            power_mw=power_mw,
            capacity_mwh=capacity_mwh,
            rte=rte,
            soc_init=soc_init,
        )
        records.append({
            "date": date,
            "profit_usd": result["profit_usd"],
            "charge_mwh": result["charge_mw"].sum(),
            "discharge_mwh": result["discharge_mw"].sum(),
            # One cycle = charging from 0 to full capacity once
            "cycles": result["charge_mw"].sum() / capacity_mwh if capacity_mwh > 0 else 0,
            "status": result["status"],
        })

    df = pd.DataFrame(records).set_index("date")
    return df
