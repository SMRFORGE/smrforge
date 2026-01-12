"""
Material composition visualization.

Provides visualization for material compositions, nuclide concentrations,
and material property mapping.
"""

from typing import Dict, List, Optional, Tuple, Union

import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib import cm
    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False
    plt = None  # type: ignore
    cm = None  # type: ignore

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False
    go = None  # type: ignore
    make_subplots = None  # type: ignore

from ..core.reactor_core import Nuclide, NuclideInventoryTracker
from ..utils.logging import get_logger

logger = get_logger("smrforge.visualization.material_composition")


def plot_nuclide_concentration(
    inventory: NuclideInventoryTracker,
    nuclide: Nuclide,
    geometry,
    backend: str = "plotly",
    **kwargs,
):
    """
    Plot nuclide concentration distribution.
    
    Visualizes the spatial distribution of a specific nuclide's concentration
    in the reactor geometry.
    
    Args:
        inventory: NuclideInventoryTracker instance
        nuclide: Nuclide to visualize
        geometry: Reactor geometry
        backend: Visualization backend
        **kwargs: Additional arguments
    
    Returns:
        Figure object
    
    Example:
        >>> from smrforge.visualization.material_composition import plot_nuclide_concentration
        >>> from smrforge.core.reactor_core import Nuclide
        >>> 
        >>> u235 = Nuclide(Z=92, A=235)
        >>> fig = plot_nuclide_concentration(inventory, u235, core)
    """
    # Get concentration data
    concentration = inventory.get_atom_density(nuclide)
    
    # Map to geometry (simplified - would need proper spatial mapping)
    if backend == "plotly":
        return _plot_concentration_plotly(geometry, nuclide, concentration, **kwargs)
    elif backend == "matplotlib":
        return _plot_concentration_matplotlib(geometry, nuclide, concentration, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def _plot_concentration_plotly(geometry, nuclide, concentration, **kwargs):
    """Plot concentration using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")
    
    from .advanced import plot_ray_traced_geometry
    
    # Create base geometry plot
    fig = plot_ray_traced_geometry(geometry, backend="plotly", color_by="material")
    
    # Add concentration overlay (simplified)
    fig.update_layout(
        title=f"{nuclide.name} Concentration Distribution",
    )
    
    return fig


def _plot_concentration_matplotlib(geometry, nuclide, concentration, **kwargs):
    """Plot concentration using matplotlib."""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib is required")
    
    from .geometry import plot_core_layout
    
    fig, ax = plot_core_layout(geometry, view="xy", color_by="material")
    ax.set_title(f"{nuclide.name} Concentration Distribution")
    
    return fig, ax


def plot_material_property(
    geometry,
    property_map: Dict[str, float],
    property_name: str,
    backend: str = "plotly",
    **kwargs,
):
    """
    Plot material property distribution.
    
    Visualizes a material property (density, temperature, etc.) across the geometry.
    
    Args:
        geometry: Reactor geometry
        property_map: Dictionary mapping material IDs to property values
        property_name: Name of the property (for labels)
        backend: Visualization backend
        **kwargs: Additional arguments
    
    Returns:
        Figure object
    
    Example:
        >>> density_map = {"fuel": 10.5, "moderator": 1.0, "reflector": 1.8}
        >>> fig = plot_material_property(core, density_map, "density")
    """
    if backend == "plotly":
        return _plot_property_plotly(geometry, property_map, property_name, **kwargs)
    elif backend == "matplotlib":
        return _plot_property_matplotlib(geometry, property_map, property_name, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def _plot_property_plotly(geometry, property_map, property_name, **kwargs):
    """Plot property using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")
    
    from .advanced import plot_ray_traced_geometry
    
    # Create custom colors based on property values
    colors = {}
    max_val = max(property_map.values())
    min_val = min(property_map.values())
    
    for mat_id, value in property_map.items():
        # Normalize to 0-1 range
        normalized = (value - min_val) / (max_val - min_val) if max_val > min_val else 0.5
        # Create color (using viridis-like colormap)
        colors[mat_id] = f"hsl({240 - normalized * 240}, 100%, {50 + normalized * 30}%)"
    
    fig = plot_ray_traced_geometry(
        geometry,
        backend="plotly",
        color_by="material",
        colors=colors,
    )
    
    fig.update_layout(title=f"{property_name.capitalize()} Distribution")
    
    return fig


def _plot_property_matplotlib(geometry, property_map, property_name, **kwargs):
    """Plot property using matplotlib."""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib is required")
    
    from .geometry import plot_core_layout
    
    fig, ax = plot_core_layout(geometry, view="xy", color_by="material")
    ax.set_title(f"{property_name.capitalize()} Distribution")
    
    return fig, ax


def plot_burnup_composition(
    inventory: NuclideInventoryTracker,
    geometry,
    nuclides: Optional[List[Nuclide]] = None,
    backend: str = "plotly",
    **kwargs,
):
    """
    Plot composition changes due to burnup.
    
    Visualizes how nuclide concentrations change with burnup.
    
    Args:
        inventory: NuclideInventoryTracker instance
        geometry: Reactor geometry
        nuclides: List of nuclides to plot (None for all)
        backend: Visualization backend
        **kwargs: Additional arguments
    
    Returns:
        Figure object
    """
    if nuclides is None:
        nuclides = inventory.nuclides
    
    if backend == "plotly":
        return _plot_burnup_composition_plotly(inventory, geometry, nuclides, **kwargs)
    elif backend == "matplotlib":
        return _plot_burnup_composition_matplotlib(inventory, geometry, nuclides, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def _plot_burnup_composition_plotly(inventory, geometry, nuclides, **kwargs):
    """Plot burnup composition using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")
    
    # Create bar chart of concentrations
    nuclide_names = [n.name for n in nuclides]
    concentrations = [inventory.get_atom_density(n) for n in nuclides]
    
    fig = go.Figure(data=go.Bar(
        x=nuclide_names,
        y=concentrations,
        marker_color="steelblue",
    ))
    
    fig.update_layout(
        title=f"Composition at Burnup: {inventory.burnup:.1f} MWd/kgU",
        xaxis_title="Nuclide",
        yaxis_title="Atom Density (atoms/barn-cm)",
        yaxis_type="log",
    )
    
    return fig


def _plot_burnup_composition_matplotlib(inventory, geometry, nuclides, **kwargs):
    """Plot burnup composition using matplotlib."""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib is required")
    
    nuclide_names = [n.name for n in nuclides]
    concentrations = [inventory.get_atom_density(n) for n in nuclides]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(nuclide_names, concentrations, color="steelblue")
    ax.set_xlabel("Nuclide")
    ax.set_ylabel("Atom Density (atoms/barn-cm)")
    ax.set_yscale("log")
    ax.set_title(f"Composition at Burnup: {inventory.burnup:.1f} MWd/kgU")
    plt.xticks(rotation=45, ha="right")
    
    return fig, ax
