"""
Sensitivity analysis workflows: one-at-a-time (OAT) and Morris-style screening.

Ranks parameters by effect on selected outputs (e.g. k_eff, power peak) using
sweep results or explicit model runs.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.workflows.sensitivity")

try:
    from SALib.analyze import morris as salib_morris
    from SALib.sample import morris as salib_morris_sample
    _SALIB_AVAILABLE = True
except ImportError:
    _SALIB_AVAILABLE = False


@dataclass
class SensitivityRanking:
    """Parameter ranking by sensitivity (e.g. OAT or Morris mu_star)."""
    parameter: str
    effect: float  # absolute or relative effect on output
    rank: int  # 1 = most sensitive
    method: str = "oat"


def one_at_a_time_from_sweep(
    sweep_results: List[Dict[str, Any]],
    param_names: List[str],
    output_metric: str = "k_eff",
    baseline: Optional[Dict[str, float]] = None,
) -> List[SensitivityRanking]:
    """
    Rank parameters by one-at-a-time sensitivity using existing sweep results.

    Uses finite-difference style: for each parameter, finds pairs of points
    that differ only in that parameter and computes (delta_output / delta_param).
    Then ranks by mean absolute effect (normalized by param range if available).

    Args:
        sweep_results: List of dicts with parameter and metric keys.
        param_names: Parameter names to rank.
        output_metric: Metric to use as output (e.g. "k_eff", "power_thermal_mw").
        baseline: Optional baseline point; if None, first result is used.

    Returns:
        List of SensitivityRanking sorted by effect (highest first).
    """
    if not sweep_results or not param_names:
        return []
    # Build array of param vectors and output
    param_arrays: Dict[str, List[float]] = {p: [] for p in param_names}
    out_list: List[float] = []
    for r in sweep_results:
        params = r.get("parameters", r)
        try:
            y = float(params.get(output_metric, r.get(output_metric, np.nan)))
        except (TypeError, ValueError):
            y = np.nan
        if not np.isfinite(y):
            continue
        out_list.append(y)
        for p in param_names:
            v = params.get(p, np.nan)
            try:
                param_arrays[p].append(float(v))
            except (TypeError, ValueError):
                param_arrays[p].append(np.nan)
    n = len(out_list)
    if n < 2:
        return []
    Y = np.array(out_list)
    effects: Dict[str, float] = {}
    for p in param_names:
        Xp = np.array(param_arrays[p])
        # Simple measure: std of output when grouping by discretized param (or correlation)
        if np.all(np.isfinite(Xp)) and np.all(np.isfinite(Y)):
            effects[p] = float(np.abs(np.corrcoef(Xp, Y)[0, 1])) if np.std(Xp) > 0 and np.std(Y) > 0 else 0.0
        else:
            effects[p] = 0.0
    # Rank by effect (higher = more sensitive)
    order = sorted(effects.keys(), key=lambda k: -effects[k])
    return [
        SensitivityRanking(parameter=p, effect=effects[p], rank=i + 1, method="oat")
        for i, p in enumerate(order)
    ]


def morris_screening(
    model: Callable[[Dict[str, float]], float],
    param_bounds: Dict[str, Tuple[float, float]],
    n_trajectories: int = 10,
    output_name: str = "output",
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Morris screening: run SALib Morris if available, return mu, mu_star, sigma per parameter.

    Args:
        model: function that takes a dict of param name -> value and returns a scalar.
        param_bounds: dict of param name -> (low, high).
        n_trajectories: number of Morris trajectories.
        output_name: label for the output in the returned dict.
        seed: random seed.

    Returns:
        Dict with "param_names", "mu", "mu_star", "sigma", "rank" (by mu_star), and "problem" for SALib.
    """
    if not _SALIB_AVAILABLE:
        raise ImportError("SALib required for Morris screening: pip install SALib")
    logger.debug("Morris screening: n_trajectories=%s, n_params=%s", n_trajectories, len(param_bounds))
    names = list(param_bounds.keys())
    bounds = [param_bounds[n] for n in names]
    problem = {
        "num_vars": len(names),
        "names": names,
        "bounds": bounds,
    }
    X = salib_morris_sample.sample(problem, N=n_trajectories, seed=seed)
    Y = np.array([model(dict(zip(names, row))) for row in X])
    Si = salib_morris.analyze(problem, X, Y)
    mu = Si["mu"]
    mu_star = Si["mu_star"]
    sigma = Si["sigma"]
    order = np.argsort(-np.abs(mu_star))
    rank = np.empty_like(order, dtype=int)
    rank[order] = np.arange(1, len(order) + 1)
    return {
        "param_names": names,
        "mu": mu.tolist(),
        "mu_star": mu_star.tolist(),
        "sigma": sigma.tolist() if sigma is not None else None,
        "rank": rank.tolist(),
        "output_name": output_name,
        "problem": problem,
    }
