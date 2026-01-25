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


def _is_burnup_time_series_inventory(obj) -> bool:
    return all(hasattr(obj, k) for k in ("nuclides", "concentrations", "times", "burnup"))


def _convert_time(times_s: np.ndarray, time_unit: str) -> Tuple[np.ndarray, str]:
    time_unit = (time_unit or "days").lower()
    if time_unit == "seconds":
        return times_s, "s"
    if time_unit == "hours":
        return times_s / 3600.0, "h"
    if time_unit == "days":
        return times_s / (24.0 * 3600.0), "days"
    if time_unit == "years":
        return times_s / (365.25 * 24.0 * 3600.0), "years"
    raise ValueError("time_unit must be one of: seconds, hours, days, years")


def plot_nuclide_evolution(
    inventory,
    nuclides: Optional[List[Nuclide]] = None,
    *,
    time_unit: str = "days",
    backend: str = "plotly",
    max_nuclides: int = 10,
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot nuclide concentration evolution over time for burnup solver inventories.
    """
    if not _is_burnup_time_series_inventory(inventory):
        raise ValueError(
            "inventory must provide (nuclides, concentrations, times, burnup) like "
            "smrforge.burnup.solver.NuclideInventory"
        )

    nuclides_all: List[Nuclide] = list(inventory.nuclides)
    conc = np.asarray(inventory.concentrations, dtype=float)
    times_s = np.asarray(inventory.times, dtype=float)
    t, t_label = _convert_time(times_s, time_unit)

    if conc.ndim != 2 or conc.shape[0] != len(nuclides_all):
        raise ValueError("inventory.concentrations must be shape [n_nuclides, n_time_steps]")

    if nuclides is None:
        # Default: top N by final concentration.
        order = np.argsort(conc[:, -1])[::-1]
        idxs = order[: max(1, min(max_nuclides, len(order)))]
    else:
        idxs = [nuclides_all.index(n) for n in nuclides if n in nuclides_all]
        if not idxs:
            raise ValueError("Requested nuclides were not found in inventory.nuclides")

    plot_title = title or "Nuclide evolution"

    if backend == "plotly":
        if not _PLOTLY_AVAILABLE:
            raise ImportError("plotly is required")
        fig = go.Figure()
        for i in idxs:
            fig.add_trace(go.Scatter(x=t, y=conc[i, :], mode="lines", name=nuclides_all[i].name))
        fig.update_layout(
            title=plot_title,
            xaxis_title=f"Time ({t_label})",
            yaxis_title="Concentration (a.u.)",
            yaxis_type=kwargs.get("yaxis_type", "log"),
            hovermode="x unified",
        )
        return fig

    if backend == "matplotlib":
        if not _MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required")
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 6)))
        for i in idxs:
            ax.plot(t, conc[i, :], linewidth=2, label=nuclides_all[i].name)
        ax.set_title(plot_title)
        ax.set_xlabel(f"Time ({t_label})")
        ax.set_ylabel("Concentration (a.u.)")
        ax.set_yscale(kwargs.get("yscale", "log"))
        ax.grid(True, alpha=0.3)
        ax.legend(ncol=2, fontsize=8)
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


def plot_composition_stacked_area(
    inventory,
    nuclide_categories: Optional[Dict[str, List[Nuclide]]] = None,
    *,
    time_unit: str = "days",
    normalize: bool = False,
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot composition evolution as a stacked area chart (burnup inventories).
    """
    if not _is_burnup_time_series_inventory(inventory):
        raise ValueError(
            "inventory must provide (nuclides, concentrations, times, burnup) like "
            "smrforge.burnup.solver.NuclideInventory"
        )

    nuclides_all: List[Nuclide] = list(inventory.nuclides)
    conc = np.asarray(inventory.concentrations, dtype=float)
    times_s = np.asarray(inventory.times, dtype=float)
    t, t_label = _convert_time(times_s, time_unit)

    if nuclide_categories is None:
        # Simple auto-buckets based on atomic number.
        act_idx = [i for i, n in enumerate(nuclides_all) if getattr(n, "Z", 0) >= 89]
        fp_idx = [i for i, n in enumerate(nuclides_all) if i not in act_idx]
        nuclide_categories = {
            "Actinides": [nuclides_all[i] for i in act_idx],
            "Other/Fission products": [nuclides_all[i] for i in fp_idx],
        }

    series: Dict[str, np.ndarray] = {}
    for name, ns in nuclide_categories.items():
        idxs = [nuclides_all.index(n) for n in ns if n in nuclides_all]
        if idxs:
            series[name] = np.sum(conc[idxs, :], axis=0)

    if not series:
        raise ValueError("No categories contained nuclides present in inventory")

    if normalize:
        total = np.sum(conc, axis=0)
        total = np.where(total > 0, total, 1.0)
        series = {k: v / total for k, v in series.items()}

    plot_title = title or "Composition evolution (stacked)"

    if backend == "plotly":
        if not _PLOTLY_AVAILABLE:
            raise ImportError("plotly is required")
        fig = go.Figure()
        for name, vals in series.items():
            fig.add_trace(go.Scatter(x=t, y=vals, mode="lines", name=name, stackgroup="one"))
        fig.update_layout(
            title=plot_title,
            xaxis_title=f"Time ({t_label})",
            yaxis_title=("Fraction" if normalize else "Concentration (a.u.)"),
            hovermode="x unified",
        )
        return fig

    if backend == "matplotlib":
        if not _MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required")
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 6)))
        labels = list(series.keys())
        ys = [series[k] for k in labels]
        ax.stackplot(t, ys, labels=labels)
        ax.set_title(plot_title)
        ax.set_xlabel(f"Time ({t_label})")
        ax.set_ylabel("Fraction" if normalize else "Concentration (a.u.)")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


def plot_burnup_vs_time(
    inventory,
    *,
    time_unit: str = "days",
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot burnup vs time for burnup inventories.
    """
    if not _is_burnup_time_series_inventory(inventory):
        raise ValueError(
            "inventory must provide (nuclides, concentrations, times, burnup) like "
            "smrforge.burnup.solver.NuclideInventory"
        )

    times_s = np.asarray(inventory.times, dtype=float)
    burnup = np.asarray(inventory.burnup, dtype=float)
    t, t_label = _convert_time(times_s, time_unit)

    plot_title = title or "Burnup vs time"

    if backend == "plotly":
        if not _PLOTLY_AVAILABLE:
            raise ImportError("plotly is required")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=t, y=burnup, mode="lines+markers", name="burnup"))
        fig.update_layout(title=plot_title, xaxis_title=f"Time ({t_label})", yaxis_title="Burnup (MWd/kgU)")
        return fig

    if backend == "matplotlib":
        if not _MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required")
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 5)))
        ax.plot(t, burnup, "o-", linewidth=2)
        ax.set_title(plot_title)
        ax.set_xlabel(f"Time ({t_label})")
        ax.set_ylabel("Burnup (MWd/kgU)")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


def plot_burnup_dashboard(
    inventory,
    *,
    time_unit: str = "days",
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Convenience dashboard combining burnup curve + composition stack.
    """
    plot_title = title or "Burnup dashboard"
    if not _is_burnup_time_series_inventory(inventory):
        raise ValueError(
            "inventory must provide (nuclides, concentrations, times, burnup) like "
            "smrforge.burnup.solver.NuclideInventory"
        )

    if backend == "plotly":
        if not _PLOTLY_AVAILABLE:
            raise ImportError("plotly is required")
        if make_subplots is None:
            raise ImportError("plotly.subplots is required")
        fig = make_subplots(rows=2, cols=1, subplot_titles=("Burnup", "Composition (stacked)"), shared_xaxes=True)
        bfig = plot_burnup_vs_time(inventory, time_unit=time_unit, backend="plotly")
        for tr in bfig.data:
            fig.add_trace(tr, row=1, col=1)
        cfig = plot_composition_stacked_area(inventory, time_unit=time_unit, backend="plotly", normalize=kwargs.get("normalize", False))
        for tr in cfig.data:
            fig.add_trace(tr, row=2, col=1)
        fig.update_layout(title=plot_title, height=700, hovermode="x unified")
        return fig

    if backend == "matplotlib":
        if not _MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required")
        fig, axes = plt.subplots(2, 1, figsize=kwargs.get("figsize", (10, 9)), sharex=True)

        # Burnup curve
        times_s = np.asarray(inventory.times, dtype=float)
        burnup = np.asarray(inventory.burnup, dtype=float)
        t, t_label = _convert_time(times_s, time_unit)
        axes[0].plot(t, burnup, "o-", linewidth=2)
        axes[0].set_ylabel("Burnup (MWd/kgU)")
        axes[0].grid(True, alpha=0.3)
        axes[0].set_title("Burnup")

        # Composition stacked area
        nuclides_all: List[Nuclide] = list(inventory.nuclides)
        conc = np.asarray(inventory.concentrations, dtype=float)
        normalize = bool(kwargs.get("normalize", False))

        # Same auto-bucketing as plot_composition_stacked_area()
        act_idx = [i for i, n in enumerate(nuclides_all) if getattr(n, "Z", 0) >= 89]
        fp_idx = [i for i, n in enumerate(nuclides_all) if i not in act_idx]
        series: Dict[str, np.ndarray] = {
            "Actinides": np.sum(conc[act_idx, :], axis=0) if act_idx else np.zeros(conc.shape[1]),
            "Other/Fission products": np.sum(conc[fp_idx, :], axis=0) if fp_idx else np.zeros(conc.shape[1]),
        }
        if normalize:
            total = np.sum(conc, axis=0)
            total = np.where(total > 0, total, 1.0)
            series = {k: v / total for k, v in series.items()}

        labels = list(series.keys())
        ys = [series[k] for k in labels]
        axes[1].stackplot(t, ys, labels=labels)
        axes[1].set_title("Composition (stacked)")
        axes[1].set_ylabel("Fraction" if normalize else "Concentration (a.u.)")
        axes[1].grid(True, alpha=0.3)
        axes[1].legend(fontsize=8)
        axes[1].set_xlabel(f"Time ({t_label})")

        fig.suptitle(plot_title)
        fig.tight_layout()
        return fig, axes

    raise ValueError(f"Unknown backend: {backend}")


__all__ = [
    "plot_nuclide_concentration",
    "plot_material_property",
    "plot_burnup_composition",
    "plot_nuclide_evolution",
    "plot_composition_stacked_area",
    "plot_burnup_vs_time",
    "plot_burnup_dashboard",
]
