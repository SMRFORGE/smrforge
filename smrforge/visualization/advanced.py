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

    arr = np.asarray(data)
    if arr.size == 0:
        raise ValueError("plot_slice requires a non-empty data array")

    axis = str(axis).lower()
    interactive = bool(kwargs.pop("interactive", False))
    colorscale = kwargs.pop("colorscale", "Viridis")

    # --- Cylindrical RZ plane helpers (common for SMRForge solver/tally outputs) ---
    def _cyl_rz_centers():
        if not (hasattr(geometry, "radial_mesh") and hasattr(geometry, "axial_mesh")):
            return None
        r_mesh = getattr(geometry, "radial_mesh")
        z_mesh = getattr(geometry, "axial_mesh")
        if r_mesh is None or z_mesh is None:
            return None
        r_mesh = np.asarray(r_mesh, dtype=float)
        z_mesh = np.asarray(z_mesh, dtype=float)
        if r_mesh.ndim != 1 or z_mesh.ndim != 1 or len(r_mesh) < 2 or len(z_mesh) < 2:
            return None
        r_centers = 0.5 * (r_mesh[:-1] + r_mesh[1:])
        z_centers = 0.5 * (z_mesh[:-1] + z_mesh[1:])
        return r_centers, z_centers

    def _as_rz_plane(a: np.ndarray) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        """Return (plane[nz,nr], r_centers[nr], z_centers[nz]) if shape matches geometry."""
        centers = _cyl_rz_centers()
        if centers is None:
            return None
        r_centers, z_centers = centers
        nr = len(r_centers)
        nz = len(z_centers)

        # Allow (nz,nr) or (nr,nz).
        if a.shape == (nz, nr):
            plane = a
        elif a.shape == (nr, nz):
            plane = a.T
        else:
            return None
        return plane, r_centers, z_centers

    # --- Handle solver-style cylindrical-with-energy-group arrays: (nz,nr,ng) ---
    if arr.ndim == 3:
        # If it looks like (nz,nr,ng) with known mesh, reduce to a (nz,nr) plane.
        centers = _cyl_rz_centers()
        if centers is not None:
            r_centers, z_centers = centers
            nr = len(r_centers)
            nz = len(z_centers)
            ng = arr.shape[-1]
            energy_group = kwargs.pop("energy_group", None)
            if arr.shape[:2] == (nz, nr):
                spatial = arr
            elif arr.shape[:2] == (nr, nz):
                spatial = np.transpose(arr, (1, 0, 2))
            else:
                spatial = None
            if spatial is not None:
                if energy_group is None:
                    plane = np.sum(spatial, axis=-1)
                    eg_label = "total"
                else:
                    g = int(energy_group)
                    if g < 0 or g >= ng:
                        raise IndexError(f"energy_group {g} out of range (0..{ng-1})")
                    plane = spatial[:, :, g]
                    eg_label = f"group {g}"

                # RZ heatmap
                fig = go.Figure(
                    data=go.Heatmap(
                        z=plane,
                        x=r_centers,
                        y=z_centers,
                        colorscale=colorscale,
                        colorbar=dict(title=field_name),
                    )
                )
                fig.update_layout(
                    title=kwargs.pop(
                        "title",
                        f"{field_name} (cylindrical R–Z, {eg_label})",
                    ),
                    xaxis_title=kwargs.pop("xaxis_title", "Radius (cm)"),
                    yaxis_title=kwargs.pop("yaxis_title", "Height (cm)"),
                )

                # Optional guide line at requested position (uses axis='z' or 'r')
                if axis in ("z", "r") and position is not None:
                    try:
                        pos = float(position)
                        if axis == "z":
                            fig.add_shape(
                                type="line",
                                x0=float(r_centers[0]),
                                x1=float(r_centers[-1]),
                                y0=pos,
                                y1=pos,
                                line=dict(color="white", width=2, dash="dash"),
                            )
                        elif axis == "r":
                            fig.add_shape(
                                type="line",
                                x0=pos,
                                x1=pos,
                                y0=float(z_centers[0]),
                                y1=float(z_centers[-1]),
                                line=dict(color="white", width=2, dash="dash"),
                            )
                    except Exception:
                        pass
                return fig

    # --- Handle cylindrical 2D planes directly: (nz,nr) or (nr,nz) ---
    if arr.ndim == 2:
        rz = _as_rz_plane(arr)
        if rz is not None:
            plane, r_centers, z_centers = rz
            fig = go.Figure(
                data=go.Heatmap(
                    z=plane,
                    x=r_centers,
                    y=z_centers,
                    colorscale=colorscale,
                    colorbar=dict(title=field_name),
                )
            )
            fig.update_layout(
                title=kwargs.pop("title", f"{field_name} (cylindrical R–Z)"),
                xaxis_title=kwargs.pop("xaxis_title", "Radius (cm)"),
                yaxis_title=kwargs.pop("yaxis_title", "Height (cm)"),
            )
            if axis in ("z", "r") and position is not None:
                try:
                    pos = float(position)
                    if axis == "z":
                        fig.add_shape(
                            type="line",
                            x0=float(r_centers[0]),
                            x1=float(r_centers[-1]),
                            y0=pos,
                            y1=pos,
                            line=dict(color="white", width=2, dash="dash"),
                        )
                    elif axis == "r":
                        fig.add_shape(
                            type="line",
                            x0=pos,
                            x1=pos,
                            y0=float(z_centers[0]),
                            y1=float(z_centers[-1]),
                            line=dict(color="white", width=2, dash="dash"),
                        )
                except Exception:
                    pass
            return fig

    # --- Cartesian 3D scalar field slicing: (nx, ny, nz) ---
    if arr.ndim != 3:
        raise ValueError(
            "plot_slice supports (nz,nr[,ng]) cylindrical arrays (with geometry meshes) or "
            "(nx,ny,nz) cartesian scalar fields"
        )

    # Coordinates (optional). Accept both x/y/z and x_coords/y_coords/z_coords.
    x_coords = kwargs.pop("x_coords", kwargs.pop("x", None))
    y_coords = kwargs.pop("y_coords", kwargs.pop("y", None))
    z_coords = kwargs.pop("z_coords", kwargs.pop("z", None))

    def _coord_1d(c, n: int, name: str):
        if c is None:
            return None
        a = np.asarray(c, dtype=float)
        if a.ndim != 1 or len(a) != n:
            raise ValueError(f"{name} must be a 1D array of length {n}")
        return a

    nx, ny, nz = arr.shape
    x1 = _coord_1d(x_coords, nx, "x_coords")
    y1 = _coord_1d(y_coords, ny, "y_coords")
    z1 = _coord_1d(z_coords, nz, "z_coords")

    def _pick_index(coords: Optional[np.ndarray], n: int, pos: float) -> int:
        if coords is None:
            # Interpret position as index if it looks integer-ish, else use center.
            if np.isfinite(pos) and abs(pos - round(pos)) < 1e-9 and 0 <= int(round(pos)) < n:
                return int(round(pos))
            return n // 2
        return int(np.argmin(np.abs(coords - pos)))

    pos = float(position) if position is not None else float("nan")
    if not np.isfinite(pos):
        pos = 0.0

    def _slice_for_index(i: int):
        if axis == "x":
            # plane is (y,z) -> display x-axis=y, y-axis=z
            raw = arr[i, :, :]  # (ny, nz)
            z_plot = raw.T      # (nz, ny)
            xh = y1 if y1 is not None else np.arange(ny)
            yh = z1 if z1 is not None else np.arange(nz)
            title_s = f"{field_name} - x={float(xh[i]) if x1 is not None else i:g}"
            xlab, ylab = "Y", "Z"
        elif axis == "y":
            # plane is (x,z) -> display x-axis=x, y-axis=z
            raw = arr[:, i, :]  # (nx, nz)
            z_plot = raw.T      # (nz, nx)
            xh = x1 if x1 is not None else np.arange(nx)
            yh = z1 if z1 is not None else np.arange(nz)
            title_s = f"{field_name} - y={float(yh[i]) if y1 is not None else i:g}"
            xlab, ylab = "X", "Z"
        elif axis == "z":
            # plane is (x,y) -> display x-axis=x, y-axis=y
            raw = arr[:, :, i]  # (nx, ny)
            z_plot = raw.T      # (ny, nx)
            xh = x1 if x1 is not None else np.arange(nx)
            yh = y1 if y1 is not None else np.arange(ny)
            title_s = f"{field_name} - z={float(z1[i]) if z1 is not None else i:g}"
            xlab, ylab = "X", "Y"
        else:
            raise ValueError("axis must be 'x', 'y', or 'z' for cartesian 3D arrays")
        return z_plot, xh, yh, title_s, xlab, ylab

    idx0 = _pick_index({"x": x1, "y": y1, "z": z1}.get(axis), {"x": nx, "y": ny, "z": nz}[axis], pos)
    z_plot0, xh0, yh0, title0, xlab0, ylab0 = _slice_for_index(idx0)

    fig = go.Figure(
        data=[
            go.Heatmap(
                z=z_plot0,
                x=xh0,
                y=yh0,
                colorscale=colorscale,
                colorbar=dict(title=field_name),
            )
        ]
    )
    fig.update_layout(
        title=kwargs.pop("title", title0),
        xaxis_title=kwargs.pop("xaxis_title", xlab0),
        yaxis_title=kwargs.pop("yaxis_title", ylab0),
    )

    if not interactive:
        return fig

    # Interactive slider across the chosen axis.
    n_frames = {"x": nx, "y": ny, "z": nz}[axis]
    max_frames = int(kwargs.pop("max_frames", 60))
    step = max(1, int(np.ceil(n_frames / max_frames)))
    indices = list(range(0, n_frames, step))
    if indices[-1] != n_frames - 1:
        indices.append(n_frames - 1)

    frames = []
    for i in indices:
        z_plot_i, xh_i, yh_i, title_i, _, _ = _slice_for_index(i)
        frames.append(
            go.Frame(
                name=str(i),
                data=[
                    go.Heatmap(
                        z=z_plot_i,
                        x=xh_i,
                        y=yh_i,
                        colorscale=colorscale,
                    )
                ],
                layout=go.Layout(title=title_i),
            )
        )
    fig.frames = frames

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                x=1.02,
                y=1.0,
                xanchor="left",
                yanchor="top",
                buttons=[
                    dict(
                        label="Play",
                        method="animate",
                        args=[
                            None,
                            {
                                "frame": {"duration": int(kwargs.pop("frame_ms", 80)), "redraw": True},
                                "transition": {"duration": 0},
                                "fromcurrent": True,
                            },
                        ],
                    ),
                    dict(
                        label="Pause",
                        method="animate",
                        args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}],
                    ),
                ],
            )
        ],
        sliders=[
            dict(
                active=0,
                y=-0.08,
                x=0.1,
                len=0.8,
                steps=[
                    dict(
                        method="animate",
                        label=str(i),
                        args=[[str(i)], {"mode": "immediate", "frame": {"duration": 0, "redraw": True}}],
                    )
                    for i in indices
                ],
            )
        ],
    )
    return fig


def _plot_slice_matplotlib(data, geometry, axis, position, field_name, **kwargs):
    """Plot slice using matplotlib."""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib is required")

    arr = np.asarray(data)
    if arr.size == 0:
        raise ValueError("plot_slice requires a non-empty data array")

    axis = str(axis).lower()
    cmap = kwargs.pop("cmap", "viridis")

    # Cylindrical RZ plane (2D) if mesh is available.
    if arr.ndim in (2, 3) and hasattr(geometry, "radial_mesh") and hasattr(geometry, "axial_mesh"):
        r_mesh = getattr(geometry, "radial_mesh")
        z_mesh = getattr(geometry, "axial_mesh")
        if r_mesh is not None and z_mesh is not None:
            r_mesh = np.asarray(r_mesh, dtype=float)
            z_mesh = np.asarray(z_mesh, dtype=float)
            r_centers = 0.5 * (r_mesh[:-1] + r_mesh[1:])
            z_centers = 0.5 * (z_mesh[:-1] + z_mesh[1:])
            nr = len(r_centers)
            nz = len(z_centers)

            plane = None
            label = ""
            if arr.ndim == 3 and arr.shape[-1] >= 1:
                energy_group = kwargs.pop("energy_group", None)
                if arr.shape[:2] == (nz, nr):
                    spatial = arr
                elif arr.shape[:2] == (nr, nz):
                    spatial = np.transpose(arr, (1, 0, 2))
                else:
                    spatial = None
                if spatial is not None:
                    if energy_group is None:
                        plane = np.sum(spatial, axis=-1)
                        label = "total"
                    else:
                        g = int(energy_group)
                        plane = spatial[:, :, g]
                        label = f"group {g}"
            if plane is None and arr.ndim == 2:
                if arr.shape == (nz, nr):
                    plane = arr
                elif arr.shape == (nr, nz):
                    plane = arr.T

            if plane is not None:
                fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 7)))
                # Show z (vertical) vs r (horizontal).
                extent = [float(r_mesh[0]), float(r_mesh[-1]), float(z_mesh[0]), float(z_mesh[-1])]
                im = ax.imshow(plane, origin="lower", aspect="auto", extent=extent, cmap=cmap)
                ax.set_xlabel(kwargs.pop("xaxis_title", "Radius (cm)"))
                ax.set_ylabel(kwargs.pop("yaxis_title", "Height (cm)"))
                ttl = kwargs.pop("title", f"{field_name} (cylindrical R–Z{', ' + label if label else ''})")
                ax.set_title(ttl)
                fig.colorbar(im, ax=ax, label=field_name)
                return fig, ax

    # Cartesian 3D scalar field slice (nx,ny,nz).
    if arr.ndim != 3:
        raise ValueError("plot_slice requires a 3D scalar field for cartesian slicing")

    x_coords = kwargs.pop("x_coords", kwargs.pop("x", None))
    y_coords = kwargs.pop("y_coords", kwargs.pop("y", None))
    z_coords = kwargs.pop("z_coords", kwargs.pop("z", None))

    nx, ny, nz = arr.shape
    x1 = np.asarray(x_coords, dtype=float) if x_coords is not None else None
    y1 = np.asarray(y_coords, dtype=float) if y_coords is not None else None
    z1 = np.asarray(z_coords, dtype=float) if z_coords is not None else None

    def _pick_index(coords: Optional[np.ndarray], n: int, pos: float) -> int:
        if coords is None:
            if np.isfinite(pos) and abs(pos - round(pos)) < 1e-9 and 0 <= int(round(pos)) < n:
                return int(round(pos))
            return n // 2
        return int(np.argmin(np.abs(coords - pos)))

    pos = float(position) if position is not None else 0.0
    if axis == "x":
        i = _pick_index(x1, nx, pos)
        raw = arr[i, :, :]  # (ny, nz)
        z_plot = raw.T      # (nz, ny)
        xh = y1 if y1 is not None else np.arange(ny)
        yh = z1 if z1 is not None else np.arange(nz)
        xlab, ylab = "Y", "Z"
        title = kwargs.pop("title", f"{field_name} slice @ x={pos:g}")
    elif axis == "y":
        i = _pick_index(y1, ny, pos)
        raw = arr[:, i, :]  # (nx, nz)
        z_plot = raw.T      # (nz, nx)
        xh = x1 if x1 is not None else np.arange(nx)
        yh = z1 if z1 is not None else np.arange(nz)
        xlab, ylab = "X", "Z"
        title = kwargs.pop("title", f"{field_name} slice @ y={pos:g}")
    elif axis == "z":
        i = _pick_index(z1, nz, pos)
        raw = arr[:, :, i]  # (nx, ny)
        z_plot = raw.T      # (ny, nx)
        xh = x1 if x1 is not None else np.arange(nx)
        yh = y1 if y1 is not None else np.arange(ny)
        xlab, ylab = "X", "Y"
        title = kwargs.pop("title", f"{field_name} slice @ z={pos:g}")
    else:
        raise ValueError("axis must be 'x', 'y', or 'z'")

    fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 7)))
    im = ax.imshow(z_plot, origin="lower", aspect="auto", cmap=cmap)
    ax.set_xlabel(kwargs.pop("xaxis_title", xlab))
    ax.set_ylabel(kwargs.pop("yaxis_title", ylab))
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label=field_name)
    return fig, ax


def _plot_isosurface_plotly(data, geometry, isovalue, field_name, **kwargs):
    """Plot isosurface using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")

    arr = np.asarray(data)
    if arr.ndim != 3:
        raise ValueError(
            "plot_isosurface expects a 3D scalar field array with shape (nx, ny, nz)"
        )

    # Optional coordinate arrays. If provided, they should be 1D arrays for each axis.
    # Note: passing explicit x/y/z grids to plotly requires flattening, which can be
    # memory-heavy for very large volumes.
    x_coords = kwargs.pop("x", None)
    y_coords = kwargs.pop("y", None)
    z_coords = kwargs.pop("z", None)

    opacity = float(kwargs.pop("opacity", 0.6))
    colorscale = kwargs.pop("colorscale", "Viridis")
    showscale = bool(kwargs.pop("showscale", True))
    caps = kwargs.pop(
        "caps",
        dict(x_show=False, y_show=False, z_show=False),
    )

    data_min = float(np.nanmin(arr))
    data_max = float(np.nanmax(arr))
    if not np.isfinite(isovalue):
        raise ValueError("isovalue must be finite")

    # Avoid the degenerate isomin == isomax case by using a tiny epsilon.
    span = max(data_max - data_min, 1.0)
    eps = span * 1e-12
    isomin = float(isovalue)
    isomax = float(isovalue + eps)

    if x_coords is not None and y_coords is not None and z_coords is not None:
        x1 = np.asarray(x_coords, dtype=float)
        y1 = np.asarray(y_coords, dtype=float)
        z1 = np.asarray(z_coords, dtype=float)
        if x1.ndim != 1 or y1.ndim != 1 or z1.ndim != 1:
            raise ValueError("x/y/z coordinates must be 1D arrays")
        if (len(x1), len(y1), len(z1)) != arr.shape:
            raise ValueError(
                f"x/y/z lengths must match data shape {arr.shape}, got "
                f"({len(x1)}, {len(y1)}, {len(z1)})"
            )
        X, Y, Z = np.meshgrid(x1, y1, z1, indexing="ij")
        x_flat = X.ravel(order="C")
        y_flat = Y.ravel(order="C")
        z_flat = Z.ravel(order="C")
    else:
        # Use integer indices as coordinates to avoid materializing coordinate grids.
        x_flat = None
        y_flat = None
        z_flat = None

    trace = go.Isosurface(
        x=x_flat,
        y=y_flat,
        z=z_flat,
        value=arr.ravel(order="C"),
        isomin=isomin,
        isomax=isomax,
        surface_count=1,
        opacity=opacity,
        caps=caps,
        colorscale=colorscale,
        showscale=showscale,
        colorbar=dict(title=field_name),
    )

    fig = go.Figure(data=[trace])
    fig.update_layout(
        title=kwargs.pop("title", f"{field_name} isosurface @ {isovalue:g}"),
        scene=dict(
            xaxis_title=kwargs.pop("xaxis_title", "X"),
            yaxis_title=kwargs.pop("yaxis_title", "Y"),
            zaxis_title=kwargs.pop("zaxis_title", "Z"),
            aspectmode="data",
        ),
    )
    return fig


def _plot_isosurface_pyvista(data, geometry, isovalue, field_name, **kwargs):
    """Plot isosurface using pyvista."""
    if not _PYVISTA_AVAILABLE:
        raise ImportError("pyvista is required")

    arr = np.asarray(data)
    if arr.ndim != 3:
        raise ValueError(
            "plot_isosurface expects a 3D scalar field array with shape (nx, ny, nz)"
        )

    # Optional uniform-grid geometry.
    origin = kwargs.pop("origin", (0.0, 0.0, 0.0))
    spacing = kwargs.pop("spacing", (1.0, 1.0, 1.0))
    cmap = kwargs.pop("cmap", "viridis")
    opacity = float(kwargs.pop("opacity", 0.6))

    grid = pv.ImageData(dimensions=arr.shape, spacing=spacing, origin=origin)
    grid[field_name] = arr.ravel(order="F")
    iso = grid.contour([float(isovalue)], scalars=field_name)

    plotter = pv.Plotter()
    plotter.add_mesh(iso, scalars=field_name, cmap=cmap, opacity=opacity)
    plotter.show_axes()
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
