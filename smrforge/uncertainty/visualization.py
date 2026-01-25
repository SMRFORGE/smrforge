"""
UQ visualization helpers (Plotly + Matplotlib).

These helpers are designed to work with `smrforge.uncertainty.uq.UQResults` and
produce figures suitable for:
- Dash dashboards (Plotly)
- static docs/scripts (Matplotlib)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

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

from smrforge.uncertainty.uq import UQResults
from smrforge.visualization._viz_common import ensure_matplotlib_available, ensure_plotly_available


def _get_output_data(results: UQResults, output_idx: int) -> np.ndarray:
    if output_idx < 0 or output_idx >= len(results.output_names):
        raise ValueError(f"output_idx must be in [0, {len(results.output_names)}), got {output_idx}")
    if results.output_samples is None or results.output_samples.size == 0:
        raise ValueError("results.output_samples is empty")
    return np.asarray(results.output_samples[:, output_idx], dtype=float)


def _percentiles(data: np.ndarray, ps: Sequence[float]) -> Dict[float, float]:
    vals = np.percentile(data, [p * 100 for p in ps])
    return {p: float(v) for p, v in zip(ps, vals)}


def plot_uq_distribution(
    results: UQResults,
    *,
    output_idx: int = 0,
    bins: int = 50,
    backend: str = "plotly",
    title: Optional[str] = None,
    show_stats: bool = True,
    show_percentiles: Tuple[float, float] = (0.05, 0.95),
    **kwargs,
):
    """
    Plot an output distribution (histogram) with optional stats/percentiles.
    """
    data = _get_output_data(results, output_idx)
    name = results.output_names[output_idx]
    plot_title = title or f"UQ distribution: {name}"

    p_lo, p_hi = show_percentiles
    pmap = _percentiles(data, [p_lo, p_hi])
    mean = float(np.mean(data))
    median = float(np.median(data))

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=data, nbinsx=bins, name=name, opacity=0.85))
        if show_stats:
            fig.add_vline(x=mean, line_dash="dash", line_color="red", annotation_text="mean")
            fig.add_vline(x=median, line_dash="dot", line_color="gray", annotation_text="median")
            fig.add_vline(x=pmap[p_lo], line_dash="dash", line_color="orange", annotation_text=f"p{int(p_lo*100)}")
            fig.add_vline(x=pmap[p_hi], line_dash="dash", line_color="orange", annotation_text=f"p{int(p_hi*100)}")
        fig.update_layout(title=plot_title, xaxis_title=name, yaxis_title="count")
        return fig

    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (9, 5)))
        ax.hist(data, bins=bins, alpha=0.85, color="steelblue")
        if show_stats:
            ax.axvline(mean, linestyle="--", color="red", label="mean")
            ax.axvline(median, linestyle=":", color="gray", label="median")
            ax.axvline(pmap[p_lo], linestyle="--", color="orange", label=f"p{int(p_lo*100)}/{int(p_hi*100)}")
            ax.axvline(pmap[p_hi], linestyle="--", color="orange")
            ax.legend()
        ax.set_title(plot_title)
        ax.set_xlabel(name)
        ax.set_ylabel("count")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


def plot_uq_correlation_matrix(
    results: UQResults,
    *,
    include_outputs: bool = True,
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot correlation matrix for parameters (and optionally outputs).
    """
    if results.parameter_samples is None or results.parameter_samples.size == 0:
        raise ValueError("results.parameter_samples is empty")

    X = np.asarray(results.parameter_samples, dtype=float)
    labels: List[str] = list(results.parameter_names)

    if include_outputs:
        Y = np.asarray(results.output_samples, dtype=float)
        X = np.concatenate([X, Y], axis=1)
        labels.extend([f"out:{n}" for n in results.output_names])

    corr = np.corrcoef(X, rowvar=False)
    plot_title = title or "UQ correlation matrix"

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure(
            data=go.Heatmap(
                z=corr,
                x=labels,
                y=labels,
                zmin=-1.0,
                zmax=1.0,
                colorscale=kwargs.get("colorscale", "RdBu"),
                colorbar=dict(title="corr"),
            )
        )
        fig.update_layout(title=plot_title)
        return fig

    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 8)))
        im = ax.imshow(corr, vmin=-1.0, vmax=1.0, cmap=kwargs.get("cmap", "RdBu"))
        ax.set_title(plot_title)
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_yticklabels(labels)
        fig.colorbar(im, ax=ax, label="corr")
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


def plot_uq_sobol_indices(
    sobol_results: Dict[str, Dict[str, Any]],
    *,
    output_name: str,
    parameter_names: Sequence[str],
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot Sobol S1/ST indices (barh).
    """
    if output_name not in sobol_results:
        raise ValueError(f"output_name '{output_name}' not in sobol_results")
    Si = sobol_results[output_name]
    S1 = np.asarray(Si.get("S1", []), dtype=float)
    ST = np.asarray(Si.get("ST", []), dtype=float)
    names = list(parameter_names)
    if S1.size != len(names) or ST.size != len(names):
        raise ValueError("Length mismatch between parameter_names and Sobol arrays")

    plot_title = title or f"Sobol indices: {output_name}"

    order = np.argsort(S1)[::-1]
    names_o = [names[i] for i in order]
    S1_o = S1[order]
    ST_o = ST[order]

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=S1_o[::-1], y=names_o[::-1], orientation="h", name="S1"))
        fig.add_trace(go.Bar(x=ST_o[::-1], y=names_o[::-1], orientation="h", name="ST", opacity=0.6))
        fig.update_layout(title=plot_title, barmode="overlay", xaxis_title="index")
        return fig

    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 6)))
        ax.barh(names_o[::-1], S1_o[::-1], label="S1", color="steelblue")
        ax.barh(names_o[::-1], ST_o[::-1], label="ST", color="coral", alpha=0.5)
        ax.set_title(plot_title)
        ax.set_xlabel("index")
        ax.grid(True, alpha=0.3, axis="x")
        ax.legend()
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


def plot_uq_morris_indices(
    morris_results: Dict[str, Dict[str, Any]],
    *,
    output_name: str,
    parameter_names: Sequence[str],
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot Morris screening indices as mu* vs sigma.
    """
    if output_name not in morris_results:
        raise ValueError(f"output_name '{output_name}' not in morris_results")
    Si = morris_results[output_name]
    mu_star = np.asarray(Si.get("mu_star", []), dtype=float)
    sigma = np.asarray(Si.get("sigma", []), dtype=float)
    names = list(parameter_names)
    if mu_star.size != len(names) or sigma.size != len(names):
        raise ValueError("Length mismatch between parameter_names and Morris arrays")

    plot_title = title or f"Morris indices: {output_name}"

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=mu_star,
                y=sigma,
                mode="markers+text",
                text=names,
                textposition="top center",
                marker=dict(size=10),
                name="morris",
            )
        )
        fig.update_layout(title=plot_title, xaxis_title="mu*", yaxis_title="sigma")
        return fig

    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (8, 6)))
        ax.scatter(mu_star, sigma)
        for n, x, y in zip(names, mu_star, sigma):
            ax.annotate(n, (x, y), fontsize=8)
        ax.set_title(plot_title)
        ax.set_xlabel("mu*")
        ax.set_ylabel("sigma")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


def plot_uq_scatter_matrix_plotly(
    results: UQResults,
    *,
    output_idx: int = 0,
    max_params: int = 4,
    title: Optional[str] = None,
):
    """
    Lightweight Plotly scatter-matrix fallback (no seaborn).
    """
    ensure_plotly_available(_PLOTLY_AVAILABLE)
    if max_params <= 0:
        raise ValueError("max_params must be > 0")
    n_params = min(len(results.parameter_names), max_params)
    if n_params == 0:
        raise ValueError("No parameters available")

    out = _get_output_data(results, output_idx)
    labels = list(results.parameter_names[:n_params]) + [results.output_names[output_idx]]
    X = np.asarray(results.parameter_samples[:, :n_params], dtype=float)
    M = np.column_stack([X, out])

    # Use plotly's Splom if available.
    fig = go.Figure(
        data=go.Splom(
            dimensions=[dict(label=labels[i], values=M[:, i]) for i in range(M.shape[1])],
            marker=dict(size=3, opacity=0.5),
        )
    )
    fig.update_layout(title=title or f"Scatter matrix: {labels[-1]}")
    return fig


__all__ = [
    "plot_uq_distribution",
    "plot_uq_correlation_matrix",
    "plot_uq_sobol_indices",
    "plot_uq_morris_indices",
    "plot_uq_scatter_matrix_plotly",
]

