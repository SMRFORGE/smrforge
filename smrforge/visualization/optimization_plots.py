"""
Optimization visualization helpers.

These helpers are intentionally generic: they accept either a plain sequence
of objective values (history) or an object that provides `.history`.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence, Tuple, Union

import numpy as np

try:
    import matplotlib.pyplot as plt

    _MATPLOTLIB_AVAILABLE = True
except ImportError:  # pragma: no cover
    _MATPLOTLIB_AVAILABLE = False
    plt = None  # type: ignore

try:
    import plotly.graph_objects as go

    _PLOTLY_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PLOTLY_AVAILABLE = False
    go = None  # type: ignore

from smrforge.visualization._viz_common import (
    ensure_matplotlib_available,
    ensure_plotly_available,
)


def _extract_history(history_or_result: Any) -> np.ndarray:
    if history_or_result is None:
        raise ValueError("history_or_result is None")

    hist = getattr(history_or_result, "history", None)
    if hist is not None:
        history_or_result = hist

    # Common SMRForge pattern: history is List[Dict] with best fitness/objective.
    if (
        isinstance(history_or_result, list)
        and history_or_result
        and isinstance(history_or_result[0], dict)
    ):
        keys = ("best_fitness", "objective", "f", "value", "score")
        series = []
        for row in history_or_result:
            if not isinstance(row, dict):
                continue
            val = None
            for k in keys:
                if k in row:
                    val = row[k]
                    break
            if val is None:
                continue
            try:
                series.append(float(val))
            except Exception:
                continue
        arr = np.asarray(series, dtype=float).reshape(-1)
    else:
        arr = np.asarray(history_or_result, dtype=float).reshape(-1)

    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        raise ValueError("No finite history values to plot")
    return arr


def plot_optimization_trace(
    history_or_result: Any,
    *,
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot objective value vs iteration.
    """
    hist = _extract_history(history_or_result)
    it = np.arange(len(hist))
    plot_title = title or "Optimization trace"

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=it, y=hist, mode="lines+markers", name="objective"))
        fig.update_layout(
            title=plot_title, xaxis_title="iteration", yaxis_title="objective"
        )
        return fig

    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (9, 5)))
        ax.plot(it, hist, "o-", linewidth=2, markersize=4)
        ax.set_title(plot_title)
        ax.set_xlabel("iteration")
        ax.set_ylabel("objective")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


__all__ = [
    "plot_optimization_trace",
]
