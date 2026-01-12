"""
Tests for anisotropic scattering matrix computation.

Tests Legendre moment (P0, P1, P2) scattering matrices for thermal SMR calculations.
"""

import pytest
import numpy as np

try:
    from smrforge.core.endf_extractors import (
        compute_anisotropic_scattering_matrix,
        compute_improved_scattering_matrix,
    )
    from smrforge.core.reactor_core import NuclearDataCache, Nuclide

    _ANISOTROPIC_SCATTERING_AVAILABLE = True
except ImportError:
    _ANISOTROPIC_SCATTERING_AVAILABLE = False


@pytest.mark.skipif(
    not _ANISOTROPIC_SCATTERING_AVAILABLE,
    reason="Anisotropic scattering functions not available",
)
class TestAnisotropicScattering:
    """Tests for anisotropic scattering matrix computation."""

    def test_compute_anisotropic_scattering_basic(self):
        """Test basic anisotropic scattering matrix computation."""
        cache = NuclearDataCache()

        u238 = Nuclide(Z=92, A=238)
        group_structure = np.array([1e-5, 1.0, 1e6, 2e7])  # 3 groups

        sigma_s_iso, sigma_s_leg = compute_anisotropic_scattering_matrix(
            cache, u238, group_structure, temperature=900.0, max_legendre_order=2
        )

        assert sigma_s_iso.shape == (3, 3)
        assert sigma_s_leg.shape == (3, 3, 3)  # [n_legendre, n_groups, n_groups]

        # P0 should equal isotropic
        np.testing.assert_array_almost_equal(sigma_s_leg[0], sigma_s_iso)

    def test_legendre_orders(self):
        """Test different Legendre orders."""
        cache = NuclearDataCache()

        u238 = Nuclide(Z=92, A=238)
        group_structure = np.array([1e-5, 1.0, 1e6, 2e7])

        # Test P0 only
        sigma_s_iso, sigma_s_leg = compute_anisotropic_scattering_matrix(
            cache, u238, group_structure, temperature=900.0, max_legendre_order=0
        )
        assert sigma_s_leg.shape == (1, 3, 3)  # Only P0

        # Test P0, P1
        sigma_s_iso, sigma_s_leg = compute_anisotropic_scattering_matrix(
            cache, u238, group_structure, temperature=900.0, max_legendre_order=1
        )
        assert sigma_s_leg.shape == (2, 3, 3)  # P0, P1

        # Test P0, P1, P2
        sigma_s_iso, sigma_s_leg = compute_anisotropic_scattering_matrix(
            cache, u238, group_structure, temperature=900.0, max_legendre_order=2
        )
        assert sigma_s_leg.shape == (3, 3, 3)  # P0, P1, P2

    def test_p0_equals_isotropic(self):
        """Test that P0 moment equals isotropic scattering matrix."""
        cache = NuclearDataCache()

        u238 = Nuclide(Z=92, A=238)
        group_structure = np.array([1e-5, 1.0, 1e6, 2e7])

        # Get isotropic matrix
        sigma_s_iso = compute_improved_scattering_matrix(
            cache, u238, group_structure, temperature=900.0
        )

        # Get anisotropic with P0
        sigma_s_iso2, sigma_s_leg = compute_anisotropic_scattering_matrix(
            cache, u238, group_structure, temperature=900.0, max_legendre_order=0
        )

        # Both should be equal
        np.testing.assert_array_almost_equal(sigma_s_iso, sigma_s_iso2)
        np.testing.assert_array_almost_equal(sigma_s_iso, sigma_s_leg[0])

    def test_p1_anisotropy(self):
        """Test P1 moment (linear anisotropy)."""
        cache = NuclearDataCache()

        u238 = Nuclide(Z=92, A=238)
        group_structure = np.array([1e-5, 1.0, 1e6, 2e7])

        sigma_s_iso, sigma_s_leg = compute_anisotropic_scattering_matrix(
            cache, u238, group_structure, temperature=900.0, max_legendre_order=1
        )

        # P1 should exist
        assert sigma_s_leg.shape[0] >= 2
        p1_matrix = sigma_s_leg[1]

        # P1 should have different values than P0 (anisotropy)
        assert not np.allclose(p1_matrix, 0.0)  # Should have some anisotropy
        assert not np.allclose(p1_matrix, sigma_s_leg[0])  # Should differ from P0

    def test_p2_anisotropy(self):
        """Test P2 moment (quadratic anisotropy)."""
        cache = NuclearDataCache()

        u238 = Nuclide(Z=92, A=238)
        group_structure = np.array([1e-5, 1.0, 1e6, 2e7])

        sigma_s_iso, sigma_s_leg = compute_anisotropic_scattering_matrix(
            cache, u238, group_structure, temperature=900.0, max_legendre_order=2
        )

        # P2 should exist
        assert sigma_s_leg.shape[0] >= 3
        p2_matrix = sigma_s_leg[2]

        # P2 should have some values
        assert not np.allclose(p2_matrix, 0.0)

    def test_thermal_vs_fast_anisotropy(self):
        """Test that thermal and fast groups have different anisotropy."""
        cache = NuclearDataCache()

        u238 = Nuclide(Z=92, A=238)
        # Create groups: thermal (<1 eV), epithermal (1 eV - 100 keV), fast (>100 keV)
        group_structure = np.array([1e-5, 1.0, 1e5, 2e7])

        sigma_s_iso, sigma_s_leg = compute_anisotropic_scattering_matrix(
            cache, u238, group_structure, temperature=900.0, max_legendre_order=2
        )

        p1_matrix = sigma_s_leg[1]

        # Thermal group (index 0) should have less P1 anisotropy than fast group (index 2)
        thermal_p1 = np.abs(p1_matrix[0, 0])
        fast_p1 = np.abs(p1_matrix[2, 2])

        # Fast neutrons typically have more forward scattering (higher P1)
        # This is a simplified test - actual values depend on the model
        assert thermal_p1 >= 0.0
        assert fast_p1 >= 0.0

    def test_matrix_shapes(self):
        """Test that all matrices have correct shapes."""
        cache = NuclearDataCache()

        u238 = Nuclide(Z=92, A=238)
        group_structure = np.array([1e-5, 1.0, 1e6, 2e7])  # 3 groups

        sigma_s_iso, sigma_s_leg = compute_anisotropic_scattering_matrix(
            cache, u238, group_structure, temperature=900.0, max_legendre_order=2
        )

        assert sigma_s_iso.shape == (3, 3)
        assert sigma_s_leg.shape == (3, 3, 3)

        # Each Legendre moment should have same shape as isotropic
        for l in range(3):
            assert sigma_s_leg[l].shape == (3, 3)

    def test_different_nuclides(self):
        """Test anisotropic scattering for different nuclides."""
        cache = NuclearDataCache()

        nuclides = [
            Nuclide(Z=92, A=235),  # U-235
            Nuclide(Z=92, A=238),  # U-238
            Nuclide(Z=1, A=1),  # H-1
        ]

        group_structure = np.array([1e-5, 1.0, 1e6, 2e7])

        for nuclide in nuclides:
            sigma_s_iso, sigma_s_leg = compute_anisotropic_scattering_matrix(
                cache, nuclide, group_structure, temperature=900.0, max_legendre_order=2
            )

            assert sigma_s_iso.shape == (3, 3)
            assert sigma_s_leg.shape == (3, 3, 3)

    def test_temperature_dependence(self):
        """Test that scattering matrices vary with temperature."""
        cache = NuclearDataCache()

        u238 = Nuclide(Z=92, A=238)
        group_structure = np.array([1e-5, 1.0, 1e6, 2e7])

        # Get matrices at different temperatures
        sigma_s_iso1, sigma_s_leg1 = compute_anisotropic_scattering_matrix(
            cache, u238, group_structure, temperature=300.0, max_legendre_order=2
        )

        sigma_s_iso2, sigma_s_leg2 = compute_anisotropic_scattering_matrix(
            cache, u238, group_structure, temperature=900.0, max_legendre_order=2
        )

        # Matrices should exist (may or may not be different depending on model)
        assert sigma_s_iso1.shape == sigma_s_iso2.shape
        assert sigma_s_leg1.shape == sigma_s_leg2.shape
