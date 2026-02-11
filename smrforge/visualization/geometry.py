"""
Geometry visualization utilities for reactor cores.

Provides 2D and 3D visualization capabilities for prismatic and pebble bed cores.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import Circle, Polygon, Rectangle

try:
    from smrforge.geometry.core_geometry import PebbleBedCore, PrismaticCore

    _GEOMETRY_TYPES_AVAILABLE = True
except ImportError:
    PrismaticCore = None  # type: ignore
    PebbleBedCore = None  # type: ignore
    _GEOMETRY_TYPES_AVAILABLE = False


def plot_core_layout(
    core: Union["PrismaticCore", "PebbleBedCore"],
    view: str = "xy",
    ax: Optional[plt.Axes] = None,
    show_labels: bool = False,
    color_by: str = "type",
    **kwargs,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot 2D core layout view.

    Args:
        core: PrismaticCore or PebbleBedCore instance
        view: View direction - 'xy' (top), 'xz' (side), 'yz' (side)
        ax: Existing matplotlib axes (creates new if None)
        show_labels: Whether to show block IDs
        color_by: Color coding - 'type', 'power', 'temperature', or 'burnup'
        **kwargs: Additional matplotlib arguments

    Returns:
        Figure and Axes objects
    """
    if not _GEOMETRY_TYPES_AVAILABLE:
        raise ImportError("Geometry module not available")

    if ax is None:
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 10)))
    else:
        fig = ax.figure

    if isinstance(core, PrismaticCore):
        _plot_prismatic_layout(core, view, ax, show_labels, color_by, **kwargs)
    elif isinstance(core, PebbleBedCore):
        _plot_pebble_bed_layout(core, view, ax, show_labels, color_by, **kwargs)
    else:
        raise ValueError(f"Unsupported core type: {type(core)}")

    ax.set_aspect("equal")
    ax.set_xlabel("X (cm)")
    ax.set_ylabel("Y (cm)" if view == "xy" else "Z (cm)")
    ax.grid(True, alpha=0.3)
    ax.set_title(f"Core Layout - {view.upper()} View")

    return fig, ax


def _plot_prismatic_layout(
    core: "PrismaticCore",
    view: str,
    ax: plt.Axes,
    show_labels: bool,
    color_by: str,
    **kwargs,
):
    """Plot prismatic core layout."""
    patches = []
    colors = []
    min_x = float("inf")
    max_x = float("-inf")
    min_y = float("inf")
    max_y = float("-inf")

    # Get color mapping
    if color_by == "type":
        color_map = {"fuel": "lightblue", "reflector": "gray", "control": "red"}
    else:
        color_map = {"fuel": "lightblue", "reflector": "gray", "control": "red"}

    # Filter blocks based on view
    if view == "xy":
        # Top view - use blocks at z=0 or average z
        z_center = core.core_height / 2 if hasattr(core, "core_height") else 0
        blocks = [b for b in core.blocks if abs(b.position.z - z_center) < 1.0]
        for block in blocks:
            vertices = block.vertices()
            hex_poly = Polygon(vertices, closed=True)
            patches.append(hex_poly)
            colors.append(color_map.get(block.block_type, "gray"))
            try:
                vx = [float(v[0]) for v in vertices]
                vy = [float(v[1]) for v in vertices]
                min_x = min(min_x, *vx)
                max_x = max(max_x, *vx)
                min_y = min(min_y, *vy)
                max_y = max(max_y, *vy)
            except Exception:
                # Best-effort extents only
                pass

            if show_labels:
                ax.text(
                    block.position.x,
                    block.position.y,
                    str(block.id),
                    ha="center",
                    va="center",
                    fontsize=8,
                )

    elif view in ["xz", "yz"]:
        # Side view - project to x-z or y-z plane
        for block in core.blocks:
            if view == "xz":
                width = block.flat_to_flat
                x = block.position.x - width / 2
                y = block.position.z - block.height / 2
            else:  # yz
                width = block.flat_to_flat
                x = block.position.y - width / 2
                y = block.position.z - block.height / 2

            rect = Rectangle((x, y), width, block.height)
            patches.append(rect)
            colors.append(color_map.get(block.block_type, "gray"))
            try:
                min_x = min(min_x, float(x))
                max_x = max(max_x, float(x + width))
                min_y = min(min_y, float(y))
                max_y = max(max_y, float(y + block.height))
            except Exception:
                pass

            if show_labels:
                ax.text(
                    x + width / 2,
                    y + block.height / 2,
                    str(block.id),
                    ha="center",
                    va="center",
                    fontsize=8,
                )

    collection = PatchCollection(
        patches, facecolors=colors, edgecolors="black", linewidths=0.5
    )
    ax.add_collection(collection)

    # Ensure reasonable axes limits (matplotlib does not auto-scale for collections).
    if min_x != float("inf") and min_y != float("inf"):
        dx = max_x - min_x
        dy = max_y - min_y
        pad_x = 0.05 * dx if dx > 0 else 1.0
        pad_y = 0.05 * dy if dy > 0 else 1.0
        ax.set_xlim(min_x - pad_x, max_x + pad_x)
        ax.set_ylim(min_y - pad_y, max_y + pad_y)


def _plot_pebble_bed_layout(
    core: "PebbleBedCore",
    view: str,
    ax: plt.Axes,
    show_labels: bool,
    color_by: str,
    **kwargs,
):
    """Plot pebble bed core layout."""
    min_x = float("inf")
    max_x = float("-inf")
    min_y = float("inf")
    max_y = float("-inf")
    if view == "xy":
        # Top view
        for pebble in core.pebbles:
            circle = Circle((pebble.position.x, pebble.position.y), pebble.radius)
            ax.add_patch(circle)
            try:
                min_x = min(min_x, float(pebble.position.x - pebble.radius))
                max_x = max(max_x, float(pebble.position.x + pebble.radius))
                min_y = min(min_y, float(pebble.position.y - pebble.radius))
                max_y = max(max_y, float(pebble.position.y + pebble.radius))
            except Exception:
                pass

            if show_labels:
                ax.text(
                    pebble.position.x,
                    pebble.position.y,
                    str(pebble.id),
                    ha="center",
                    va="center",
                    fontsize=6,
                )

    elif view in ["xz", "yz"]:
        # Side view
        for pebble in core.pebbles:
            if view == "xz":
                x = pebble.position.x
                y = pebble.position.z
            else:
                x = pebble.position.y
                y = pebble.position.z

            circle = Circle((x, y), pebble.radius)
            ax.add_patch(circle)
            try:
                min_x = min(min_x, float(x - pebble.radius))
                max_x = max(max_x, float(x + pebble.radius))
                min_y = min(min_y, float(y - pebble.radius))
                max_y = max(max_y, float(y + pebble.radius))
            except Exception:
                pass

    if min_x != float("inf") and min_y != float("inf"):
        dx = max_x - min_x
        dy = max_y - min_y
        pad_x = 0.05 * dx if dx > 0 else 1.0
        pad_y = 0.05 * dy if dy > 0 else 1.0
        ax.set_xlim(min_x - pad_x, max_x + pad_x)
        ax.set_ylim(min_y - pad_y, max_y + pad_y)


def plot_flux_on_geometry(
    flux: np.ndarray,
    geometry: Union["PrismaticCore", "PebbleBedCore"],
    view: str = "xy",
    ax: Optional[plt.Axes] = None,
    **kwargs,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot flux distribution overlaid on geometry.

    Args:
        flux: Flux array (must match geometry mesh)
        geometry: PrismaticCore or PebbleBedCore instance
        view: View direction
        ax: Existing matplotlib axes
        **kwargs: Additional arguments for plotting

    Returns:
        Figure and Axes objects
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 10)))
    else:
        fig = ax.figure

    # Create mesh grid based on geometry
    if isinstance(geometry, PrismaticCore):
        if geometry.radial_mesh is not None and geometry.axial_mesh is not None:
            # Create 2D mesh for the view
            if view == "xy":
                r = geometry.radial_mesh
                theta = np.linspace(0, 2 * np.pi, 100)
                R, Theta = np.meshgrid(r, theta)
                X = R * np.cos(Theta)
                Y = R * np.sin(Theta)
                # Interpolate flux to mesh (simplified - would need proper interpolation)
                ax.contourf(X, Y, flux.reshape(len(r), 100).T, **kwargs)
            else:
                # Side view
                r = geometry.radial_mesh
                z = geometry.axial_mesh
                R, Z = np.meshgrid(r, z)
                ax.contourf(R, Z, flux, **kwargs)
        else:
            # Fallback to basic layout
            plot_core_layout(geometry, view, ax, **kwargs)

    return fig, ax


def plot_power_distribution(
    power: np.ndarray,
    geometry: Union["PrismaticCore", "PebbleBedCore"],
    view: str = "xy",
    ax: Optional[plt.Axes] = None,
    **kwargs,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot power distribution overlaid on geometry.

    Args:
        power: Power density array (W/cm³) or power per block/pebble
        geometry: Geometry instance
        view: View direction
        ax: Existing matplotlib axes
        **kwargs: Additional arguments (e.g., cmap='hot')

    Returns:
        Figure and Axes objects
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 10)))
    else:
        fig = ax.figure

    # Similar to flux plotting but with power colormap
    kwargs.setdefault("cmap", "hot")
    return plot_flux_on_geometry(power, geometry, view, ax, **kwargs)


def plot_temperature_distribution(
    temperature: np.ndarray,
    geometry: Union["PrismaticCore", "PebbleBedCore"],
    view: str = "xy",
    ax: Optional[plt.Axes] = None,
    **kwargs,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot temperature distribution overlaid on geometry.

    Args:
        temperature: Temperature array (K)
        geometry: Geometry instance
        view: View direction
        ax: Existing matplotlib axes
        **kwargs: Additional arguments (e.g., cmap='coolwarm')

    Returns:
        Figure and Axes objects
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 10)))
    else:
        fig = ax.figure

    kwargs.setdefault("cmap", "coolwarm")
    return plot_flux_on_geometry(temperature, geometry, view, ax, **kwargs)
