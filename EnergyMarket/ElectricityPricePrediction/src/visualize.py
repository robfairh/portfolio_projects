"""
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
})


def plot_actual_vs_predicted(
    y_test: pd.Series,
    lgbm_preds: pd.Series,
    naive_preds: pd.Series,
    window_days: int = 14,
    output_path: str = "actual_vs_predicted.png",
) -> None:
    """
    Plot actual vs predicted prices for a sample window of the test period.
    """
    n_hours = window_days * 24
    actual = y_test.iloc[:n_hours]
    lgbm = lgbm_preds.iloc[:n_hours]
    naive = naive_preds.reindex(actual.index)

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(actual.index, actual.values, color="black", linewidth=1.5, label="Actual", zorder=3)
    ax.plot(lgbm.index, lgbm.values, color="tab:blue", linewidth=1.5, label="LightGBM", zorder=2)
    ax.plot(naive.index, naive.values, color="tab:orange", linewidth=1.0, linestyle="--", alpha=0.8, label="Naive (T-24h)")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    fig.autofmt_xdate(rotation=30, ha="right")

    ax.set_xlabel("Date (Eastern Time)", fontsize=11)
    ax.set_ylabel("Day-Ahead LMP ($/MWh)", fontsize=11)
    ax.set_title(f"Actual vs Predicted - {window_days}-Day Test Window", fontsize=13, fontweight="bold")
    ax.legend(framealpha=0.9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {output_path}")


def plot_feature_importance(
    importance_df: pd.DataFrame,
    output_path: str = "feature_importance.png",
) -> None:
    """
    Horizontal bar chart of LightGBM feature importances.
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.barh(
        importance_df["feature"],
        importance_df["importance"],
        color="tab:blue",
        alpha=0.85,
    )
    ax.invert_yaxis()  # top = most important

    # Label each bar with its value
    for bar, val in zip(bars, importance_df["importance"]):
        ax.text(bar.get_width() + importance_df["importance"].max() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{val:,}", va="center", fontsize=9)

    ax.set_xlabel("Importance (Split Count)", fontsize=11)
    ax.set_title("LightGBM Feature Importance", fontsize=13, fontweight="bold")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {output_path}")
