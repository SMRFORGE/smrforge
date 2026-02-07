"""
Visualizations for design-study features: sensitivity, Pareto (with knee),
safety margins, scenario comparison, and design-space atlas.

Works with workflow outputs from smrforge.workflows (sensitivity, pareto_report,
safety_report, scenario_design, atlas) and supports Plotly and Matplotlib backends.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np

try:
    import matplotlib.pyplot as plt
    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False
    plt = None  # type: ignore

try:
    import plotly.graph_objects as go
    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False
    go = None  # type: ignore

from ._viz_common import ensure_matplotlib_available, ensure_plotly_available


def plot_sensitivity_ranking(
    rankings: Union[List[Any], List[Dict[str, Any]]],
    *,
    title: Optional[str] = None,
    backend: str = "plotly",
    **kwargs,
) -> Any:
    """
    Bar chart of parameter sensitivity ranking (e.g. from one_at_a_time_from_sweep or Morris mu_star).

    Args:
        rankings: List of SensitivityRanking or dicts with 'parameter' and 'effect' (or 'mu_star').
        title: Plot title.
        backend: 'plotly' or 'matplotlib'.

    Returns:
        Plotly Figure or (matplotlib Figure, Axes).
    """
    params = []
    effects = []
    for r in rankings:
        if hasattr(r, "parameter"):
            params.append(r.parameter)
            effects.append(getattr(r, "effect", getattr(r, "mu_star", 0.0)))
        else:
            params.append(r.get("parameter", ""))
            effects.append(r.get("effect", r.get("mu_star", 0.0)))
    if not params:
        raise ValueError("rankings is empty")
    effects = np.asarray(effects, dtype=float)
    order = np.argsort(effects)[::-1]
    params = [params[i] for i in order]
    effects = effects[order]
    plot_title = title or "Sensitivity ranking"

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure(go.Bar(x=effects, y=params, orientation="h"))
        fig.update_layout(title=plot_title, xaxis_title="effect", yaxis_title="", margin=dict(l=120))
        return fig
    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (8, max(4, len(params) * 0.35))))
        ax.barh(params, effects, color="steelblue", alpha=0.85)
        ax.set_title(plot_title)
        ax.set_xlabel("effect")
        ax.grid(True, alpha=0.3, axis="x")
        fig.tight_layout()
        return fig, ax
    raise ValueError(f"Unknown backend: {backend}")


def plot_sobol_workflow(
    sobol_dict: Dict[str, Dict[str, Any]],
    *,
    output_key: str = "Y0",
    title: Optional[str] = None,
    backend: str = "plotly",
    **kwargs,
) -> Any:
    """
    Plot Sobol S1/ST indices from workflow sobol_indices_from_sweep_results output.

    Args:
        sobol_dict: Dict mapping output key -> {"S1": [...], "ST": [...], "param_names": [...]}.
        output_key: Key to plot (e.g. "Y0").
        title: Plot title.
        backend: 'plotly' or 'matplotlib'.
    """
    if output_key not in sobol_dict:
        raise ValueError(f"output_key '{output_key}' not in sobol_dict. Keys: {list(sobol_dict.keys())}")
    Si = sobol_dict[output_key]
    names = Si.get("param_names", [])
    S1 = np.asarray(Si.get("S1", []), dtype=float)
    ST = np.asarray(Si.get("ST", []), dtype=float)
    if len(names) != len(S1) or len(names) != len(ST):
        raise ValueError("param_names length does not match S1/ST")
    order = np.argsort(S1)[::-1]
    names = [names[i] for i in order]
    S1 = S1[order]
    ST = ST[order]
    plot_title = title or f"Sobol indices: {output_key}"

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=S1[::-1], y=names[::-1], orientation="h", name="S1"))
        fig.add_trace(go.Bar(x=ST[::-1], y=names[::-1], orientation="h", name="ST", opacity=0.6))
        fig.update_layout(title=plot_title, barmode="overlay", xaxis_title="index", margin=dict(l=120))
        return fig
    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (8, max(4, len(names) * 0.35))))
        ax.barh(names[::-1], S1[::-1], label="S1", color="steelblue")
        ax.barh(names[::-1], ST[::-1], label="ST", color="coral", alpha=0.5)
        ax.set_title(plot_title)
        ax.set_xlabel("index")
        ax.legend()
        ax.grid(True, alpha=0.3, axis="x")
        fig.tight_layout()
        return fig, ax
    raise ValueError(f"Unknown backend: {backend}")


def plot_pareto_with_knee(
    x: np.ndarray,
    y: np.ndarray,
    pareto_mask: np.ndarray,
    knee_index: Optional[int] = None,
    *,
    metric_x: str = "x",
    metric_y: str = "y",
    maximize_x: bool = True,
    maximize_y: bool = True,
    title: Optional[str] = None,
    backend: str = "plotly",
    **kwargs,
) -> Any:
    """
    Pareto front scatter with optional knee point highlighted.

    Args:
        x, y: Full objective arrays.
        pareto_mask: Boolean mask of Pareto-optimal points (same length as x, y).
        knee_index: Index into the Pareto subset (into np.where(pareto_mask)[0]) to mark as knee.
        metric_x, metric_y: Axis labels.
        title: Plot title.
        backend: 'plotly' or 'matplotlib'.
    """
    x = np.asarray(x)
    y = np.asarray(y)
    plot_title = title or f"Pareto front: {metric_x} vs {metric_y}"
    x_pareto = x[pareto_mask]
    y_pareto = y[pareto_mask]
    knee_x = knee_y = None
    if knee_index is not None and 0 <= knee_index < len(x_pareto):
        knee_x = x_pareto[knee_index]
        knee_y = y_pareto[knee_index]

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=y, mode="markers", name="All", marker=dict(size=6, opacity=0.5)))
        fig.add_trace(go.Scatter(x=x_pareto, y=y_pareto, mode="markers", name="Pareto", marker=dict(size=10)))
        if knee_x is not None:
            fig.add_trace(go.Scatter(
                x=[knee_x], y=[knee_y], mode="markers", name="Knee",
                marker=dict(size=16, symbol="star", color="gold", line=dict(width=2, color="darkorange"))
            ))
        fig.update_layout(title=plot_title, xaxis_title=metric_x, yaxis_title=metric_y)
        return fig
    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (8, 6)))
        ax.scatter(x, y, s=20, alpha=0.5, label="All")
        ax.scatter(x_pareto, y_pareto, s=60, label="Pareto")
        if knee_x is not None:
            ax.scatter([knee_x], [knee_y], s=200, marker="*", c="gold", edgecolors="darkorange", linewidths=2, label="Knee")
        ax.set_title(plot_title)
        ax.set_xlabel(metric_x)
        ax.set_ylabel(metric_y)
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return fig, ax
    raise ValueError(f"Unknown backend: {backend}")


def plot_safety_margins(
    report: Union[Any, Dict[str, Any]],
    *,
    title: Optional[str] = None,
    backend: str = "plotly",
    **kwargs,
) -> Any:
    """
    Bar chart of constraint value vs limit (margins) from SafetyMarginReport.

    Args:
        report: SafetyMarginReport or its to_dict() with 'margins' list.
        title: Plot title.
        backend: 'plotly' or 'matplotlib'.
    """
    if hasattr(report, "to_dict"):
        report = report.to_dict()
    margins = report.get("margins", [])
    if not margins:
        raise ValueError("report has no margins")
    names = []
    values = []
    limits = []
    within = []
    for m in margins:
        names.append(m.get("name", ""))
        values.append(m.get("value", 0))
        limits.append(m.get("limit", 0))
        within.append(m.get("within_limit", True))
    names = np.array(names)
    values = np.array(values)
    limits = np.array(limits)
    within = np.array(within)
    plot_title = title or "Safety margins (value vs limit)"

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure()
        fig.add_trace(go.Bar(y=names, x=values, orientation="h", name="value", marker_color=["green" if w else "red" for w in within]))
        fig.add_trace(go.Bar(y=names, x=limits, orientation="h", name="limit", marker_color="lightgray", opacity=0.7))
        fig.update_layout(title=plot_title, barmode="group", xaxis_title="value / limit", margin=dict(l=140))
        return fig
    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (8, max(4, len(names) * 0.4))))
        y_pos = np.arange(len(names))
        width = 0.35
        colors = ["green" if w else "red" for w in within]
        ax.barh(y_pos - width / 2, values, width, label="value", color=colors, alpha=0.85)
        ax.barh(y_pos + width / 2, limits, width, label="limit", color="lightgray", alpha=0.7)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names)
        ax.set_title(plot_title)
        ax.set_xlabel("value / limit")
        ax.legend()
        ax.grid(True, alpha=0.3, axis="x")
        fig.tight_layout()
        return fig, ax
    raise ValueError(f"Unknown backend: {backend}")


def plot_scenario_comparison(
    scenario_results: Dict[str, Any],
    *,
    metrics: Optional[Sequence[str]] = None,
    title: Optional[str] = None,
    backend: str = "plotly",
    **kwargs,
) -> Any:
    """
    Grouped bar chart of key metrics across scenarios (e.g. from run_scenario_design).

    Args:
        scenario_results: Dict mapping scenario name -> ScenarioResult or dict with 'metrics', 'passed'.
        metrics: Metric keys to plot (default: k_eff, power_thermal_mw if present).
        title: Plot title.
        backend: 'plotly' or 'matplotlib'.
    """
    names = list(scenario_results.keys())
    if not names:
        raise ValueError("scenario_results is empty")
    first = scenario_results[names[0]]
    mdict = getattr(first, "metrics", first) if hasattr(first, "metrics") else first.get("metrics", first)
    if metrics is None:
        metrics = [k for k in ("k_eff", "power_thermal_mw") if k in mdict]
    if not metrics:
        metrics = [k for k in mdict if isinstance(mdict.get(k), (int, float))][:5]
    data = {m: [] for m in metrics}
    for sname in names:
        r = scenario_results[sname]
        met = getattr(r, "metrics", r) if hasattr(r, "metrics") else r.get("metrics", {})
        for m in metrics:
            data[m].append(met.get(m, np.nan))
    plot_title = title or "Scenario comparison"

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure()
        for i, m in enumerate(metrics):
            fig.add_trace(go.Bar(name=m, x=names, y=data[m]))
        fig.update_layout(title=plot_title, barmode="group", xaxis_title="scenario")
        return fig
    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (8, 5)))
        x = np.arange(len(names))
        width = 0.8 / len(metrics)
        for i, m in enumerate(metrics):
            offset = (i - len(metrics) / 2 + 0.5) * width
            ax.bar(x + offset, data[m], width, label=m)
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=45, ha="right")
        ax.set_title(plot_title)
        ax.set_ylabel("value")
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")
        fig.tight_layout()
        return fig, ax
    raise ValueError(f"Unknown backend: {backend}")


def plot_atlas_designs(
    entries: Union[List[Any], List[Dict[str, Any]]],
    *,
    x_metric: str = "power_mw",
    y_metric: str = "k_eff",
    color_by: str = "passed",
    title: Optional[str] = None,
    backend: str = "plotly",
    **kwargs,
) -> Any:
    """
    Scatter plot of atlas designs (e.g. power vs k_eff) colored by pass/fail.

    Args:
        entries: List of AtlasEntry or dicts with power_mw, metrics_summary (or k_eff), passed.
        x_metric: Key for x (e.g. 'power_mw' or key in metrics_summary).
        y_metric: Key for y (e.g. 'k_eff'; can be in metrics_summary).
        color_by: 'passed' or metric key.
        title: Plot title.
        backend: 'plotly' or 'matplotlib'.
    """
    xs = []
    ys = []
    colors = []
    labels = []
    for e in entries:
        if hasattr(e, "design_id"):
            design_id = e.design_id
            power_mw = getattr(e, "power_mw", 0)
            ms = getattr(e, "metrics_summary", {}) or {}
            passed = getattr(e, "passed", False)
        else:
            design_id = e.get("design_id", "")
            power_mw = e.get("power_mw", 0)
            ms = e.get("metrics_summary", {}) or {}
            passed = e.get("passed", False)
        if x_metric == "power_mw":
            xv = power_mw
        else:
            xv = ms.get(x_metric, np.nan)
        if y_metric == "power_mw":
            yv = power_mw
        else:
            yv = ms.get(y_metric, np.nan)
        if not np.isfinite(xv) or not np.isfinite(yv):
            continue
        xs.append(xv)
        ys.append(yv)
        colors.append("green" if passed else "red")
        labels.append(design_id)
    if not xs:
        raise ValueError("No valid (x, y) points in atlas entries")
    xs = np.array(xs)
    ys = np.array(ys)
    plot_title = title or f"Design atlas: {x_metric} vs {y_metric}"

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure()
        for passed in (True, False):
            mask = np.array(colors) == ("green" if passed else "red")
            if not np.any(mask):
                continue
            name = "Pass" if passed else "Fail"
            idx = np.where(mask)[0]
            fig.add_trace(go.Scatter(
                x=xs[mask], y=ys[mask], mode="markers+text", name=name,
                text=[labels[i] for i in idx], textposition="top center",
                marker=dict(size=12, color="green" if passed else "red", symbol="circle")
            ))
        fig.update_layout(title=plot_title, xaxis_title=x_metric, yaxis_title=y_metric)
        return fig
    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (8, 6)))
        for passed in (True, False):
            mask = np.array(colors) == ("green" if passed else "red")
            ax.scatter(xs[mask], ys[mask], c="green" if passed else "red", label="Pass" if passed else "Fail", s=80)
        for i, lb in enumerate(labels):
            ax.annotate(lb, (xs[i], ys[i]), xytext=(0, 8), textcoords="offset points", fontsize=8, ha="center")
        ax.set_title(plot_title)
        ax.set_xlabel(x_metric)
        ax.set_ylabel(y_metric)
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return fig, ax
    raise ValueError(f"Unknown backend: {backend}")


__all__ = [
    "plot_sensitivity_ranking",
    "plot_sobol_workflow",
    "plot_pareto_with_knee",
    "plot_safety_margins",
    "plot_scenario_comparison",
    "plot_atlas_designs",
]
