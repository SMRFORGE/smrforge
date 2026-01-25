"""
Economics visualization helpers.

Consumes breakdown dicts produced by:
- `smrforge.economics.cost_modeling.CapitalCostEstimator.get_cost_breakdown()`
- `smrforge.economics.cost_modeling.OperatingCostEstimator.get_cost_breakdown()`
- `smrforge.economics.cost_modeling.LCOECalculator.get_cost_breakdown()`
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Tuple, Union

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


def plot_capex_breakdown(
    breakdown: Dict[str, float],
    *,
    backend: str = "plotly",
    kind: str = "waterfall",  # 'waterfall' | 'bar'
    top_n: int = 12,
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot capital cost breakdown as waterfall or bar chart.
    """
    if not isinstance(breakdown, dict) or not breakdown:
        raise ValueError("breakdown must be a non-empty dict")

    total_key = "total_overnight_cost"
    total = float(breakdown.get(total_key, sum(v for v in breakdown.values() if isinstance(v, (int, float)))))

    items = [(k, float(v)) for k, v in breakdown.items() if k != total_key]
    items = [(k, v) for k, v in items if v != 0.0]
    items.sort(key=lambda kv: abs(kv[1]), reverse=True)
    items = items[: max(1, top_n)]

    labels = [k for k, _ in items]
    values = [v for _, v in items]
    plot_title = title or "Capital cost breakdown"

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        if kind == "waterfall":
            fig = go.Figure(
                data=go.Waterfall(
                    x=labels + [total_key],
                    y=values + [total],
                    measure=["relative"] * len(values) + ["total"],
                    connector={"line": {"color": "rgba(63,63,63,0.6)"}},
                )
            )
            fig.update_layout(title=plot_title, yaxis_title="USD")
            return fig
        if kind == "bar":
            fig = go.Figure(data=go.Bar(x=values[::-1], y=labels[::-1], orientation="h"))
            fig.update_layout(title=plot_title, xaxis_title="USD", yaxis_title="component")
            return fig
        raise ValueError("kind must be 'waterfall' or 'bar'")

    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        if kind == "bar":
            fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 6)))
            ax.barh(labels[::-1], values[::-1], color="steelblue")
            ax.set_title(plot_title)
            ax.set_xlabel("USD")
            ax.grid(True, alpha=0.3, axis="x")
            fig.tight_layout()
            return fig, ax
        if kind == "waterfall":
            fig, ax = plt.subplots(figsize=kwargs.get("figsize", (12, 6)))
            cum = 0.0
            xs = list(range(len(values)))
            for i, v in enumerate(values):
                ax.bar(i, v, bottom=cum, color="steelblue" if v >= 0 else "salmon")
                cum += v
            ax.axhline(total, color="black", linestyle="--", linewidth=1)
            ax.set_xticks(xs)
            ax.set_xticklabels(labels, rotation=45, ha="right")
            ax.set_title(plot_title)
            ax.set_ylabel("USD")
            ax.grid(True, alpha=0.3, axis="y")
            fig.tight_layout()
            return fig, ax
        raise ValueError("kind must be 'waterfall' or 'bar'")

    raise ValueError(f"Unknown backend: {backend}")


def plot_lcoe_breakdown(
    lcoe_breakdown: Dict[str, float],
    *,
    backend: str = "plotly",
    kind: str = "stacked",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot LCOE contribution breakdown (stacked bar).
    """
    if not isinstance(lcoe_breakdown, dict) or not lcoe_breakdown:
        raise ValueError("lcoe_breakdown must be a non-empty dict")

    cap = float(lcoe_breakdown.get("capital_contribution", 0.0))
    op = float(lcoe_breakdown.get("operating_contribution", 0.0))
    de = float(lcoe_breakdown.get("decommissioning_contribution", 0.0))
    plot_title = title or "LCOE breakdown"

    if backend == "plotly":
        ensure_plotly_available(_PLOTLY_AVAILABLE)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=["LCOE"], y=[cap], name="Capital"))
        fig.add_trace(go.Bar(x=["LCOE"], y=[op], name="Operating"))
        fig.add_trace(go.Bar(x=["LCOE"], y=[de], name="Decommissioning"))
        fig.update_layout(title=plot_title, barmode="stack", yaxis_title="USD/kWh")
        return fig

    if backend == "matplotlib":
        ensure_matplotlib_available(_MATPLOTLIB_AVAILABLE)
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (6, 5)))
        ax.bar(["LCOE"], [cap], label="Capital")
        ax.bar(["LCOE"], [op], bottom=[cap], label="Operating")
        ax.bar(["LCOE"], [de], bottom=[cap + op], label="Decommissioning")
        ax.set_title(plot_title)
        ax.set_ylabel("USD/kWh")
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


__all__ = [
    "plot_capex_breakdown",
    "plot_lcoe_breakdown",
]

