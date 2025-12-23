"""
Integration tests for SMRForge - test complete workflows.
"""

from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.integration


class TestCompleteWorkflow:
    """Test complete reactor analysis workflows."""

    def test_basic_neutronics_workflow(self, solver):
        """Test basic neutronics workflow: solve -> power distribution."""
        # Solve eigenvalue problem
        k_eff, flux = solver.solve_steady_state()

        # Verify solution
        assert 0.5 < k_eff < 2.0
        assert flux is not None
        assert flux.shape == (solver.nz, solver.nr, solver.ng)

        # Compute power distribution
        total_power = 10e6  # 10 MW
        power = solver.compute_power_distribution(total_power)

        # Verify power distribution
        assert power.shape == (solver.nz, solver.nr)
        assert np.all(power >= 0)

        # Check power conservation
        volumes = solver._cell_volumes()
        total_power_computed = np.sum(power * volumes)
        assert np.isclose(total_power_computed, total_power, rtol=1e-3)

    def test_reactivity_coefficients_workflow(self, solved_solver):
        """Test reactivity coefficients computation."""
        # Need a solved solver
        reactivity_coeffs = solved_solver.compute_reactivity_coefficients(
            temperature_range=(900.0, 1100.0), n_points=3
        )

        assert reactivity_coeffs is not None
        assert "doppler" in reactivity_coeffs
        assert np.isfinite(reactivity_coeffs["doppler"])

    def test_multiple_mesh_sizes(self, simple_xs_data, solver_options):
        """Test that workflow works with different mesh sizes."""
        from tests.test_utilities import SimpleGeometry

        mesh_sizes = [
            (6, 11),  # Small
            (11, 21),  # Medium
            (21, 41),  # Large
        ]

        results = []
        for nr, nz in mesh_sizes:
            geometry = SimpleGeometry()
            geometry.radial_mesh = np.linspace(0, 100, nr)
            geometry.axial_mesh = np.linspace(0, 400, nz)

            from smrforge.neutronics.solver import MultiGroupDiffusion

            solver = MultiGroupDiffusion(geometry, simple_xs_data, solver_options)
            k_eff, flux = solver.solve_steady_state()

            results.append({"mesh": (nr, nz), "k_eff": k_eff, "flux_shape": flux.shape})

        # All should converge
        assert len(results) == len(mesh_sizes)
        assert all(0.5 < r["k_eff"] < 2.0 for r in results)

    def test_different_group_structures(self, simple_geometry, solver_options):
        """Test workflow with different number of energy groups."""
        from smrforge.neutronics.solver import MultiGroupDiffusion
        from smrforge.validation.models import CrossSectionData
        from tests.test_utilities import create_test_xs_data

        n_groups_list = [2, 4]

        for n_groups in n_groups_list:
            xs_dict = create_test_xs_data(n_groups=n_groups, n_materials=2)
            xs_data = CrossSectionData(n_groups=n_groups, n_materials=2, **xs_dict)

            solver = MultiGroupDiffusion(simple_geometry, xs_data, solver_options)
            k_eff, flux = solver.solve_steady_state()

            assert np.isfinite(k_eff)
            assert flux.shape == (solver.nz, solver.nr, n_groups)

    @pytest.mark.slow
    def test_convergence_study(self, simple_xs_data, tight_solver_options):
        """Test convergence with different tolerances."""
        from smrforge.neutronics.solver import MultiGroupDiffusion
        from tests.test_utilities import SimpleGeometry

        tolerances = [1e-3, 1e-5, 1e-7]
        results = []

        for tol in tolerances:
            options = tight_solver_options.model_copy()
            options.tolerance = tol

            geometry = SimpleGeometry()
            solver = MultiGroupDiffusion(geometry, simple_xs_data, options)
            k_eff, flux = solver.solve_steady_state()

            results.append({"tolerance": tol, "k_eff": k_eff})

        # k_eff should be similar across tolerances (within reasonable range)
        k_eff_values = [r["k_eff"] for r in results]
        k_eff_range = max(k_eff_values) - min(k_eff_values)
        assert k_eff_range < 0.01, "k_eff should converge with tighter tolerance"


class TestValidationIntegration:
    """Test integration with validation framework."""

    def test_pydantic_validation_in_workflow(self, sample_reactor_spec):
        """Test that Pydantic validation works in complete workflow."""
        # Spec should be valid
        assert sample_reactor_spec.name == "Test-Reactor"
        assert sample_reactor_spec.power_thermal == 10e6

        # Try to modify with invalid value
        with pytest.raises(Exception):  # Pydantic validation error
            sample_reactor_spec.power_thermal = -1000


class TestPresetIntegration:
    """Test integration with preset reactor designs."""

    def test_preset_design_validation(self):
        """Test that preset designs validate correctly."""
        try:
            from smrforge.presets.htgr import ValarAtomicsReactor

            reactor = ValarAtomicsReactor()
            assert reactor.spec.name == "Valar-10"
            assert reactor.spec.power_thermal == 10e6
        except ImportError:
            pytest.skip("Preset designs not available")


class TestErrorHandling:
    """Test error handling in workflows."""

    def test_workflow_handles_invalid_inputs(self, simple_geometry, solver_options):
        """Test that workflow handles invalid inputs gracefully."""
        from smrforge.validation.models import CrossSectionData

        # Invalid XS data (sigma_a > sigma_t)
        invalid_xs = CrossSectionData(
            n_groups=2,
            n_materials=1,
            sigma_t=np.array([[0.5, 0.8]]),
            sigma_a=np.array([[0.6, 0.9]]),  # Invalid
            sigma_f=np.array([[0.05, 0.15]]),
            nu_sigma_f=np.array([[0.125, 0.375]]),
            sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
            chi=np.array([[1.0, 0.0]]),
            D=np.array([[1.5, 0.4]]),
        )

        from smrforge.neutronics.solver import MultiGroupDiffusion

        with pytest.raises((ValueError, AssertionError)):
            solver = MultiGroupDiffusion(simple_geometry, invalid_xs, solver_options)

    def test_solver_fails_gracefully_on_non_convergence(
        self, simple_geometry, simple_xs_data
    ):
        """Test that solver fails gracefully when not converging."""
        from smrforge.neutronics.solver import MultiGroupDiffusion
        from smrforge.validation.models import SolverOptions

        # Impossible tolerance
        options = SolverOptions(
            max_iterations=5,  # Very few iterations
            tolerance=1e-15,  # Very tight tolerance
            verbose=False,
        )

        solver = MultiGroupDiffusion(simple_geometry, simple_xs_data, options)

        with pytest.raises(RuntimeError, match="Failed to converge"):
            solver.solve_steady_state()
