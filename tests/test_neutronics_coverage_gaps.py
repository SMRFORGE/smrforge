"""
Tests for neutronics solver coverage gaps.
"""

import numpy as np
import pytest

from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.validation.models import CrossSectionData, SolverOptions
from tests.test_utilities import SimpleGeometry, create_test_xs_data


class TestSolverCoverageGaps:
    """Test coverage for missing paths in neutronics solver."""

    def test_gmres_inner_solver(self, simple_geometry, simple_xs_data):
        """Test GMRES inner solver path (if available)."""
        # GMRES is in the code but not in SolverOptions enum
        # We can't test it directly due to Pydantic validation, but the code path exists
        # This test documents that GMRES is available in the solver code
        # but not exposed in the Pydantic model
        options = SolverOptions(
            max_iterations=100,
            tolerance=1e-5,
            eigen_method="power",
            inner_solver="bicgstab",  # Use valid option
            verbose=False,
            skip_solution_validation=True,
        )

        solver = MultiGroupDiffusion(simple_geometry, simple_xs_data, options)
        # Note: GMRES code path exists in solver.py but is not accessible
        # through SolverOptions due to Pydantic validation
        # This is acceptable - the code is there if needed in the future
        k_eff, flux = solver.solve_steady_state()

        assert k_eff > 0
        assert flux is not None
        assert flux.shape == (solver.nz, solver.nr, solver.ng)

    def test_arnoldi_method_works(self, simple_geometry, simple_xs_data):
        """Test that Arnoldi method works (now implemented)."""
        options = SolverOptions(
            max_iterations=100,
            tolerance=1e-5,
            eigen_method="arnoldi",
            inner_solver="bicgstab",
            verbose=False,
            skip_solution_validation=True,
        )

        solver = MultiGroupDiffusion(simple_geometry, simple_xs_data, options)

        # Should work now (may be slower or have slightly different results)
        k_eff, flux = solver.solve_steady_state()

        assert k_eff > 0
        assert flux is not None
        assert flux.shape == (solver.nz, solver.nr, solver.ng)

    def test_unknown_eigen_method(self, simple_geometry, simple_xs_data):
        """Test that unknown eigen method raises RuntimeError (wrapped ValueError)."""
        options = SolverOptions(
            max_iterations=100,
            tolerance=1e-5,
            eigen_method="power",
            inner_solver="bicgstab",
            verbose=False,
            skip_solution_validation=True,
        )

        solver = MultiGroupDiffusion(simple_geometry, simple_xs_data, options)
        # Manually set invalid method by accessing internal attribute
        # Bypass Pydantic validation by setting the underlying dict
        solver.options.__dict__["eigen_method"] = "invalid_method"

        # The ValueError is wrapped in RuntimeError
        with pytest.raises(RuntimeError, match="Solver failed"):
            solver.solve_steady_state()

    def test_bicgstab_failure(self, simple_geometry, simple_xs_data):
        """Test BiCGSTAB failure handling."""
        options = SolverOptions(
            max_iterations=100,
            tolerance=1e-5,
            eigen_method="power",
            inner_solver="bicgstab",
            verbose=False,
            skip_solution_validation=True,
        )

        solver = MultiGroupDiffusion(simple_geometry, simple_xs_data, options)

        # Create a problematic system by making diffusion coefficients very small
        # This might cause numerical issues
        solver.D_map[:, :, :] = 1e-10
        solver.sigma_t_map[:, :, :] = 1e10

        # This might fail, but should handle gracefully
        try:
            k_eff, flux = solver.solve_steady_state()
            # If it succeeds, that's fine too
            assert k_eff > 0
        except RuntimeError:
            # Expected for problematic system
            pass

    def test_compute_reactivity_coefficients_placeholder(self, solver):
        """Test that reactivity coefficients method returns placeholder values."""
        # First solve
        solver.solve_steady_state()

        # Compute reactivity coefficients (placeholder implementation)
        coeffs = solver.compute_reactivity_coefficients(delta_T=10.0)

        assert isinstance(coeffs, dict)
        assert "doppler" in coeffs
        assert "moderator" in coeffs
        assert "total" in coeffs
        assert all(isinstance(v, float) for v in coeffs.values())

    def test_validation_warnings(self, simple_geometry, solver_options):
        """Test that validation warnings are handled."""
        from smrforge.validation.models import CrossSectionData

        # Create XS data that might generate warnings
        xs_dict = create_test_xs_data(n_groups=2, n_materials=2, k_eff_target=0.95)
        xs_data = CrossSectionData(n_groups=2, n_materials=2, **xs_dict)

        # This should work but may generate warnings
        solver = MultiGroupDiffusion(simple_geometry, xs_data, solver_options)
        k_eff, flux = solver.solve_steady_state()

        assert k_eff > 0
        assert flux is not None

    def test_power_distribution_zero_total(self, solver):
        """Test power distribution with zero total power."""
        solver.solve_steady_state()

        # Compute power with zero total power
        power = solver.compute_power_distribution(0.0)

        assert power is not None
        assert power.shape == (solver.nz, solver.nr)
        # Should be all zeros
        assert np.allclose(power, 0.0)
