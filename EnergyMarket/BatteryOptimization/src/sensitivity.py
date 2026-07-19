"""
"""
import pandas as pd
from src.simulate import run_simulation


def annualized_profit(results: pd.DataFrame) -> float:
    """Scale observed daily profit to an annual figure."""
    n_days = len(results)
    if n_days == 0:
        return 0.0
    return results["profit_usd"].sum() / n_days * 365


def annual(days, **kwargs) -> float:
    results = run_simulation(days, **kwargs)
    return annualized_profit(results)


def to_df(d):
    return pd.DataFrame.from_dict(
        d, orient="index", columns=["annual_profit_usd"]
    )
