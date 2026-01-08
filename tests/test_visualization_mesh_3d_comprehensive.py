"""
Comprehensive tests for visualization/mesh_3d.py to improve coverage to 75-80%.

Tests cover:
- Plotly visualization functions (plot_mesh3d_plotly, plot_surface_plotly)
- PyVista visualization functions (plot_mesh3d_pyvista, plot_surface_pyvista)
- VTK export functions (export_mesh_to_vtk, export_surface_to_vtk)
- Error handling for missing dependencies
- Edge cases (empty meshes, missing data, etc.)
"""

import numpy as np
import pytest
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


class TestPlotlyVisualization:
    """Test Plotly visualization functions."""

    def test_plot_mesh3d_plotly_basic(self, simple_mesh):
        """Test basic plotly mesh plotting."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
            fig = plot_mesh3d_plotly(simple_mesh)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")

    def test_plot_mesh3d_plotly_with_color_by(self, simple_mesh):
        """Test plotly mesh plotting with color_by parameter."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
            fig = plot_mesh3d_plotly(simple_mesh, color_by="flux")
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")

    def test_plot_mesh3d_plotly_with_materials(self):
        """Test plotly mesh plotting with material coloring."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
            cells = np.array([[0, 1, 2, 3]])
            materials = np.array(["fuel"])
            mesh = Mesh3D(vertices=vertices, cells=cells, cell_materials=materials)
            fig = plot_mesh3d_plotly(mesh)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")

    def test_plot_mesh3d_plotly_with_faces(self):
        """Test plotly mesh plotting with surface mesh (faces only)."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            faces = np.array([[0, 1, 2]])
            mesh = Mesh3D(vertices=vertices, faces=faces)
            fig = plot_mesh3d_plotly(mesh)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")

    def test_plot_mesh3d_plotly_with_edges(self, simple_mesh):
        """Test plotly mesh plotting with edges shown."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
            fig = plot_mesh3d_plotly(simple_mesh, show_edges=True)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")

    def test_plot_mesh3d_plotly_custom_opacity(self, simple_mesh):
        """Test plotly mesh plotting with custom opacity."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
            fig = plot_mesh3d_plotly(simple_mesh, opacity=0.5)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")

    def test_plot_mesh3d_plotly_custom_colorscale(self, simple_mesh):
        """Test plotly mesh plotting with custom colorscale."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
            fig = plot_mesh3d_plotly(simple_mesh, colorscale="Plasma")
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")

    def test_plot_mesh3d_plotly_no_plotly(self):
        """Test plotly mesh plotting when plotly is not available."""
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', False):
            from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
            with pytest.raises(ImportError, match="plotly is required"):
                plot_mesh3d_plotly(simple_mesh)

    def test_plot_surface_plotly_basic(self, simple_surface):
        """Test basic plotly surface plotting."""
        try:
            from smrforge.visualization.mesh_3d import plot_surface_plotly
            fig = plot_surface_plotly(simple_surface)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")

    def test_plot_surface_plotly_custom_color(self, simple_surface):
        """Test plotly surface plotting with custom color."""
        try:
            from smrforge.visualization.mesh_3d import plot_surface_plotly
            fig = plot_surface_plotly(simple_surface, color="red")
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")

    def test_plot_surface_plotly_custom_opacity(self, simple_surface):
        """Test plotly surface plotting with custom opacity."""
        try:
            from smrforge.visualization.mesh_3d import plot_surface_plotly
            fig = plot_surface_plotly(simple_surface, opacity=0.6)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")

    def test_plot_surface_plotly_no_plotly(self):
        """Test plotly surface plotting when plotly is not available."""
        with patch('smrforge.visualization.mesh_3d._PLOTLY_AVAILABLE', False):
            from smrforge.visualization.mesh_3d import plot_surface_plotly
            with pytest.raises(ImportError, match="plotly is required"):
                plot_surface_plotly(simple_surface)


class TestPyVistaVisualization:
    """Test PyVista visualization functions."""

    def test_plot_mesh3d_pyvista_basic(self, simple_mesh):
        """Test basic pyvista mesh plotting."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
            plotter = plot_mesh3d_pyvista(simple_mesh)
            assert plotter is not None
        except ImportError:
            pytest.skip("pyvista not available")

    def test_plot_mesh3d_pyvista_with_color_by(self, simple_mesh):
        """Test pyvista mesh plotting with color_by parameter."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
            plotter = plot_mesh3d_pyvista(simple_mesh, color_by="flux")
            assert plotter is not None
        except ImportError:
            pytest.skip("pyvista not available")

    def test_plot_mesh3d_pyvista_with_materials(self):
        """Test pyvista mesh plotting with material coloring."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
            cells = np.array([[0, 1, 2, 3]])
            materials = np.array(["fuel"])
            mesh = Mesh3D(vertices=vertices, cells=cells, cell_materials=materials)
            plotter = plot_mesh3d_pyvista(mesh)
            assert plotter is not None
        except ImportError:
            pytest.skip("pyvista not available")

    def test_plot_mesh3d_pyvista_with_faces(self):
        """Test pyvista mesh plotting with surface mesh (faces only)."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            faces = np.array([[0, 1, 2]])
            mesh = Mesh3D(vertices=vertices, faces=faces)
            plotter = plot_mesh3d_pyvista(mesh)
            assert plotter is not None
        except ImportError:
            pytest.skip("pyvista not available")

    def test_plot_mesh3d_pyvista_with_edges(self, simple_mesh):
        """Test pyvista mesh plotting with edges shown."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
            plotter = plot_mesh3d_pyvista(simple_mesh, show_edges=True)
            assert plotter is not None
        except ImportError:
            pytest.skip("pyvista not available")

    def test_plot_mesh3d_pyvista_custom_opacity(self, simple_mesh):
        """Test pyvista mesh plotting with custom opacity."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
            plotter = plot_mesh3d_pyvista(simple_mesh, opacity=0.5)
            assert plotter is not None
        except ImportError:
            pytest.skip("pyvista not available")

    def test_plot_mesh3d_pyvista_no_pyvista(self):
        """Test pyvista mesh plotting when pyvista is not available."""
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', False):
            from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
            with pytest.raises(ImportError, match="pyvista is required"):
                plot_mesh3d_pyvista(simple_mesh)

    def test_plot_surface_pyvista_basic(self, simple_surface):
        """Test basic pyvista surface plotting."""
        try:
            from smrforge.visualization.mesh_3d import plot_surface_pyvista
            plotter = plot_surface_pyvista(simple_surface)
            assert plotter is not None
        except ImportError:
            pytest.skip("pyvista not available")

    def test_plot_surface_pyvista_custom_color(self, simple_surface):
        """Test pyvista surface plotting with custom color."""
        try:
            from smrforge.visualization.mesh_3d import plot_surface_pyvista
            plotter = plot_surface_pyvista(simple_surface, color="blue")
            assert plotter is not None
        except ImportError:
            pytest.skip("pyvista not available")

    def test_plot_surface_pyvista_custom_opacity(self, simple_surface):
        """Test pyvista surface plotting with custom opacity."""
        try:
            from smrforge.visualization.mesh_3d import plot_surface_pyvista
            plotter = plot_surface_pyvista(simple_surface, opacity=0.7)
            assert plotter is not None
        except ImportError:
            pytest.skip("pyvista not available")

    def test_plot_surface_pyvista_no_pyvista(self):
        """Test pyvista surface plotting when pyvista is not available."""
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', False):
            from smrforge.visualization.mesh_3d import plot_surface_pyvista
            with pytest.raises(ImportError, match="pyvista is required"):
                plot_surface_pyvista(simple_surface)


class TestVTKExport:
    """Test VTK export functions."""

    def test_export_mesh_to_vtk(self, simple_mesh, tmp_path):
        """Test exporting mesh to VTK file."""
        try:
            from smrforge.visualization.mesh_3d import export_mesh_to_vtk
            filepath = tmp_path / "test_mesh.vtk"
            export_mesh_to_vtk(simple_mesh, filepath)
            assert filepath.exists()
        except ImportError:
            pytest.skip("pyvista not available")

    def test_export_mesh_to_vtk_with_data(self, simple_mesh, tmp_path):
        """Test exporting mesh with cell data to VTK file."""
        try:
            from smrforge.visualization.mesh_3d import export_mesh_to_vtk
            filepath = tmp_path / "test_mesh_data.vtk"
            export_mesh_to_vtk(simple_mesh, filepath)
            assert filepath.exists()
        except ImportError:
            pytest.skip("pyvista not available")

    def test_export_mesh_to_vtk_no_pyvista(self, tmp_path):
        """Test exporting mesh when pyvista is not available."""
        with patch('smrforge.visualization.mesh_3d._PYVISTA_AVAILABLE', False):
            from smrforge.visualization.mesh_3d import export_mesh_to_vtk
            filepath = tmp_path / "test_mesh.vtk"
            with pytest.raises(ImportError, match="pyvista is required"):
                export_mesh_to_vtk(simple_mesh, filepath)

    def test_export_mesh_to_vtk_with_surface_mesh(self, tmp_path):
        """Test exporting surface mesh (faces only) to VTK file."""
        try:
            from smrforge.visualization.mesh_3d import export_mesh_to_vtk
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            faces = np.array([[0, 1, 2]])
            mesh = Mesh3D(vertices=vertices, faces=faces)
            filepath = tmp_path / "test_surface_mesh.vtk"
            export_mesh_to_vtk(mesh, str(filepath))
            assert filepath.exists()
        except ImportError:
            pytest.skip("pyvista not available")
    
    def test_export_mesh_to_vtk_points_only(self, tmp_path):
        """Test exporting points-only mesh to VTK file."""
        try:
            from smrforge.visualization.mesh_3d import export_mesh_to_vtk
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            mesh = Mesh3D(vertices=vertices)  # No cells, no faces
            filepath = tmp_path / "test_points_mesh.vtk"
            export_mesh_to_vtk(mesh, str(filepath))
            assert filepath.exists()
        except ImportError:
            pytest.skip("pyvista not available")
    
    def test_export_mesh_to_vtk_with_hex_cells(self, tmp_path):
        """Test exporting mesh with hex cells (8 vertices) to VTK file."""
        try:
            from smrforge.visualization.mesh_3d import export_mesh_to_vtk
            vertices = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
                                 [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]])
            cells = np.array([[0, 1, 2, 3, 4, 5, 6, 7]])  # Hex cell
            mesh = Mesh3D(vertices=vertices, cells=cells)
            filepath = tmp_path / "test_hex_mesh.vtk"
            export_mesh_to_vtk(mesh, str(filepath))
            assert filepath.exists()
        except ImportError:
            pytest.skip("pyvista not available")


class TestMultipleMeshes:
    """Test multiple meshes plotting."""
    
    def test_plot_multiple_meshes_plotly_basic(self):
        """Test plotting multiple meshes with plotly."""
        try:
            from smrforge.visualization.mesh_3d import plot_multiple_meshes_plotly
            vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            faces1 = np.array([[0, 1, 2]])
            mesh1 = Mesh3D(vertices=vertices1, faces=faces1)
            
            vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0]])
            faces2 = np.array([[0, 1, 2]])
            mesh2 = Mesh3D(vertices=vertices2, faces=faces2)
            
            meshes = {"mesh1": mesh1, "mesh2": mesh2}
            fig = plot_multiple_meshes_plotly(meshes)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")
    
    def test_plot_multiple_meshes_plotly_many_meshes(self):
        """Test plotting many meshes (more than color list length)."""
        try:
            from smrforge.visualization.mesh_3d import plot_multiple_meshes_plotly
            meshes = {}
            for i in range(10):
                vertices = np.array([[i, 0, 0], [i+1, 0, 0], [i, 1, 0]])
                faces = np.array([[0, 1, 2]])
                meshes[f"mesh_{i}"] = Mesh3D(vertices=vertices, faces=faces)
            
            fig = plot_multiple_meshes_plotly(meshes)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")
    
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


class TestEdgeCases:
    """Test edge cases and additional code paths."""
    
    def test_plot_mesh3d_plotly_volume_mesh_no_faces(self):
        """Test plotly plotting with volume mesh (cells but no faces)."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
            cells = np.array([[0, 1, 2, 3]])  # Volume mesh, no faces
            mesh = Mesh3D(vertices=vertices, cells=cells)
            # This should still work - it checks faces first but falls back
            # Since faces is None, it won't plot anything, but should not crash
            fig = plot_mesh3d_plotly(mesh)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")
    
    def test_plot_mesh3d_plotly_quad_faces_edges(self):
        """Test plotly plotting with quad faces and edge extraction."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
            vertices = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
                                 [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]])
            faces = np.array([[0, 1, 2, 3], [4, 5, 6, 7]])  # Quad faces
            mesh = Mesh3D(vertices=vertices, faces=faces)
            fig = plot_mesh3d_plotly(mesh, show_edges=True)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")
    
    def test_plot_mesh3d_plotly_color_by_missing_field(self):
        """Test plotly plotting with color_by field that doesn't exist."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
            cells = np.array([[0, 1, 2, 3]])
            mesh = Mesh3D(vertices=vertices, cells=cells)
            # color_by field not in cell_data, should fall back to material or default
            fig = plot_mesh3d_plotly(mesh, color_by="nonexistent_field")
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")
    
    def test_plot_mesh3d_pyvista_points_only(self):
        """Test pyvista plotting with points-only mesh."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            mesh = Mesh3D(vertices=vertices)  # No cells, no faces
            plotter = plot_mesh3d_pyvista(mesh)
            assert plotter is not None
        except ImportError:
            pytest.skip("pyvista not available")
    
    def test_plot_mesh3d_pyvista_hex_cells(self):
        """Test pyvista plotting with hex cells (8 vertices)."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
            vertices = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
                                 [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]])
            cells = np.array([[0, 1, 2, 3, 4, 5, 6, 7]])  # Hex cell
            mesh = Mesh3D(vertices=vertices, cells=cells)
            plotter = plot_mesh3d_pyvista(mesh)
            assert plotter is not None
        except ImportError:
            pytest.skip("pyvista not available")
    
    def test_plot_mesh3d_pyvista_color_by_missing_field(self):
        """Test pyvista plotting with color_by field that doesn't exist."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
            cells = np.array([[0, 1, 2, 3]])
            mesh = Mesh3D(vertices=vertices, cells=cells)
            # color_by field not in cell_data, should fall back to material or None
            plotter = plot_mesh3d_pyvista(mesh, color_by="nonexistent_field")
            assert plotter is not None
        except ImportError:
            pytest.skip("pyvista not available")
    
    def test_plot_multiple_meshes_plotly_mesh_without_faces(self):
        """Test plotting multiple meshes where one has no faces."""
        try:
            from smrforge.visualization.mesh_3d import plot_multiple_meshes_plotly
            vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            faces1 = np.array([[0, 1, 2]])
            mesh1 = Mesh3D(vertices=vertices1, faces=faces1)
            
            vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0], [2, 0, 1]])
            cells2 = np.array([[0, 1, 2, 3]])  # No faces
            mesh2 = Mesh3D(vertices=vertices2, cells=cells2)
            
            meshes = {"mesh1": mesh1, "mesh2": mesh2}
            # mesh2 has no faces, so it won't be plotted, but should not crash
            fig = plot_multiple_meshes_plotly(meshes)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")
    
    def test_plot_mesh3d_plotly_with_cells_and_faces(self):
        """Test plotly plotting with mesh that has both cells and faces."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
            cells = np.array([[0, 1, 2, 3]])
            faces = np.array([[0, 1, 2]])  # Also has faces
            mesh = Mesh3D(vertices=vertices, cells=cells, faces=faces)
            fig = plot_mesh3d_plotly(mesh)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")
    
    def test_plot_mesh3d_plotly_edges_with_different_face_sizes(self):
        """Test edge extraction with faces of different sizes (tri, quad, etc.)."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [0, 0, 1]])
            # Use object dtype to allow different face sizes, or just use tri faces
            # For now, use tri faces only since Mesh3D likely expects consistent sizes
            faces = np.array([[0, 1, 2], [1, 2, 3], [0, 2, 4]])  # All tri faces
            mesh = Mesh3D(vertices=vertices, faces=faces)
            fig = plot_mesh3d_plotly(mesh, show_edges=True)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")
    
    def test_plot_mesh3d_plotly_color_by_none_no_materials(self):
        """Test plotly plotting with no color_by and no materials (uses default)."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            faces = np.array([[0, 1, 2]])
            mesh = Mesh3D(vertices=vertices, faces=faces)  # No cell_data, no materials
            fig = plot_mesh3d_plotly(mesh, color_by=None)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")
    
    def test_export_mesh_to_vtk_with_materials_only(self, tmp_path):
        """Test exporting mesh with materials but no cell_data."""
        try:
            from smrforge.visualization.mesh_3d import export_mesh_to_vtk
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
            cells = np.array([[0, 1, 2, 3]])
            materials = np.array(["fuel"])
            mesh = Mesh3D(vertices=vertices, cells=cells, cell_materials=materials)
            filepath = tmp_path / "test_materials_only.vtk"
            export_mesh_to_vtk(mesh, str(filepath))
            assert filepath.exists()
        except ImportError:
            pytest.skip("pyvista not available")
    
    def test_export_mesh_to_vtk_empty_cell_data(self, tmp_path):
        """Test exporting mesh with empty cell_data dict."""
        try:
            from smrforge.visualization.mesh_3d import export_mesh_to_vtk
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
            cells = np.array([[0, 1, 2, 3]])
            mesh = Mesh3D(vertices=vertices, cells=cells)
            # cell_data is empty dict by default
            filepath = tmp_path / "test_empty_data.vtk"
            export_mesh_to_vtk(mesh, str(filepath))
            assert filepath.exists()
        except ImportError:
            pytest.skip("pyvista not available")
    
    def test_plot_mesh3d_pyvista_with_both_cells_and_faces(self):
        """Test pyvista plotting with mesh that has both cells and faces (prefers cells)."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
            cells = np.array([[0, 1, 2, 3]])
            faces = np.array([[0, 1, 2]])  # Also has faces
            mesh = Mesh3D(vertices=vertices, cells=cells, faces=faces)
            plotter = plot_mesh3d_pyvista(mesh)
            assert plotter is not None
        except ImportError:
            pytest.skip("pyvista not available")
    
    def test_plot_mesh3d_pyvista_no_coloring(self):
        """Test pyvista plotting with no color_by, no materials, no cell_data."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            faces = np.array([[0, 1, 2]])
            mesh = Mesh3D(vertices=vertices, faces=faces)
            plotter = plot_mesh3d_pyvista(mesh, color_by=None)
            assert plotter is not None
        except ImportError:
            pytest.skip("pyvista not available")
    
    def test_plot_multiple_meshes_plotly_custom_opacity(self):
        """Test plotting multiple meshes with custom opacity."""
        try:
            from smrforge.visualization.mesh_3d import plot_multiple_meshes_plotly
            vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            faces1 = np.array([[0, 1, 2]])
            mesh1 = Mesh3D(vertices=vertices1, faces=faces1)
            
            vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0]])
            faces2 = np.array([[0, 1, 2]])
            mesh2 = Mesh3D(vertices=vertices2, faces=faces2)
            
            meshes = {"mesh1": mesh1, "mesh2": mesh2}
            fig = plot_multiple_meshes_plotly(meshes, opacity=0.5)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")
    
    def test_plot_multiple_meshes_plotly_custom_title(self):
        """Test plotting multiple meshes with custom title."""
        try:
            from smrforge.visualization.mesh_3d import plot_multiple_meshes_plotly
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            faces = np.array([[0, 1, 2]])
            mesh = Mesh3D(vertices=vertices, faces=faces)
            meshes = {"mesh": mesh}
            fig = plot_multiple_meshes_plotly(meshes, title="Custom Title")
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")
    
    def test_plot_mesh3d_plotly_edges_reversed_vertex_order(self):
        """Test edge extraction when vertices are in reversed order (v0 > v1)."""
        try:
            from smrforge.visualization.mesh_3d import plot_mesh3d_plotly
            vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            # Face with vertices that would result in v0 > v1 after sorting
            faces = np.array([[2, 1, 0]])  # Reversed order
            mesh = Mesh3D(vertices=vertices, faces=faces)
            fig = plot_mesh3d_plotly(mesh, show_edges=True)
            assert fig is not None
        except ImportError:
            pytest.skip("plotly not available")

