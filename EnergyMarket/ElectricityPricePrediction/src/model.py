"""
"""
import numpy as np
import pandas as pd
from typing import Optional
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


_DEFAULT_PARAMS = {
    "objective": "regression",
    "n_estimators": 500,
    "learning_rate": 0.05,
    "num_leaves": 63,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 5,
    "random_state": 42,
    "verbose": -1,
}


def train_lgbm(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: Optional[dict] = None,
) -> LGBMRegressor:
    """ Train a LightGBM regressor and return the fitted model """
    model = LGBMRegressor(**(params or _DEFAULT_PARAMS))
    model.fit(X_train, y_train)
    return model


def make_naive_forecast(y_train: pd.Series, y_test: pd.Series) -> pd.Series:
    """
    Naive benchmark: predict each hour's price as the price 24 hours prior.

    Concatenates train+test before shifting so the first 24 test-set hours
    correctly pull from the last 24 training-set hours (not NaN).
    """
    full = pd.concat([y_train, y_test])
    naive = full.shift(24).loc[y_test.index]
    return naive.dropna()


def evaluate(y_true: pd.Series, y_pred, model_name: str = "") -> dict:
    """ Compute MAE and RMSE, returning a results dict """
    # Align index in case naive forecast dropped a few boundary NaNs
    common = y_true.index.intersection(pd.Series(y_pred, index=y_true.index).index)
    y_true = y_true.loc[common]
    if hasattr(y_pred, "loc"):
        y_pred = y_pred.loc[common]

    return {
        "Model": model_name,
        "MAE": round(float(mean_absolute_error(y_true, y_pred)), 2),
        "RMSE": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 2),
    }


def compare_models(
    model: LGBMRegressor,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Predict with LightGBM and naive benchmark, evaluate both.

    Returns (comparison_df, lgbm_preds, naive_preds).
    """
    lgbm_preds = pd.Series(model.predict(X_test), index=y_test.index, name="lgbm")
    naive_preds = make_naive_forecast(y_train, y_test)

    # Align y_test to naive (which may drop a few boundary rows)
    common_idx = y_test.index.intersection(naive_preds.index)

    results = [
        evaluate(y_test.loc[common_idx], lgbm_preds.loc[common_idx], "LightGBM"),
        evaluate(y_test.loc[common_idx], naive_preds.loc[common_idx], "Naive (T-24h)"),
    ]
    comparison_df = pd.DataFrame(results).set_index("Model")
    return comparison_df, lgbm_preds, naive_preds


def get_feature_importance(model: LGBMRegressor, feature_names: list) -> pd.DataFrame:
    """ Return feature importances sorted descending """
    return (
        pd.DataFrame({"feature": feature_names, "importance": model.feature_importances_})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )
