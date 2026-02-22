"""
Surrogate models for fast evaluation of reactor outputs.

Fit a simple model (RBF, linear, or GP) to (X, y) from DoE/UQ runs;
evaluate new designs in milliseconds without re-running physics.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.workflows.surrogate")

try:
    from scipy.interpolate import RBFInterpolator

    _RBF_AVAILABLE = True
except ImportError:  # pragma: no cover
    _RBF_AVAILABLE = False


def _maybe_record_ai_model(
    audit_trail: Optional[Any],
    surrogate: "SurrogateModel",
    config_hash: Optional[str] = None,
) -> None:
    """Record surrogate to audit trail when provided (regulatory traceability)."""
    if audit_trail is None:
        return
    try:
        from smrforge.ai.audit import record_ai_model

        version = getattr(surrogate, "config_hash", None) or config_hash
        record_ai_model(
            audit_trail,
            surrogate.method,
            version=str(version) if version else None,
            config_hash=config_hash,
        )
    except Exception as e:
        logger.debug("Could not record AI model to audit trail: %s", e)


@dataclass
class SurrogateModel:
    """Fitted surrogate: predict(x) and metadata."""

    method: str  # "rbf" | "linear"
    param_names: List[str]
    output_name: str
    n_samples: int
    predict: Callable[[np.ndarray], np.ndarray]


def fit_surrogate(
    X: np.ndarray,
    y: np.ndarray,
    param_names: Optional[List[str]] = None,
    output_name: str = "output",
    method: str = "rbf",
    audit_trail: Optional[Any] = None,
    **factory_kwargs: Any,
) -> SurrogateModel:
    """
    Fit a surrogate model to (X, y).

    Uses the plugin registry first: if ``method`` is registered via
    register_surrogate(), the registered factory is used. Otherwise uses
    built-in methods "rbf" and "linear". Pro/Enterprise or third parties
    can add custom ML models without forking.

    Args:
        X: (n_samples, n_params) training inputs.
        y: (n_samples,) training outputs.
        param_names: Parameter names (for metadata).
        output_name: Output label.
        method: "rbf" (default), "linear", or a registered name.
        audit_trail: Optional CalculationAuditTrail to record ai_models_used.
        **factory_kwargs: Extra kwargs passed to registered factory.

    Returns:
        SurrogateModel with .predict(X_new) returning (n_new,) array.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float).ravel()
    n_params = X.shape[1]
    param_names = param_names or [f"x{i}" for i in range(n_params)]
    logger.debug(
        "Fitting surrogate: method=%s, n_samples=%s, n_params=%s",
        method,
        X.shape[0],
        n_params,
    )

    # Built-in methods first (common path; skips registry import/lookup)
    if method == "linear":
        # y = X @ coef + intercept
        ones = np.ones((X.shape[0], 1))
        X_aug = np.hstack([ones, X])
        coef, residuals, rank, s = np.linalg.lstsq(X_aug, y, rcond=None)

        def predict(Xnew):
            Xnew = np.asarray(Xnew, dtype=float)
            if Xnew.ndim == 1:
                Xnew = Xnew.reshape(1, -1)
            ones_new = np.ones((Xnew.shape[0], 1))
            Xnew_aug = np.hstack([ones_new, Xnew])
            return (Xnew_aug @ coef).ravel()

        sur = SurrogateModel(
            method="linear",
            param_names=param_names,
            output_name=output_name,
            n_samples=X.shape[0],
            predict=predict,
        )
        _maybe_record_ai_model(audit_trail, sur, config_hash=None)
        return sur
    if method == "rbf":
        if not _RBF_AVAILABLE:
            raise ImportError(
                "scipy.interpolate.RBFInterpolator required for method='rbf'"
            )
        rbf = RBFInterpolator(X, y)

        def predict(Xnew):
            Xnew = np.asarray(Xnew, dtype=float)
            if Xnew.ndim == 1:
                Xnew = Xnew.reshape(1, -1)
            return rbf(Xnew).ravel()

        sur = SurrogateModel(
            method="rbf",
            param_names=param_names,
            output_name=output_name,
            n_samples=X.shape[0],
            predict=predict,
        )
        _maybe_record_ai_model(audit_trail, sur, config_hash=None)
        return sur

    # Fall back to plugin registry (Pro/Enterprise, third-party ML models)
    from .plugin_registry import get_surrogate, list_surrogates

    factory = get_surrogate(method)
    if factory is not None:
        obj = factory(
            X, y, param_names=param_names, output_name=output_name, **factory_kwargs
        )
        predict_fn = getattr(obj, "predict", None)
        if callable(predict_fn):

            def _predict(Xnew: np.ndarray) -> np.ndarray:
                return np.asarray(predict_fn(Xnew)).ravel()

            sur = SurrogateModel(
                method=method,
                param_names=param_names,
                output_name=output_name,
                n_samples=X.shape[0],
                predict=_predict,
            )
            _maybe_record_ai_model(audit_trail, sur, config_hash=None)
            return sur
        raise ValueError(
            f"Registry factory for '{method}' did not return object with .predict()"
        )

    registered = list_surrogates()
    available = sorted(set(["rbf", "linear"] + registered))
    raise ValueError(
        f"method must be one of {available}, got {method!r}. "
        f"Use register_surrogate() to add custom models."
    )


def surrogate_from_sweep_results(
    results: List[Dict[str, Any]],
    param_names: List[str],
    output_metric: str = "k_eff",
    method: str = "rbf",
    audit_trail: Optional[Any] = None,
) -> SurrogateModel:
    """
    Build a surrogate from a list of sweep result dicts.

    Args:
        results: List of {"parameters": {name: val, ...}, output_metric: val} or flat.
        param_names: Parameter names (order = columns of X).
        output_metric: Key for output value.
        method: "rbf" or "linear" or registered name.
        audit_trail: Optional CalculationAuditTrail to record ai_models_used.

    Returns:
        SurrogateModel.
    """
    rows_x = []
    rows_y = []
    for r in results:
        params = r.get("parameters", r)
        try:
            y = float(params.get(output_metric, r.get(output_metric, np.nan)))
        except (TypeError, ValueError):  # pragma: no cover
            continue
        if not np.isfinite(y):
            continue
        row = [float(params.get(p, np.nan)) for p in param_names]
        if any(not np.isfinite(v) for v in row):
            continue
        rows_x.append(row)
        rows_y.append(y)
    if len(rows_x) < 2:
        raise ValueError("Need at least 2 valid samples to fit surrogate")
    X = np.array(rows_x)
    y = np.array(rows_y)
    return fit_surrogate(
        X,
        y,
        param_names=param_names,
        output_name=output_metric,
        method=method,
        audit_trail=audit_trail,
    )
