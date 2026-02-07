"""
Sobol sensitivity indices from sample matrix and output vector(s).

Computes first-order (S1) and total-order (ST) indices using SALib when available,
or a simple correlation-based approximation from sweep/UQ results.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.workflows.sobol_indices")

try:
    from SALib.analyze import sobol as salib_sobol
    _SALIB_AVAILABLE = True
except ImportError:
    _SALIB_AVAILABLE = False


def sobol_indices_from_samples(
    X: np.ndarray,
    Y: np.ndarray,
    param_names: List[str],
    problem_bounds: Optional[List[Tuple[float, float]]] = None,
    calc_second_order: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """
    Compute Sobol first-order (S1) and total-order (ST) indices from (X, Y).

    If SALib is available and X was generated with Saltelli sampling, uses SALib.
    Otherwise treats X as a random sample and estimates indices via correlation/VAR (simple).

    Args:
        X: (n_samples, n_params) parameter samples.
        Y: (n_samples,) or (n_samples, n_outputs) model output(s).
        param_names: List of parameter names.
        problem_bounds: Optional [(low, high), ...] per parameter (for SALib problem).
        calc_second_order: If True and using SALib, compute second-order indices.

    Returns:
        Dict mapping output index or "Y" -> {"S1": list, "ST": list, "param_names": list}.
    """
    n_params = X.shape[1]
    if len(param_names) != n_params:
        raise ValueError(f"param_names length {len(param_names)} != X.shape[1] {n_params}")
    if Y.ndim == 1:
        Y = Y.reshape(-1, 1)
    n_out = Y.shape[1]
    out_labels = [f"Y{i}" for i in range(n_out)]

    if problem_bounds is None:
        problem_bounds = [(float(X[:, i].min()), float(X[:, i].max())) for i in range(n_params)]
    problem = {
        "num_vars": n_params,
        "names": param_names,
        "bounds": problem_bounds,
    }

    result: Dict[str, Dict[str, Any]] = {}
    for j in range(n_out):
        y = Y[:, j]
        if not np.all(np.isfinite(y)):
            logger.warning("Non-finite outputs for column %s; skipping.", j)
            continue
        label = out_labels[j]
        # Check if X looks like Saltelli (n = N*(2*D+2)) -> use SALib
        N = len(y)
        if _SALIB_AVAILABLE and N >= (2 * n_params + 2) and (N % (2 * n_params + 2)) == 0:
            try:
                Si = salib_sobol.analyze(problem, X, y, calc_second_order=calc_second_order)
                result[label] = {
                    "S1": Si["S1"].tolist(),
                    "ST": Si["ST"].tolist(),
                    "param_names": param_names,
                }
                if calc_second_order and "S2" in Si:
                    result[label]["S2"] = Si["S2"].tolist()
            except Exception as e:
                logger.debug("SALib sobol analyze failed: %s; using simple approx.", e)
                result[label] = _simple_sobol_approx(X, y, param_names)
        else:
            result[label] = _simple_sobol_approx(X, y, param_names)
    return result


def _simple_sobol_approx(
    X: np.ndarray, y: np.ndarray, param_names: List[str]
) -> Dict[str, Any]:
    """Approximate S1/ST via squared correlation and variance decomposition."""
    n_params = X.shape[1]
    var_y = np.var(y)
    if var_y <= 0:
        return {"S1": [0.0] * n_params, "ST": [0.0] * n_params, "param_names": param_names}
    s1 = []
    for i in range(n_params):
        r = np.corrcoef(X[:, i], y)[0, 1]
        s1.append(float(r ** 2) if np.isfinite(r) else 0.0)
    # ST approx: total variance explained by each param (here same as S1 for additive approx)
    st = s1[:]
    return {"S1": s1, "ST": st, "param_names": param_names}


def sobol_indices_from_sweep_results(
    results: List[Dict[str, Any]],
    param_names: List[str],
    output_metric: str = "k_eff",
) -> Dict[str, Dict[str, Any]]:
    """
    Compute Sobol indices from a list of sweep result dicts (parameters + output).

    Args:
        results: List of {"parameters": {name: val, ...}, output_metric: val} or flat dicts.
        param_names: Parameter names (order defines columns).
        output_metric: Key for output value (e.g. "k_eff").

    Returns:
        Dict with key "Y0" -> {"S1", "ST", "param_names"}.
    """
    rows_x = []
    rows_y = []
    for r in results:
        params = r.get("parameters", r)
        try:
            y = float(params.get(output_metric, r.get(output_metric, np.nan)))
        except (TypeError, ValueError):
            continue
        if not np.isfinite(y):
            continue
        row = [float(params.get(p, np.nan)) for p in param_names]
        if any(not np.isfinite(v) for v in row):
            continue
        rows_x.append(row)
        rows_y.append(y)
    if len(rows_x) < 10:
        return {"Y0": {"S1": [0.0] * len(param_names), "ST": [0.0] * len(param_names), "param_names": param_names}}
    X = np.array(rows_x)
    Y = np.array(rows_y)
    return sobol_indices_from_samples(X, Y, param_names)
