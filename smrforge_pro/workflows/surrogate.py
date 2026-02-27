"""
Pro surrogate models: RBF, linear, and plugin-registry backends.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

from smrforge.utils.logging import get_logger

from .plugin_registry import get_surrogate

logger = get_logger("smrforge_pro.workflows.surrogate")


def fit_surrogate(
    X: Union[np.ndarray, List[Dict[str, float]]],
    y: Union[np.ndarray, List[float]],
    method: str = "rbf",
    param_names: Optional[List[str]] = None,
    **kwargs: Any,
) -> "SurrogateModel":
    """
    Fit surrogate model from training data.

    Args:
        X: Design points (2D array or list of param dicts)
        y: Target values
        method: "rbf", "linear", or registered custom name
        param_names: Parameter names for dict interface
        **kwargs: Passed to backend

    Returns:
        SurrogateModel with .predict(params) interface
    """
    X_arr, y_arr, param_names = _prepare_fit_data(X, y, param_names)
    audit_trail = kwargs.pop("audit_trail", None)
    backend_kwargs = {k: v for k, v in kwargs.items() if k not in ("audit_trail",)}

    factory = get_surrogate(method)
    if factory is not None:
        model = factory(X_arr, y_arr, **backend_kwargs)
        surr = SurrogateModel(model, param_names)
    elif method == "rbf":
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import RBF

        kernel = RBF(length_scale=1.0)
        gp = GaussianProcessRegressor(kernel=kernel, **backend_kwargs)
        gp.fit(X_arr, y_arr)
        surr = SurrogateModel(gp, param_names)
    elif method == "linear":
        from sklearn.linear_model import LinearRegression

        lr = LinearRegression(**backend_kwargs)
        lr.fit(X_arr, y_arr)
        surr = SurrogateModel(lr, param_names)
    else:
        raise ValueError(f"Unknown method '{method}'. Use rbf, linear, or register_surrogate first.")

    if audit_trail is not None:
        try:
            import pickle
            import tempfile
            from smrforge_pro.ai.surrogates import model_hash
            with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
                fname = f.name
                pickle.dump(surr._backend, f)
            mh = model_hash(fname)
            Path(fname).unlink(missing_ok=True)
        except Exception:
            mh = "unknown"
        audit_trail.ai_models_used.append({"model_hash": mh, "method": method})
    return surr


def physics_informed_surrogate_from_sweep(
    results: List[Dict[str, Any]],
    params: List[str],
    output_metric: str = "k_eff",
    method: str = "rbf",
    output_path: Optional[Union[str, Path]] = None,
    physics_constraint: Optional[str] = "k_eff_positive",
    **kwargs: Any,
) -> "SurrogateModel":
    """
    Fit surrogate from sweep results with physics constraints (UQ + constraints).

    Document-specified: physics_informed_surrogate_from_sweep (Path C Product Updates).
    Applies physics constraints (e.g. k_eff > 0) when fitting.

    Args:
        results: Sweep results
        params: Parameter names
        output_metric: Metric to predict
        method: Surrogate method
        output_path: Optional save path
        physics_constraint: "k_eff_positive" (filter k_eff<=0), "none", or custom
        **kwargs: Passed to fit_surrogate

    Returns:
        Fitted SurrogateModel
    """
    filtered = list(results)
    if physics_constraint == "k_eff_positive" and output_metric == "k_eff":
        filtered = [r for r in results if r.get(output_metric, 0) > 0]
        if len(filtered) < len(results):
            from smrforge.utils.logging import get_logger
            get_logger("smrforge_pro.workflows.surrogate").info(
                "Physics constraint: excluded %d points with k_eff<=0", len(results) - len(filtered)
            )
    return surrogate_from_sweep_results(
        filtered, params, output_metric=output_metric, method=method, output_path=output_path, **kwargs
    )


def surrogate_from_sweep_results(
    results: List[Dict[str, Any]],
    params: List[str],
    output_metric: str = "k_eff",
    method: str = "rbf",
    output_path: Optional[Union[str, Path]] = None,
    **kwargs: Any,
) -> "SurrogateModel":
    """
    Fit surrogate from parameter sweep results.

    Args:
        results: List of {parameters: {x: v}, k_eff: v, ...}
        params: Parameter names to use as inputs
        output_metric: Metric to predict (e.g. k_eff)
        method: Surrogate method
        output_path: Optional path to save model
        **kwargs: Passed to fit_surrogate

    Returns:
        Fitted SurrogateModel
    """
    X = []
    y = []
    for r in results:
        p = r.get("parameters", r)
        X.append([p.get(k, 0.0) for k in params])
        y.append(r.get(output_metric, 0.0))

    surr = fit_surrogate(
        np.array(X),
        np.array(y),
        method=method,
        param_names=params,
        **kwargs,
    )

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        surr.save(output_path)

    return surr


def _prepare_fit_data(X, y, param_names):
    """Convert X,y to arrays and infer param_names."""
    if isinstance(X, list) and X and isinstance(X[0], dict):
        param_names = param_names or list(X[0].keys())
        X_arr = np.array([[x.get(k, 0.0) for k in param_names] for x in X])
    else:
        X_arr = np.asarray(X)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(-1, 1)
        param_names = param_names or [f"x{i}" for i in range(X_arr.shape[1])]
    y_arr = np.asarray(y).ravel()
    return X_arr, y_arr, param_names


class SurrogateModel:
    """Surrogate model with predict(params_dict) interface."""

    def __init__(self, backend: Any, param_names: Optional[List[str]] = None):
        self._backend = backend
        self._param_names = param_names or []

    def predict(self, params: Union[Dict[str, float], np.ndarray]) -> float:
        """Predict output for given parameters."""
        if isinstance(params, dict):
            order = self._param_names or sorted(params.keys())
            X = np.array([[params.get(k, 0.0) for k in order]], dtype=np.float64)
        else:
            X = np.asarray(params)
            if X.ndim == 1:
                X = X.reshape(1, -1)
        return float(self._backend.predict(X)[0])

    def save(self, path: Union[str, Path]) -> None:
        """Save model to file (.pkl for sklearn)."""
        path = Path(path)
        if path.suffix.lower() == ".pkl":
            import pickle

            with open(path, "wb") as f:
                pickle.dump(self._backend, f)
        else:
            import pickle

            with open(path.with_suffix(".pkl"), "wb") as f:
                pickle.dump(self._backend, f)
