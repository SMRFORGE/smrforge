"""
Shared visualization helpers.

This module is intentionally small and dependency-light. It centralizes:
- optional dependency checks (plotly/matplotlib)
- conversion to dashboard-safe Plotly dicts

It is considered internal; public plotting helpers should live in the
corresponding domain modules (e.g. sweep_plots, validation_plots, etc.).
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def ensure_plotly_available(is_available: bool) -> None:
    """Raise a clear ImportError if Plotly isn't installed."""
    if not is_available:
        raise ImportError(
            "plotly is required for this visualization. Install with: pip install plotly"
        )


def ensure_matplotlib_available(is_available: bool) -> None:
    """Raise a clear ImportError if Matplotlib isn't installed."""
    if not is_available:
        raise ImportError(
            "matplotlib is required for this visualization. Install with: pip install matplotlib"
        )


def as_plotly_dict(fig: Any, *, title: Optional[str] = None) -> Dict[str, Any]:
    """
    Convert a Plotly Figure (or already-JSONable dict) into a plain dict.

    This is useful for Dash `dcc.Graph(figure=...)` and for returning figure
    payloads from callback demo runners.
    """
    if fig is None:
        return {"data": [], "layout": {"title": title or ""}}

    if isinstance(fig, dict):
        if title:
            layout = fig.get("layout") or {}
            layout.setdefault("title", title)
            fig["layout"] = layout
        return fig

    to_dict = getattr(fig, "to_dict", None)
    if callable(to_dict):
        d = to_dict()
        if title:
            layout = d.get("layout") or {}
            layout.setdefault("title", title)
            d["layout"] = layout
        return d

    # Last-resort: return an empty figure payload rather than crashing a dashboard.
    return {"data": [], "layout": {"title": title or "Unsupported figure type"}}
