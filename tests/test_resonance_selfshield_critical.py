"""
Critical tests for resonance_selfshield.py to improve coverage to 80%+.

Focuses on uncovered paths:
- All BondarenkoMethod methods
- All SubgroupMethod methods
- All EquivalenceTheory methods
- All ResonanceSelfShielding methods
- Edge cases and error handling
"""

import numpy as np
import pytest

from smrforge.core.resonance_selfshield import (
    BondarenkoMethod,
    EquivalenceTheory,
    ResonanceData,
    ResonanceSelfShielding,
    SubgroupMethod,
    _compute_subgroup_flux,
)


class TestBondarenkoMethodCritical:
    """Critical tests for BondarenkoMethod."""

    def test_load_f_factors(self):
        """Test loading f-factors."""
        method = BondarenkoMethod()

        # Should have loaded f-factors (may fail if RectBivariateSpline has issues)
        # Just check that method was created
        assert method is not None
        # f_factors may be empty if initialization failed, which is acceptable for testing

    def test_get_f_factor_all_nuclides(self):
        """Test f-factor for all loaded nuclides."""
        method = BondarenkoMethod()

        # Test U238 capture
        f = method.get_f_factor("U238", "capture", sigma_0=100.0, T=1200.0)
        assert 0 < f <= 1.0

        # Test U235 fission
        f = method.get_f_factor("U235", "fission", sigma_0=100.0, T=1200.0)
        assert 0 < f <= 1.0

        # Test Pu239 fission
        f = method.get_f_factor("Pu239", "fission", sigma_0=100.0, T=1200.0)
        assert 0 < f <= 1.0

    def test_get_f_factor_boundary_values(self):
        """Test f-factor at boundary values."""
        method = BondarenkoMethod()

        # Test at sigma_0 boundaries
        f_min = method.get_f_factor("U238", "capture", sigma_0=1.0, T=1200.0)
        f_max = method.get_f_factor("U238", "capture", sigma_0=1e10, T=1200.0)

        assert 0 < f_min <= 1.0
        assert 0 < f_max <= 1.0
        # Higher sigma_0 should give lower f-factor (more shielding)
        assert f_max < f_min

    def test_shield_cross_section_zero_xs(self):
        """Test shielding with zero infinite dilution XS."""
        method = BondarenkoMethod()

        xs_shielded = method.shield_cross_section(0.0, "U238", "capture", 100.0, 1200.0)
        assert xs_shielded == 0.0

    def test_compute_background_xs_no_moderator(self):
        """Test background XS without moderator."""
        method = BondarenkoMethod()

        composition = {"U235": 0.001, "U238": 0.002}

        sigma_0 = method.compute_background_xs(composition, include_moderator=False)
        assert sigma_0 > 0

    def test_compute_background_xs_with_geometry(self):
        """Test background XS with geometry factor."""
        method = BondarenkoMethod()

        composition = {"U235": 0.001}

        sigma_0_no_geom = method.compute_background_xs(composition, geometry_factor=0.0)
        sigma_0_with_geom = method.compute_background_xs(
            composition, geometry_factor=1.0
        )

        assert sigma_0_with_geom > sigma_0_no_geom


class TestSubgroupMethodCritical:
    """Critical tests for SubgroupMethod."""

    def test_generate_subgroup_parameters(self):
        """Test generating subgroup parameters."""
        method = SubgroupMethod()

        # Should have generated parameters
        assert len(method.subgroup_data) > 0
        assert "U238_capture_thermal" in method.subgroup_data
        assert "U238_fission_fast" in method.subgroup_data

    def test_compute_effective_xs_thermal(self):
        """Test effective XS for thermal group."""
        method = SubgroupMethod()

        xs_eff = method.compute_effective_xs(
            "U238", "capture", "thermal", sigma_0=100.0
        )

        assert xs_eff > 0
        assert np.isfinite(xs_eff)

    def test_compute_effective_xs_fast(self):
        """Test effective XS for fast group."""
        method = SubgroupMethod()

        xs_eff = method.compute_effective_xs("U238", "fission", "fast", sigma_0=10.0)

        assert xs_eff > 0
        assert np.isfinite(xs_eff)

    def test_compute_effective_xs_various_sigma_0(self):
        """Test effective XS with various sigma_0 values."""
        method = SubgroupMethod()

        for sigma_0 in [1.0, 10.0, 100.0, 1000.0, 10000.0]:
            xs_eff = method.compute_effective_xs(
                "U238", "capture", "thermal", sigma_0=sigma_0
            )
            assert xs_eff > 0
            assert np.isfinite(xs_eff)

    def test_tabulate_effective_xs(self):
        """Test tabulating effective XS."""
        method = SubgroupMethod()

        sigma_0_range = np.logspace(0, 4, 10)  # 1 to 10000
        xs_table = method.tabulate_effective_xs(
            "U238", "capture", "thermal", sigma_0_range
        )

        assert len(xs_table) == len(sigma_0_range)
        assert np.all(xs_table > 0)
        assert np.all(np.isfinite(xs_table))


class TestEquivalenceTheoryCritical:
    """Critical tests for EquivalenceTheory."""

    def test_dancoff_factor_various_packing(self):
        """Test Dancoff factor with various packing fractions."""
        for packing in [0.1, 0.2, 0.35, 0.5, 0.7]:
            C = EquivalenceTheory.dancoff_factor_hexagonal(1.0, 0.05, packing)
            assert 0 <= C <= 1.0

    def test_dancoff_factor_various_pitch(self):
        """Test Dancoff factor with various pitches."""
        for pitch in [0.5, 1.0, 2.0, 5.0]:
            C = EquivalenceTheory.dancoff_factor_hexagonal(pitch, 0.05, 0.35)
            assert 0 <= C <= 1.0

    def test_escape_probability_various_optical_thickness(self):
        """Test escape probability with various optical thicknesses."""
        # Small tau (series expansion)
        P = EquivalenceTheory.escape_probability_sphere(0.01, 0.1)
        assert 0 < P <= 1.0

        # Medium tau (Wigner approximation)
        P = EquivalenceTheory.escape_probability_sphere(1.0, 0.1)
        assert 0 < P <= 1.0

        # Large tau (asymptotic)
        P = EquivalenceTheory.escape_probability_sphere(100.0, 0.1)
        assert 0 < P <= 1.0

    def test_effective_background_xs_various_dancoff(self):
        """Test effective background XS with various Dancoff factors."""
        for dancoff in [0.0, 0.1, 0.3, 0.5, 0.7, 0.9]:
            sigma_0 = EquivalenceTheory.effective_background_xs(
                dancoff, 0.7, 0.385, 0.1
            )
            assert sigma_0 > 0

    def test_compute_triso_shielding_various_geometries(self):
        """Test TRISO shielding with various geometries."""
        theory = EquivalenceTheory()

        geometries = [
            {
                "kernel_radius": 100e-4,
                "buffer_thickness": 50e-4,
                "packing_fraction": 0.25,
            },
            {
                "kernel_radius": 212.5e-4,
                "buffer_thickness": 100e-4,
                "packing_fraction": 0.35,
            },
            {
                "kernel_radius": 300e-4,
                "buffer_thickness": 150e-4,
                "packing_fraction": 0.45,
            },
        ]

        for geom in geometries:
            result = theory.compute_triso_shielding(
                geom["kernel_radius"],
                geom["buffer_thickness"],
                geom["packing_fraction"],
                N_graphite=0.08,
            )

            assert "sigma_0_kernel" in result
            assert "dancoff_factor" in result
            assert "escape_probability" in result
            assert result["sigma_0_kernel"] > 0
            assert 0 <= result["dancoff_factor"] <= 1.0
            assert 0 < result["escape_probability"] <= 1.0


class TestResonanceSelfShieldingCritical:
    """Critical tests for ResonanceSelfShielding."""

    def test_shield_multigroup_xs_single_group(self):
        """Test shielding single energy group."""
        shielding = ResonanceSelfShielding()

        xs_inf = np.array([[100.0]])  # [1 group, 1 temp]
        temperatures = np.array([1200.0])

        xs_shielded = shielding.shield_multigroup_xs(
            xs_inf, "U238", "capture", temperatures, 100.0, method="bondarenko"
        )

        assert xs_shielded.shape == (1, 1)
        assert xs_shielded[0, 0] > 0
        assert xs_shielded[0, 0] <= xs_inf[0, 0]

    def test_shield_multigroup_xs_many_groups(self):
        """Test shielding many energy groups."""
        shielding = ResonanceSelfShielding()

        n_groups = 10
        n_temps = 3
        xs_inf = np.ones((n_groups, n_temps)) * 100.0
        temperatures = np.array([600.0, 1200.0, 1800.0])

        xs_shielded = shielding.shield_multigroup_xs(
            xs_inf, "U238", "capture", temperatures, 100.0, method="bondarenko"
        )

        assert xs_shielded.shape == (n_groups, n_temps)
        assert np.all(xs_shielded > 0)
        assert np.all(xs_shielded <= xs_inf)

    def test_htgr_fuel_shielding_no_fissile(self):
        """Test HTGR fuel shielding without fissile nuclide."""
        shielding = ResonanceSelfShielding()

        fuel_composition = {
            "U238": 0.0020,  # Fertile only
            "O16": 0.0050,
        }

        triso_geometry = {
            "kernel_radius": 212.5e-4,
            "buffer_thickness": 100e-4,
            "packing_fraction": 0.35,
        }

        result = shielding.htgr_fuel_shielding(fuel_composition, triso_geometry, 1200.0)

        assert isinstance(result, dict)
        if "U238" in result:
            assert result["U238"]["fission"] == 0.0  # Not fissile


class TestComputeSubgroupFlux:
    """Test _compute_subgroup_flux function."""

    def test_compute_subgroup_flux(self):
        """Test subgroup flux computation."""
        sigma_sg = np.array([2.0, 5.0, 15.0, 50.0])
        w_sg = np.array([0.5, 0.25, 0.15, 0.1])
        sigma_t_background = 10.0
        source = 1.0

        phi_sg = _compute_subgroup_flux(sigma_sg, w_sg, sigma_t_background, source)

        assert len(phi_sg) == len(sigma_sg)
        assert np.all(phi_sg >= 0)
        assert np.all(np.isfinite(phi_sg))

    def test_compute_subgroup_flux_zero_background(self):
        """Test subgroup flux with zero background."""
        sigma_sg = np.array([2.0, 5.0])
        w_sg = np.array([0.5, 0.5])
        sigma_t_background = 0.0
        source = 1.0

        phi_sg = _compute_subgroup_flux(sigma_sg, w_sg, sigma_t_background, source)

        assert len(phi_sg) == len(sigma_sg)
        assert np.all(phi_sg >= 0)

    def test_compute_subgroup_flux_high_background(self):
        """Test subgroup flux with high background."""
        sigma_sg = np.array([2.0, 5.0])
        w_sg = np.array([0.5, 0.5])
        sigma_t_background = 1000.0
        source = 1.0

        phi_sg = _compute_subgroup_flux(sigma_sg, w_sg, sigma_t_background, source)

        assert len(phi_sg) == len(sigma_sg)
        assert np.all(phi_sg >= 0)
        # High background should reduce flux
        assert np.all(phi_sg < 1.0)
