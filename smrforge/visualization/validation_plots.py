"""
Validation visualization helpers.

Supports both validation result types used in SMRForge:
- `smrforge.validation.data_validation.ValidationResult` (issues + summary())
- `smrforge.validation.constraints.ValidationResult` (passed/violations/warnings)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

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

from smrforge.visualization._viz_common import ensure_matplotlib_available, ensure_plotly_available


def _summary_counts(result: Any) -> Dict[str, int]:
    # data_validation.ValidationResult has summary()
    summary = getattr(result, "summary", None)
    if callable(summary):
        s = summary()
        if isinstance(s, dict):
            return {str(k): int(v) for k, v in s.items()}

    # constraints.ValidationResult shape: passed/violations/warnings
    if hasattr(result, "violations") or hasattr(result, "warnings"):
        violations = getattr(result, "violations", []) or []
        warnings = getattr(result, "warnings", []) or []
        return {
            "critical": 0,
            "error": int(len(violations)),
            "warning": int(len(warnings)),
            "info": 0,
        }

    raise ValueError("Unsupported validation result type (no summary(), no violations/warnings)")


def plot_validation_summary(
    result: Any,
    *,
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot a simple summary of validation severities.
    """
    counts = _summary_counts(result)
    levels = ["critical", "error", "warning", "info"]
    vals = [counts.get(l, 0) for l in levels]
    colors = ["darkred", "red", "orange", "steelblue"]
    plot_title = title or "Validation summary"

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=vals, y=levels, orientation="h", marker=dict(color=colors)))
        fig.update_layout(title=plot_title, xaxis_title="count", yaxis_title="level")
        return fig

    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (8, 4)))
        ax.barh(levels, vals, color=colors)
        ax.set_title(plot_title)
        ax.set_xlabel("count")
        ax.grid(True, alpha=0.3, axis="x")
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


def plot_validation_issues(
    result: Any,
    *,
    max_items: int = 20,
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot top validation issues/violations.
    """
    plot_title = title or "Validation issues"

    issues = getattr(result, "issues", None)
    if issues is not None:
        # data_validation.ValidationResult
        # Aggregate by parameter
        counts: Dict[str, int] = {}
        for i in issues:
            param = getattr(i, "parameter", "unknown")
            counts[str(param)] = counts.get(str(param), 0) + 1
        items = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[: max_items]
        labels = [k for k, _ in items]
        vals = [v for _, v in items]

        if backend == "plotly":
            ensure_plotly_available(_PLOTLY_AVAILABLE)
            fig = go.Figure()
            fig.add_trace(go.Bar(x=vals[::-1], y=labels[::-1], orientation="h", marker=dict(color="steelblue")))
            fig.update_layout(title=plot_title, xaxis_title="count", yaxis_title="parameter")
            return fig

        if backend == "matplotlib":
            ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
            fig, ax = plt.subplots(figsize=kwargs.get("figsize", (9, 6)))
            ax.barh(labels[::-1], vals[::-1], color="steelblue")
            ax.set_title(plot_title)
            ax.set_xlabel("count")
            ax.grid(True, alpha=0.3, axis="x")
            fig.tight_layout()
            return fig, ax

        raise ValueError(f"Unknown backend: {backend}")

    # constraints.ValidationResult
    violations = list(getattr(result, "violations", []) or []) + list(getattr(result, "warnings", []) or [])
    if not violations:
        raise ValueError("No violations/warnings found to plot.")

    # Score by absolute distance to limit, show sign too.
    rows: List[Tuple[str, float, str]] = []
    for v in violations[: max_items]:
        name = str(getattr(v, "constraint_name", "constraint"))
        value = float(getattr(v, "value", 0.0))
        limit = float(getattr(v, "limit", 0.0))
        sev = str(getattr(v, "severity", "warning"))
        rows.append((name, value - limit, sev))

    rows.sort(key=lambda r: abs(r[1]), reverse=True)
    labels = [r[0] for r in rows]
    deltas = [r[1] for r in rows]
    sevs = [r[2] for r in rows]
    colors = ["red" if s == "error" else "orange" for s in sevs]

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=deltas[::-1], y=labels[::-1], orientation="h", marker=dict(color=colors[::-1])))
        fig.update_layout(
            title=plot_title,
            xaxis_title="value - limit",
            yaxis_title="constraint",
        )
        return fig

    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 6)))
        ax.barh(labels[::-1], deltas[::-1], color=colors[::-1])
        ax.axvline(0.0, color="black", linestyle="--", linewidth=1)
        ax.set_title(plot_title)
        ax.set_xlabel("value - limit")
        ax.grid(True, alpha=0.3, axis="x")
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


__all__ = [
    "plot_validation_summary",
    "plot_validation_issues",
]

