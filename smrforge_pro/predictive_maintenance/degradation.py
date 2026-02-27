"""
Predictive maintenance: creep, swelling, FGR degradation models.
"""

from typing import Any, Dict, List, Optional

import numpy as np

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.predictive_maintenance")


def fit_degradation_model(
    burnup_history: np.ndarray,
    damage_metric: np.ndarray,
    model_type: str = "linear",
    **kwargs: Any,
) -> Any:
    """Fit degradation model from burnup vs damage history."""
    from sklearn.linear_model import LinearRegression
    X = burnup_history.reshape(-1, 1)
    y = damage_metric.ravel()
    lr = LinearRegression().fit(X, y)
    return lr


def predict_rul(
    model: Any,
    current_damage: float,
    threshold: float,
    burnup_rate: float = 1.0,
) -> float:
    """Predict remaining useful life (RUL) until threshold."""
    if hasattr(model, "predict"):
        rem = threshold - current_damage
        if rem <= 0:
            return 0.0
        rate = model.coef_[0] if hasattr(model, "coef_") else 0.01
        return rem / (rate * burnup_rate) if rate > 0 else float("inf")
    return 0.0
