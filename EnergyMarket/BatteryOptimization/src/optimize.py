"""
"""
import math
import numpy as np
import pyomo.environ as pyo
from typing import Optional
from src.constants import *


def build_and_solve(
    prices: np.ndarray,
    power_mw: float = POWER_MW,
    capacity_mwh: float = CAPACITY_MWH,
    rte: float = RTE,
    soc_init: float = 200.0,
    soc_final: Optional[float] = None,
    solver: str = "highs",
) -> dict:
    """
    Solve the single-day arbitrage LP and return schedule + profit.

    Parameters
    ----------
    prices       : hourly day-ahead prices ($/MWh), length T
    power_mw     : rated charge/discharge power (MW)
    capacity_mwh : usable energy capacity (MWh)
    rte          : round-trip (charge & discharge) efficiency (0–1)
    soc_init     : initial state of charge (MWh)
    soc_final    : optional terminal SOC constraint (MWh)
    solver       : Pyomo solver name

    Returns
    -------
    dict with keys: charge_mw, discharge_mw, soc_mwh, profit_usd, status
    """
    T = len(prices)
    hours = range(T)

    # Split RTE symmetrically into one-way charge/discharge efficiencies
    eta_c = math.sqrt(rte)
    eta_d = math.sqrt(rte)

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=hours)

    # --- Decision variables ---
    # Charge Power, i.e. How much we should charge each hour
    model.c = pyo.Var(model.T, domain=pyo.NonNegativeReals, bounds=(0, power_mw))
    # Discharge Power, i.e. How much we should discharge each hour
    model.d = pyo.Var(model.T, domain=pyo.NonNegativeReals, bounds=(0, power_mw))
    # State of charge, i.e. How much energy is stored each hour
    model.soc = pyo.Var(model.T, domain=pyo.NonNegativeReals, bounds=(0, capacity_mwh))

    # --- Objective: maximize revenue ---
    # Charging: Buys electricity and costs money
    # Discharging: Sells electricity and makes money
    model.profit = pyo.Objective(
        expr=sum(prices[t] * (model.d[t] - model.c[t]) for t in hours),
        sense=pyo.maximize,
    )

    # --- SOC dynamics ---
    def soc_rule(m, t):
        soc_prev = soc_init if t == 0 else m.soc[t - 1]
        return m.soc[t] == soc_prev + eta_c * m.c[t] - (1.0 / eta_d) * m.d[t]

    model.soc_dynamics = pyo.Constraint(model.T, rule=soc_rule)

    # --- Optional terminal SOC constraint ---
    if soc_final is not None:
        model.terminal = pyo.Constraint(expr=model.soc[T - 1] == soc_final)

    # --- Solve ---
    opt = pyo.SolverFactory(solver)
    result = opt.solve(model, tee=False)  # tee=True prints out logs from optimization

    status = str(result.solver.termination_condition)
    if status != "optimal":
        return {
            "charge_mw": np.zeros(T),
            "discharge_mw": np.zeros(T),
            "soc_mwh": np.full(T, soc_init),
            "profit_usd": 0.0,
            "status": status,
        }

    charge = np.array([pyo.value(model.c[t]) for t in hours])
    discharge = np.array([pyo.value(model.d[t]) for t in hours])
    soc = np.array([pyo.value(model.soc[t]) for t in hours])
    profit = pyo.value(model.profit)

    return {
        "charge_mw": charge,
        "discharge_mw": discharge,
        "soc_mwh": soc,
        "profit_usd": profit,
        "status": status,
    }
