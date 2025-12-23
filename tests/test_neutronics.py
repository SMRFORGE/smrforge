"""
Comprehensive tests for neutronics module
"""

from pathlib import Path

import numpy as np
import pytest

from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.validation.models import CrossSectionData, SolverOptions


class SimpleGeometry:
    """Simple geometry for testing."""

    def __init__(self, core_diameter=200.0, core_height=400.0):
        self.core_diameter = core_diameter
        self.core_height = core_height
        # Create mesh
        self.radial_mesh = np.linspace(0, core_diameter / 2, 11)
        self.axial_mesh = np.linspace(0, core_height, 21)


@pytest.fixture
def simple_geometry():
    """Create a simple geometry for testing."""
    return SimpleGeometry()


@pytest.fixture
def simple_xs_data():
    """Create simple 2-group cross section data."""
    return CrossSectionData(
        n_groups=2,
        n_materials=2,  # Fuel and reflector
        sigma_t=np.array(
            [
                [0.30, 0.90],  # Fuel
                [0.28, 0.75],  # Reflector
            ]
        ),
        sigma_a=np.array(
            [
                [0.008, 0.12],  # Fuel
                [0.002, 0.025],  # Reflector
            ]
        ),
        sigma_f=np.array(
            [
                [0.006, 0.10],  # Fuel
                [0.0, 0.0],  # Reflector
            ]
        ),
        nu_sigma_f=np.array(
            [
                [0.015, 0.25],  # Fuel
                [0.0, 0.0],  # Reflector
            ]
        ),
        sigma_s=np.array(
            [
                [[0.29, 0.01], [0.0, 0.78]],  # Fuel scattering
                [[0.28, 0.0], [0.0, 0.73]],  # Reflector scattering
            ]
        ),
        chi=np.array(
            [
                [1.0, 0.0],  # Fission spectrum
                [1.0, 0.0],  # Reflector (not used)
            ]
        ),
        D=np.array(
            [
                [1.0, 0.4],  # Diffusion coefficients
                [1.2, 0.5],
            ]
        ),
    )


@pytest.fixture
def solver_options():
    """Create solver options for testing."""
    return SolverOptions(
        max_iterations=100,
        tolerance=1e-5,
        eigen_method="power",
        inner_solver="bicgstab",
        verbose=False,
    )


@pytest.fixture
def solver(simple_geometry, simple_xs_data, solver_options):
    """Create a solver instance for testing."""
    return MultiGroupDiffusion(simple_geometry, simple_xs_data, solver_options)


class TestImports:
    """Test module imports."""

    def test_neutronics_import(self):
        """Test that neutronics module can be imported."""
        from smrforge import neutronics

        assert neutronics is not None

    def test_solver_import(self):
        """Test that MultiGroupDiffusion can be imported."""
        from smrforge.neutronics.solver import MultiGroupDiffusion

        assert MultiGroupDiffusion is not None

    def test_validation_imports(self):
        """Test that validation models can be imported."""
        from smrforge.validation.models import CrossSectionData, SolverOptions

        assert CrossSectionData is not None
        assert SolverOptions is not None


class TestSolverInitialization:
    """Test solver initialization."""

    def test_solver_creation(self, simple_geometry, simple_xs_data, solver_options):
        """Test that solver can be created."""
        solver = MultiGroupDiffusion(simple_geometry, simple_xs_data, solver_options)
        assert solver is not None
        assert solver.xs.n_groups == 2
        assert solver.xs.n_materials == 2

    def test_solver_mesh_setup(self, solver):
        """Test that mesh is set up correctly."""
        assert solver.nr > 0
        assert solver.nz > 0
        assert solver.ng == 2
        assert solver.r_centers is not None
        assert solver.z_centers is not None

    def test_solver_arrays_allocated(self, solver):
        """Test that solution arrays are allocated."""
        assert solver.flux is not None
        assert solver.source is not None
        assert solver.D_map is not None
        assert solver.sigma_t_map is not None
        assert solver.material_map is not None

    def test_invalid_xs_data(self, simple_geometry, solver_options):
        """Test that invalid cross section data is rejected."""
        # Create invalid XS data (sigma_a > sigma_t)
        invalid_xs = CrossSectionData(
            n_groups=2,
            n_materials=1,
            sigma_t=np.array([[0.5, 0.8]]),
            sigma_a=np.array([[0.6, 0.9]]),  # Invalid: > sigma_t
            sigma_f=np.array([[0.05, 0.15]]),
            nu_sigma_f=np.array([[0.125, 0.375]]),
            sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
            chi=np.array([[1.0, 0.0]]),
            D=np.array([[1.5, 0.4]]),
        )

        with pytest.raises(ValueError):
            MultiGroupDiffusion(simple_geometry, invalid_xs, solver_options)


class TestSolverMethods:
    """Test solver methods."""

    def test_solve_steady_state(self, solver):
        """Test steady-state eigenvalue solve."""
        k_eff, flux = solver.solve_steady_state()

        # Check that solution is reasonable
        assert 0.5 < k_eff < 2.0, f"k_eff = {k_eff} is unreasonable"
        assert flux is not None
        assert flux.shape == (solver.nz, solver.nr, solver.ng)
        assert np.all(flux >= 0), "Flux should be non-negative"
        assert np.all(np.isfinite(flux)), "Flux should be finite"

    def test_solve_convergence(self, solver):
        """Test that solver converges."""
        k_eff, flux = solver.solve_steady_state()

        # Check solver state
        assert solver.k_eff == k_eff
        assert np.allclose(solver.flux, flux)

    def test_compute_power_distribution(self, solver):
        """Test power distribution computation."""
        # First solve for flux
        k_eff, flux = solver.solve_steady_state()

        # Compute power distribution
        total_power = 10e6  # 10 MW
        power = solver.compute_power_distribution(total_power)

        # Check power distribution
        assert power is not None
        assert power.shape == (solver.nz, solver.nr)
        assert np.all(power >= 0), "Power should be non-negative"

        # Check that total power is correct (within tolerance)
        volumes = solver._cell_volumes()
        total_power_computed = np.sum(power * volumes)
        assert np.isclose(total_power_computed, total_power, rtol=1e-3)

    def test_cell_volumes(self, solver):
        """Test cell volume computation."""
        volumes = solver._cell_volumes()

        assert volumes is not None
        assert volumes.shape == (solver.nz, solver.nr)
        assert np.all(volumes > 0), "Volumes should be positive"

        # Test caching (second call should return same array)
        volumes2 = solver._cell_volumes()
        assert np.array_equal(volumes, volumes2)

    def test_compute_k_eff(self, solver):
        """Test k_eff computation."""
        # Set up a simple flux
        solver.flux = np.ones((solver.nz, solver.nr, solver.ng))
        solver._update_xs_maps()

        k_eff = solver._compute_k_eff()

        assert np.isfinite(k_eff)
        assert k_eff > 0


class TestSolverValidation:
    """Test solver validation and error handling."""

    def test_solver_validates_physics(self, simple_geometry, solver_options):
        """Test that solver validates physics constraints."""
        # Create XS with sigma_f > sigma_a (invalid)
        invalid_xs = CrossSectionData(
            n_groups=2,
            n_materials=1,
            sigma_t=np.array([[0.5, 0.8]]),
            sigma_a=np.array([[0.05, 0.1]]),
            sigma_f=np.array([[0.1, 0.2]]),  # Invalid: > sigma_a
            nu_sigma_f=np.array([[0.25, 0.5]]),
            sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
            chi=np.array([[1.0, 0.0]]),
            D=np.array([[1.5, 0.4]]),
        )

        # This should be caught by Pydantic validation before physics check
        # But test that solver still validates
        with pytest.raises((ValueError, AssertionError)):
            MultiGroupDiffusion(simple_geometry, invalid_xs, solver_options)

    def test_solver_tolerance(self, simple_geometry, simple_xs_data):
        """Test that solver respects tolerance settings."""
        # Use tight tolerance
        tight_options = SolverOptions(
            max_iterations=1000, tolerance=1e-8, verbose=False
        )

        solver = MultiGroupDiffusion(simple_geometry, simple_xs_data, tight_options)
        k_eff, flux = solver.solve_steady_state()

        # Solution should exist
        assert np.isfinite(k_eff)

    def test_solver_max_iterations(self, simple_geometry, simple_xs_data):
        """Test that solver respects max iterations."""
        # Use very few iterations (may not converge)
        tight_options = SolverOptions(
            max_iterations=5,  # Very few iterations
            tolerance=1e-10,  # Very tight tolerance
            verbose=False,
        )

        solver = MultiGroupDiffusion(simple_geometry, simple_xs_data, tight_options)

        # Should either converge or raise RuntimeError
        try:
            k_eff, flux = solver.solve_steady_state()
            assert np.isfinite(k_eff)
        except RuntimeError:
            # Expected if doesn't converge
            pass


class TestSolverPerformance:
    """Test solver performance characteristics."""

    def test_solver_performance_small_mesh(self, simple_xs_data, solver_options):
        """Test solver with small mesh."""
        geometry = SimpleGeometry(core_diameter=100.0, core_height=200.0)
        geometry.radial_mesh = np.linspace(0, 50, 6)  # Small mesh
        geometry.axial_mesh = np.linspace(0, 200, 11)

        solver = MultiGroupDiffusion(geometry, simple_xs_data, solver_options)

        import time

        start = time.time()
        k_eff, flux = solver.solve_steady_state()
        elapsed = time.time() - start

        assert elapsed < 5.0, "Small mesh should solve quickly"
        assert np.isfinite(k_eff)

    def test_solver_scaling(self, simple_xs_data, solver_options):
        """Test that solver works with different mesh sizes."""
        mesh_sizes = [(5, 10), (10, 20), (15, 30)]

        for nr, nz in mesh_sizes:
            geometry = SimpleGeometry()
            geometry.radial_mesh = np.linspace(0, 100, nr + 1)
            geometry.axial_mesh = np.linspace(0, 400, nz + 1)

            solver = MultiGroupDiffusion(geometry, simple_xs_data, solver_options)
            k_eff, flux = solver.solve_steady_state()

            assert np.isfinite(k_eff)
            assert flux.shape == (nz, nr, 2)


class TestMultiGroupMethods:
    """Test multi-group specific methods."""

    def test_update_xs_maps(self, solver):
        """Test cross section map updates."""
        # Update XS maps
        solver._update_xs_maps()

        # Check that maps are correct shape
        assert solver.D_map.shape == (solver.nz, solver.nr, solver.ng)
        assert solver.sigma_t_map.shape == (solver.nz, solver.nr, solver.ng)
        assert solver.sigma_a_map.shape == (solver.nz, solver.nr, solver.ng)
        assert solver.nu_sigma_f_map.shape == (solver.nz, solver.nr, solver.ng)

        # Check that values are positive
        assert np.all(solver.D_map >= 0)
        assert np.all(solver.sigma_t_map >= 0)

    def test_update_fission_source(self, solver):
        """Test fission source update."""
        # Set up flux
        solver.flux = np.ones((solver.nz, solver.nr, solver.ng))
        solver._update_xs_maps()

        # Update fission source
        k_eff = 1.0
        solver._update_fission_source(k_eff)

        # Check source shape and values
        assert solver.source.shape == (solver.nz, solver.nr, solver.ng)
        assert np.all(solver.source >= 0)

    def test_update_scattering_source(self, solver):
        """Test scattering source update."""
        # Set up flux
        solver.flux = np.ones((solver.nz, solver.nr, solver.ng))
        solver._update_xs_maps()

        # Update scattering source for group 0
        solver._update_scattering_source(0)

        # Source should be updated
        assert solver.source is not None


class TestArnoldiMethod:
    """Test Arnoldi eigenvalue method."""

    def test_arnoldi_not_implemented(self, solver):
        """Test that Arnoldi method raises NotImplementedError."""
        # Change to Arnoldi method
        solver.options.eigen_method = "arnoldi"

        with pytest.raises(NotImplementedError):
            solver._arnoldi_method()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_flux_before_solve(self, solver):
        """Test that methods fail gracefully before solve."""
        # Try to compute power before solving
        with pytest.raises(RuntimeError):
            solver.compute_power_distribution(1e6)

    def test_zero_absorption(self, simple_geometry, solver_options):
        """Test handling of edge case with very low absorption."""
        # Create XS with very low absorption (edge case)
        xs_low_absorption = CrossSectionData(
            n_groups=2,
            n_materials=1,
            sigma_t=np.array([[0.5, 0.8]]),
            sigma_a=np.array([[1e-10, 1e-10]]),  # Very low
            sigma_f=np.array([[0.0, 0.0]]),  # No fission
            nu_sigma_f=np.array([[0.0, 0.0]]),
            sigma_s=np.array([[[0.49, 0.01], [0.0, 0.79]]]),
            chi=np.array([[1.0, 0.0]]),
            D=np.array([[1.5, 0.4]]),
        )

        solver = MultiGroupDiffusion(simple_geometry, xs_low_absorption, solver_options)

        # May raise RuntimeError or produce very large k_eff
        try:
            k_eff, flux = solver.solve_steady_state()
            assert np.isfinite(k_eff)
        except RuntimeError:
            # Expected for this edge case
            pass


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
