"""
"""
import pandas as pd


FEATURE_COLS = [
    "hour_of_day",
    "day_of_week",
    "month",
    "is_weekend",
    "temperature_2m",
    "price_lag_24h",
    "price_lag_48h",
    "price_lag_168h",
    "price_roll_7d_mean",
]


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """ Add calendar features derived from the DatetimeIndex """
    df = df.copy()
    df["hour_of_day"] = df.index.hour
    df["day_of_week"] = df.index.dayofweek  # 0 = Monday, 6 = Sunday
    df["month"] = df.index.month
    df["is_weekend"] = (df.index.dayofweek >= 5).astype(int)
    return df


def add_lag_features(df: pd.DataFrame, target_col: str = "lmp_usd_mwh") -> pd.DataFrame:
    """
    Add lagged price features.

    shift(N) on a sorted chronological index only looks N steps backward,
    so these features are leakage-free even when computed on the full dataset
    before the train/test split.
    """
    df = df.copy()
    df["price_lag_24h"] = df[target_col].shift(24)     # same hour yesterday
    df["price_lag_48h"] = df[target_col].shift(48)     # same hour two days ago
    df["price_lag_168h"] = df[target_col].shift(168)   # same hour last week
    # 7-day rolling mean provides a smoothed price level signal
    df["price_roll_7d_mean"] = df[target_col].shift(1).rolling(168).mean()
    return df


def build_feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Apply all feature engineering steps and return (X, y).

    The first 168 rows are dropped because price_lag_168h requires one full
    week of history to be non-null.
    """
    df = add_calendar_features(df)
    df = add_lag_features(df)

    # Drop the warm-up period where rolling/lag features are NaN
    df = df.dropna(subset=["price_lag_168h", "price_roll_7d_mean"])

    X = df[FEATURE_COLS]
    y = df["lmp_usd_mwh"]
    return X, y


def chronological_split(
    X: pd.DataFrame,
    y: pd.Series,
    test_months: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Timestamp]:
    """
    Split features and target into train/test using a chronological cutoff.

    Never shuffles. Preserving time order is essential to prevent leakage.
    Returns (X_train, X_test, y_train, y_test, split_date).
    """
    split_date = X.index.max() - pd.DateOffset(months=test_months)

    train_mask = X.index <= split_date
    test_mask = X.index > split_date

    return (
        X[train_mask],
        X[test_mask],
        y[train_mask],
        y[test_mask],
        split_date,
    )
