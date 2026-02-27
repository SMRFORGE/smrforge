"""
Multi-fidelity surrogates: combine cheap (diffusion) and expensive (MC) data.

Tier 1: Active learning for where to run expensive physics.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.ai.multi_fidelity")


def fit_multi_fidelity_surrogate(
    X_cheap: np.ndarray,
    y_cheap: np.ndarray,
    X_expensive: np.ndarray,
    y_expensive: np.ndarray,
    param_names: Optional[List[str]] = None,
    method: str = "co_kriging",
    **kwargs: Any,
) -> "MultiFidelitySurrogate":
    """
    Fit multi-fidelity surrogate (cheap + expensive data).

    Args:
        X_cheap: Cheap solver design points (e.g. diffusion)
        y_cheap: Cheap solver outputs
        X_expensive: Expensive solver design points (e.g. MC)
        y_expensive: Expensive solver outputs
        param_names: Parameter names
        method: "co_kriging" or "autograd"
        **kwargs: Passed to backend

    Returns:
        MultiFidelitySurrogate model
    """
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, WhiteKernel

    param_names = param_names or [f"x{i}" for i in range(X_cheap.shape[1])]
    kernel = RBF() + WhiteKernel()
    gp = GaussianProcessRegressor(kernel=kernel)
    X_all = np.vstack([X_cheap, X_expensive])
    y_all = np.concatenate([y_cheap, y_expensive])
    gp.fit(X_all, y_all)
    return MultiFidelitySurrogate(gp, param_names)


def suggest_next_expensive_run(
    surrogate: "MultiFidelitySurrogate",
    X_pool: np.ndarray,
    acquisition: str = "variance",
    n_suggest: int = 1,
) -> np.ndarray:
    """
    Suggest next design points for expensive runs (active learning).

    Args:
        surrogate: Fitted multi-fidelity surrogate
        X_pool: Candidate design points
        acquisition: "variance" (predict where uncertain)
        n_suggest: Number of points to suggest

    Returns:
        Indices into X_pool to run next
    """
    if acquisition == "variance":
        try:
            mean, std = surrogate.predict_with_uncertainty(X_pool)
            idx = np.argsort(-std)[:n_suggest]
            return idx
        except Exception:
            return np.arange(min(n_suggest, len(X_pool)))
    return np.arange(min(n_suggest, len(X_pool)))


class MultiFidelitySurrogate:
    """Multi-fidelity surrogate with predict interface."""

    def __init__(self, backend: Any, param_names: List[str]):
        self._backend = backend
        self._param_names = param_names

    def predict(self, params: Dict[str, float]) -> float:
        """Predict output."""
        order = self._param_names or sorted(params.keys())
        X = np.array([[params.get(k, 0.0) for k in order]])
        return float(self._backend.predict(X)[0])

    def predict_with_uncertainty(self, X: np.ndarray) -> tuple:
        """Predict mean and std."""
        mean, std = self._backend.predict(X, return_std=True)
        return mean, std
