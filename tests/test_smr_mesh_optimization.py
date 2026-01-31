"""
Tests for SMR-specific mesh optimization.

Tests compact geometry meshing, SMR-optimized refinement, and adaptive refinement.
"""

import pytest
import numpy as np

try:
    from smrforge.geometry.smr_mesh_optimization import (
        SMRMeshOptimizer,
        SMRMeshParams,
    )

    _SMR_MESH_OPTIMIZATION_AVAILABLE = True
except ImportError:
    _SMR_MESH_OPTIMIZATION_AVAILABLE = False


@pytest.mark.skipif(
    not _SMR_MESH_OPTIMIZATION_AVAILABLE,
    reason="SMR mesh optimization not available",
)
class TestSMRMeshParams:
    """Tests for SMRMeshParams dataclass."""

    def test_default_params(self):
        """Test default parameters."""
        params = SMRMeshParams()

        assert params.base_resolution == 20
        assert params.fuel_pin_refinement == 2.0
        assert params.assembly_boundary_refinement == 1.5
        assert params.min_cell_size == 0.1
        assert params.max_cell_size == 5.0

    def test_custom_params(self):
        """Test custom parameters."""
        params = SMRMeshParams(
            base_resolution=30,
            fuel_pin_refinement=3.0,
            min_cell_size=0.05,
        )

        assert params.base_resolution == 30
        assert params.fuel_pin_refinement == 3.0
        assert params.min_cell_size == 0.05


@pytest.mark.skipif(
    not _SMR_MESH_OPTIMIZATION_AVAILABLE,
    reason="SMR mesh optimization not available",
)
class TestSMRMeshOptimizer:
    """Tests for SMRMeshOptimizer class."""

    def test_optimizer_creation(self):
        """Test creating mesh optimizer."""
        optimizer = SMRMeshOptimizer()
        assert optimizer.default_params is not None

    def test_generate_smr_mesh_basic(self):
        """Test basic SMR mesh generation."""
        optimizer = SMRMeshOptimizer()

        mesh = optimizer.generate_smr_mesh(
            core_diameter=200.0,  # cm
            core_height=365.76,  # cm
        )

        assert "radial_mesh" in mesh
        assert "axial_mesh" in mesh
        assert len(mesh["radial_mesh"]) > 0
        assert len(mesh["axial_mesh"]) > 0

        # Check mesh bounds
        assert mesh["radial_mesh"][0] == pytest.approx(0.0)
        assert mesh["radial_mesh"][-1] == pytest.approx(100.0)  # r_max = diameter/2
        assert mesh["axial_mesh"][0] == pytest.approx(0.0)
        assert mesh["axial_mesh"][-1] == pytest.approx(365.76)

    def test_generate_smr_mesh_no_refinement_returns_base_meshes(self):
        """Cover no-refinement paths (return base meshes)."""
        optimizer = SMRMeshOptimizer()

        params = SMRMeshParams(
            base_resolution=5,
            core_boundary_refinement=1.0,  # disables boundary refinement points
            assembly_boundary_refinement=1.0,
            fuel_pin_refinement=1.0,
        )

        mesh = optimizer.generate_smr_mesh(
            core_diameter=200.0,
            core_height=365.76,
            params=params,
        )

        assert np.allclose(mesh["radial_mesh"], np.linspace(0.0, 100.0, 5))
        assert np.allclose(mesh["axial_mesh"], np.linspace(0.0, 365.76, 5))
        assert mesh["x_mesh"] is None
        assert mesh["y_mesh"] is None
        assert mesh["z_mesh"] is None

    def test_generate_smr_mesh_xy_no_refinement_when_positions_outside_core(self):
        """Cover xy-mesh branches where x_refine/y_refine remain empty."""
        optimizer = SMRMeshOptimizer()
        params = SMRMeshParams(base_resolution=7, core_boundary_refinement=1.0)

        # Non-empty positions triggers XY mesh generation, but abs(x/y) >= r_max prevents refinement.
        assembly_positions = [(101.0, 101.0)]
        mesh = optimizer.generate_smr_mesh(
            core_diameter=200.0,
            core_height=365.76,
            assembly_positions=assembly_positions,
            params=params,
        )

        r_max = 100.0
        assert np.allclose(mesh["x_mesh"], np.linspace(-r_max, r_max, 7))
        assert np.allclose(mesh["y_mesh"], np.linspace(-r_max, r_max, 7))

    def test_generate_smr_mesh_with_assemblies(self):
        """Test mesh generation with assembly positions."""
        optimizer = SMRMeshOptimizer()

        # Create assembly positions (3x3 grid)
        assembly_positions = [
            (-20.0, -20.0),
            (0.0, -20.0),
            (20.0, -20.0),
            (-20.0, 0.0),
            (0.0, 0.0),
            (20.0, 0.0),
            (-20.0, 20.0),
            (0.0, 20.0),
            (20.0, 20.0),
        ]

        mesh = optimizer.generate_smr_mesh(
            core_diameter=200.0,
            core_height=365.76,
            assembly_positions=assembly_positions,
        )

        assert "radial_mesh" in mesh
        assert "x_mesh" in mesh
        assert "y_mesh" in mesh

        # Mesh should have refinement near assemblies
        assert len(mesh["radial_mesh"]) >= 20  # Base resolution

    def test_generate_smr_mesh_with_fuel_pins(self):
        """Test mesh generation with fuel pin positions."""
        optimizer = SMRMeshOptimizer()

        # Create fuel pin positions (small subset)
        fuel_pin_positions = [
            (0.0, 0.0, 100.0),
            (1.26, 0.0, 100.0),
            (0.0, 1.26, 100.0),
        ]

        mesh = optimizer.generate_smr_mesh(
            core_diameter=200.0,
            core_height=365.76,
            fuel_pin_positions=fuel_pin_positions,
        )

        assert "radial_mesh" in mesh
        assert "axial_mesh" in mesh

        # Mesh should have refinement near fuel pins
        assert len(mesh["radial_mesh"]) >= 20

    def test_custom_params(self):
        """Test mesh generation with custom parameters."""
        optimizer = SMRMeshOptimizer()

        params = SMRMeshParams(
            base_resolution=30,
            fuel_pin_refinement=3.0,
            min_cell_size=0.05,
        )

        mesh = optimizer.generate_smr_mesh(
            core_diameter=200.0,
            core_height=365.76,
            params=params,
        )

        # Should have more points with higher resolution
        assert len(mesh["radial_mesh"]) >= 30

    def test_enforce_cell_sizes(self):
        """Test cell size enforcement."""
        optimizer = SMRMeshOptimizer()

        # Create mesh with very small cells
        test_mesh = np.array([0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 1.0])

        params = SMRMeshParams(min_cell_size=0.1)

        filtered_mesh = optimizer._enforce_cell_sizes(test_mesh, params)

        # Should remove points that create cells smaller than min_cell_size
        cell_sizes = np.diff(filtered_mesh)
        assert np.all(cell_sizes >= params.min_cell_size)

    def test_enforce_cell_sizes_mesh_with_single_point_returns_unchanged(self):
        """Cover short-mesh early return."""
        optimizer = SMRMeshOptimizer()
        params = SMRMeshParams()
        mesh = np.array([0.0])
        out = optimizer._enforce_cell_sizes(mesh, params)
        assert np.array_equal(out, mesh)

    def test_estimate_mesh_quality(self):
        """Test mesh quality estimation."""
        optimizer = SMRMeshOptimizer()

        mesh = optimizer.generate_smr_mesh(
            core_diameter=200.0,
            core_height=365.76,
        )

        quality = optimizer.estimate_mesh_quality(mesh, 200.0, 365.76)

        assert "n_radial_cells" in quality
        assert "n_axial_cells" in quality
        assert "n_cells" in quality
        assert "avg_radial_cell_size" in quality
        assert "avg_axial_cell_size" in quality
        assert "aspect_ratio" in quality

        # Quality metrics should be positive
        assert quality["n_cells"] > 0
        assert quality["avg_radial_cell_size"] > 0
        assert quality["avg_axial_cell_size"] > 0

    def test_optimize_mesh_for_flux(self):
        """Test flux-based mesh optimization."""
        optimizer = SMRMeshOptimizer()

        mesh = optimizer.generate_smr_mesh(
            core_diameter=200.0,
            core_height=365.76,
        )

        # Create dummy flux distribution
        n_r = len(mesh["radial_mesh"]) - 1
        n_z = len(mesh["axial_mesh"]) - 1
        flux = np.ones((n_r, n_z))

        # Should return mesh (placeholder implementation)
        refined_mesh = optimizer.optimize_mesh_for_flux(mesh, flux)

        assert "radial_mesh" in refined_mesh
        assert "axial_mesh" in refined_mesh
