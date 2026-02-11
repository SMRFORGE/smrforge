"""
3D mesh visualization using plotly and pyvista.

Provides functions to visualize 3D meshes extracted from reactor geometry.
"""

from typing import Dict, Optional, Tuple

import numpy as np

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False

    # Create dummy classes for type hints
    class DummyFigure:
        pass

    go = type("go", (), {"Figure": DummyFigure, "Mesh3d": DummyFigure, "Scatter3d": DummyFigure})()  # type: ignore

try:
    import pyvista as pv

    _PYVISTA_AVAILABLE = True
except ImportError:
    _PYVISTA_AVAILABLE = False

    # Create dummy classes for type hints
    class DummyPlotter:
        pass

    pv = type("pv", (), {"Plotter": DummyPlotter, "UnstructuredGrid": DummyPlotter, "PolyData": DummyPlotter})()  # type: ignore

from ..geometry.mesh_3d import Mesh3D, Surface


def plot_mesh3d_plotly(
    mesh: Mesh3D,
    color_by: Optional[str] = None,
    colorscale: str = "Viridis",
    show_edges: bool = False,
    opacity: float = 1.0,
    title: str = "3D Mesh",
):
    """
    Plot 3D mesh using plotly.

    Args:
        mesh: Mesh3D instance
        color_by: Optional field name to color by (e.g., "flux", "power", "material")
        colorscale: Plotly colorscale name
        show_edges: Whether to show mesh edges
        opacity: Mesh opacity (0-1)
        title: Plot title

    Returns:
        plotly.graph_objects.Figure
    """
    if not _PLOTLY_AVAILABLE:
        raise ImportError(
            "plotly is required for 3D visualization. Install with: pip install plotly"
        )

    fig = go.Figure()

    # Determine coloring
    if color_by and color_by in mesh.cell_data:
        # Color by cell data
        color_data = mesh.cell_data[color_by]
        colorbar_title = color_by
    elif mesh.cell_materials is not None:
        # Color by material
        unique_materials = np.unique(mesh.cell_materials)
        material_map = {mat: i for i, mat in enumerate(unique_materials)}
        color_data = np.array([material_map[mat] for mat in mesh.cell_materials])
        colorbar_title = "Material"
        colorscale = "Set3"  # Better for discrete materials
    else:
        color_data = None
        colorbar_title = None

    # Plot mesh
    if mesh.faces is not None:
        # Surface mesh
        fig.add_trace(
            go.Mesh3d(
                x=mesh.vertices[:, 0],
                y=mesh.vertices[:, 1],
                z=mesh.vertices[:, 2],
                i=mesh.faces[:, 0],
                j=mesh.faces[:, 1],
                k=mesh.faces[:, 2],
                intensity=color_data if color_data is not None else mesh.vertices[:, 2],
                colorscale=colorscale,
                showscale=color_data is not None,
                colorbar=dict(title=colorbar_title) if color_data is not None else None,
                opacity=opacity,
                name="Mesh",
            )
        )

    # Add edges if requested
    if show_edges and mesh.faces is not None:
        # Extract edges from faces
        edges = set()
        for face in mesh.faces:
            n_verts = len(face)
            for i in range(n_verts):
                v0, v1 = face[i], face[(i + 1) % n_verts]
                if v0 > v1:  # Ensure consistent ordering
                    v0, v1 = v1, v0
                edges.add((v0, v1))

        # Plot edges
        for v0, v1 in edges:
            fig.add_trace(
                go.Scatter3d(
                    x=[mesh.vertices[v0, 0], mesh.vertices[v1, 0]],
                    y=[mesh.vertices[v0, 1], mesh.vertices[v1, 1]],
                    z=[mesh.vertices[v0, 2], mesh.vertices[v1, 2]],
                    mode="lines",
                    line=dict(color="black", width=1),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    # Update layout
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title="X (cm)",
            yaxis_title="Y (cm)",
            zaxis_title="Z (cm)",
            aspectmode="data",
        ),
        width=800,
        height=600,
    )

    return fig


def plot_surface_plotly(
    surface: Surface,
    color: str = "lightblue",
    opacity: float = 0.8,
    title: str = "Surface",
):
    """
    Plot surface using plotly.

    Args:
        surface: Surface instance
        color: Surface color
        opacity: Surface opacity (0-1)
        title: Plot title

    Returns:
        plotly.graph_objects.Figure
    """
    if not _PLOTLY_AVAILABLE:
        raise ImportError(
            "plotly is required for 3D visualization. Install with: pip install plotly"
        )

    fig = go.Figure()

    fig.add_trace(
        go.Mesh3d(
            x=surface.vertices[:, 0],
            y=surface.vertices[:, 1],
            z=surface.vertices[:, 2],
            i=surface.faces[:, 0],
            j=surface.faces[:, 1],
            k=surface.faces[:, 2],
            color=color,
            opacity=opacity,
            name=surface.surface_type,
        )
    )

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title="X (cm)",
            yaxis_title="Y (cm)",
            zaxis_title="Z (cm)",
            aspectmode="data",
        ),
        width=800,
        height=600,
    )

    return fig


def plot_mesh3d_pyvista(
    mesh: Mesh3D,
    color_by: Optional[str] = None,
    show_edges: bool = False,
    opacity: float = 1.0,
    **kwargs,
) -> pv.Plotter:
    """
    Plot 3D mesh using pyvista.

    Args:
        mesh: Mesh3D instance
        color_by: Optional field name to color by
        show_edges: Whether to show mesh edges
        opacity: Mesh opacity (0-1)
        **kwargs: Additional pyvista arguments

    Returns:
        pyvista.Plotter instance
    """
    if not _PYVISTA_AVAILABLE:
        raise ImportError(
            "pyvista is required for 3D visualization. Install with: pip install pyvista"
        )

    # Create pyvista mesh
    if mesh.cells is not None:
        # Volume mesh
        # Convert cells to pyvista format
        cell_array = []
        for cell in mesh.cells:
            n_verts = len(cell)
            cell_array.append(n_verts)
            cell_array.extend(cell)

        pv_mesh = pv.UnstructuredGrid(cell_array, mesh.cells, mesh.vertices)
    elif mesh.faces is not None:
        # Surface mesh
        pv_mesh = pv.PolyData(mesh.vertices, mesh.faces)
    else:
        # Points only
        pv_mesh = pv.PolyData(mesh.vertices)

    # Add data arrays
    if color_by and color_by in mesh.cell_data:
        pv_mesh[color_by] = mesh.cell_data[color_by]
        scalars = color_by
    elif mesh.cell_materials is not None:
        pv_mesh["material"] = mesh.cell_materials
        scalars = "material"
    else:
        scalars = None

    # Create plotter
    plotter = pv.Plotter(**kwargs)

    # Add mesh
    plotter.add_mesh(
        pv_mesh,
        scalars=scalars,
        show_edges=show_edges,
        opacity=opacity,
        **kwargs,
    )

    return plotter


def plot_surface_pyvista(
    surface: Surface,
    color: str = "lightblue",
    opacity: float = 0.8,
    **kwargs,
) -> pv.Plotter:
    """
    Plot surface using pyvista.

    Args:
        surface: Surface instance
        color: Surface color
        opacity: Surface opacity (0-1)
        **kwargs: Additional pyvista arguments

    Returns:
        pyvista.Plotter instance
    """
    if not _PYVISTA_AVAILABLE:
        raise ImportError(
            "pyvista is required for 3D visualization. Install with: pip install pyvista"
        )

    # Create pyvista mesh
    pv_mesh = pv.PolyData(surface.vertices, surface.faces)

    # Create plotter
    plotter = pv.Plotter(**kwargs)

    # Add surface
    plotter.add_mesh(pv_mesh, color=color, opacity=opacity, **kwargs)

    return plotter


def export_mesh_to_vtk(mesh: Mesh3D, filename: str):
    """
    Export mesh to VTK format for ParaView.

    Args:
        mesh: Mesh3D instance
        filename: Output filename (.vtk or .vtu)
    """
    if not _PYVISTA_AVAILABLE:
        raise ImportError(
            "pyvista is required for VTK export. Install with: pip install pyvista"
        )

    # Create pyvista mesh
    if mesh.cells is not None:
        cell_array = []
        for cell in mesh.cells:
            n_verts = len(cell)
            cell_array.append(n_verts)
            cell_array.extend(cell)
        pv_mesh = pv.UnstructuredGrid(cell_array, mesh.cells, mesh.vertices)
    elif mesh.faces is not None:
        pv_mesh = pv.PolyData(mesh.vertices, mesh.faces)
    else:
        pv_mesh = pv.PolyData(mesh.vertices)

    # Add data arrays
    for name, data in mesh.cell_data.items():
        pv_mesh[name] = data

    if mesh.cell_materials is not None:
        pv_mesh["material"] = mesh.cell_materials

    # Save
    pv_mesh.save(filename)


def plot_multiple_meshes_plotly(
    meshes: Dict[str, Mesh3D],
    color_by: Optional[str] = None,
    opacity: float = 0.8,
    title: str = "Multiple Meshes",
):
    """
    Plot multiple meshes in a single plotly figure.

    Args:
        meshes: Dictionary mapping name -> Mesh3D
        color_by: Optional field name to color by
        opacity: Mesh opacity (0-1)
        title: Plot title

    Returns:
        plotly.graph_objects.Figure
    """
    if not _PLOTLY_AVAILABLE:
        raise ImportError(
            "plotly is required for 3D visualization. Install with: pip install plotly"
        )

    fig = go.Figure()

    colors = ["lightblue", "lightcoral", "lightgreen", "lightyellow", "lightpink"]

    for i, (name, mesh) in enumerate(meshes.items()):
        color = colors[i % len(colors)]

        if mesh.faces is not None:
            fig.add_trace(
                go.Mesh3d(
                    x=mesh.vertices[:, 0],
                    y=mesh.vertices[:, 1],
                    z=mesh.vertices[:, 2],
                    i=mesh.faces[:, 0],
                    j=mesh.faces[:, 1],
                    k=mesh.faces[:, 2],
                    color=color,
                    opacity=opacity,
                    name=name,
                )
            )

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title="X (cm)",
            yaxis_title="Y (cm)",
            zaxis_title="Z (cm)",
            aspectmode="data",
        ),
        width=800,
        height=600,
    )

    return fig
