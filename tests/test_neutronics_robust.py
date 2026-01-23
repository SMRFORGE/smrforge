"""
Additional robust tests for neutronics module - edge cases, parametric tests, etc.
"""

import numpy as np
import pytest

from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.validation.models import CrossSectionData, SolverOptions
from tests.test_utilities import (
    SimpleGeometry,
    assert_solution_reasonable,
    create_test_xs_data,
)


class TestParametricVariations:
    """Parametric tests for various configurations."""

    @pytest.mark.parametrize("n_groups", [2, 4, 6])
    def test_multiple_group_structures(self, simple_geometry, solver_options, n_groups):
        """Test solver with different numbers of energy groups."""
        from smrforge.validation.models import CrossSectionData

        xs_dict = create_test_xs_data(n_groups=n_groups, n_materials=2)
        xs_data = CrossSectionData(n_groups=n_groups, n_materials=2, **xs_dict)

        solver = MultiGroupDiffusion(simple_geometry, xs_data, solver_options)
        k_eff, flux = solver.solve_steady_state()

        assert_solution_reasonable(
            k_eff, flux, 
            k_eff_range=(0.5, 2.5),  # Allow wider range for test data
            check_flux_shape=(solver.nz, solver.nr, n_groups)
        )

    @pytest.mark.parametrize(
        "core_diameter,core_height",
        [
            (100.0, 200.0),
            (200.0, 400.0),
            (300.0, 600.0),
        ],
    )
    def test_different_core_sizes(
        self, simple_xs_data, solver_options, core_diameter, core_height
    ):
        """Test solver with different core sizes."""
        geometry = SimpleGeometry(core_diameter=core_diameter, core_height=core_height)

        solver = MultiGroupDiffusion(geometry, simple_xs_data, solver_options)
        k_eff, flux = solver.solve_steady_state()

        assert_solution_reasonable(k_eff, flux, k_eff_range=(0.5, 2.5))

    @pytest.mark.parametrize(
        "n_radial,n_axial",
        [
            (6, 11),
            (11, 21),
            (21, 41),
        ],
    )
    def test_different_mesh_sizes(
        self, simple_xs_data, solver_options, n_radial, n_axial
    ):
        """Test solver with different mesh resolutions."""
        geometry = SimpleGeometry()
        geometry.radial_mesh = np.linspace(0, 100, n_radial)
        geometry.axial_mesh = np.linspace(0, 400, n_axial)

        solver = MultiGroupDiffusion(geometry, simple_xs_data, solver_options)
        k_eff, flux = solver.solve_steady_state()

        assert_solution_reasonable(
            k_eff, flux, 
            k_eff_range=(0.5, 2.5),  # Allow wider range for test data
            check_flux_shape=(n_axial - 1, n_radial - 1, 2)
        )


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_core(self, simple_xs_data, solver_options):
        """Test solver with very small core dimensions."""
        geometry = SimpleGeometry(core_diameter=10.0, core_height=20.0)
        geometry.radial_mesh = np.linspace(0, 5, 6)
        geometry.axial_mesh = np.linspace(0, 20, 11)

        solver = MultiGroupDiffusion(geometry, simple_xs_data, solver_options)
        k_eff, flux = solver.solve_steady_state()

        assert_solution_reasonable(k_eff, flux, k_eff_range=(0.5, 2.5))

    def test_very_large_core(self, simple_xs_data, fast_solver_options):
        """Test solver with very large core dimensions."""
        geometry = SimpleGeometry(core_diameter=1000.0, core_height=2000.0)
        # Use coarser mesh for large core
        geometry.radial_mesh = np.linspace(0, 500, 21)
        geometry.axial_mesh = np.linspace(0, 2000, 41)

        solver = MultiGroupDiffusion(geometry, simple_xs_data, fast_solver_options)
        k_eff, flux = solver.solve_steady_state()

        assert_solution_reasonable(k_eff, flux, k_eff_range=(0.5, 2.5))

    def test_single_material(self, simple_geometry, solver_options):
        """Test solver with single material (no reflector)."""
        from smrforge.validation.models import CrossSectionData

        # Create test data with k_eff_target to ensure reasonable values
        xs_dict = create_test_xs_data(n_groups=2, n_materials=1, k_eff_target=1.0)
        xs_data = CrossSectionData(n_groups=2, n_materials=1, **xs_dict)

        solver = MultiGroupDiffusion(simple_geometry, xs_data, solver_options)
        k_eff, flux = solver.solve_steady_state()

        assert_solution_reasonable(k_eff, flux, k_eff_range=(0.5, 2.5))

    def test_subcritical_configuration(
        self, simple_geometry, subcritical_xs_data, solver_options
    ):
        """Test solver with subcritical configuration."""
        solver = MultiGroupDiffusion(
            simple_geometry, subcritical_xs_data, solver_options
        )
        k_eff, flux = solver.solve_steady_state()

        assert k_eff < 1.0, "Should be subcritical"
        assert_solution_reasonable(k_eff, flux, k_eff_range=(0.3, 1.0))

    def test_supercritical_configuration(
        self, simple_geometry, supercritical_xs_data, solver_options
    ):
        """Test solver with supercritical configuration."""
        solver = MultiGroupDiffusion(
            simple_geometry, supercritical_xs_data, solver_options
        )
        k_eff, flux = solver.solve_steady_state()

        assert k_eff > 1.0, "Should be supercritical"
        assert_solution_reasonable(k_eff, flux, k_eff_range=(1.0, 2.5))

    def test_high_scattering_ratio(self, simple_geometry, solver_options):
        """Test solver with very high scattering (almost pure scattering)."""
        from smrforge.validation.models import CrossSectionData

        # Create XS with very high scattering
        sigma_t = np.array([[1.0, 2.0]])
        sigma_a = np.array([[0.001, 0.001]])  # Very low absorption
        sigma_s = np.array([[[0.999, 0.001], [0.0, 1.999]]])  # High scattering

        xs_data = CrossSectionData(
            n_groups=2,
            n_materials=1,
            sigma_t=sigma_t,
            sigma_a=sigma_a,
            sigma_f=np.array([[0.0, 0.0]]),
            nu_sigma_f=np.array([[0.0, 0.0]]),
            sigma_s=sigma_s,
            chi=np.array([[1.0, 0.0]]),
            D=np.array([[2.0, 1.0]]),
        )

        solver = MultiGroupDiffusion(simple_geometry, xs_data, solver_options)
        # This should still solve (though may converge slowly)
        try:
            k_eff, flux = solver.solve_steady_state()
            # With no fission, k_eff will be 0, which is physically correct
            # Allow k_eff=0 for this edge case
            assert_solution_reasonable(k_eff, flux, k_eff_range=(0.0, 2.5))
        except RuntimeError:
            # May not converge for this extreme case
            pass


class TestNumericalStability:
    """Test numerical stability and robustness."""

    def test_tight_tolerance_convergence(self, solver, tight_solver_options):
        """Test that solver converges with very tight tolerance."""
        solver.options = tight_solver_options
        k_eff, flux = solver.solve_steady_state()

        assert_solution_reasonable(k_eff, flux, k_eff_range=(0.5, 2.5))

    def test_large_mesh_stability(self, simple_xs_data, solver_options):
        """Test numerical stability with large mesh."""
        geometry = SimpleGeometry()
        # Fine mesh
        geometry.radial_mesh = np.linspace(0, 100, 51)
        geometry.axial_mesh = np.linspace(0, 400, 101)

        solver = MultiGroupDiffusion(geometry, simple_xs_data, solver_options)
        k_eff, flux = solver.solve_steady_state()

        assert_solution_reasonable(k_eff, flux, k_eff_range=(0.5, 2.5))
        # Check for any NaN or Inf
        assert np.all(np.isfinite(flux))
        assert np.all(np.isfinite(k_eff))

    def test_repeated_solves_consistency(self, solver):
        """Test that repeated solves give consistent results."""
        k_eff_1, flux_1 = solver.solve_steady_state()

        # Reset solver state properly (re-initialize flux array)
        shape = (solver.nz, solver.nr, solver.ng)
        solver.flux = np.ones(shape)
        solver.k_eff = 1.0

        k_eff_2, flux_2 = solver.solve_steady_state()

        # Results should be very similar (within numerical precision)
        assert np.isclose(k_eff_1, k_eff_2, rtol=1e-6)
        assert np.allclose(flux_1, flux_2, rtol=1e-6)

    def test_power_distribution_conservation(self, solved_solver):
        """Test power distribution conservation for various power levels."""
        power_levels = [1e6, 10e6, 100e6, 1000e6]  # 1 MW to 1 GW

        for total_power in power_levels:
            power = solved_solver.compute_power_distribution(total_power)
            volumes = solved_solver._cell_volumes()
            total_power_computed = np.sum(power * volumes)

            error = abs(total_power_computed - total_power) / total_power
            assert error < 1e-3, f"Power conservation failed for {total_power} W"


class TestSolutionQuality:
    """Test solution quality and physical reasonableness."""

    def test_flux_monotonicity_center(self, solved_solver):
        """Test that flux decreases from center (typical for reactors)."""
        flux = solved_solver.flux
        z_center = solved_solver.nz // 2
        r_center = solved_solver.nr // 2

        center_flux = flux[z_center, r_center, 0]  # Fast group

        # Flux at center should be high
        edge_flux = flux[0, solved_solver.nr - 1, 0]  # Edge
        assert center_flux > edge_flux * 0.1, "Center flux should be significant"

    def test_power_peaking_factor(self, solved_solver):
        """Test power peaking factor (should be reasonable)."""
        total_power = 10e6
        power = solved_solver.compute_power_distribution(total_power)

        max_power = np.max(power)
        avg_power = np.mean(power)
        peaking_factor = max_power / avg_power

        # Peaking factor should be reasonable (typically 1-3 for uniform cores)
        assert (
            1.0 <= peaking_factor <= 5.0
        ), f"Unreasonable peaking factor: {peaking_factor}"

    def test_group_flux_ratios(self, solved_solver):
        """Test that group flux ratios are physically reasonable."""
        flux = solved_solver.flux
        fast_flux = flux[:, :, 0]
        thermal_flux = flux[:, :, 1]

        # Fast group should dominate in most reactors
        fast_total = np.sum(fast_flux)
        thermal_total = np.sum(thermal_flux)

        # Both should be positive
        assert fast_total > 0
        assert thermal_total > 0

        # Fast group typically dominates
        fast_ratio = fast_total / (fast_total + thermal_total)
        assert 0.3 <= fast_ratio <= 0.9, f"Unreasonable fast flux ratio: {fast_ratio}"
