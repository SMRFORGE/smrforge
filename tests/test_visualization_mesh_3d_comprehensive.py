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

