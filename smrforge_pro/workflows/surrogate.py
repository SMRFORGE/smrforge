"""
Surrogate fitting - RBF/linear from sweep results or X,y.

Pro tier: Full fit_surrogate, surrogate_from_sweep_results, SurrogateModel.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

from smrforge_pro.ai.audit import record_ai_model
from smrforge_pro.ai.surrogates import model_hash


class SurrogateModel:
    """Fitted RBF or linear surrogate with predict(spec), model_hash()."""

    def __init__(
        self,
        model: Any,
        param_names: List[str],
        output_metric: str,
        method: str,
        path: Optional[Path] = None,
    ):
        self._model = model
        self.param_names = param_names
        self.output_metric = output_metric
        self.method = method
        self._path = path
        self._hash_cache: Optional[str] = None

    def predict(
        self,
        spec: Union[Dict[str, Any], np.ndarray],
    ) -> Union[float, np.ndarray]:
        """Predict from spec dict or feature array."""
        if isinstance(spec, np.ndarray):
            x = np.atleast_2d(spec)
        else:
            params = spec.get("parameters", spec)
            x = np.array([[float(params[p]) for p in self.param_names]])
        # RBFInterpolator is callable; sklearn has .predict
        if callable(self._model) and not hasattr(self._model, "predict"):
            out = self._model(x)
        else:
            out = self._model.predict(x)
        out = np.asarray(out)
        if out.size == 1:
            return float(out.flat[0])
        return out

    def model_hash(self) -> str:
        """SHA-256 hash for audit trail. Uses file hash if saved, else serialized weights."""
        if self._hash_cache:
            return self._hash_cache
        if self._path and self._path.exists():
            self._hash_cache = model_hash(self._path)
            return self._hash_cache
        # Hash serialized model state (RBF centers/weights or linear coef)
        import hashlib
        import pickle

        data = pickle.dumps(self._model)
        self._hash_cache = hashlib.sha256(data).hexdigest()
        return self._hash_cache


def fit_surrogate(
    X: Union[np.ndarray, List],
    y: Union[np.ndarray, List],
    method: str = "rbf",
    param_names: Optional[List[str]] = None,
    output_metric: str = "output",
    audit_trail: Optional[Any] = None,
    **kwargs: Any,
) -> SurrogateModel:
    """
    Fit RBF or linear surrogate from X, y arrays.

    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        method: "rbf" or "linear"
        param_names: Names for features (for predict spec->vector)
        output_metric: Output metric name
        audit_trail: Optional CalculationAuditTrail; record_ai_model called when provided
        **kwargs: Passed to RBF/LinearRegression

    Returns:
        SurrogateModel with predict(), model_hash()
    """
    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    try:
        from scipy.interpolate import RBFInterpolator
    except ImportError:
        RBFInterpolator = None  # type: ignore

    X = np.asarray(X)
    y = np.asarray(y).ravel()
    if X.ndim == 1:
        X = X.reshape(-1, 1)

    n_features = X.shape[1]
    param_names = param_names or [f"x{i}" for i in range(n_features)]

    if method == "linear":
        pipe = Pipeline([
            ("scale", StandardScaler()),
            ("reg", LinearRegression(**kwargs)),
        ])
        pipe.fit(X, y)
    elif method == "rbf":
        if RBFInterpolator is None:
            raise ImportError("RBF method requires scipy>=1.7. pip install scipy")
        pipe = RBFInterpolator(X, y, **kwargs)
    else:
        raise ValueError(f"Unknown method: {method}. Use 'rbf' or 'linear'.")

    surr = SurrogateModel(
        model=pipe,
        param_names=param_names,
        output_metric=output_metric,
        method=method,
    )

    if audit_trail is not None:
        mh = surr.model_hash()
        config_hash = str(hash((tuple(param_names), output_metric, method)))
        record_ai_model(
            audit_trail,
            name=f"fit_surrogate_{method}",
            version="1.0",
            config_hash=config_hash,
            model_hash=mh,
            param_names=param_names,
            output_metric=output_metric,
        )

    return surr


def surrogate_from_sweep_results(
    results: Union[List[Dict[str, Any]], "SweepResult"],
    param_names: List[str],
    output_metric: str = "k_eff",
    method: str = "rbf",
    output_path: Optional[Union[str, Path]] = None,
    audit_trail: Optional[Any] = None,
    **kwargs: Any,
) -> SurrogateModel:
    """
    Fit surrogate from parameter sweep results (RBF or linear).

    Args:
        results: List of {"parameters": {p: v}, "k_eff": ...} or SweepResult
        param_names: Parameter names to use as features
        output_metric: Output key (e.g., "k_eff")
        method: "rbf" or "linear"
        output_path: Optional path to save .pkl
        audit_trail: Optional; record_ai_model when provided
        **kwargs: Passed to fit_surrogate

    Returns:
        SurrogateModel
    """
    if hasattr(results, "results"):
        results = results.results
    X = []
    y = []
    for r in results:
        if "error" in r:
            continue
        params = r.get("parameters", r)
        row = [float(params[p]) for p in param_names]
        X.append(row)
        y.append(float(r[output_metric]))
    X = np.array(X)
    y = np.array(y)
    surr = fit_surrogate(
        X,
        y,
        method=method,
        param_names=param_names,
        output_metric=output_metric,
        audit_trail=audit_trail,
        **kwargs,
    )
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        import pickle

        with open(output_path, "wb") as f:
            pickle.dump(
                {
                    "model": surr._model,
                    "param_names": surr.param_names,
                    "output_metric": surr.output_metric,
                    "method": surr.method,
                },
                f,
            )
        surr._path = output_path
    return surr
