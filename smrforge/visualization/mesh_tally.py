"""
Mesh tally visualization for flux and reaction rate data.

Provides specialized visualization for mesh-based flux and reaction rate
data, similar to OpenMC's mesh tally visualization.
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

try:
    import pyvista as pv
    _PYVISTA_AVAILABLE = True
except ImportError:
    _PYVISTA_AVAILABLE = False
    pv = None  # type: ignore

from ..geometry.mesh_3d import Mesh3D
from ..utils.logging import get_logger

logger = get_logger("smrforge.visualization.mesh_tally")


def _extract_uncertainty_for_view(
    mesh_tally: "MeshTally",
    energy_group: Optional[int],
    *,
    mode: str = "relative",
    eps: float = 1e-30,
) -> Optional[np.ndarray]:
    """
    Extract an uncertainty array matching the plotted data.

    Assumes ``mesh_tally.uncertainty`` is an absolute 1-sigma array with the same
    shape as ``mesh_tally.data``.
    """
    if mesh_tally.uncertainty is None:
        return None

    unc = np.asarray(mesh_tally.uncertainty)
    dat = np.asarray(mesh_tally.data)
    if unc.shape != dat.shape:
        raise ValueError("mesh_tally.uncertainty must have the same shape as mesh_tally.data")

    if dat.ndim > 3:
        if energy_group is not None:
            unc_view = unc[..., energy_group]
            data_view = dat[..., energy_group]
        else:
            # Total: combine independent group uncertainties in quadrature.
            unc_view = np.sqrt(np.sum(np.square(unc), axis=-1))
            data_view = np.sum(dat, axis=-1)
    else:
        unc_view = unc
        data_view = dat

    mode = (mode or "relative").lower()
    if mode in ("absolute", "abs"):
        return np.asarray(unc_view, dtype=float)

    if mode in ("relative", "rel", "percent", "pct"):
        denom = np.maximum(np.abs(np.asarray(data_view, dtype=float)), eps)
        rel = np.asarray(unc_view, dtype=float) / denom
        if mode in ("percent", "pct"):
            rel = rel * 100.0
        return rel

    raise ValueError("uncertainty_mode must be 'relative', 'percent', or 'absolute'")


class MeshTally:
    """
    Mesh tally data container for visualization.
    
    Represents flux or reaction rate data on a spatial mesh, similar to
    OpenMC's mesh tally structure.
    
    Attributes:
        name: Tally name
        tally_type: Type of tally - 'flux', 'fission_rate', 'capture_rate', etc.
        data: Tally data array [nx, ny, nz, ng] or [nr, nz, ng] for cylindrical
        uncertainty: Optional uncertainty array (same shape as data)
        mesh_coords: Mesh coordinate arrays (x, y, z) or (r, z)
        energy_groups: Energy group boundaries [eV]
        geometry_type: 'cartesian' or 'cylindrical'
    """
    
    def __init__(
        self,
        name: str,
        tally_type: str,
        data: np.ndarray,
        mesh_coords: Tuple[np.ndarray, ...],
        energy_groups: Optional[np.ndarray] = None,
        uncertainty: Optional[np.ndarray] = None,
        geometry_type: str = "cartesian",
    ):
        """
        Initialize mesh tally.
        
        Args:
            name: Tally name
            tally_type: Type of tally ('flux', 'fission_rate', 'capture_rate', etc.)
            data: Tally data array
            mesh_coords: Coordinate arrays (x, y, z) for cartesian or (r, z) for cylindrical
            energy_groups: Energy group boundaries [eV]
            uncertainty: Optional uncertainty array
            geometry_type: 'cartesian' or 'cylindrical'
        """
        self.name = name
        self.tally_type = tally_type
        self.data = data
        self.mesh_coords = mesh_coords
        self.energy_groups = energy_groups
        self.uncertainty = uncertainty
        self.geometry_type = geometry_type
    
    def get_total(self) -> np.ndarray:
        """Get total (sum over all energy groups)."""
        if self.data.ndim > 3:
            return np.sum(self.data, axis=-1)
        return self.data
    
    def get_group(self, group: int) -> np.ndarray:
        """Get data for specific energy group."""
        if self.data.ndim > 3:
            return self.data[..., group]
        elif group == 0:
            return self.data
        else:
            raise IndexError(f"Energy group {group} out of range")
    
    def get_energy_spectrum(self, position: Tuple[int, ...]) -> np.ndarray:
        """Get energy spectrum at specific position."""
        if self.data.ndim > 3:
            return self.data[position]
        else:
            return np.array([self.data[position]])  # Single group


def plot_mesh_tally(
    mesh_tally: MeshTally,
    geometry,
    field: str = "flux",
    energy_group: Optional[int] = None,
    backend: str = "plotly",
    show_uncertainty: bool = False,
    **kwargs,
):
    """
    Plot mesh tally results on geometry.
    
    Visualizes flux or reaction rate data from a mesh tally, similar to
    OpenMC's plot_mesh_tally function.
    
    Args:
        mesh_tally: MeshTally instance with flux/reaction rate data
        geometry: Reactor geometry
        field: Field to plot ('flux', 'fission_rate', 'capture_rate', etc.)
        energy_group: Energy group index (None for total)
        backend: Visualization backend - 'plotly', 'pyvista', 'matplotlib'
        show_uncertainty: Whether to show uncertainty visualization
        **kwargs: Additional plotting arguments
    
    Returns:
        Figure object (backend-dependent)
    
    Example:
        >>> from smrforge.visualization.mesh_tally import MeshTally, plot_mesh_tally
        >>> 
        >>> # Create mesh tally from flux data
        >>> flux_data = solver.get_flux()  # [nz, nr, ng]
        >>> r_coords = geometry.radial_mesh
        >>> z_coords = geometry.axial_mesh
        >>> 
        >>> tally = MeshTally(
        ...     name="flux",
        ...     tally_type="flux",
        ...     data=flux_data,
        ...     mesh_coords=(r_coords, z_coords),
        ...     geometry_type="cylindrical"
        ... )
        >>> 
        >>> # Plot total flux
        >>> fig = plot_mesh_tally(tally, geometry, field="flux", backend="plotly")
        >>> fig.show()
    """
    if backend == "plotly":
        return _plot_mesh_tally_plotly(mesh_tally, geometry, field, energy_group, show_uncertainty, **kwargs)
    elif backend == "pyvista":
        return _plot_mesh_tally_pyvista(mesh_tally, geometry, field, energy_group, show_uncertainty, **kwargs)
    elif backend == "matplotlib":
        return _plot_mesh_tally_matplotlib(mesh_tally, geometry, field, energy_group, show_uncertainty, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def _plot_mesh_tally_plotly(mesh_tally, geometry, field, energy_group, show_uncertainty, **kwargs):
    """Plot mesh tally using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")
    
    # Get data for specified group or total
    if energy_group is not None:
        data = mesh_tally.get_group(energy_group)
        title = f"{mesh_tally.name} - Group {energy_group}"
    else:
        data = mesh_tally.get_total()
        title = f"{mesh_tally.name} - Total"
    
    # Handle different geometry types
    if mesh_tally.geometry_type == "cylindrical":
        # Cylindrical (r, z) - create 2D plot
        r_coords, z_coords = mesh_tally.mesh_coords
        r_centers = (r_coords[:-1] + r_coords[1:]) / 2
        z_centers = (z_coords[:-1] + z_coords[1:]) / 2

        if show_uncertainty and mesh_tally.uncertainty is not None:
            uncertainty_mode = kwargs.pop("uncertainty_mode", "percent")
            unc_view = _extract_uncertainty_for_view(
                mesh_tally, energy_group, mode=str(uncertainty_mode)
            )
            unc_title = (
                "Relative uncertainty (%)"
                if str(uncertainty_mode).lower() in ("percent", "pct")
                else ("Relative uncertainty" if str(uncertainty_mode).lower() in ("relative", "rel") else "Uncertainty")
            )

            fig = make_subplots(
                rows=1,
                cols=2,
                subplot_titles=(title, unc_title),
                horizontal_spacing=0.12,
            )
            fig.add_trace(
                go.Heatmap(
                    z=data,
                    x=r_centers,
                    y=z_centers,
                    colorscale="Viridis",
                    colorbar=dict(title=field),
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Heatmap(
                    z=unc_view,
                    x=r_centers,
                    y=z_centers,
                    colorscale="Magma",
                    colorbar=dict(title=unc_title),
                ),
                row=1,
                col=2,
            )
            fig.update_xaxes(title_text="Radius (cm)", row=1, col=1)
            fig.update_yaxes(title_text="Height (cm)", row=1, col=1)
            fig.update_xaxes(title_text="Radius (cm)", row=1, col=2)
            fig.update_yaxes(title_text="Height (cm)", row=1, col=2)
            fig.update_layout(title=kwargs.pop("suptitle", f"{mesh_tally.name} (value + uncertainty)"))
        else:
            fig = go.Figure(
                data=go.Heatmap(
                    z=data,
                    x=r_centers,
                    y=z_centers,
                    colorscale="Viridis",
                    colorbar=dict(title=field),
                )
            )

            fig.update_layout(
                title=title,
                xaxis_title="Radius (cm)",
                yaxis_title="Height (cm)",
            )
    
    else:
        # Cartesian (x, y, z) - create 3D volume or slice
        x_coords, y_coords, z_coords = mesh_tally.mesh_coords
        
        # For 3D, create volume plot
        x, y, z = np.meshgrid(
            (x_coords[:-1] + x_coords[1:]) / 2,
            (y_coords[:-1] + y_coords[1:]) / 2,
            (z_coords[:-1] + z_coords[1:]) / 2,
            indexing="ij",
        )
        
        fig = go.Figure(data=go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=data.flatten(),
            isomin=data.min(),
            isomax=data.max(),
            opacity=0.3,
            surface_count=10,
            colorbar=dict(title=field),
        ))
        
        fig.update_layout(
            title=title,
            scene=dict(
                xaxis_title="X (cm)",
                yaxis_title="Y (cm)",
                zaxis_title="Z (cm)",
            ),
        )

    return fig


def _plot_mesh_tally_pyvista(mesh_tally, geometry, field, energy_group, show_uncertainty, **kwargs):
    """Plot mesh tally using pyvista."""
    if not _PYVISTA_AVAILABLE:
        raise ImportError("pyvista is required")
    
    # Get data
    if energy_group is not None:
        data = mesh_tally.get_group(energy_group)
    else:
        data = mesh_tally.get_total()
    
    # Create mesh
    if mesh_tally.geometry_type == "cylindrical":
        r_coords, z_coords = mesh_tally.mesh_coords
        r_centers = (r_coords[:-1] + r_coords[1:]) / 2
        z_centers = (z_coords[:-1] + z_coords[1:]) / 2
        
        # Create structured grid
        r_grid, z_grid = np.meshgrid(r_centers, z_centers, indexing="ij")
        theta = np.linspace(0, 2 * np.pi, 20)
        r_3d = r_grid[:, :, np.newaxis] * np.ones((1, 1, len(theta)))
        z_3d = z_grid[:, :, np.newaxis] * np.ones((1, 1, len(theta)))
        theta_3d = np.ones_like(r_3d) * theta[np.newaxis, np.newaxis, :]
        
        x = r_3d * np.cos(theta_3d)
        y = r_3d * np.sin(theta_3d)
        z = z_3d
        
        grid = pv.StructuredGrid(x, y, z)
        grid[field] = np.repeat(data[:, :, np.newaxis], len(theta), axis=2).flatten(order="F")
    
    else:
        x_coords, y_coords, z_coords = mesh_tally.mesh_coords
        x, y, z = np.meshgrid(
            (x_coords[:-1] + x_coords[1:]) / 2,
            (y_coords[:-1] + y_coords[1:]) / 2,
            (z_coords[:-1] + z_coords[1:]) / 2,
            indexing="ij",
        )
        
        grid = pv.StructuredGrid(x, y, z)
        grid[field] = data.flatten(order="F")
    
    plotter = pv.Plotter()
    plotter.add_mesh(grid, scalars=field, cmap="viridis")
    plotter.show_axes()
    
    return plotter


def _plot_mesh_tally_matplotlib(mesh_tally, geometry, field, energy_group, show_uncertainty, **kwargs):
    """Plot mesh tally using matplotlib."""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib is required")
    
    # Get data
    if energy_group is not None:
        data = mesh_tally.get_group(energy_group)
        title = f"{mesh_tally.name} - Group {energy_group}"
    else:
        data = mesh_tally.get_total()
        title = f"{mesh_tally.name} - Total"
    
    if mesh_tally.geometry_type == "cylindrical":
        # 2D plot
        r_coords, z_coords = mesh_tally.mesh_coords
        r_centers = (r_coords[:-1] + r_coords[1:]) / 2
        z_centers = (z_coords[:-1] + z_coords[1:]) / 2

        if show_uncertainty and mesh_tally.uncertainty is not None:
            uncertainty_mode = kwargs.pop("uncertainty_mode", "percent")
            unc_view = _extract_uncertainty_for_view(
                mesh_tally, energy_group, mode=str(uncertainty_mode)
            )
            unc_label = (
                "Relative uncertainty (%)"
                if str(uncertainty_mode).lower() in ("percent", "pct")
                else ("Relative uncertainty" if str(uncertainty_mode).lower() in ("relative", "rel") else "Uncertainty")
            )

            fig, (ax0, ax1) = plt.subplots(1, 2, figsize=kwargs.get("figsize", (14, 6)), sharey=True)
            im0 = ax0.contourf(r_centers, z_centers, data, levels=20, cmap="viridis")
            ax0.set_xlabel("Radius (cm)")
            ax0.set_ylabel("Height (cm)")
            ax0.set_title(title)
            plt.colorbar(im0, ax=ax0, label=field)

            im1 = ax1.contourf(r_centers, z_centers, unc_view, levels=20, cmap="magma")
            ax1.set_xlabel("Radius (cm)")
            ax1.set_title(unc_label)
            plt.colorbar(im1, ax=ax1, label=unc_label)
            return fig, (ax0, ax1)

        fig, ax = plt.subplots(figsize=(8, 10))
        im = ax.contourf(r_centers, z_centers, data, levels=20, cmap="viridis")
        ax.set_xlabel("Radius (cm)")
        ax.set_ylabel("Height (cm)")
        ax.set_title(title)
        plt.colorbar(im, ax=ax, label=field)

        return fig, ax
    
    else:
        # 3D - create slice or projection
        if show_uncertainty and mesh_tally.uncertainty is not None:
            uncertainty_mode = kwargs.pop("uncertainty_mode", "percent")
            unc_view = _extract_uncertainty_for_view(
                mesh_tally, energy_group, mode=str(uncertainty_mode)
            )
            unc_label = (
                "Relative uncertainty (%)"
                if str(uncertainty_mode).lower() in ("percent", "pct")
                else ("Relative uncertainty" if str(uncertainty_mode).lower() in ("relative", "rel") else "Uncertainty")
            )

            fig, (ax0, ax1) = plt.subplots(1, 2, figsize=kwargs.get("figsize", (14, 6)))
            x_coords, y_coords, z_coords = mesh_tally.mesh_coords
            x_centers = (x_coords[:-1] + x_coords[1:]) / 2
            y_centers = (y_coords[:-1] + y_coords[1:]) / 2
            z_centers = (z_coords[:-1] + z_coords[1:]) / 2

            mid_z = len(z_centers) // 2
            X, Y = np.meshgrid(x_centers, y_centers, indexing="xy")

            im0 = ax0.contourf(X, Y, data[:, :, mid_z], levels=20, cmap="viridis")
            ax0.set_title(f"{title} - Slice at z={z_centers[mid_z]:.1f} cm")
            ax0.set_xlabel("X (cm)")
            ax0.set_ylabel("Y (cm)")
            plt.colorbar(im0, ax=ax0, label=field)

            im1 = ax1.contourf(X, Y, unc_view[:, :, mid_z], levels=20, cmap="magma")
            ax1.set_title(f"{unc_label} - Slice at z={z_centers[mid_z]:.1f} cm")
            ax1.set_xlabel("X (cm)")
            ax1.set_ylabel("Y (cm)")
            plt.colorbar(im1, ax=ax1, label=unc_label)
            return fig, (ax0, ax1)

        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection="3d")
        
        x_coords, y_coords, z_coords = mesh_tally.mesh_coords
        x_centers = (x_coords[:-1] + x_coords[1:]) / 2
        y_centers = (y_coords[:-1] + y_coords[1:]) / 2
        z_centers = (z_coords[:-1] + z_coords[1:]) / 2
        
        # Plot slice at mid-point
        mid_z = len(z_centers) // 2
        X, Y = np.meshgrid(x_centers, y_centers)
        Z = data[:, :, mid_z]
        
        ax.contourf(X, Y, Z, levels=20, cmap="viridis", alpha=0.8)
        ax.set_xlabel("X (cm)")
        ax.set_ylabel("Y (cm)")
        ax.set_zlabel("Z (cm)")
        ax.set_title(f"{title} - Slice at z={z_centers[mid_z]:.1f} cm")
        
        return fig, ax


def plot_multi_group_mesh_tally(
    mesh_tally: MeshTally,
    geometry,
    backend: str = "plotly",
    **kwargs,
):
    """
    Plot multiple energy groups in a grid layout.
    
    Args:
        mesh_tally: MeshTally instance
        geometry: Reactor geometry
        backend: Visualization backend
        **kwargs: Additional arguments
    
    Returns:
        Figure with subplots for each energy group
    """
    if mesh_tally.data.ndim < 3:
        # Single group - use regular plot
        return plot_mesh_tally(mesh_tally, geometry, backend=backend, **kwargs)
    
    n_groups = mesh_tally.data.shape[-1]
    
    if backend == "plotly":
        if not _PLOTLY_AVAILABLE:
            raise ImportError("plotly is required")
        
        # Create subplots
        cols = min(3, n_groups)
        rows = (n_groups + cols - 1) // cols
        
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=[f"Group {g}" for g in range(n_groups)],
            specs=[[{"type": "heatmap"}] * cols for _ in range(rows)],
        )
        
        for group in range(n_groups):
            row = group // cols + 1
            col = group % cols + 1
            
            data = mesh_tally.get_group(group)
            
            if mesh_tally.geometry_type == "cylindrical":
                r_coords, z_coords = mesh_tally.mesh_coords
                r_centers = (r_coords[:-1] + r_coords[1:]) / 2
                z_centers = (z_coords[:-1] + z_coords[1:]) / 2
                
                fig.add_trace(
                    go.Heatmap(
                        z=data,
                        x=r_centers,
                        y=z_centers,
                        colorscale="Viridis",
                        showscale=(group == 0),
                    ),
                    row=row,
                    col=col,
                )
        
        fig.update_layout(title=f"{mesh_tally.name} - All Energy Groups")
        return fig
    
    else:
        # For other backends, create separate figures
        figs = []
        for group in range(n_groups):
            fig = plot_mesh_tally(mesh_tally, geometry, energy_group=group, backend=backend, **kwargs)
            figs.append(fig)
        return figs
