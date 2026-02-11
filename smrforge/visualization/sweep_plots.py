"""
Parameter sweep visualization helpers.

Designed to work with `smrforge.workflows.parameter_sweep.SweepResult` and
to return either Plotly figures (for dashboards) or Matplotlib figures
(for static docs/scripts).
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

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

from ._viz_common import ensure_matplotlib_available, ensure_plotly_available


def _maybe_asdict(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    return obj


def _flatten_parameters_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flatten a nested `parameters` dict column into top-level columns.

    `ParameterSweep` stores results like:
      {"parameters": {"enrichment": 0.195, ...}, "k_eff": ..., "success": True}
    """
    if "parameters" not in df.columns:
        return df

    # Best-effort: only flatten if column looks dict-like.
    params_series = df["parameters"]
    if params_series.isna().all():
        return df.drop(columns=["parameters"])

    try:
        expanded = params_series.apply(
            lambda x: x if isinstance(x, dict) else {}
        ).apply(pd.Series)
    except Exception:
        return df

    # Avoid overwriting existing columns; suffix if needed.
    for col in expanded.columns:
        if col in df.columns:
            expanded = expanded.rename(columns={col: f"param_{col}"})

    return pd.concat([df.drop(columns=["parameters"]), expanded], axis=1)


def _to_dataframe(
    sweep_result: Any,
    *,
    include_failed: bool = False,
) -> pd.DataFrame:
    """
    Convert a SweepResult (or compatible inputs) into a flat DataFrame.
    """
    if sweep_result is None:
        return pd.DataFrame()

    # SweepResult has .to_dataframe() in our codebase.
    to_df = getattr(sweep_result, "to_dataframe", None)
    if callable(to_df):
        df = to_df()
    elif isinstance(sweep_result, pd.DataFrame):
        df = sweep_result.copy()
    elif isinstance(sweep_result, (list, tuple)):
        df = pd.DataFrame([_maybe_asdict(r) for r in sweep_result])
    elif isinstance(sweep_result, dict):
        # Accept {"results": [...], ...} shapes
        if "results" in sweep_result and isinstance(sweep_result["results"], list):
            df = pd.DataFrame([_maybe_asdict(r) for r in sweep_result["results"]])
        else:
            df = pd.DataFrame([_maybe_asdict(sweep_result)])
    else:
        df = pd.DataFrame([_maybe_asdict(sweep_result)])

    if df.empty:
        return df

    df = _flatten_parameters_column(df)

    if not include_failed and "success" in df.columns:
        # Some cases may omit success; keep them unless explicitly False.
        df = df[df["success"] != False]  # noqa: E712

    return df


def plot_sweep_heatmap(
    sweep_result: Any,
    *,
    x_param: str,
    y_param: str,
    metric: str = "k_eff",
    agg: str = "mean",
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot a 2D sweep heatmap for a metric over two parameters.
    """
    df = _to_dataframe(sweep_result)
    if df.empty:
        raise ValueError("Sweep result is empty; cannot plot heatmap.")

    if (
        x_param not in df.columns
        or y_param not in df.columns
        or metric not in df.columns
    ):
        raise ValueError(
            f"Missing required columns. Need: {x_param}, {y_param}, {metric}. "
            f"Have: {list(df.columns)}"
        )

    pivot = pd.pivot_table(
        df, values=metric, index=y_param, columns=x_param, aggfunc=agg
    )
    pivot = pivot.sort_index(axis=0).sort_index(axis=1)

    plot_title = title or f"{metric} heatmap"

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure(
            data=go.Heatmap(
                z=pivot.values,
                x=(
                    pivot.columns.astype(float)
                    if np.issubdtype(pivot.columns.dtype, np.number)
                    else pivot.columns
                ),
                y=(
                    pivot.index.astype(float)
                    if np.issubdtype(pivot.index.dtype, np.number)
                    else pivot.index
                ),
                colorscale=kwargs.get("colorscale", "Viridis"),
                colorbar=dict(title=metric),
            )
        )
        fig.update_layout(title=plot_title, xaxis_title=x_param, yaxis_title=y_param)
        return fig

    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (8, 6)))
        im = ax.imshow(
            pivot.values,
            aspect="auto",
            origin="lower",
            cmap=kwargs.get("cmap", "viridis"),
        )
        ax.set_title(plot_title)
        ax.set_xlabel(x_param)
        ax.set_ylabel(y_param)
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(list(pivot.columns), rotation=45, ha="right")
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(list(pivot.index))
        fig.colorbar(im, ax=ax, label=metric)
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


def plot_sweep_tornado(
    sweep_result: Any,
    *,
    metric: str = "k_eff",
    params: Optional[Sequence[str]] = None,
    mode: str = "range",  # 'range' | 'corr'
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Tornado-style sensitivity plot over sweep results.

    - mode='range': for each parameter, compute (max - min) of the metric's mean
      across that parameter's unique values.
    - mode='corr': absolute Pearson correlation between parameter and metric.
    """
    df = _to_dataframe(sweep_result)
    if df.empty:
        raise ValueError("Sweep result is empty; cannot plot tornado.")

    if metric not in df.columns:
        raise ValueError(f"Metric '{metric}' not present. Have: {list(df.columns)}")

    # Infer parameter columns: numeric columns excluding metrics/success.
    if params is None:
        # Treat anything numeric but not the metric itself as candidate param.
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        params = [c for c in numeric_cols if c not in {metric} and c != "success"]

    params = list(params)
    if not params:
        raise ValueError("No parameter columns found for tornado plot.")

    effects: List[Tuple[str, float]] = []
    y = pd.to_numeric(df[metric], errors="coerce")

    for p in params:
        if p not in df.columns:
            continue
        x = pd.to_numeric(df[p], errors="coerce")
        ok = ~(x.isna() | y.isna())
        if not ok.any():
            continue

        if mode == "corr":
            if ok.sum() < 2:
                val = 0.0
            else:
                val = float(abs(np.corrcoef(x[ok].to_numpy(), y[ok].to_numpy())[0, 1]))
        elif mode == "range":
            grouped = df.loc[ok, [p, metric]].groupby(p)[metric].mean()
            val = float(grouped.max() - grouped.min()) if len(grouped) >= 2 else 0.0
        else:
            raise ValueError("mode must be 'range' or 'corr'")

        if np.isfinite(val):
            effects.append((p, val))

    if not effects:
        raise ValueError("No effects computed; check parameter columns and data.")

    effects.sort(key=lambda kv: kv[1], reverse=True)
    labels = [k for k, _ in effects]
    values = [v for _, v in effects]

    plot_title = title or (f"Tornado sensitivity ({mode}) for {metric}")

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure(
            data=go.Bar(
                x=values[::-1],
                y=labels[::-1],
                orientation="h",
                marker=dict(color=kwargs.get("color", "steelblue")),
            )
        )
        fig.update_layout(
            title=plot_title,
            xaxis_title=("|corr|" if mode == "corr" else "Δ metric"),
            yaxis_title="Parameter",
        )
        return fig

    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (9, 6)))
        ax.barh(labels[::-1], values[::-1], color=kwargs.get("color", "steelblue"))
        ax.set_title(plot_title)
        ax.set_xlabel("|corr|" if mode == "corr" else "Δ metric")
        ax.grid(True, alpha=0.3, axis="x")
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


def _pareto_front_mask(
    x: np.ndarray,
    y: np.ndarray,
    *,
    maximize_x: bool,
    maximize_y: bool,
) -> np.ndarray:
    """
    Return a boolean mask marking Pareto-optimal points for 2 objectives.
    """
    n = len(x)
    keep = np.ones(n, dtype=bool)
    for i in range(n):
        if not keep[i]:
            continue
        for j in range(n):
            if i == j or not keep[i]:
                continue
            better_or_equal_x = x[j] >= x[i] if maximize_x else x[j] <= x[i]
            better_or_equal_y = y[j] >= y[i] if maximize_y else y[j] <= y[i]
            strictly_better = (x[j] != x[i]) or (y[j] != y[i])
            if better_or_equal_x and better_or_equal_y and strictly_better:
                keep[i] = False
    return keep


def plot_sweep_pareto(
    sweep_result: Any,
    *,
    metric_x: str,
    metric_y: str,
    maximize_x: bool = True,
    maximize_y: bool = False,
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot a 2-objective Pareto front from sweep results.
    """
    df = _to_dataframe(sweep_result)
    if df.empty:
        raise ValueError("Sweep result is empty; cannot plot Pareto.")

    for col in (metric_x, metric_y):
        if col not in df.columns:
            raise ValueError(
                f"Missing '{col}' in sweep results. Have: {list(df.columns)}"
            )

    x = pd.to_numeric(df[metric_x], errors="coerce").to_numpy()
    y = pd.to_numeric(df[metric_y], errors="coerce").to_numpy()
    ok = np.isfinite(x) & np.isfinite(y)
    x = x[ok]
    y = y[ok]
    if x.size == 0:
        raise ValueError("No finite points to plot for Pareto front.")

    mask = _pareto_front_mask(x, y, maximize_x=maximize_x, maximize_y=maximize_y)

    plot_title = title or f"Pareto front: {metric_x} vs {metric_y}"

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=x, y=y, mode="markers", name="All", marker=dict(size=7, opacity=0.6)
            )
        )
        fig.add_trace(
            go.Scatter(
                x=x[mask], y=y[mask], mode="markers", name="Pareto", marker=dict(size=9)
            )
        )
        fig.update_layout(title=plot_title, xaxis_title=metric_x, yaxis_title=metric_y)
        return fig

    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (8, 6)))
        ax.scatter(x, y, s=20, alpha=0.6, label="All")
        ax.scatter(x[mask], y[mask], s=40, label="Pareto")
        ax.set_title(plot_title)
        ax.set_xlabel(metric_x)
        ax.set_ylabel(metric_y)
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


def plot_sweep_correlation_matrix(
    sweep_result: Any,
    *,
    include_metrics: Optional[Sequence[str]] = None,
    include_params: Optional[Sequence[str]] = None,
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot a correlation matrix over selected parameters/metrics.

    If `sweep_result.summary_stats['correlations']` exists it will be used as a hint,
    but we recompute from the underlying DataFrame to ensure consistent ordering.
    """
    df = _to_dataframe(sweep_result)
    if df.empty:
        raise ValueError("Sweep result is empty; cannot plot correlation matrix.")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c != "success"]

    if include_params is None and include_metrics is None:
        cols = numeric_cols
    else:
        cols: List[str] = []
        if include_params:
            cols.extend([c for c in include_params if c in df.columns])
        if include_metrics:
            cols.extend([c for c in include_metrics if c in df.columns])
        cols = [c for c in cols if c in numeric_cols]

    if len(cols) < 2:
        raise ValueError("Need at least two numeric columns to compute correlations.")

    corr = df[cols].corr()
    plot_title = title or "Correlation matrix"

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure(
            data=go.Heatmap(
                z=corr.values,
                x=list(corr.columns),
                y=list(corr.index),
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
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (8, 7)))
        im = ax.imshow(
            corr.values, vmin=-1.0, vmax=1.0, cmap=kwargs.get("cmap", "RdBu")
        )
        ax.set_title(plot_title)
        ax.set_xticks(range(len(cols)))
        ax.set_yticks(range(len(cols)))
        ax.set_xticklabels(cols, rotation=45, ha="right")
        ax.set_yticklabels(cols)
        fig.colorbar(im, ax=ax, label="corr")
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


__all__ = [
    "plot_sweep_heatmap",
    "plot_sweep_tornado",
    "plot_sweep_pareto",
    "plot_sweep_correlation_matrix",
]
