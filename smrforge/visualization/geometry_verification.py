"""
Geometry verification visualization tools.

Provides visualization for geometry verification, including:
- Overlap detection visualization
- Geometry consistency checks
- Material assignment verification
- Boundary visualization
"""

from typing import Dict, List, Optional, Tuple, Union

import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Polygon, Rectangle

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

from ..geometry.mesh_3d import Mesh3D
from ..utils.logging import get_logger

logger = get_logger("smrforge.visualization.geometry_verification")


def plot_overlap_detection(
    geometry,
    overlaps: List[Tuple],
    backend: str = "plotly",
    **kwargs,
):
    """
    Visualize detected geometry overlaps.

    Highlights regions where geometry components overlap, which indicates
    modeling errors.

    Args:
        geometry: Reactor geometry
        overlaps: List of overlap tuples (component1, component2, overlap_region)
        backend: Visualization backend
        **kwargs: Additional arguments

    Returns:
        Figure object

    Example:
        >>> from smrforge.geometry.validation import detect_overlaps
        >>> from smrforge.visualization.geometry_verification import plot_overlap_detection
        >>>
        >>> overlaps = detect_overlaps(core)
        >>> fig = plot_overlap_detection(core, overlaps)
    """
    if backend == "plotly":
        return _plot_overlaps_plotly(geometry, overlaps, **kwargs)
    elif backend == "matplotlib":
        return _plot_overlaps_matplotlib(geometry, overlaps, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def _plot_overlaps_plotly(geometry, overlaps, **kwargs):
    """Plot overlaps using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")

    fig = go.Figure()

    # Plot geometry
    if hasattr(geometry, "blocks"):
        for block in geometry.blocks:
            # Add block visualization
            pass

    # Highlight overlaps
    for comp1, comp2, overlap_region in overlaps:
        # Add overlap region visualization
        if hasattr(overlap_region, "vertices"):
            vertices = overlap_region.vertices()
            x = [v[0] for v in vertices]
            y = [v[1] for v in vertices]
            z = (
                [v[2] for v in vertices]
                if len(vertices[0]) > 2
                else [0] * len(vertices)
            )

            fig.add_trace(
                go.Scatter3d(
                    x=x + [x[0]],
                    y=y + [y[0]],
                    z=z + [z[0]],
                    mode="lines",
                    line=dict(color="red", width=5),
                    name=f"Overlap: {comp1} & {comp2}",
                )
            )

    fig.update_layout(
        title="Geometry Overlap Detection",
        scene=dict(
            xaxis_title="X (cm)",
            yaxis_title="Y (cm)",
            zaxis_title="Z (cm)",
        ),
    )

    return fig


def _plot_overlaps_matplotlib(geometry, overlaps, **kwargs):
    """Plot overlaps using matplotlib."""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib is required")

    fig, ax = plt.subplots(figsize=(10, 10))

    # Plot geometry
    if hasattr(geometry, "blocks"):
        for block in geometry.blocks:
            vertices = block.vertices()
            poly = Polygon(vertices, alpha=0.3, edgecolor="black")
            ax.add_patch(poly)

    # Highlight overlaps
    for comp1, comp2, overlap_region in overlaps:
        if hasattr(overlap_region, "vertices"):
            vertices = overlap_region.vertices()
            poly = Polygon(
                vertices, alpha=0.7, facecolor="red", edgecolor="darkred", linewidth=2
            )
            ax.add_patch(poly)

    ax.set_aspect("equal")
    ax.set_xlabel("X (cm)")
    ax.set_ylabel("Y (cm)")
    ax.set_title("Geometry Overlap Detection")
    ax.grid(True, alpha=0.3)

    return fig, ax


def plot_geometry_consistency(
    geometry,
    consistency_checks: Dict[str, bool],
    issues: List[str],
    backend: str = "plotly",
    **kwargs,
):
    """
    Visualize geometry consistency check results.

    Shows geometry with highlighted issues and consistency check results.

    Args:
        geometry: Reactor geometry
        consistency_checks: Dictionary of check names to pass/fail status
        issues: List of issue descriptions
        backend: Visualization backend
        **kwargs: Additional arguments

    Returns:
        Figure object
    """
    if backend == "plotly":
        return _plot_consistency_plotly(geometry, consistency_checks, issues, **kwargs)
    elif backend == "matplotlib":
        return _plot_consistency_matplotlib(
            geometry, consistency_checks, issues, **kwargs
        )
    else:
        raise ValueError(f"Unknown backend: {backend}")


def _plot_consistency_plotly(geometry, consistency_checks, issues, **kwargs):
    """Plot consistency check results using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")

    from .advanced import plot_ray_traced_geometry

    # Create base geometry plot
    fig = plot_ray_traced_geometry(geometry, backend="plotly")

    # Add annotations for issues
    annotations = []
    for i, issue in enumerate(issues):
        annotations.append(
            dict(
                text=issue,
                x=0.02,
                y=0.98 - i * 0.05,
                xref="paper",
                yref="paper",
                showarrow=False,
                bgcolor="red" if "error" in issue.lower() else "yellow",
                bordercolor="black",
                borderwidth=1,
            )
        )

    # Add check status
    check_text = "<br>".join(
        [
            f"{name}: {'✓' if status else '✗'}"
            for name, status in consistency_checks.items()
        ]
    )

    annotations.append(
        dict(
            text=check_text,
            x=0.98,
            y=0.98,
            xref="paper",
            yref="paper",
            showarrow=False,
            bgcolor="lightgreen" if all(consistency_checks.values()) else "lightyellow",
            bordercolor="black",
            borderwidth=1,
            align="right",
        )
    )

    fig.update_layout(annotations=annotations)

    return fig


def _plot_consistency_matplotlib(geometry, consistency_checks, issues, **kwargs):
    """Plot consistency check results using matplotlib."""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib is required")

    from .geometry import plot_core_layout

    fig, ax = plot_core_layout(geometry, view="xy")

    # Add text annotations
    y_pos = 0.95
    for issue in issues:
        ax.text(
            0.02,
            y_pos,
            issue,
            transform=ax.transAxes,
            bbox=dict(
                boxstyle="round",
                facecolor="red" if "error" in issue.lower() else "yellow",
            ),
            fontsize=8,
        )
        y_pos -= 0.05

    # Add check status
    check_text = "\n".join(
        [
            f"{name}: {'✓' if status else '✗'}"
            for name, status in consistency_checks.items()
        ]
    )

    ax.text(
        0.98,
        0.98,
        check_text,
        transform=ax.transAxes,
        bbox=dict(
            boxstyle="round",
            facecolor=(
                "lightgreen" if all(consistency_checks.values()) else "lightyellow"
            ),
        ),
        fontsize=8,
        verticalalignment="top",
        horizontalalignment="right",
    )

    return fig, ax


def plot_material_assignment(
    geometry,
    material_map: Dict,
    backend: str = "plotly",
    **kwargs,
):
    """
    Visualize material assignments for verification.

    Shows geometry colored by material ID to verify correct material assignments.

    Args:
        geometry: Reactor geometry
        material_map: Dictionary mapping component IDs to material names/IDs
        backend: Visualization backend
        **kwargs: Additional arguments

    Returns:
        Figure object
    """
    from .advanced import plot_material_boundaries

    return plot_material_boundaries(
        geometry,
        materials=list(material_map.values()),
        backend=backend,
        **kwargs,
    )
