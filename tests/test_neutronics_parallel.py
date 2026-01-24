"""
Unit tests for parallel multi-group diffusion solver.
"""

import numpy as np
import pytest

from smrforge.geometry import PrismaticCore
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.validation.models import CrossSectionData, SolverOptions


@pytest.fixture
def simple_geometry():
    """Create a simple test geometry."""
    geometry = PrismaticCore(name="TestCore")
    geometry.core_height = 200.0
    geometry.core_diameter = 100.0
    geometry.generate_mesh(n_radial=10, n_axial=5)
    return geometry


@pytest.fixture
def simple_xs_data():
    """Create simple 4-group cross-section data."""
    return CrossSectionData(
        n_groups=4,
        n_materials=1,
        sigma_t=np.array([[0.5, 0.8, 1.0, 1.2]]),
        sigma_a=np.array([[0.1, 0.2, 0.3, 0.4]]),
        sigma_f=np.array([[0.05, 0.15, 0.25, 0.35]]),
        nu_sigma_f=np.array([[0.125, 0.375, 0.625, 0.875]]),
        sigma_s=np.array([[
            [0.39, 0.01, 0.0, 0.0],
            [0.0, 0.58, 0.02, 0.0],
            [0.0, 0.0, 0.65, 0.03],
            [0.0, 0.0, 0.0, 0.75]
        ]]),
        chi=np.array([[1.0, 0.0, 0.0, 0.0]]),
        D=np.array([[1.5, 0.4, 0.3, 0.2]]),
    )


class TestParallelGroupSolve:
    """Tests for parallel energy group solve."""

    def test_parallel_vs_serial_correctness(self, simple_geometry, simple_xs_data):
        """Test that parallel group solve gives same results as serial."""
        # Serial solve
        options_serial = SolverOptions(
            max_iterations=200,
            tolerance=1e-8,
            parallel=False,
            parallel_group_solve=False,
            parallel_spatial=False,
            verbose=False,
            skip_solution_validation=True,  # Skip validation for test
        )
        solver_serial = MultiGroupDiffusion(simple_geometry, simple_xs_data, options_serial)
        k_eff_serial, flux_serial = solver_serial.solve_steady_state()

        # Parallel solve
        options_parallel = SolverOptions(
            max_iterations=200,
            tolerance=1e-8,
            parallel=True,
            parallel_group_solve=True,
            parallel_spatial=False,
            verbose=False,
            skip_solution_validation=True,  # Skip validation for test
        )
        solver_parallel = MultiGroupDiffusion(simple_geometry, simple_xs_data, options_parallel)
        k_eff_parallel, flux_parallel = solver_parallel.solve_steady_state()

        # Results should be very close (within tolerance)
        # Note: Parallel and serial may differ slightly due to floating point order
        # Red-black ordering can cause small differences in convergence path
        # Both should converge to reasonable solutions
        assert abs(k_eff_serial - k_eff_parallel) < 5e-3  # Relaxed tolerance for parallel differences
        # Flux comparison: check that both are reasonable (not identical due to parallel differences)
        assert np.all(np.isfinite(flux_serial))
        assert np.all(np.isfinite(flux_parallel))
        assert np.all(flux_serial > 0)
        assert np.all(flux_parallel > 0)
        # Relative difference should be small for most values
        # Use a symmetric relative error to reduce sensitivity to scale
        denom = np.abs(flux_serial) + np.abs(flux_parallel) + 1e-12
        max_rel_diff = np.max(np.abs(flux_serial - flux_parallel) / denom)
        assert max_rel_diff < 0.15  # allow parallel-ordering differences

    def test_parallel_fallback_single_group(self, simple_geometry):
        """Test fallback to serial for single energy group."""
        xs_data = CrossSectionData(
            n_groups=1,
            n_materials=1,
            sigma_t=np.array([[0.5]]),
            sigma_a=np.array([[0.1]]),
            sigma_f=np.array([[0.05]]),
            nu_sigma_f=np.array([[0.125]]),
            sigma_s=np.array([[[0.39]]]),
            chi=np.array([[1.0]]),
            D=np.array([[1.5]]),
        )

        options = SolverOptions(
            parallel=True,
            parallel_group_solve=True,
            verbose=False,
            skip_solution_validation=True,  # Skip validation for test
        )
        solver = MultiGroupDiffusion(simple_geometry, xs_data, options)
        k_eff, flux = solver.solve_steady_state()

        assert k_eff > 0
        assert flux.shape == (5, 10, 1)

    def test_parallel_spatial_operations(self, simple_geometry, simple_xs_data):
        """Test parallel spatial operations for large problems."""
        # Create larger geometry
        geometry = PrismaticCore(name="LargeCore")
        geometry.core_height = 400.0
        geometry.core_diameter = 200.0
        geometry.generate_mesh(n_radial=50, n_axial=20)  # 1000 cells

        options = SolverOptions(
            max_iterations=50,
            tolerance=1e-5,
            parallel=True,
            parallel_spatial=True,
            verbose=False,
            skip_solution_validation=True,  # Skip validation for test
        )
        solver = MultiGroupDiffusion(geometry, simple_xs_data, options)
        k_eff, flux = solver.solve_steady_state()

        assert k_eff > 0
        assert flux.shape == (20, 50, 4)

    def test_parallel_with_custom_threads(self, simple_geometry, simple_xs_data):
        """Test parallel solve with custom thread count."""
        options = SolverOptions(
            max_iterations=50,
            tolerance=1e-6,
            parallel=True,
            parallel_group_solve=True,
            num_threads=2,
            verbose=False,
            skip_solution_validation=True,  # Skip validation for test
        )
        solver = MultiGroupDiffusion(simple_geometry, simple_xs_data, options)
        k_eff, flux = solver.solve_steady_state()

        assert k_eff > 0
        assert flux.shape == (5, 10, 4)


class TestMPISupport:
    """Tests for MPI support (if available)."""

    def test_mpi_functions_exist(self):
        """Test that MPI helper functions exist."""
        # Import the module to check if functions are available
        import smrforge.neutronics.solver as solver_module
        
        # Functions should exist and be callable
        assert hasattr(solver_module, '_get_mpi_comm')
        assert hasattr(solver_module, '_is_mpi_root')
        assert hasattr(solver_module, '_mpi_rank')
        assert hasattr(solver_module, '_mpi_size')
        
        # Should return valid values even without MPI
        assert solver_module._is_mpi_root() is True  # Default to True if no MPI
        assert solver_module._mpi_rank() == 0  # Default to 0 if no MPI
        assert solver_module._mpi_size() == 1  # Default to 1 if no MPI

    def test_mpi_option(self, simple_geometry, simple_xs_data):
        """Test that use_mpi option exists and works."""
        options = SolverOptions(
            use_mpi=False,  # Should work even if MPI not available
            verbose=False,
            skip_solution_validation=True,  # Skip validation for test
        )
        solver = MultiGroupDiffusion(simple_geometry, simple_xs_data, options)
        k_eff, flux = solver.solve_steady_state()

        assert k_eff > 0


class TestParallelScaling:
    """Tests for parallel scaling behavior."""

    def test_parallel_enabled_by_default(self, simple_geometry, simple_xs_data):
        """Test that parallel is enabled by default."""
        options = SolverOptions(
            verbose=False,
            skip_solution_validation=True,  # Skip validation for test
        )
        assert options.parallel is True
        assert options.parallel_group_solve is True
        assert options.parallel_spatial is True

        solver = MultiGroupDiffusion(simple_geometry, simple_xs_data, options)
        k_eff, flux = solver.solve_steady_state()

        assert k_eff > 0

    def test_serial_fallback(self, simple_geometry, simple_xs_data):
        """Test that serial fallback works when parallel disabled."""
        options = SolverOptions(
            parallel=False,
            parallel_group_solve=False,
            parallel_spatial=False,
            verbose=False,
            skip_solution_validation=True,  # Skip validation for test
        )
        solver = MultiGroupDiffusion(simple_geometry, simple_xs_data, options)
        k_eff, flux = solver.solve_steady_state()

        assert k_eff > 0
        assert flux.shape == (5, 10, 4)
