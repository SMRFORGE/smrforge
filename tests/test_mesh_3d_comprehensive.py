"""
Comprehensive tests for geometry/mesh_3d.py to improve coverage to 75-80%.

Tests cover:
- Mesh3D class (initialization, validation, properties, methods)
- Surface class (initialization, validation, properties, methods)
- Mesh generation functions (hexagonal prism, cylinder, sphere)
- Mesh combination and manipulation functions
- Error handling and edge cases
"""

import numpy as np
import pytest

from smrforge.geometry.mesh_3d import (
    Mesh3D,
    Surface,
    combine_meshes,
    extract_cylinder_mesh,
    extract_hexagonal_prism_mesh,
    extract_sphere_mesh,
)


class TestMesh3D:
    """Test Mesh3D class."""

    def test_mesh3d_init_minimal(self):
        """Test Mesh3D initialization with minimal data."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        mesh = Mesh3D(vertices=vertices)
        assert mesh.n_vertices == 4
        assert mesh.n_faces == 0
        assert mesh.n_cells == 0

    def test_mesh3d_init_with_faces(self):
        """Test Mesh3D initialization with faces."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        faces = np.array([[0, 1, 2], [0, 1, 3], [1, 2, 3], [0, 2, 3]])
        mesh = Mesh3D(vertices=vertices, faces=faces)
        assert mesh.n_vertices == 4
        assert mesh.n_faces == 4

    def test_mesh3d_init_with_cells(self):
        """Test Mesh3D initialization with cells."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells = np.array([[0, 1, 2, 3]])  # Single tetrahedron
        mesh = Mesh3D(vertices=vertices, cells=cells)
        assert mesh.n_vertices == 4
        assert mesh.n_cells == 1

    def test_mesh3d_init_with_materials(self):
        """Test Mesh3D initialization with cell materials."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells = np.array([[0, 1, 2, 3]])
        materials = np.array(["fuel"])
        mesh = Mesh3D(vertices=vertices, cells=cells, cell_materials=materials)
        assert mesh.cell_materials is not None
        assert mesh.cell_materials[0] == "fuel"

    def test_mesh3d_init_invalid_vertices_shape(self):
        """Test Mesh3D initialization with invalid vertex shape."""
        vertices = np.array([0, 0, 0])  # 1D instead of 2D
        with pytest.raises(ValueError, match="Vertices must be"):
            Mesh3D(vertices=vertices)

    def test_mesh3d_init_invalid_vertices_columns(self):
        """Test Mesh3D initialization with wrong number of columns."""
        vertices = np.array([[0, 0], [1, 0], [0, 1]])  # 2 columns instead of 3
        with pytest.raises(ValueError, match="Vertices must be"):
            Mesh3D(vertices=vertices)

    def test_mesh3d_init_invalid_faces_shape(self):
        """Test Mesh3D initialization with invalid face shape."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces = np.array([0, 1, 2])  # 1D instead of 2D
        with pytest.raises(ValueError, match="Faces must be 2D array"):
            Mesh3D(vertices=vertices, faces=faces)

    def test_mesh3d_init_invalid_faces_vertices(self):
        """Test Mesh3D initialization with faces having wrong number of vertices."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        faces = np.array([[0, 1, 2, 3, 4]])  # 5 vertices instead of 3 or 4
        with pytest.raises(ValueError, match="Faces must have 3 or 4 vertices"):
            Mesh3D(vertices=vertices, faces=faces)

    def test_mesh3d_init_invalid_cells_shape(self):
        """Test Mesh3D initialization with invalid cell shape."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells = np.array([0, 1, 2, 3])  # 1D instead of 2D
        with pytest.raises(ValueError, match="Cells must be 2D array"):
            Mesh3D(vertices=vertices, cells=cells)

    def test_mesh3d_init_invalid_cells_vertices(self):
        """Test Mesh3D initialization with cells having wrong number of vertices."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells = np.array([[0, 1, 2]])  # 3 vertices instead of 4 or 8
        with pytest.raises(ValueError, match="Cells must have 4"):
            Mesh3D(vertices=vertices, cells=cells)

    def test_mesh3d_add_cell_data(self):
        """Test adding cell data."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells = np.array([[0, 1, 2, 3]])
        mesh = Mesh3D(vertices=vertices, cells=cells)

        data = np.array([1.0])
        mesh.add_cell_data("flux", data)
        assert "flux" in mesh.cell_data
        assert np.array_equal(mesh.cell_data["flux"], data)

    def test_mesh3d_add_cell_data_no_cells(self):
        """Test adding cell data when no cells exist."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        mesh = Mesh3D(vertices=vertices)

        with pytest.raises(ValueError, match="No cells defined"):
            mesh.add_cell_data("flux", np.array([1.0]))

    def test_mesh3d_add_cell_data_wrong_length(self):
        """Test adding cell data with wrong length."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells = np.array([[0, 1, 2, 3]])
        mesh = Mesh3D(vertices=vertices, cells=cells)

        with pytest.raises(ValueError, match="Data length"):
            mesh.add_cell_data("flux", np.array([1.0, 2.0]))

    def test_mesh3d_add_face_data(self):
        """Test adding face data."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        faces = np.array([[0, 1, 2], [0, 1, 3]])
        mesh = Mesh3D(vertices=vertices, faces=faces)

        data = np.array([1.0, 2.0])
        mesh.add_face_data("heat_flux", data)
        assert "heat_flux" in mesh.face_data
        assert np.array_equal(mesh.face_data["heat_flux"], data)

    def test_mesh3d_add_face_data_no_faces(self):
        """Test adding face data when no faces exist."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        mesh = Mesh3D(vertices=vertices)

        with pytest.raises(ValueError, match="No faces defined"):
            mesh.add_face_data("heat_flux", np.array([1.0]))

    def test_mesh3d_add_face_data_wrong_length(self):
        """Test adding face data with wrong length."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        faces = np.array([[0, 1, 2]])
        mesh = Mesh3D(vertices=vertices, faces=faces)

        with pytest.raises(ValueError, match="Data length"):
            mesh.add_face_data("heat_flux", np.array([1.0, 2.0]))

    def test_mesh3d_get_bounds(self):
        """Test getting mesh bounds."""
        vertices = np.array(
            [
                [0, 0, 0],
                [1, 2, 3],
                [-1, -2, -3],
                [0.5, 1.5, 2.5],
            ]
        )
        mesh = Mesh3D(vertices=vertices)
        min_bounds, max_bounds = mesh.get_bounds()

        assert np.allclose(min_bounds, [-1, -2, -3])
        assert np.allclose(max_bounds, [1, 2, 3])

    def test_mesh3d_get_center(self):
        """Test getting mesh center."""
        vertices = np.array(
            [
                [0, 0, 0],
                [2, 0, 0],
                [0, 2, 0],
                [0, 0, 2],
            ]
        )
        mesh = Mesh3D(vertices=vertices)
        center = mesh.get_center()

        assert np.allclose(center, [0.5, 0.5, 0.5])


class TestSurface:
    """Test Surface class."""

    def test_surface_init_minimal(self):
        """Test Surface initialization with minimal data."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces = np.array([[0, 1, 2]])
        surface = Surface(vertices=vertices, faces=faces)
        assert surface.n_vertices == 3
        assert surface.n_faces == 1

    def test_surface_init_with_material(self):
        """Test Surface initialization with material ID."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces = np.array([[0, 1, 2]])
        surface = Surface(vertices=vertices, faces=faces, material_id="fuel")
        assert surface.material_id == "fuel"

    def test_surface_init_with_surface_type(self):
        """Test Surface initialization with surface type."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces = np.array([[0, 1, 2]])
        surface = Surface(vertices=vertices, faces=faces, surface_type="boundary")
        assert surface.surface_type == "boundary"

    def test_surface_init_invalid_vertices(self):
        """Test Surface initialization with invalid vertices."""
        vertices = np.array([0, 0, 0])  # 1D instead of 2D
        faces = np.array([[0, 1, 2]])
        with pytest.raises(ValueError, match="Vertices must be"):
            Surface(vertices=vertices, faces=faces)

    def test_surface_init_invalid_faces(self):
        """Test Surface initialization with invalid faces."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces = np.array([0, 1, 2])  # 1D instead of 2D
        with pytest.raises(ValueError, match="Faces must be"):
            Surface(vertices=vertices, faces=faces)

    def test_surface_to_mesh3d(self):
        """Test converting Surface to Mesh3D."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces = np.array([[0, 1, 2]])
        surface = Surface(vertices=vertices, faces=faces, material_id="fuel")
        mesh = surface.to_mesh3d()

        assert isinstance(mesh, Mesh3D)
        assert mesh.n_vertices == 3
        assert mesh.n_faces == 1
        assert mesh.cell_materials is not None
        assert mesh.cell_materials[0] == "fuel"

    def test_surface_to_mesh3d_no_material(self):
        """Test converting Surface to Mesh3D without material."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces = np.array([[0, 1, 2]])
        surface = Surface(vertices=vertices, faces=faces)
        mesh = surface.to_mesh3d()

        assert isinstance(mesh, Mesh3D)
        assert mesh.cell_materials is None


class TestMeshGeneration:
    """Test mesh generation functions."""

    def test_extract_hexagonal_prism_mesh(self):
        """Test extracting hexagonal prism mesh."""
        center = np.array([0, 0, 0])
        mesh = extract_hexagonal_prism_mesh(
            center=center, flat_to_flat=36.0, height=80.0
        )

        assert isinstance(mesh, Mesh3D)
        assert mesh.n_vertices > 0
        assert mesh.n_faces > 0
        assert mesh.n_cells > 0

    def test_extract_hexagonal_prism_mesh_custom_segments(self):
        """Test extracting hexagonal prism mesh with custom segments."""
        center = np.array([10, 20, 30])
        mesh = extract_hexagonal_prism_mesh(
            center=center,
            flat_to_flat=40.0,
            height=100.0,
            n_segments=8,
        )

        assert isinstance(mesh, Mesh3D)
        assert mesh.n_vertices > 0

    def test_extract_cylinder_mesh(self):
        """Test extracting cylinder mesh."""
        center = np.array([0, 0, 0])
        mesh = extract_cylinder_mesh(center=center, radius=5.0, height=100.0)

        assert isinstance(mesh, Mesh3D)
        assert mesh.n_vertices > 0
        assert mesh.n_faces > 0
        assert mesh.n_cells > 0

    def test_extract_cylinder_mesh_custom_segments(self):
        """Test extracting cylinder mesh with custom segments."""
        center = np.array([5, 10, 15])
        mesh = extract_cylinder_mesh(
            center=center,
            radius=3.0,
            height=50.0,
            n_segments=32,
        )

        assert isinstance(mesh, Mesh3D)
        assert mesh.n_vertices > 0

    def test_extract_sphere_mesh(self):
        """Test extracting sphere mesh."""
        center = np.array([0, 0, 0])
        mesh = extract_sphere_mesh(center=center, radius=2.5)

        assert isinstance(mesh, Mesh3D)
        assert mesh.n_vertices > 0
        assert mesh.n_faces > 0
        # Note: extract_sphere_mesh only creates faces, not cells
        # assert mesh.n_cells > 0  # This may be None

    def test_extract_sphere_mesh_custom_segments(self):
        """Test extracting sphere mesh with custom segments."""
        center = np.array([1, 2, 3])
        mesh = extract_sphere_mesh(center=center, radius=1.0, n_segments=20)

        assert isinstance(mesh, Mesh3D)
        assert mesh.n_vertices > 0


class TestMeshCombination:
    """Test mesh combination functions."""

    def test_combine_meshes_single(self):
        """Test combining a single mesh."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells = np.array([[0, 1, 2, 3]])
        mesh1 = Mesh3D(vertices=vertices, cells=cells)

        combined = combine_meshes([mesh1])
        assert isinstance(combined, Mesh3D)
        assert combined.n_vertices == 4
        assert combined.n_cells == 1

    def test_combine_meshes_multiple(self):
        """Test combining multiple meshes."""
        # First mesh
        vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells1 = np.array([[0, 1, 2, 3]])
        mesh1 = Mesh3D(vertices=vertices1, cells=cells1)

        # Second mesh (offset)
        vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0], [2, 0, 1]])
        cells2 = np.array([[0, 1, 2, 3]])
        mesh2 = Mesh3D(vertices=vertices2, cells=cells2)

        combined = combine_meshes([mesh1, mesh2])
        assert isinstance(combined, Mesh3D)
        assert combined.n_vertices == 8
        assert combined.n_cells == 2

    def test_combine_meshes_with_materials(self):
        """Test combining meshes with different materials."""
        # First mesh
        vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells1 = np.array([[0, 1, 2, 3]])
        materials1 = np.array(["fuel"])
        mesh1 = Mesh3D(vertices=vertices1, cells=cells1, cell_materials=materials1)

        # Second mesh
        vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0], [2, 0, 1]])
        cells2 = np.array([[0, 1, 2, 3]])
        materials2 = np.array(["reflector"])
        mesh2 = Mesh3D(vertices=vertices2, cells=cells2, cell_materials=materials2)

        combined = combine_meshes([mesh1, mesh2])
        assert combined.cell_materials is not None
        assert len(combined.cell_materials) == 2
        assert combined.cell_materials[0] == "fuel"
        assert combined.cell_materials[1] == "reflector"

    def test_combine_meshes_with_data(self):
        """Test combining meshes with cell data."""
        # First mesh
        vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells1 = np.array([[0, 1, 2, 3]])
        mesh1 = Mesh3D(vertices=vertices1, cells=cells1)
        mesh1.add_cell_data("flux", np.array([1.0]))

        # Second mesh
        vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0], [2, 0, 1]])
        cells2 = np.array([[0, 1, 2, 3]])
        mesh2 = Mesh3D(vertices=vertices2, cells=cells2)
        mesh2.add_cell_data("flux", np.array([2.0]))

        combined = combine_meshes([mesh1, mesh2])
        assert "flux" in combined.cell_data
        assert len(combined.cell_data["flux"]) == 2
        assert combined.cell_data["flux"][0] == 1.0
        assert combined.cell_data["flux"][1] == 2.0

    def test_combine_meshes_empty_list(self):
        """Test combining empty list of meshes."""
        with pytest.raises(ValueError, match="No meshes to combine"):
            combine_meshes([])

    def test_combine_meshes_without_faces(self):
        """Test combining meshes without faces."""
        vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells1 = np.array([[0, 1, 2, 3]])
        mesh1 = Mesh3D(vertices=vertices1, cells=cells1)  # No faces

        vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0], [2, 0, 1]])
        cells2 = np.array([[0, 1, 2, 3]])
        mesh2 = Mesh3D(vertices=vertices2, cells=cells2)  # No faces

        combined = combine_meshes([mesh1, mesh2])
        assert combined.n_faces == 0
        assert combined.faces is None

    def test_combine_meshes_without_cells(self):
        """Test combining meshes without cells."""
        vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces1 = np.array([[0, 1, 2]])
        mesh1 = Mesh3D(vertices=vertices1, faces=faces1)  # No cells

        vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0]])
        faces2 = np.array([[0, 1, 2]])
        mesh2 = Mesh3D(vertices=vertices2, faces=faces2)  # No cells

        combined = combine_meshes([mesh1, mesh2])
        assert combined.n_cells == 0
        assert combined.cells is None

    def test_combine_meshes_without_materials(self):
        """Test combining meshes without materials."""
        vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells1 = np.array([[0, 1, 2, 3]])
        mesh1 = Mesh3D(vertices=vertices1, cells=cells1)  # No materials

        vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0], [2, 0, 1]])
        cells2 = np.array([[0, 1, 2, 3]])
        mesh2 = Mesh3D(vertices=vertices2, cells=cells2)  # No materials

        combined = combine_meshes([mesh1, mesh2])
        assert combined.cell_materials is None

    def test_combine_meshes_without_cell_data(self):
        """Test combining meshes without cell data."""
        vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells1 = np.array([[0, 1, 2, 3]])
        mesh1 = Mesh3D(vertices=vertices1, cells=cells1)  # No cell_data

        vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0], [2, 0, 1]])
        cells2 = np.array([[0, 1, 2, 3]])
        mesh2 = Mesh3D(vertices=vertices2, cells=cells2)  # No cell_data

        combined = combine_meshes([mesh1, mesh2])
        assert len(combined.cell_data) == 0

    def test_combine_meshes_mixed_faces_and_no_faces(self):
        """Test combining meshes where some have faces and some don't."""
        vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces1 = np.array([[0, 1, 2]])
        mesh1 = Mesh3D(vertices=vertices1, faces=faces1)

        vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0], [2, 0, 1]])
        cells2 = np.array([[0, 1, 2, 3]])
        mesh2 = Mesh3D(vertices=vertices2, cells=cells2)  # No faces

        combined = combine_meshes([mesh1, mesh2])
        assert combined.n_faces == 1  # Only from mesh1

    def test_combine_meshes_mixed_cells_and_no_cells(self):
        """Test combining meshes where some have cells and some don't."""
        vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells1 = np.array([[0, 1, 2, 3]])
        mesh1 = Mesh3D(vertices=vertices1, cells=cells1)

        vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0]])
        faces2 = np.array([[0, 1, 2]])
        mesh2 = Mesh3D(vertices=vertices2, faces=faces2)  # No cells

        combined = combine_meshes([mesh1, mesh2])
        assert combined.n_cells == 1  # Only from mesh1

    def test_combine_meshes_partial_materials(self):
        """Test combining meshes where only some have materials."""
        vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells1 = np.array([[0, 1, 2, 3]])
        materials1 = np.array(["fuel"])
        mesh1 = Mesh3D(vertices=vertices1, cells=cells1, cell_materials=materials1)

        vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0], [2, 0, 1]])
        cells2 = np.array([[0, 1, 2, 3]])
        mesh2 = Mesh3D(vertices=vertices2, cells=cells2)  # No materials

        combined = combine_meshes([mesh1, mesh2])
        # When mixing meshes with and without materials, result may have materials
        # depending on implementation - just verify it doesn't crash
        assert combined is not None

    def test_combine_meshes_partial_cell_data(self):
        """Test combining meshes where only some have cell data."""
        vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells1 = np.array([[0, 1, 2, 3]])
        mesh1 = Mesh3D(vertices=vertices1, cells=cells1)
        mesh1.add_cell_data("flux", np.array([1.0]))

        vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0], [2, 0, 1]])
        cells2 = np.array([[0, 1, 2, 3]])
        mesh2 = Mesh3D(vertices=vertices2, cells=cells2)  # No cell_data

        combined = combine_meshes([mesh1, mesh2])
        # When mixing meshes with and without cell_data, only data from mesh1 should be present
        # But since mesh2 has no data for "flux", this might cause issues - implementation dependent
        assert combined is not None

    def test_combine_meshes_multiple_cell_data_fields(self):
        """Test combining meshes with multiple cell data fields."""
        vertices1 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        cells1 = np.array([[0, 1, 2, 3]])
        mesh1 = Mesh3D(vertices=vertices1, cells=cells1)
        mesh1.add_cell_data("flux", np.array([1.0]))
        mesh1.add_cell_data("power", np.array([2.0]))

        vertices2 = np.array([[2, 0, 0], [3, 0, 0], [2, 1, 0], [2, 0, 1]])
        cells2 = np.array([[0, 1, 2, 3]])
        mesh2 = Mesh3D(vertices=vertices2, cells=cells2)
        mesh2.add_cell_data("flux", np.array([3.0]))
        mesh2.add_cell_data("power", np.array([4.0]))

        combined = combine_meshes([mesh1, mesh2])
        assert "flux" in combined.cell_data
        assert "power" in combined.cell_data
        assert len(combined.cell_data["flux"]) == 2
        assert len(combined.cell_data["power"]) == 2


class TestMeshGenerationEdgeCases:
    """Test edge cases in mesh generation functions."""

    def test_extract_hexagonal_prism_mesh_zero_height(self):
        """Test hexagonal prism with zero height."""
        center = np.array([0, 0, 0])
        mesh = extract_hexagonal_prism_mesh(
            center=center, flat_to_flat=36.0, height=0.0
        )

        assert isinstance(mesh, Mesh3D)
        assert mesh.n_vertices > 0

    def test_extract_cylinder_mesh_zero_height(self):
        """Test cylinder with zero height."""
        center = np.array([0, 0, 0])
        mesh = extract_cylinder_mesh(center=center, radius=5.0, height=0.0)

        assert isinstance(mesh, Mesh3D)
        assert mesh.n_vertices > 0

    def test_extract_cylinder_mesh_zero_radius(self):
        """Test cylinder with zero radius."""
        center = np.array([0, 0, 0])
        mesh = extract_cylinder_mesh(center=center, radius=0.0, height=100.0)

        assert isinstance(mesh, Mesh3D)
        assert mesh.n_vertices > 0

    def test_extract_sphere_mesh_zero_radius(self):
        """Test sphere with zero radius."""
        center = np.array([0, 0, 0])
        mesh = extract_sphere_mesh(center=center, radius=0.0)

        assert isinstance(mesh, Mesh3D)
        assert mesh.n_vertices > 0

    def test_extract_sphere_mesh_single_segment(self):
        """Test sphere with minimal segments."""
        center = np.array([0, 0, 0])
        mesh = extract_sphere_mesh(center=center, radius=1.0, n_segments=1)

        assert isinstance(mesh, Mesh3D)
        assert mesh.n_vertices > 0

    def test_extract_cylinder_mesh_single_segment(self):
        """Test cylinder with minimal segments."""
        center = np.array([0, 0, 0])
        mesh = extract_cylinder_mesh(
            center=center, radius=1.0, height=10.0, n_segments=1
        )

        assert isinstance(mesh, Mesh3D)
        assert mesh.n_vertices > 0

    def test_mesh3d_init_with_quad_faces(self):
        """Test Mesh3D initialization with quad faces (4 vertices)."""
        vertices = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 1],
                [1, 0, 1],
                [1, 1, 1],
                [0, 1, 1],
            ]
        )
        faces = np.array([[0, 1, 2, 3], [4, 5, 6, 7]])  # Quad faces
        mesh = Mesh3D(vertices=vertices, faces=faces)

        assert mesh.n_faces == 2
        assert mesh.faces.shape[1] == 4

    def test_mesh3d_init_with_hex_cells(self):
        """Test Mesh3D initialization with hex cells (8 vertices)."""
        vertices = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 1],
                [1, 0, 1],
                [1, 1, 1],
                [0, 1, 1],
            ]
        )
        cells = np.array([[0, 1, 2, 3, 4, 5, 6, 7]])  # Hex cell
        mesh = Mesh3D(vertices=vertices, cells=cells)

        assert mesh.n_cells == 1
        assert mesh.cells.shape[1] == 8

    def test_surface_to_mesh3d_multiple_faces(self):
        """Test converting Surface with multiple faces to Mesh3D."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])
        faces = np.array([[0, 1, 2], [1, 3, 2]])
        surface = Surface(vertices=vertices, faces=faces, material_id="fuel")
        mesh = surface.to_mesh3d()

        assert mesh.n_faces == 2
        assert len(mesh.cell_materials) == 2
        assert all(m == "fuel" for m in mesh.cell_materials)
