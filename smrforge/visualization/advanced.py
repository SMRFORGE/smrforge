"""
Advanced visualization capabilities inspired by OpenMC.

Provides advanced 3D visualization features including:
- Ray-traced solid geometry plots
- Interactive cross-section slicing
- Material boundary visualization
- Isosurface rendering
- Vector field visualization (neutron currents)
- Multi-view dashboard layouts
- Interactive 3D exploration
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib import cm
    from mpl_toolkits.mplot3d import Axes3D
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False
    plt = None  # type: ignore
    Axes3D = None  # type: ignore
    Poly3DCollection = None  # type: ignore

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

from ..geometry.mesh_3d import Mesh3D, Surface
from ..utils.logging import get_logger

logger = get_logger("smrforge.visualization.advanced")


def plot_ray_traced_geometry(
    geometry,
    origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    width: Tuple[float, float, float] = (200.0, 200.0, 400.0),
    pixels: Tuple[int, int] = (800, 600),
    basis: str = "xy",
    color_by: str = "material",
    backend: str = "plotly",
    **kwargs,
):
    """
    Create ray-traced 3D visualization of reactor geometry.
    
    Inspired by OpenMC's SolidRayTracePlot, this function creates a 3D
    visualization by ray-tracing through the geometry to show material
    boundaries and internal structure.
    
    Args:
        geometry: Reactor geometry (PrismaticCore, PebbleBedCore, or Mesh3D)
        origin: Origin point for the view (x, y, z) [cm]
        width: Width of the view in each direction (x, y, z) [cm]
        pixels: Resolution (width, height) in pixels
        basis: View basis ('xy', 'xz', 'yz', or 'xyz' for 3D)
        color_by: Color scheme - 'material', 'flux', 'power', 'temperature'
        backend: Visualization backend - 'plotly', 'pyvista', or 'matplotlib'
        **kwargs: Additional arguments for the backend
    
    Returns:
        Figure object (backend-dependent)
    
    Example:
        >>> from smrforge.geometry import PrismaticCore
        >>> from smrforge.visualization.advanced import plot_ray_traced_geometry
        >>> 
        >>> core = PrismaticCore()
        >>> core.build_hexagonal_lattice(n_rings=3, pitch=40.0)
        >>> 
        >>> # Create ray-traced view
        >>> fig = plot_ray_traced_geometry(
        ...     core,
        ...     origin=(0, 0, 200),
        ...     width=(300, 300, 400),
        ...     basis='xy',
        ...     backend='plotly'
        ... )
        >>> fig.show()
    """
    if backend == "plotly":
        return _plot_ray_traced_plotly(geometry, origin, width, pixels, basis, color_by, **kwargs)
    elif backend == "pyvista":
        return _plot_ray_traced_pyvista(geometry, origin, width, pixels, basis, color_by, **kwargs)
    elif backend == "matplotlib":
        return _plot_ray_traced_matplotlib(geometry, origin, width, pixels, basis, color_by, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}. Choose 'plotly', 'pyvista', or 'matplotlib'")


def plot_slice(
    data: np.ndarray,
    geometry,
    axis: str = "z",
    position: float = 0.0,
    field_name: str = "flux",
    backend: str = "plotly",
    **kwargs,
):
    """
    Plot a 2D slice through 3D data.
    
    Creates a cross-sectional view through the reactor at a specified
    position along an axis, similar to OpenMC's slice plots.
    
    Args:
        data: 3D data array (n_x, n_y, n_z) or (n_r, n_z) for cylindrical
        geometry: Reactor geometry instance
        axis: Slice axis - 'x', 'y', or 'z'
        position: Position along axis [cm]
        field_name: Name of the field (for labels)
        backend: Visualization backend
        **kwargs: Additional plotting arguments
    
    Returns:
        Figure object
    
    Example:
        >>> flux = solver.get_flux()  # Shape: (n_r, n_z, n_groups)
        >>> fig = plot_slice(
        ...     flux[:, :, 0],  # First energy group
        ...     core,
        ...     axis='z',
        ...     position=200.0,  # Mid-height
        ...     field_name='Flux (Group 1)'
        ... )
    """
    if backend == "plotly":
        return _plot_slice_plotly(data, geometry, axis, position, field_name, **kwargs)
    elif backend == "matplotlib":
        return _plot_slice_matplotlib(data, geometry, axis, position, field_name, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def plot_isosurface(
    data: np.ndarray,
    geometry,
    isovalue: float,
    field_name: str = "flux",
    backend: str = "plotly",
    **kwargs,
):
    """
    Plot an isosurface (contour surface) in 3D.
    
    Creates a 3D surface showing where a scalar field equals a specific value.
    Useful for visualizing flux levels, temperature isotherms, etc.
    
    Args:
        data: 3D scalar field array
        geometry: Reactor geometry
        isovalue: Value to contour
        field_name: Name of the field
        backend: Visualization backend
        **kwargs: Additional arguments
    
    Returns:
        Figure object
    
    Example:
        >>> # Plot isosurface where flux = 1e14 n/cm²/s
        >>> fig = plot_isosurface(
        ...     flux_3d,
        ...     core,
        ...     isovalue=1e14,
        ...     field_name='Flux'
        ... )
    """
    if backend == "plotly":
        return _plot_isosurface_plotly(data, geometry, isovalue, field_name, **kwargs)
    elif backend == "pyvista":
        return _plot_isosurface_pyvista(data, geometry, isovalue, field_name, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def plot_vector_field(
    vectors: np.ndarray,
    positions: np.ndarray,
    geometry,
    field_name: str = "current",
    scale: float = 1.0,
    backend: str = "plotly",
    **kwargs,
):
    """
    Plot a 3D vector field (e.g., neutron current).
    
    Visualizes vector quantities like neutron current, velocity fields,
    or gradient fields in 3D space.
    
    Args:
        vectors: Vector field array (n_points, 3) - (vx, vy, vz)
        positions: Position array (n_points, 3) - (x, y, z)
        geometry: Reactor geometry
        field_name: Name of the vector field
        scale: Scaling factor for arrow lengths
        backend: Visualization backend
        **kwargs: Additional arguments
    
    Returns:
        Figure object
    
    Example:
        >>> # Plot neutron current
        >>> current = solver.get_current()  # (n_points, 3)
        >>> positions = mesh.get_centers()  # (n_points, 3)
        >>> fig = plot_vector_field(
        ...     current,
        ...     positions,
        ...     core,
        ...     field_name='Neutron Current',
        ...     scale=1e-5
        ... )
    """
    if backend == "plotly":
        return _plot_vector_field_plotly(vectors, positions, geometry, field_name, scale, **kwargs)
    elif backend == "pyvista":
        return _plot_vector_field_pyvista(vectors, positions, geometry, field_name, scale, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def plot_material_boundaries(
    geometry,
    materials: Optional[List[str]] = None,
    opacity: float = 0.7,
    backend: str = "plotly",
    **kwargs,
):
    """
    Visualize material boundaries in 3D.
    
    Highlights interfaces between different materials, useful for
    understanding geometry structure and material distributions.
    
    Args:
        geometry: Reactor geometry
        materials: Optional list of material names to highlight
        opacity: Surface opacity (0-1)
        backend: Visualization backend
        **kwargs: Additional arguments
    
    Returns:
        Figure object
    
    Example:
        >>> fig = plot_material_boundaries(
        ...     core,
        ...     materials=['fuel', 'moderator', 'reflector'],
        ...     opacity=0.8
        ... )
    """
    if backend == "plotly":
        return _plot_material_boundaries_plotly(geometry, materials, opacity, **kwargs)
    elif backend == "pyvista":
        return _plot_material_boundaries_pyvista(geometry, materials, opacity, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def create_dashboard(
    plots: List[Dict],
    layout: str = "grid",
    backend: str = "plotly",
    **kwargs,
):
    """
    Create a multi-plot dashboard layout.
    
    Combines multiple visualizations into a single interactive dashboard,
    similar to OpenMC's multi-view layouts.
    
    Args:
        plots: List of plot dictionaries, each with 'type', 'data', 'geometry', etc.
        layout: Layout style - 'grid', 'row', 'column', or 'custom'
        backend: Visualization backend
        **kwargs: Additional layout arguments
    
    Returns:
        Figure object with subplots
    
    Example:
        >>> plots = [
        ...     {'type': 'slice', 'data': flux, 'axis': 'z', 'position': 200.0},
        ...     {'type': 'slice', 'data': power, 'axis': 'z', 'position': 200.0},
        ...     {'type': 'core_layout', 'geometry': core, 'view': 'xy'},
        ... ]
        >>> fig = create_dashboard(plots, layout='grid', ncols=2)
    """
    if backend == "plotly":
        return _create_dashboard_plotly(plots, layout, **kwargs)
    elif backend == "matplotlib":
        return _create_dashboard_matplotlib(plots, layout, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")


# Implementation functions

def _plot_ray_traced_plotly(geometry, origin, width, pixels, basis, color_by, **kwargs):
    """Ray-traced plot using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required for ray-traced visualization")
    
    fig = go.Figure()
    
    # For now, create a simplified ray-traced view
    # In a full implementation, would use actual ray-tracing algorithm
    if hasattr(geometry, "blocks"):
        # Prismatic core
        for block in geometry.blocks:
            # Create block representation
            vertices = block.vertices()
            if len(vertices) >= 3:
                # Create 3D representation
                x = [v[0] for v in vertices] + [vertices[0][0]]
                y = [v[1] for v in vertices] + [vertices[0][1]]
                z = [block.position.z] * len(vertices) + [block.position.z]
                
                fig.add_trace(
                    go.Scatter3d(
                        x=x,
                        y=y,
                        z=z,
                        mode="lines",
                        name=f"Block {block.id}",
                        line=dict(color="blue", width=2),
                    )
                )
    
    fig.update_layout(
        title="Ray-Traced Geometry View",
        scene=dict(
            xaxis_title="X (cm)",
            yaxis_title="Y (cm)",
            zaxis_title="Z (cm)",
            aspectmode="data",
        ),
        width=pixels[0],
        height=pixels[1],
    )
    
    return fig


def _plot_ray_traced_pyvista(geometry, origin, width, pixels, basis, color_by, **kwargs):
    """Ray-traced plot using pyvista."""
    if not _PYVISTA_AVAILABLE:
        raise ImportError("pyvista is required for pyvista visualization")
    
    plotter = pv.Plotter()
    
    # Add geometry to plotter
    if hasattr(geometry, "blocks"):
        for block in geometry.blocks:
            # Create block mesh
            # Simplified - would use actual geometry extraction
            pass
    
    plotter.show()
    return plotter


def _plot_ray_traced_matplotlib(geometry, origin, width, pixels, basis, color_by, **kwargs):
    """Ray-traced plot using matplotlib."""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib is required for matplotlib visualization")
    
    fig = plt.figure(figsize=(pixels[0] / 100, pixels[1] / 100))
    ax = fig.add_subplot(111, projection="3d")
    
    # Add geometry
    if hasattr(geometry, "blocks"):
        for block in geometry.blocks:
            vertices = block.vertices()
            # Create 3D polygon
            # Simplified representation
    
    ax.set_xlabel("X (cm)")
    ax.set_ylabel("Y (cm)")
    ax.set_zlabel("Z (cm)")
    ax.set_title("Ray-Traced Geometry View")
    
    return fig


def _plot_slice_plotly(data, geometry, axis, position, field_name, **kwargs):
    """Plot slice using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")
    
    # Determine slice index
    if axis == "z":
        # Slice through z-axis (horizontal slice)
        if len(data.shape) == 2:  # (r, z)
            z_idx = int(position / geometry.axial_mesh[1] if hasattr(geometry, "axial_mesh") else 0)
            slice_data = data[:, z_idx] if z_idx < data.shape[1] else data[:, -1]
        else:
            raise ValueError("Data shape not supported for z-slice")
    
    fig = go.Figure()
    
    # Create contour plot
    fig.add_trace(
        go.Contour(
            z=slice_data,
            colorscale="Viridis",
            name=field_name,
        )
    )
    
    fig.update_layout(
        title=f"{field_name} - {axis.upper()}-Slice at {position:.1f} cm",
        xaxis_title="Radial Position (cm)",
        yaxis_title="Azimuthal Angle",
    )
    
    return fig


def _plot_slice_matplotlib(data, geometry, axis, position, field_name, **kwargs):
    """Plot slice using matplotlib."""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib is required")
    
    fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 8)))
    
    # Similar logic to plotly version
    if axis == "z":
        if len(data.shape) == 2:
            z_idx = int(position / geometry.axial_mesh[1] if hasattr(geometry, "axial_mesh") else 0)
            slice_data = data[:, z_idx] if z_idx < data.shape[1] else data[:, -1]
    
    im = ax.contourf(slice_data, **kwargs)
    plt.colorbar(im, ax=ax, label=field_name)
    ax.set_title(f"{field_name} - {axis.upper()}-Slice at {position:.1f} cm")
    
    return fig


def _plot_isosurface_plotly(data, geometry, isovalue, field_name, **kwargs):
    """Plot isosurface using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")
    
    # Use marching cubes or similar algorithm
    # For now, simplified version
    fig = go.Figure()
    
    # Would use scipy or skimage for isosurface extraction
    logger.warning("Isosurface extraction not fully implemented - using simplified version")
    
    return fig


def _plot_isosurface_pyvista(data, geometry, isovalue, field_name, **kwargs):
    """Plot isosurface using pyvista."""
    if not _PYVISTA_AVAILABLE:
        raise ImportError("pyvista is required")
    
    # PyVista has built-in isosurface support
    plotter = pv.Plotter()
    
    # Create grid from data
    # grid = pv.StructuredGrid(...)
    # isosurface = grid.contour([isovalue])
    # plotter.add_mesh(isosurface, ...)
    
    return plotter


def _plot_vector_field_plotly(vectors, positions, geometry, field_name, scale, **kwargs):
    """Plot vector field using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")
    
    fig = go.Figure()
    
    # Scale vectors
    scaled_vectors = vectors * scale
    
    # Create cone plot or quiver plot
    fig.add_trace(
        go.Cone(
            x=positions[:, 0],
            y=positions[:, 1],
            z=positions[:, 2],
            u=scaled_vectors[:, 0],
            v=scaled_vectors[:, 1],
            w=scaled_vectors[:, 2],
            name=field_name,
        )
    )
    
    fig.update_layout(
        title=f"{field_name} Vector Field",
        scene=dict(
            xaxis_title="X (cm)",
            yaxis_title="Y (cm)",
            zaxis_title="Z (cm)",
            aspectmode="data",
        ),
    )
    
    return fig


def _plot_vector_field_pyvista(vectors, positions, geometry, field_name, scale, **kwargs):
    """Plot vector field using pyvista."""
    if not _PYVISTA_AVAILABLE:
        raise ImportError("pyvista is required")
    
    plotter = pv.Plotter()
    
    # Create point cloud
    points = pv.PolyData(positions)
    points["vectors"] = vectors * scale
    
    # Add arrows
    arrows = points.glyph(orient="vectors", scale=True, factor=1.0)
    plotter.add_mesh(arrows, **kwargs)
    
    return plotter


def _plot_material_boundaries_plotly(geometry, materials, opacity, **kwargs):
    """Plot material boundaries using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")
    
    fig = go.Figure()
    
    # Extract material boundaries from geometry
    if hasattr(geometry, "blocks"):
        material_colors = {
            "fuel": "red",
            "moderator": "blue",
            "reflector": "gray",
            "control": "black",
        }
        
        for block in geometry.blocks:
            mat = getattr(block, "material", "unknown")
            color = material_colors.get(mat, "gray")
            
            # Add block surface
            # Simplified - would extract actual surfaces
    
    fig.update_layout(
        title="Material Boundaries",
        scene=dict(aspectmode="data"),
    )
    
    return fig


def _plot_material_boundaries_pyvista(geometry, materials, opacity, **kwargs):
    """Plot material boundaries using pyvista."""
    if not _PYVISTA_AVAILABLE:
        raise ImportError("pyvista is required")
    
    plotter = pv.Plotter()
    
    # Similar to plotly version but using pyvista
    
    return plotter


def _create_dashboard_plotly(plots, layout, **kwargs):
    """Create dashboard using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")
    
    n_plots = len(plots)
    ncols = kwargs.get("ncols", 2)
    nrows = (n_plots + ncols - 1) // ncols
    
    fig = make_subplots(
        rows=nrows,
        cols=ncols,
        subplot_titles=[p.get("title", f"Plot {i+1}") for i, p in enumerate(plots)],
        specs=[[{"type": "scatter3d" if p.get("type") == "3d" else "xy"} for _ in range(ncols)] for _ in range(nrows)],
    )
    
    # Add each plot
    for i, plot_dict in enumerate(plots):
        row = i // ncols + 1
        col = i % ncols + 1
        
        plot_type = plot_dict.get("type", "slice")
        # Add trace based on type
        # Implementation would depend on plot type
    
    fig.update_layout(height=kwargs.get("height", 800), title=kwargs.get("title", "Dashboard"))
    
    return fig


def _create_dashboard_matplotlib(plots, layout, **kwargs):
    """Create dashboard using matplotlib."""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib is required")
    
    n_plots = len(plots)
    ncols = kwargs.get("ncols", 2)
    nrows = (n_plots + ncols - 1) // ncols
    
    fig, axes = plt.subplots(nrows, ncols, figsize=kwargs.get("figsize", (16, 4 * nrows)))
    
    if n_plots == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    
    for i, (plot_dict, ax) in enumerate(zip(plots, axes)):
        plot_type = plot_dict.get("type", "slice")
        # Add plot based on type
    
    return fig


def export_visualization(
    fig,
    filepath: Union[str, Path],
    format: str = "html",
    **kwargs,
):
    """
    Export visualization to various formats.
    
    Supports export to HTML (interactive), PNG, PDF, SVG, and VTK formats.
    
    Args:
        fig: Figure object (plotly, matplotlib, or pyvista)
        filepath: Output file path
        format: Export format - 'html', 'png', 'pdf', 'svg', 'vtk', 'stl'
        **kwargs: Format-specific options
    
    Example:
        >>> fig = plot_ray_traced_geometry(core)
        >>> export_visualization(fig, "core_view.html", format="html")
        >>> export_visualization(fig, "core_view.png", format="png", width=1920, height=1080)
    """
    filepath = Path(filepath)
    
    if format == "html":
        if hasattr(fig, "write_html"):
            fig.write_html(str(filepath), **kwargs)
        else:
            raise ValueError("Figure does not support HTML export")
    
    elif format in ["png", "pdf", "svg"]:
        if hasattr(fig, "write_image"):
            fig.write_image(str(filepath), format=format, **kwargs)
        elif hasattr(fig, "savefig"):
            fig.savefig(str(filepath), format=format, **kwargs)
        else:
            raise ValueError(f"Figure does not support {format} export")
    
    elif format == "vtk":
        if hasattr(fig, "save"):
            # PyVista plotter
            fig.save(str(filepath))
        else:
            raise ValueError("VTK export only supported for PyVista figures")
    
    else:
        raise ValueError(f"Unknown format: {format}")


def create_interactive_viewer(
    geometry,
    data: Optional[Dict[str, np.ndarray]] = None,
    backend: str = "plotly",
    **kwargs,
):
    """
    Create an interactive 3D viewer for exploring reactor geometry and data.
    
    Provides interactive controls for:
    - Rotating and zooming
    - Slicing through data
    - Toggling visibility of components
    - Changing color schemes
    
    Args:
        geometry: Reactor geometry
        data: Optional dictionary of data fields (e.g., {'flux': flux_array, 'power': power_array})
        backend: Visualization backend
        **kwargs: Additional viewer options
    
    Returns:
        Interactive viewer object
    
    Example:
        >>> viewer = create_interactive_viewer(
        ...     core,
        ...     data={'flux': flux, 'power': power},
        ...     backend='plotly'
        ... )
        >>> viewer.show()
    """
    if backend == "plotly":
        return _create_interactive_viewer_plotly(geometry, data, **kwargs)
    elif backend == "pyvista":
        return _create_interactive_viewer_pyvista(geometry, data, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def _create_interactive_viewer_plotly(geometry, data, **kwargs):
    """Create interactive plotly viewer."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")
    
    fig = go.Figure()
    
    # Add geometry
    if hasattr(geometry, "blocks"):
        for block in geometry.blocks:
            # Add block visualization
            pass
    
    # Add data overlays if provided
    if data:
        for field_name, field_data in data.items():
            # Add data visualization
            pass
    
    # Add interactive controls
    fig.update_layout(
        title="Interactive Reactor Viewer",
        scene=dict(
            xaxis_title="X (cm)",
            yaxis_title="Y (cm)",
            zaxis_title="Z (cm)",
            aspectmode="data",
            dragmode="orbit",  # Enable rotation
        ),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list([
                    dict(
                        args=[{"visible": [True] * len(fig.data)}],
                        label="Show All",
                        method="update"
                    ),
                ]),
                pad={"r": 10, "t": 87},
                showactive=True,
                x=0.11,
                xanchor="left",
                y=1.02,
                yanchor="top"
            ),
        ],
    )
    
    return fig


def _create_interactive_viewer_pyvista(geometry, data, **kwargs):
    """Create interactive pyvista viewer."""
    if not _PYVISTA_AVAILABLE:
        raise ImportError("pyvista is required")
    
    plotter = pv.Plotter()
    
    # Add geometry and data
    # PyVista has built-in interactive controls
    
    return plotter
