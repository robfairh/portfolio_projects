"""
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from src.constants import *


plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
    "figure.dpi": 120,
})


def plot_price_profile(prices: np.ndarray, date, output_path: str) -> None:
    """Plot 1: Hourly electricity price profile for a sample day."""
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.step(HOURS, prices, where="post", color="tab:blue", linewidth=2)
    ax.fill_between(HOURS, prices, step="post", alpha=0.15, color="tab:blue")
    ax.set_xticks(HOURS)
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Day-Ahead LMP ($/MWh)")
    ax.set_title(f"Electricity Price Profile — {date}", fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {output_path}")


def plot_dispatch_and_soc(
    prices: np.ndarray,
    charge: np.ndarray,
    discharge: np.ndarray,
    soc: np.ndarray,
    capacity_mwh: float,
    date,
    output_path: str,
) -> None:
    fig, (ax1, ax4) = plt.subplots(
        2, 1, figsize=(12, 8), sharex=True,
        gridspec_kw={"height_ratios": [2, 1]}
    )

    profit = np.cumsum(prices * (discharge - charge)) / 1000

    # ===== Top subplot: Dispatch =====

    # Power (left axis)
    ax1.bar(HOURS, discharge, color="tab:green", alpha=0.7,
            label="Discharge (MW)", width=0.4, align="edge")
    ax1.bar([h - 0.4 for h in HOURS], -charge, color="tab:red", alpha=0.7,
            label="Charge (MW)", width=0.4, align="edge")
    ax1.axhline(0, color="grey", linewidth=0.8)
    ax1.set_ylabel("Power (MW)")

    # Price (right axis)
    ax2 = ax1.twinx()
    ax2.step(HOURS, prices, where="post", color="black",
             linewidth=1.2, label="Price ($/MWh)")
    ax2.set_ylabel("Price ($/MWh)")

    # Profit (far-right axis)
    ax3 = ax1.twinx()
    ax3.spines["right"].set_position(("outward", 60))
    ax3.plot(HOURS, profit, "--", color="tab:blue",
             linewidth=2, label="Cumulative Profit ($k)")
    ax3.axhline(0, color="tab:blue", linestyle="--", linewidth=0.8)
    ax3.set_ylabel("Profit ($k)", color="tab:blue")
    ax3.tick_params(axis="y", colors="tab:blue")

    # Combined legend
    lines, labels = [], []
    for ax in (ax1, ax2, ax3):
        l, lab = ax.get_legend_handles_labels()
        lines += l
        labels += lab
    ax1.legend(lines, labels, loc="lower right")

    ax1.set_title(f"BESS Dispatch Schedule — {date}", fontweight="bold")

    # ===== Bottom subplot: SOC =====

    ax4.step(HOURS, soc, where="post", color="tab:purple",
             linewidth=2, label="SOC (MWh)")
    ax4.fill_between(HOURS, soc, step="post",
                     alpha=0.15, color="tab:purple")
    ax4.axhline(capacity_mwh, color="tab:red",
                linestyle="--", linewidth=1,
                label=f"Max capacity ({capacity_mwh:.0f} MWh)")
    ax4.axhline(0, color="tab:orange",
                linestyle="--", linewidth=1,
                label="Min SOC")

    ax4.set_ylabel("SOC (MWh)")
    ax4.set_xlabel("Hour of Day")
    ax4.set_xticks(HOURS)
    ax4.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_profit_distribution(results: pd.DataFrame, output_path: str) -> None:
    """Plot 4: Distribution of daily profits across the simulation period."""
    profits = results["profit_usd"]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(profits, bins=40, color="tab:blue", alpha=0.8, edgecolor="white", linewidth=0.5)
    ax.axvline(profits.mean(), color="tab:red", linestyle="--", linewidth=1.5,
               label=f"Mean: ${profits.mean():,.0f}")
    ax.axvline(profits.median(), color="tab:orange", linestyle="--", linewidth=1.5,
               label=f"Median: ${profits.median():,.0f}")
    ax.set_xlabel("Daily Profit ($/day)")
    ax.set_ylabel("Number of Days")
    ax.set_title("Daily Profit Distribution (Full Simulation Period)", fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.legend(framealpha=0.9)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {output_path}")


def plot_sensitivity(sensitivity: dict, output_path: str) -> None:
    """Plot 5: Sensitivity of annual profit to RTE, capacity, and power rating."""
    labels = {
        "rte": ("Round-Trip Efficiency", lambda x: f"{x:.0%}"),
        "capacity": ("Energy Capacity (MWh)", lambda x: f"{x:.0f}"),
        "power": ("Power Rating (MW)", lambda x: f"{x:.0f}"),
    }

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Sensitivity Analysis — Annual Profit vs Key Parameters", fontweight="bold", fontsize=13)

    for ax, (key, (title, fmt)) in zip(axes, labels.items()):
        df = sensitivity[key]
        x = df.index.tolist()
        y = df["annual_profit_usd"].tolist()
        x_labels = [fmt(v) for v in x]

        ax.bar(x_labels, [v / 1e6 for v in y], color="tab:blue", alpha=0.8, edgecolor="white")
        ax.set_title(title, fontweight="bold")
        ax.set_xlabel(title)
        ax.set_ylabel("Annual Profit ($M)" if ax is axes[0] else "")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:.1f}M"))

        # Highlight baseline bar
        baseline_labels = {"rte": "90%", "capacity": "400", "power": "100"}
        for i, label in enumerate(x_labels):
            if label == baseline_labels[key]:
                ax.patches[i].set_edgecolor("tab:red")
                ax.patches[i].set_linewidth(2)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {output_path}")
