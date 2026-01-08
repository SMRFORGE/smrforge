"""
Comparison visualization utilities for multiple reactor designs.

Provides functions to create side-by-side and overlaid comparisons of different
reactor designs, enabling easy visual comparison of flux distributions, power
profiles, temperature distributions, and other metrics.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False
    go = None  # type: ignore

try:
    from smrforge.geometry.core_geometry import PebbleBedCore, PrismaticCore

    _GEOMETRY_TYPES_AVAILABLE = True
except ImportError:
    PrismaticCore = None  # type: ignore
    PebbleBedCore = None  # type: ignore
    _GEOMETRY_TYPES_AVAILABLE = False

from .geometry import plot_core_layout


def compare_designs_matplotlib(
    designs: Dict[str, Dict[str, Union[np.ndarray, "PrismaticCore", "PebbleBedCore"]]],
    field_name: str = "flux",
    view: str = "xy",
    n_cols: int = 2,
    figsize: Optional[Tuple[float, float]] = None,
    colorbar_shared: bool = True,
    titles: Optional[Dict[str, str]] = None,
    **kwargs,
) -> Tuple[plt.Figure, np.ndarray]:
    """
    Create side-by-side comparison of multiple reactor designs.

    Args:
        designs: Dictionary mapping design name -> {'geometry': Core, 'data': array}
                 or design name -> {'geometry': Core} (for layout only)
        field_name: Name of field to visualize
        view: View direction ('xy', 'xz', 'yz')
        n_cols: Number of columns in comparison grid
        figsize: Figure size (auto-calculated if None)
        colorbar_shared: Whether to use shared colorbar scale
        titles: Optional custom titles for each design
        **kwargs: Additional matplotlib arguments

    Returns:
        Figure and axes array

    Examples:
        Compare two reactor designs::

            designs = {
                "Design A": {
                    "geometry": core_a,
                    "data": flux_a
                },
                "Design B": {
                    "geometry": core_b,
                    "data": flux_b
                }
            }

            fig, axes = compare_designs_matplotlib(
                designs=designs,
                field_name="flux",
                view="xy"
            )
            plt.tight_layout()
            plt.show()
    """
    if not _GEOMETRY_TYPES_AVAILABLE:
        raise ImportError("Geometry module not available")

    design_names = list(designs.keys())
    n_designs = len(design_names)
    n_rows = int(np.ceil(n_designs / n_cols))

    if figsize is None:
        figsize = (6 * n_cols, 6 * n_rows)

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize, squeeze=False)
    axes = axes.flatten()

    # Determine shared colorbar scale if needed
    vmin, vmax = None, None
    if colorbar_shared and any("data" in design for design in designs.values()):
        all_data = [design["data"] for design in designs.values() if "data" in design]
        if all_data:
            vmin = min(np.min(data) for data in all_data)
            vmax = max(np.max(data) for data in all_data)

    # Plot each design
    ims = []
    for i, name in enumerate(design_names):
        ax = axes[i]
        design_data = designs[name]

        # Get geometry
        geometry = design_data.get("geometry")
        if geometry is None:
            raise ValueError(f"No geometry provided for design '{name}'")

        # Plot layout
        plot_core_layout(geometry, view=view, ax=ax, show_labels=False, **kwargs)

        # Overlay data if provided
        if "data" in design_data:
            data = design_data["data"]
            if isinstance(data, np.ndarray):
                if data.ndim == 2:
                    im = ax.imshow(
                        data,
                        extent=ax.get_xlim() + ax.get_ylim(),
                        origin="lower",
                        interpolation="bilinear",
                        cmap=kwargs.get("cmap", "viridis"),
                        vmin=vmin,
                        vmax=vmax,
                        alpha=kwargs.get("alpha", 0.7),
                    )
                    ims.append(im)

                    # Add colorbar if not shared or last design
                    if not colorbar_shared or i == len(design_names) - 1:
                        plt.colorbar(im, ax=ax, label=field_name)

        # Set title
        if titles and name in titles:
            title = titles[name]
        else:
            title = name
        ax.set_title(title)

    # Add shared colorbar if needed
    if colorbar_shared and ims:
        fig.colorbar(ims[0], ax=axes, label=field_name)

    # Hide unused axes
    for i in range(n_designs, len(axes)):
        axes[i].axis("off")

    plt.tight_layout()

    return fig, axes


def compare_designs_plotly(
    designs: Dict[str, Dict[str, Union[np.ndarray, "PrismaticCore", "PebbleBedCore"]]],
    field_name: str = "flux",
    view: str = "xy",
    n_cols: int = 2,
    subplot_titles: Optional[List[str]] = None,
    colorbar_shared: bool = True,
    **kwargs,
) -> "go.Figure":
    """
    Create interactive side-by-side comparison using plotly.

    Args:
        designs: Dictionary mapping design name -> {'geometry': Core, 'data': array}
        field_name: Name of field to visualize
        view: View direction ('xy', 'xz', 'yz')
        n_cols: Number of columns in comparison grid
        subplot_titles: Optional custom titles for subplots
        colorbar_shared: Whether to use shared colorbar scale
        **kwargs: Additional plotly arguments

    Returns:
        plotly.graph_objects.Figure

    Examples:
        Compare two reactor designs interactively::

            designs = {
                "Design A": {"geometry": core_a, "data": flux_a},
                "Design B": {"geometry": core_b, "data": flux_b}
            }

            fig = compare_designs_plotly(designs, field_name="flux")
            fig.show()
    """
    if not _PLOTLY_AVAILABLE:
        raise ImportError(
            "plotly is required for interactive comparisons. Install with: pip install plotly"
        )
    if not _GEOMETRY_TYPES_AVAILABLE:
        raise ImportError("Geometry module not available")

    design_names = list(designs.keys())
    n_designs = len(design_names)
    n_rows = int(np.ceil(n_designs / n_cols))

    if subplot_titles is None:
        subplot_titles = design_names

    # Create subplots
    fig = make_subplots(
        rows=n_rows,
        cols=n_cols,
        subplot_titles=subplot_titles,
        specs=[[{"type": "xy"} for _ in range(n_cols)] for _ in range(n_rows)],
    )

    # Determine shared colorbar scale if needed
    vmin, vmax = None, None
    if colorbar_shared and any("data" in design for design in designs.values()):
        all_data = [design["data"] for design in designs.values() if "data" in design]
        if all_data:
            vmin = min(np.min(data) for data in all_data)
            vmax = max(np.max(data) for data in all_data)

    # Plot each design
    for i, name in enumerate(design_names):
        row = i // n_cols + 1
        col = i % n_cols + 1

        design_data = designs[name]
        geometry = design_data.get("geometry")
        if geometry is None:
            raise ValueError(f"No geometry provided for design '{name}'")

        # Extract data for plotly
        if "data" in design_data:
            data = design_data["data"]
            if isinstance(data, np.ndarray) and data.ndim == 2:
                # Create heatmap
                fig.add_trace(
                    go.Heatmap(
                        z=data,
                        colorscale=kwargs.get("colorscale", "Viridis"),
                        zmin=vmin,
                        zmax=vmax,
                        showscale=(not colorbar_shared or i == n_designs - 1),
                        colorbar=dict(title=field_name) if (not colorbar_shared or i == n_designs - 1) else None,
                        name=name,
                    ),
                    row=row,
                    col=col,
                )

        # Update axis labels
        fig.update_xaxes(title_text="X (cm)" if view in ["xy", "xz"] else "Y (cm)", row=row, col=col)
        fig.update_yaxes(title_text="Y (cm)" if view == "xy" else "Z (cm)", row=row, col=col)

    fig.update_layout(
        title_text=f"{field_name.title()} Comparison",
        height=400 * n_rows,
        width=600 * n_cols,
    )

    return fig


def compare_metrics_matplotlib(
    metrics: Dict[str, Dict[str, np.ndarray]],
    x_label: str = "Time (days)",
    y_label: str = "Value",
    figsize: tuple = (12, 6),
    **kwargs,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Compare time-dependent metrics across multiple designs.

    Args:
        metrics: Dictionary mapping design name -> {metric_name: time_series_array}
        x_label: X-axis label
        y_label: Y-axis label
        figsize: Figure size
        **kwargs: Additional matplotlib arguments

    Returns:
        Figure and axes

    Examples:
        Compare keff over time for multiple designs::

            metrics = {
                "Design A": {"keff": keff_a},
                "Design B": {"keff": keff_b}
            }

            fig, ax = compare_metrics_matplotlib(
                metrics,
                x_label="Time (days)",
                y_label="k-eff"
            )
            plt.show()
    """
    fig, ax = plt.subplots(figsize=figsize)

    colors = plt.cm.tab10(np.linspace(0, 1, len(metrics)))

    for i, (design_name, design_metrics) in enumerate(metrics.items()):
        for metric_name, time_series in design_metrics.items():
            if isinstance(time_series, np.ndarray):
                if time_series.ndim == 1:
                    # 1D array - assume it's values vs indices
                    x = np.arange(len(time_series))
                    ax.plot(x, time_series, label=f"{design_name} - {metric_name}", color=colors[i], **kwargs)
                elif time_series.ndim == 2 and time_series.shape[1] == 2:
                    # 2D array with shape (n, 2) - assume (time, value)
                    ax.plot(time_series[:, 0], time_series[:, 1], label=f"{design_name} - {metric_name}", color=colors[i], **kwargs)

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_title("Design Comparison")

    plt.tight_layout()

    return fig, ax


def overlay_comparison_matplotlib(
    geometries: List[Union["PrismaticCore", "PebbleBedCore"]],
    labels: List[str],
    view: str = "xy",
    ax: Optional[plt.Axes] = None,
    colors: Optional[List[str]] = None,
    alpha: float = 0.6,
    **kwargs,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create overlaid comparison of multiple geometries on the same axes.

    Args:
        geometries: List of geometry objects
        labels: List of labels for each geometry
        view: View direction ('xy', 'xz', 'yz')
        ax: Existing matplotlib axes (creates new if None)
        colors: Optional list of colors for each geometry
        alpha: Transparency (0-1)
        **kwargs: Additional matplotlib arguments

    Returns:
        Figure and axes

    Examples:
        Overlay two reactor designs::

            fig, ax = overlay_comparison_matplotlib(
                geometries=[core_a, core_b],
                labels=["Design A", "Design B"],
                view="xy",
                colors=["blue", "red"]
            )
            plt.show()
    """
    if not _GEOMETRY_TYPES_AVAILABLE:
        raise ImportError("Geometry module not available")

    if len(geometries) != len(labels):
        raise ValueError("Number of geometries must match number of labels")

    if ax is None:
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 10)))
    else:
        fig = ax.figure

    if colors is None:
        colors = plt.cm.tab10(np.linspace(0, 1, len(geometries)))

    for i, (geometry, label, color) in enumerate(zip(geometries, labels, colors)):
        plot_core_layout(
            geometry,
            view=view,
            ax=ax,
            show_labels=False,
            alpha=alpha,
            edgecolors=color,
            facecolors="none",
            **kwargs,
        )
        # Add label annotation at center
        if isinstance(geometry, PrismaticCore) and len(geometry.blocks) > 0:
            center = geometry.blocks[0].position
            ax.text(center.x, center.y, label, color=color, fontsize=10, weight="bold")

    ax.set_title("Overlaid Geometry Comparison")
    ax.legend(labels)

    return fig, ax

