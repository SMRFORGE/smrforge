"""
Mesh diagnostics visualization.

These helpers focus on mesh quality summaries and distributions. They work with:
- `smrforge.geometry.mesh_generation.MeshQuality`
- arrays of cell sizes (lengths/areas/volumes) when available
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Optional, Sequence, Tuple, Union

import numpy as np

try:
    import matplotlib.pyplot as plt

    _MATPLOTLIB_AVAILABLE = True
except ImportError:  # pragma: no cover
    _MATPLOTLIB_AVAILABLE = False
    plt = None  # type: ignore

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    _PLOTLY_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PLOTLY_AVAILABLE = False
    go = None  # type: ignore
    make_subplots = None  # type: ignore

from smrforge.geometry.mesh_generation import MeshQuality
from smrforge.visualization._viz_common import ensure_matplotlib_available, ensure_plotly_available


_DEFAULT_THRESHOLDS = {
    "min_angle": (">=", 10.0),
    "max_angle": ("<=", 170.0),
    "aspect_ratio": ("<=", 10.0),
    "skewness": (">=", 0.3),
}


def _quality_to_dict(quality: Union[MeshQuality, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(quality, MeshQuality):
        return asdict(quality)
    if is_dataclass(quality):
        return asdict(quality)
    if isinstance(quality, dict):
        return dict(quality)
    raise ValueError(f"quality must be MeshQuality or dict, got {type(quality)}")


def plot_mesh_quality_metrics(
    quality: Union[MeshQuality, Dict[str, Any]],
    *,
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot mesh quality metrics as a compact summary chart.
    """
    q = _quality_to_dict(quality)
    metrics = {k: float(q[k]) for k in ("min_angle", "max_angle", "aspect_ratio", "skewness", "jacobian") if k in q}
    if not metrics:
        raise ValueError("No recognized metrics found in quality")

    plot_title = title or "Mesh quality metrics"

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=list(metrics.keys()), y=list(metrics.values()), marker_color="steelblue"))
        # Add threshold annotations where available
        ann = []
        for k, (op, thr) in _DEFAULT_THRESHOLDS.items():
            if k in metrics:
                ann.append(f"{k} {op} {thr}")
        if ann:
            fig.update_layout(
                annotations=[
                    dict(
                        text="; ".join(ann),
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=1.15,
                        showarrow=False,
                        font=dict(size=11),
                    )
                ]
            )
        fig.update_layout(title=plot_title, xaxis_title="metric", yaxis_title="value")
        return fig

    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (9, 4)))
        ax.bar(list(metrics.keys()), list(metrics.values()), color="steelblue")
        ax.set_title(plot_title)
        ax.set_xlabel("metric")
        ax.set_ylabel("value")
        ax.grid(True, alpha=0.3, axis="y")
        ax.tick_params(axis="x", rotation=30)
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


def plot_mesh_cell_size_distribution(
    sizes: np.ndarray,
    *,
    backend: str = "plotly",
    log_scale: bool = True,
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot a distribution of cell sizes (length/area/volume) if available.
    """
    s = np.asarray(sizes, dtype=float).reshape(-1)
    s = s[np.isfinite(s)]
    if s.size == 0:
        raise ValueError("sizes must contain at least one finite value")

    plot_title = title or "Cell size distribution"
    bins = int(kwargs.get("bins", 50))

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=s, nbinsx=bins, name="size"))
        fig.update_layout(title=plot_title, xaxis_title="size", yaxis_title="count")
        if log_scale:
            fig.update_xaxes(type="log")
        return fig

    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (9, 4)))
        ax.hist(s, bins=bins, color="steelblue", alpha=0.85)
        ax.set_title(plot_title)
        ax.set_xlabel("size")
        ax.set_ylabel("count")
        if log_scale:
            ax.set_xscale("log")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


def plot_mesh_verification_dashboard(
    *,
    quality: Optional[Union[MeshQuality, Dict[str, Any]]] = None,
    sizes: Optional[np.ndarray] = None,
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Create a small dashboard combining quality metrics + optional size distribution.
    """
    plot_title = title or "Mesh verification dashboard"

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        if make_subplots is None:
            raise ImportError("plotly.subplots is required")

        rows = 2 if (quality is not None and sizes is not None) else 1
        fig = make_subplots(
            rows=rows,
            cols=1,
            subplot_titles=(
                ["Quality metrics"]
                + (["Cell size distribution"] if (quality is not None and sizes is not None) else [])
            ),
            vertical_spacing=0.12,
        )

        if quality is not None:
            qfig = plot_mesh_quality_metrics(quality, backend="plotly")
            for tr in qfig.data:
                fig.add_trace(tr, row=1, col=1)
            fig.update_xaxes(title_text="metric", row=1, col=1)
            fig.update_yaxes(title_text="value", row=1, col=1)

        if quality is None and sizes is not None:
            sfig = plot_mesh_cell_size_distribution(sizes, backend="plotly", log_scale=bool(kwargs.get("log_scale", True)))
            for tr in sfig.data:
                fig.add_trace(tr, row=1, col=1)
        elif quality is not None and sizes is not None:
            sfig = plot_mesh_cell_size_distribution(sizes, backend="plotly", log_scale=bool(kwargs.get("log_scale", True)))
            for tr in sfig.data:
                fig.add_trace(tr, row=2, col=1)

        fig.update_layout(title=plot_title, height=650 if rows == 2 else 350)
        return fig

    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        if quality is not None and sizes is not None:
            fig, axes = plt.subplots(2, 1, figsize=kwargs.get("figsize", (9, 8)))
            qfig, qax = plot_mesh_quality_metrics(quality, backend="matplotlib")
            plt.close(qfig)
            sfig, sax = plot_mesh_cell_size_distribution(sizes, backend="matplotlib", log_scale=bool(kwargs.get("log_scale", True)))
            plt.close(sfig)
            # Replot directly for simplicity
            q = _quality_to_dict(quality)
            metrics = {k: float(q[k]) for k in ("min_angle", "max_angle", "aspect_ratio", "skewness", "jacobian") if k in q}
            axes[0].bar(list(metrics.keys()), list(metrics.values()), color="steelblue")
            axes[0].set_title("Quality metrics")
            axes[0].grid(True, alpha=0.3, axis="y")
            s = np.asarray(sizes, dtype=float).reshape(-1)
            s = s[np.isfinite(s)]
            axes[1].hist(s, bins=int(kwargs.get("bins", 50)), color="steelblue", alpha=0.85)
            axes[1].set_title("Cell size distribution")
            if kwargs.get("log_scale", True):
                axes[1].set_xscale("log")
            axes[1].grid(True, alpha=0.3)
            fig.suptitle(plot_title)
            fig.tight_layout()
            return fig, axes
        # Fallback single-panel
        if quality is not None:
            return plot_mesh_quality_metrics(quality, backend="matplotlib", title=plot_title, **kwargs)
        if sizes is not None:
            return plot_mesh_cell_size_distribution(sizes, backend="matplotlib", title=plot_title, **kwargs)
        raise ValueError("Provide at least one of: quality, sizes")

    raise ValueError(f"Unknown backend: {backend}")


__all__ = [
    "plot_mesh_quality_metrics",
    "plot_mesh_cell_size_distribution",
    "plot_mesh_verification_dashboard",
]

