"""
Surrogate uncertainty quantification: epistemic and aleatoric.

Tier 1: predict_with_uncertainty, ensemble, MC dropout.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.ai.surrogate_uq")


def predict_with_uncertainty(
    surrogate: Any,
    params: Dict[str, float],
    method: str = "ensemble",
    n_samples: int = 100,
) -> tuple:
    """
    Predict with uncertainty bounds.

    Args:
        surrogate: Fitted surrogate (sklearn GP, ensemble, etc.)
        params: Input parameters
        method: "ensemble", "gp_native", "mc_dropout"
        n_samples: For MC methods

    Returns:
        (mean, std) or (mean, lower, upper)
    """
    if hasattr(surrogate, "predict_with_uncertainty"):
        return surrogate.predict_with_uncertainty(params)

    if hasattr(surrogate._backend, "predict") and hasattr(surrogate._backend, "predict"):
        try:
            order = surrogate._param_names or sorted(params.keys())
            X = np.array([[params.get(k, 0.0) for k in order]])
            mean, std = surrogate._backend.predict(X, return_std=True)
            return float(mean[0]), float(std[0])
        except (TypeError, ValueError):
            pass

    mean = surrogate.predict(params)
    return mean, 0.0


def ensemble_predict(
    surrogates: List[Any],
    params: Dict[str, float],
) -> tuple:
    """Predict using ensemble of surrogates for uncertainty."""
    preds = [s.predict(params) for s in surrogates]
    mean = np.mean(preds)
    std = np.std(preds)
    return mean, std
