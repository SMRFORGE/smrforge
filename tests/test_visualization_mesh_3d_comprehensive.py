"""
Comprehensive tests for visualization/mesh_3d.py to improve coverage to 75-80%.

Tests cover:
- Plotly visualization functions (plot_mesh3d_plotly, plot_surface_plotly)
- PyVista visualization functions (plot_mesh3d_pyvista, plot_surface_pyvista)
- VTK export functions (export_mesh_to_vtk)
- Error handling for missing dependencies
- Edge cases (empty meshes, missing data, etc.)

All tests use mocks to ensure code paths are covered even when plotly/pyvista are not installed.
"""

import numpy as np
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock

from smrforge.geometry.mesh_3d import Mesh3D, Surface


@pytest.fixture
def simple_mesh():
    """Create a simple mesh for testing."""
    vertices = np.array([
        [0, 0, 0],
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ])
    cells = np.array([[0, 1, 2, 3]])  # Single tetrahedron
    mesh = Mesh3D(vertices=vertices, cells=cells)
    mesh.add_cell_data("flux", np.array([1.0]))
    return mesh


@pytest.fixture
def simple_surface():
    """Create a simple surface for testing."""
    vertices = np.array([
        [0, 0, 0],
        [1, 0, 0],
        [0, 1, 0],
    ])
    faces = np.array([[0, 1, 2]])
    surface = Surface(vertices=vertices, faces=faces)
    return surface


@pytest.fixture
def mock_plotly():
    """Create mock plotly objects."""
    mock_fig = MagicMock()
    mock_mesh3d = MagicMock()
    mock_scatter3d = MagicMock()
    
    mock_go = MagicMock()
    mock_go.Figure.return_value = mock_fig
    mock_go.Mesh3d = mock_mesh3d
    mock_go.Scatter3d = mock_scatter3d
    
    return mock_go, mock_fig


@pytest.fixture
def mock_pyvista():
    """Create mock pyvista objects."""
    mock_plotter = MagicMock()
    mock_unstructured_grid = MagicMock()
    mock_polydata = MagicMock()
    
    # Mock save method
    mock_unstructured_grid.save = MagicMock()
    mock_polydata.save = MagicMock()
    
    mock_pv = MagicMock()
    mock_pv.Plotter.return_value = mock_plotter
    mock_pv.UnstructuredGrid.return_value = mock_unstructured_grid
    mock_pv.PolyData.return_value = mock_polydata
    
    return mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata


class TestPlotlyVisualization:
    """Test Plotly visualization functions."""

    def test_plot_mesh3d_plotly_basic(self, simple_mesh, mock_plotly):
        """Test basic plotly mesh plotting."""
        mock_go, mock_fig = mock_plotly
        # Add faces to simple_mesh so it can be plotted
        simple_mesh.faces = np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]])
        
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
                fig = plot_mesh3d_plotly(simple_mesh)
                assert fig is not None
                mock_go.Figure.assert_called_once()
                # Should add trace for mesh
                assert mock_fig.add_trace.called

    def test_plot_mesh3d_plotly_with_color_by(self, simple_mesh, mock_plotly):
        """Test plotly mesh plotting with color_by parameter."""
        mock_go, mock_fig = mock_plotly
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
                fig = plot_mesh3d_plotly(simple_mesh, color_by="flux")
                assert fig is not None
                mock_go.Figure.assert_called_once()

    def test_plot_mesh3d_plotly_with_materials(self, mock_plotly):
        """Test plotly mesh plotting with material coloring."""
        mock_go, mock_fig = mock_plotly
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells = np.array([[0, 1, 2, 3]])
        materials = np.array(["fuel", "moderator"])
        mesh = Mesh3D(vertices=vertices, cells=cells, cell_materials=materials)
        
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
                fig = plot_mesh3d_plotly(mesh)
                assert fig is not None
                # Should use Set3 colorscale for materials
                mock_go.Figure.assert_called_once()

    def test_plot_mesh3d_plotly_with_faces(self, mock_plotly):
        """Test plotly mesh plotting with surface mesh (faces only)."""
        mock_go, mock_fig = mock_plotly
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces = np.array([[0, 1, 2]])
        mesh = Mesh3D(vertices=vertices, faces=faces)
        
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
                fig = plot_mesh3d_plotly(mesh)
                assert fig is not None
                mock_go.Figure.assert_called_once()

    def test_plot_mesh3d_plotly_with_edges(self, simple_mesh, mock_plotly):
        """Test plotly mesh plotting with edges shown."""
        mock_go, mock_fig = mock_plotly
        # Add faces to simple_mesh for edge extraction
        simple_mesh.faces = np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]])
        
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
                fig = plot_mesh3d_plotly(simple_mesh, show_edges=True)
                assert fig is not None
                # Should add multiple traces (mesh + edges)
                assert mock_fig.add_trace.call_count >= 2

    def test_plot_mesh3d_plotly_custom_opacity(self, simple_mesh, mock_plotly):
        """Test plotly mesh plotting with custom opacity."""
        mock_go, mock_fig = mock_plotly
        simple_mesh.faces = np.array([[0, 1, 2]])
        
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
                fig = plot_mesh3d_plotly(simple_mesh, opacity=0.5)
                assert fig is not None

    def test_plot_mesh3d_plotly_custom_colorscale(self, simple_mesh, mock_plotly):
        """Test plotly mesh plotting with custom colorscale."""
        mock_go, mock_fig = mock_plotly
        simple_mesh.faces = np.array([[0, 1, 2]])
        
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
                fig = plot_mesh3d_plotly(simple_mesh, colorscale="Plasma")
                assert fig is not None

    def test_plot_mesh3d_plotly_no_plotly(self, simple_mesh):
        """Test plotly mesh plotting when plotly is not available."""
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', False):
            from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
            with pytest.raises(ImportError, match="plotly is required"):
                plot_mesh3d_plotly(simple_mesh)

    def test_plot_mesh3d_plotly_no_color_by_no_materials(self, mock_plotly):
        """Test plotly plotting with no color_by and no materials (uses default z-coordinate)."""
        mock_go, mock_fig = mock_plotly
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        faces = np.array([[0, 1, 2], [0, 1, 3]])
        mesh = Mesh3D(vertices=vertices, faces=faces)  # No cell_data, no materials
        
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
                fig = plot_mesh3d_plotly(mesh, color_by=None)
                assert fig is not None

    def test_plot_mesh3d_plotly_color_by_missing_field(self, mock_plotly):
        """Test plotly plotting with color_by field that doesn't exist."""
        mock_go, mock_fig = mock_plotly
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells = np.array([[0, 1, 2, 3]])
        faces = np.array([[0, 1, 2]])
        mesh = Mesh3D(vertices=vertices, cells=cells, faces=faces)
        
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
                # color_by field not in cell_data, should fall back to material or default
                fig = plot_mesh3d_plotly(mesh, color_by="nonexistent_field")
                assert fig is not None

    def test_plot_mesh3d_plotly_volume_mesh_no_faces(self, mock_plotly):
        """Test plotly plotting with volume mesh (cells but no faces)."""
        mock_go, mock_fig = mock_plotly
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells = np.array([[0, 1, 2, 3]])  # Volume mesh, no faces
        mesh = Mesh3D(vertices=vertices, cells=cells)
        
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
                # Since faces is None, it won't plot mesh, but should not crash
                fig = plot_mesh3d_plotly(mesh)
                assert fig is not None

    def test_plot_mesh3d_plotly_edges_quad_faces(self, mock_plotly):
        """Test plotly plotting with quad faces and edge extraction."""
        mock_go, mock_fig = mock_plotly
        vertices = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
                             [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]])
        faces = np.array([[0, 1, 2, 3], [4, 5, 6, 7]])  # Quad faces
        mesh = Mesh3D(vertices=vertices, faces=faces)
        
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
                fig = plot_mesh3d_plotly(mesh, show_edges=True)
                assert fig is not None
                # Should add edges for quad faces
                assert mock_fig.add_trace.call_count >= 2

    def test_plot_mesh3d_plotly_edges_reversed_vertex_order(self, mock_plotly):
        """Test edge extraction when vertices are in reversed order (v0 > v1)."""
        mock_go, mock_fig = mock_plotly
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        # Face with vertices that would result in v0 > v1 after sorting
        faces = np.array([[2, 1, 0]])  # Reversed order
        mesh = Mesh3D(vertices=vertices, faces=faces)
        
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
                fig = plot_mesh3d_plotly(mesh, show_edges=True)
                assert fig is not None

    def test_plot_surface_plotly_basic(self, simple_surface, mock_plotly):
        """Test basic plotly surface plotting."""
        mock_go, mock_fig = mock_plotly
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_surface_plotly
                fig = plot_surface_plotly(simple_surface)
                assert fig is not None
                mock_go.Figure.assert_called_once()

    def test_plot_surface_plotly_custom_color(self, simple_surface, mock_plotly):
        """Test plotly surface plotting with custom color."""
        mock_go, mock_fig = mock_plotly
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_surface_plotly
                fig = plot_surface_plotly(simple_surface, color="red")
                assert fig is not None

    def test_plot_surface_plotly_custom_opacity(self, simple_surface, mock_plotly):
        """Test plotly surface plotting with custom opacity."""
        mock_go, mock_fig = mock_plotly
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_surface_plotly
                fig = plot_surface_plotly(simple_surface, opacity=0.6)
                assert fig is not None

    def test_plot_surface_plotly_no_plotly(self, simple_surface):
        """Test plotly surface plotting when plotly is not available."""
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', False):
            from smrforge.visualization.mesh_3d import plot_surface_plotly
            with pytest.raises(ImportError, match="plotly is required"):
                plot_surface_plotly(simple_surface)

    def test_plot_multiple_meshes_plotly_basic(self, mock_plotly):
        """Test plotting multiple meshes with plotly."""
        mock_go, mock_fig = mock_plotly
        vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces1 = np.array([[0, 1, 2]])
        mesh1 = Mesh3D(vertices=vertices1, faces=faces1)
        
        vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0]])
        faces2 = np.array([[0, 1, 2]])
        mesh2 = Mesh3D(vertices=vertices2, faces=faces2)
        
        meshes = {"mesh1": mesh1, "mesh2": mesh2}
        
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_multiple_meshes_plotly
                fig = plot_multiple_meshes_plotly(meshes)
                assert fig is not None
                # Should add trace for each mesh
                assert mock_fig.add_trace.call_count == 2

    def test_plot_multiple_meshes_plotly_many_meshes(self, mock_plotly):
        """Test plotting many meshes (more than color list length)."""
        mock_go, mock_fig = mock_plotly
        meshes = {}
        for i in range(10):
            vertices = np.array([[i, 0, 0], [i+1, 0, 0], [i, 1, 0]])
            faces = np.array([[0, 1, 2]])
            meshes[f"mesh_{i}"] = Mesh3D(vertices=vertices, faces=faces)
        
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_multiple_meshes_plotly
                fig = plot_multiple_meshes_plotly(meshes)
                assert fig is not None
                # Should cycle through colors
                assert mock_fig.add_trace.call_count == 10

    def test_plot_multiple_meshes_plotly_mesh_without_faces(self, mock_plotly):
        """Test plotting multiple meshes where one has no faces."""
        mock_go, mock_fig = mock_plotly
        vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces1 = np.array([[0, 1, 2]])
        mesh1 = Mesh3D(vertices=vertices1, faces=faces1)
        
        vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0], [2, 0, 1]])
        cells2 = np.array([[0, 1, 2, 3]])  # No faces
        mesh2 = Mesh3D(vertices=vertices2, cells=cells2)
        
        meshes = {"mesh1": mesh1, "mesh2": mesh2}
        
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_multiple_meshes_plotly
                # mesh2 has no faces, so it won't be plotted, but should not crash
                fig = plot_multiple_meshes_plotly(meshes)
                assert fig is not None
                # Only mesh1 should be plotted
                assert mock_fig.add_trace.call_count == 1

    def test_plot_multiple_meshes_plotly_custom_opacity(self, mock_plotly):
        """Test plotting multiple meshes with custom opacity."""
        mock_go, mock_fig = mock_plotly
        vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces1 = np.array([[0, 1, 2]])
        mesh1 = Mesh3D(vertices=vertices1, faces=faces1)
        
        vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0]])
        faces2 = np.array([[0, 1, 2]])
        mesh2 = Mesh3D(vertices=vertices2, faces=faces2)
        
        meshes = {"mesh1": mesh1, "mesh2": mesh2}
        
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_multiple_meshes_plotly
                fig = plot_multiple_meshes_plotly(meshes, opacity=0.5)
                assert fig is not None

    def test_plot_multiple_meshes_plotly_custom_title(self, mock_plotly):
        """Test plotting multiple meshes with custom title."""
        mock_go, mock_fig = mock_plotly
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces = np.array([[0, 1, 2]])
        mesh = Mesh3D(vertices=vertices, faces=faces)
        meshes = {"mesh": mesh}
        
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.go', mock_go):
                from smrforge.visualization.mesh_3d import plot_multiple_meshes_plotly
                fig = plot_multiple_meshes_plotly(meshes, title="Custom Title")
                assert fig is not None

    def test_plot_multiple_meshes_plotly_no_plotly(self):
        """Test plotting multiple meshes when plotly is not available."""
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', False):
            from smrforge.visualization.mesh_3d import plot_multiple_meshes_plotly
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            faces = np.array([[0, 1, 2]])
            mesh = Mesh3D(vertices=vertices, faces=faces)
            meshes = {"mesh": mesh}
            with pytest.raises(ImportError, match="plotly is required"):
                plot_multiple_meshes_plotly(meshes)


class TestPyVistaVisualization:
    """Test PyVista visualization functions."""

    def test_plot_mesh3d_pyvista_basic(self, simple_mesh, mock_pyvista):
        """Test basic pyvista mesh plotting."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
                plotter = plot_mesh3d_pyvista(simple_mesh)
                assert plotter is not None
                mock_pv.UnstructuredGrid.assert_called()

    def test_plot_mesh3d_pyvista_with_color_by(self, simple_mesh, mock_pyvista):
        """Test pyvista mesh plotting with color_by parameter."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
                plotter = plot_mesh3d_pyvista(simple_mesh, color_by="flux")
                assert plotter is not None

    def test_plot_mesh3d_pyvista_with_materials(self, mock_pyvista):
        """Test pyvista mesh plotting with material coloring."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells = np.array([[0, 1, 2, 3]])
        materials = np.array(["fuel"])
        mesh = Mesh3D(vertices=vertices, cells=cells, cell_materials=materials)
        
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
                plotter = plot_mesh3d_pyvista(mesh)
                assert plotter is not None

    def test_plot_mesh3d_pyvista_with_faces(self, mock_pyvista):
        """Test pyvista mesh plotting with surface mesh (faces only)."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces = np.array([[0, 1, 2]])
        mesh = Mesh3D(vertices=vertices, faces=faces)
        
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
                plotter = plot_mesh3d_pyvista(mesh)
                assert plotter is not None
                mock_pv.PolyData.assert_called()

    def test_plot_mesh3d_pyvista_points_only(self, mock_pyvista):
        """Test pyvista plotting with points-only mesh."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        mesh = Mesh3D(vertices=vertices)  # No cells, no faces
        
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
                plotter = plot_mesh3d_pyvista(mesh)
                assert plotter is not None
                mock_pv.PolyData.assert_called()

    def test_plot_mesh3d_pyvista_with_edges(self, simple_mesh, mock_pyvista):
        """Test pyvista mesh plotting with edges shown."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
                plotter = plot_mesh3d_pyvista(simple_mesh, show_edges=True)
                assert plotter is not None
                mock_plotter.add_mesh.assert_called()

    def test_plot_mesh3d_pyvista_custom_opacity(self, simple_mesh, mock_pyvista):
        """Test pyvista mesh plotting with custom opacity."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
                plotter = plot_mesh3d_pyvista(simple_mesh, opacity=0.5)
                assert plotter is not None

    def test_plot_mesh3d_pyvista_no_pyvista(self, simple_mesh):
        """Test pyvista mesh plotting when pyvista is not available."""
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', False):
            from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
            with pytest.raises(ImportError, match="pyvista is required"):
                plot_mesh3d_pyvista(simple_mesh)

    def test_plot_mesh3d_pyvista_color_by_missing_field(self, mock_pyvista):
        """Test pyvista plotting with color_by field that doesn't exist."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells = np.array([[0, 1, 2, 3]])
        mesh = Mesh3D(vertices=vertices, cells=cells)
        
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
                # color_by field not in cell_data, should fall back to material or None
                plotter = plot_mesh3d_pyvista(mesh, color_by="nonexistent_field")
                assert plotter is not None

    def test_plot_mesh3d_pyvista_with_both_cells_and_faces(self, mock_pyvista):
        """Test pyvista plotting with mesh that has both cells and faces (prefers cells)."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells = np.array([[0, 1, 2, 3]])
        faces = np.array([[0, 1, 2]])  # Also has faces
        mesh = Mesh3D(vertices=vertices, cells=cells, faces=faces)
        
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
                plotter = plot_mesh3d_pyvista(mesh)
                assert plotter is not None
                # Should prefer cells (UnstructuredGrid) over faces
                mock_pv.UnstructuredGrid.assert_called()

    def test_plot_mesh3d_pyvista_no_coloring(self, mock_pyvista):
        """Test pyvista plotting with no color_by, no materials, no cell_data."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces = np.array([[0, 1, 2]])
        mesh = Mesh3D(vertices=vertices, faces=faces)
        
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
                plotter = plot_mesh3d_pyvista(mesh, color_by=None)
                assert plotter is not None

    def test_plot_mesh3d_pyvista_hex_cells(self, mock_pyvista):
        """Test pyvista plotting with hex cells (8 vertices)."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        vertices = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
                             [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]])
        cells = np.array([[0, 1, 2, 3, 4, 5, 6, 7]])  # Hex cell
        mesh = Mesh3D(vertices=vertices, cells=cells)
        
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
                plotter = plot_mesh3d_pyvista(mesh)
                assert plotter is not None

    def test_plot_surface_pyvista_basic(self, simple_surface, mock_pyvista):
        """Test basic pyvista surface plotting."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import plot_surface_pyvista
                plotter = plot_surface_pyvista(simple_surface)
                assert plotter is not None
                mock_pv.PolyData.assert_called()

    def test_plot_surface_pyvista_custom_color(self, simple_surface, mock_pyvista):
        """Test pyvista surface plotting with custom color."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import plot_surface_pyvista
                plotter = plot_surface_pyvista(simple_surface, color="blue")
                assert plotter is not None

    def test_plot_surface_pyvista_custom_opacity(self, simple_surface, mock_pyvista):
        """Test pyvista surface plotting with custom opacity."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import plot_surface_pyvista
                plotter = plot_surface_pyvista(simple_surface, opacity=0.7)
                assert plotter is not None

    def test_plot_surface_pyvista_no_pyvista(self, simple_surface):
        """Test pyvista surface plotting when pyvista is not available."""
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', False):
            from smrforge.visualization.mesh_3d import plot_surface_pyvista
            with pytest.raises(ImportError, match="pyvista is required"):
                plot_surface_pyvista(simple_surface)


class TestVTKExport:
    """Test VTK export functions."""

    def test_export_mesh_to_vtk(self, simple_mesh, tmp_path, mock_pyvista):
        """Test exporting mesh to VTK file."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        filepath = tmp_path / "test_mesh.vtk"
        
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import export_mesh_to_vtk
                export_mesh_to_vtk(simple_mesh, str(filepath))
                mock_unstructured_grid.save.assert_called_once_with(str(filepath))

    def test_export_mesh_to_vtk_with_data(self, simple_mesh, tmp_path, mock_pyvista):
        """Test exporting mesh with cell data to VTK file."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        filepath = tmp_path / "test_mesh_data.vtk"
        
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import export_mesh_to_vtk
                export_mesh_to_vtk(simple_mesh, str(filepath))
                mock_unstructured_grid.save.assert_called()

    def test_export_mesh_to_vtk_no_pyvista(self, simple_mesh, tmp_path):
        """Test exporting mesh when pyvista is not available."""
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', False):
            from smrforge.visualization.mesh_3d import export_mesh_to_vtk
            filepath = tmp_path / "test_mesh.vtk"
            with pytest.raises(ImportError, match="pyvista is required"):
                export_mesh_to_vtk(simple_mesh, str(filepath))

    def test_export_mesh_to_vtk_with_surface_mesh(self, tmp_path, mock_pyvista):
        """Test exporting surface mesh (faces only) to VTK file."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces = np.array([[0, 1, 2]])
        mesh = Mesh3D(vertices=vertices, faces=faces)
        filepath = tmp_path / "test_surface_mesh.vtk"
        
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import export_mesh_to_vtk
                export_mesh_to_vtk(mesh, str(filepath))
                mock_polydata.save.assert_called_once_with(str(filepath))

    def test_export_mesh_to_vtk_points_only(self, tmp_path, mock_pyvista):
        """Test exporting points-only mesh to VTK file."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        mesh = Mesh3D(vertices=vertices)  # No cells, no faces
        filepath = tmp_path / "test_points_mesh.vtk"
        
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import export_mesh_to_vtk
                export_mesh_to_vtk(mesh, str(filepath))
                mock_polydata.save.assert_called_once_with(str(filepath))

    def test_export_mesh_to_vtk_with_hex_cells(self, tmp_path, mock_pyvista):
        """Test exporting mesh with hex cells (8 vertices) to VTK file."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        vertices = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
                             [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]])
        cells = np.array([[0, 1, 2, 3, 4, 5, 6, 7]])  # Hex cell
        mesh = Mesh3D(vertices=vertices, cells=cells)
        filepath = tmp_path / "test_hex_mesh.vtk"
        
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import export_mesh_to_vtk
                export_mesh_to_vtk(mesh, str(filepath))
                mock_unstructured_grid.save.assert_called()

    def test_export_mesh_to_vtk_with_materials_only(self, tmp_path, mock_pyvista):
        """Test exporting mesh with materials but no cell_data."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells = np.array([[0, 1, 2, 3]])
        materials = np.array(["fuel"])
        mesh = Mesh3D(vertices=vertices, cells=cells, cell_materials=materials)
        filepath = tmp_path / "test_materials_only.vtk"
        
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import export_mesh_to_vtk
                export_mesh_to_vtk(mesh, str(filepath))
                mock_unstructured_grid.save.assert_called()

    def test_export_mesh_to_vtk_empty_cell_data(self, tmp_path, mock_pyvista):
        """Test exporting mesh with empty cell_data dict."""
        mock_pv, mock_plotter, mock_unstructured_grid, mock_polydata = mock_pyvista
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells = np.array([[0, 1, 2, 3]])
        mesh = Mesh3D(vertices=vertices, cells=cells)
        # cell_data is empty dict by default
        filepath = tmp_path / "test_empty_data.vtk"
        
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', True):
            with patch('smrforge.visualization.mesh_3d.pv', mock_pv):
                from smrforge.visualization.mesh_3d import export_mesh_to_vtk
                export_mesh_to_vtk(mesh, str(filepath))
                mock_unstructured_grid.save.assert_called()
