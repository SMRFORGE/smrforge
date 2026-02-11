"""
Pareto front summary report and knee-point selection.

Exports a short summary (n_designs, trade-off, optional knee point) from
Pareto-optimal points for two objectives.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def pareto_knee_point(
    x: np.ndarray,
    y: np.ndarray,
    *,
    maximize_x: bool = True,
    maximize_y: bool = True,
) -> Optional[int]:
    """
    Select a knee point on the 2D Pareto front: best compromise (normalized distance to ideal).

    Ideal is (max(x), max(y)) if both maximize, else (min(x), max(y)) etc.
    We normalize each axis to [0,1] then pick the Pareto point closest to (1,1) in normalized space
    (or the point that maximizes minimum of the two normalized coordinates).

    Returns:
        Index into (x, y) of the knee point, or None if empty.
    """
    if len(x) == 0 or len(y) == 0 or len(x) != len(y):
        return None
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    xmin, xmax = x.min(), x.max()
    ymin, ymax = y.min(), y.max()
    if xmax <= xmin:
        xnorm = np.ones_like(x)
    else:
        xnorm = (x - xmin) / (xmax - xmin)
        if not maximize_x:
            xnorm = 1.0 - xnorm
    if ymax <= ymin:
        ynorm = np.ones_like(y)
    else:
        ynorm = (y - ymin) / (ymax - ymin)
        if not maximize_y:
            ynorm = 1.0 - ynorm
    # Knee = point that maximizes min(xnorm, ynorm) (balanced) or sum (if prefer)
    score = np.minimum(xnorm, ynorm)
    return int(np.argmax(score))


def pareto_summary_report(
    pareto_points: List[Dict[str, Any]],
    metric_x: str,
    metric_y: str,
    knee_index: Optional[int] = None,
    maximize_x: bool = True,
    maximize_y: bool = True,
) -> Dict[str, Any]:
    """
    Build a summary report for a Pareto set.

    Args:
        pareto_points: List of result dicts on the Pareto front.
        metric_x: Name of first metric.
        metric_y: Name of second metric.
        knee_index: Optional index of knee point in pareto_points.
        maximize_x, maximize_y: Whether each metric is "higher is better".

    Returns:
        Dict with n_pareto, metric_x, metric_y, trade_off_summary, knee_point (dict or null), extremes.
    """
    if not pareto_points:
        return {
            "n_pareto": 0,
            "metric_x": metric_x,
            "metric_y": metric_y,
            "trade_off_summary": "No Pareto points.",
            "knee_point": None,
            "extremes": {},
        }

    def get_v(d: Dict, k: str) -> float:
        v = d.get(k)
        if v is None and "parameters" in d:
            v = d["parameters"].get(k)
        try:
            return float(v)
        except (TypeError, ValueError):
            return np.nan

    x_vals = [get_v(p, metric_x) for p in pareto_points]
    y_vals = [get_v(p, metric_y) for p in pareto_points]
    x_vals = [v for v in x_vals if np.isfinite(v)]
    y_vals = [v for v in y_vals if np.isfinite(v)]
    if len(x_vals) != len(pareto_points) or len(y_vals) != len(pareto_points):
        x_vals = [get_v(p, metric_x) for p in pareto_points]
        y_vals = [get_v(p, metric_y) for p in pareto_points]
    x_arr = np.array(x_vals)
    y_arr = np.array(y_vals)
    if knee_index is None and len(x_arr) > 0:
        knee_index = pareto_knee_point(
            x_arr, y_arr, maximize_x=maximize_x, maximize_y=maximize_y
        )
    knee_point = (
        pareto_points[knee_index]
        if knee_index is not None and 0 <= knee_index < len(pareto_points)
        else None
    )
    trade = (
        f"Trade-off between {metric_x} and {metric_y}: "
        f"{len(pareto_points)} Pareto-optimal designs. "
    )
    if len(x_arr) >= 2:
        trade += (
            f"{metric_x} range [{float(x_arr.min()):.4g}, {float(x_arr.max()):.4g}]; "
        )
        trade += (
            f"{metric_y} range [{float(y_arr.min()):.4g}, {float(y_arr.max()):.4g}]."
        )
    return {
        "n_pareto": len(pareto_points),
        "metric_x": metric_x,
        "metric_y": metric_y,
        "trade_off_summary": trade,
        "knee_point": knee_point,
        "extremes": (
            {
                "best_x": (
                    pareto_points[int(np.argmax(x_arr))]
                    if maximize_x
                    else pareto_points[int(np.argmin(x_arr))]
                ),
                "best_y": (
                    pareto_points[int(np.argmax(y_arr))]
                    if maximize_y
                    else pareto_points[int(np.argmin(y_arr))]
                ),
            }
            if len(pareto_points) > 0
            else {}
        ),
    }
