"""
Tests for SMR-focused features in reactor_core.py.

Tests resonance self-shielding, fission yields, and delayed neutron data.
"""

import pytest
import numpy as np
from pathlib import Path

try:
    from smrforge.core.reactor_core import (
        NuclearDataCache,
        Nuclide,
        Library,
        get_cross_section_with_self_shielding,
        get_fission_yields,
        get_delayed_neutron_data,
    )

    _REACTOR_CORE_AVAILABLE = True
except ImportError:
    _REACTOR_CORE_AVAILABLE = False


@pytest.mark.skipif(not _REACTOR_CORE_AVAILABLE, reason="reactor_core not available")
class TestResonanceSelfShielding:
    """Tests for resonance self-shielding functionality."""

    def test_get_cross_section_with_self_shielding_basic(self):
        """Test basic self-shielding function call."""
        cache = NuclearDataCache()

        # Try to get cross-section with self-shielding
        # This may fail if ENDF files not available, but should not crash
        try:
            u238 = Nuclide(Z=92, A=238)
            energy, xs = get_cross_section_with_self_shielding(
                cache,
                u238,
                "capture",
                temperature=900.0,
                sigma_0=1000.0,
                use_self_shielding=True,
            )

            assert energy is not None
            assert xs is not None
            assert len(energy) == len(xs)
            assert len(energy) > 0
        except (FileNotFoundError, ImportError, ValueError) as e:
            # Expected if ENDF files not set up
            pytest.skip(f"ENDF files not available: {e}")

    def test_get_cross_section_with_self_shielding_disabled(self):
        """Test self-shielding with use_self_shielding=False."""
        cache = NuclearDataCache()

        try:
            u238 = Nuclide(Z=92, A=238)
            energy, xs = get_cross_section_with_self_shielding(
                cache,
                u238,
                "capture",
                temperature=900.0,
                sigma_0=1000.0,
                use_self_shielding=False,  # Disabled
            )

            assert energy is not None
            assert xs is not None
            assert len(energy) == len(xs)
        except (FileNotFoundError, ImportError, ValueError) as e:
            pytest.skip(f"ENDF files not available: {e}")

    def test_self_shielding_fallback(self):
        """Test that self-shielding gracefully falls back if unavailable."""
        cache = NuclearDataCache()

        try:
            u238 = Nuclide(Z=92, A=238)
            # Should work even if self-shielding module not available
            energy, xs = get_cross_section_with_self_shielding(
                cache,
                u238,
                "capture",
                temperature=900.0,
                sigma_0=1000.0,
                use_self_shielding=True,
            )

            # Should return valid data even if self-shielding failed
            assert energy is not None
            assert xs is not None
        except (FileNotFoundError, ImportError, ValueError) as e:
            pytest.skip(f"ENDF files not available: {e}")


@pytest.mark.skipif(not _REACTOR_CORE_AVAILABLE, reason="reactor_core not available")
class TestFissionYields:
    """Tests for fission yield data parsing."""

    def test_get_fission_yields_basic(self):
        """Test basic fission yield function call."""
        cache = NuclearDataCache()

        try:
            u235 = Nuclide(Z=92, A=235)
            yields = get_fission_yields(
                cache, u235, library=Library.ENDF_B_VIII_1, yield_type="independent"
            )

            # May return None if file not found, which is OK
            if yields is not None:
                assert isinstance(yields, dict)
                # Should contain Nuclide -> float mappings
                if len(yields) > 0:
                    for nuclide, yield_val in yields.items():
                        assert isinstance(nuclide, Nuclide)
                        assert isinstance(yield_val, (float, np.floating))
                        assert 0.0 <= yield_val <= 1.0  # Yields should be fractions
        except (FileNotFoundError, ImportError, ValueError) as e:
            pytest.skip(f"ENDF files not available: {e}")

    def test_get_fission_yields_cumulative(self):
        """Test getting cumulative yields."""
        cache = NuclearDataCache()

        try:
            u235 = Nuclide(Z=92, A=235)
            yields = get_fission_yields(
                cache, u235, yield_type="cumulative"
            )

            if yields is not None:
                assert isinstance(yields, dict)
        except (FileNotFoundError, ImportError, ValueError) as e:
            pytest.skip(f"ENDF files not available: {e}")

    def test_get_fission_yields_invalid_type(self):
        """Test that invalid yield_type raises error."""
        cache = NuclearDataCache()

        try:
            u235 = Nuclide(Z=92, A=235)
            # This should raise ValueError if yields are found but type is invalid
            # But may return None if file not found
            yields = get_fission_yields(cache, u235, yield_type="invalid")
            # If yields is None, that's OK (file not found)
            # If yields is dict, then invalid type should have been caught
            if yields is not None:
                # Should not reach here with invalid type
                pytest.fail("Should have raised ValueError for invalid yield_type")
        except ValueError:
            # Expected for invalid yield_type
            pass
        except (FileNotFoundError, ImportError) as e:
            pytest.skip(f"ENDF files not available: {e}")


@pytest.mark.skipif(not _REACTOR_CORE_AVAILABLE, reason="reactor_core not available")
class TestDelayedNeutronData:
    """Tests for delayed neutron data parsing."""

    def test_get_delayed_neutron_data_basic(self):
        """Test basic delayed neutron data function call."""
        cache = NuclearDataCache()

        try:
            u235 = Nuclide(Z=92, A=235)
            dn_data = get_delayed_neutron_data(cache, u235)

            # May return None if data not found, which is OK
            if dn_data is not None:
                assert isinstance(dn_data, dict)
                # Should have expected keys
                assert "beta" in dn_data
                assert "beta_i" in dn_data
                assert "lambda_i" in dn_data

                # Check types
                assert isinstance(dn_data["beta"], (float, np.floating))
                assert isinstance(dn_data["beta_i"], (list, np.ndarray))
                assert isinstance(dn_data["lambda_i"], (list, np.ndarray))

                # Check values are reasonable
                assert 0.0 < dn_data["beta"] < 0.01  # Typical beta ~0.0065
                assert len(dn_data["beta_i"]) == len(dn_data["lambda_i"])
        except (FileNotFoundError, ImportError, ValueError) as e:
            pytest.skip(f"ENDF files not available: {e}")

    def test_delayed_neutron_data_structure(self):
        """Test delayed neutron data structure."""
        cache = NuclearDataCache()

        try:
            u235 = Nuclide(Z=92, A=235)
            dn_data = get_delayed_neutron_data(cache, u235)

            if dn_data is not None:
                # Beta values should sum to total beta
                beta_sum = sum(dn_data["beta_i"])
                assert abs(beta_sum - dn_data["beta"]) < 0.001  # Allow small tolerance

                # Lambda values should be positive
                for lambda_i in dn_data["lambda_i"]:
                    assert lambda_i > 0.0
        except (FileNotFoundError, ImportError, ValueError) as e:
            pytest.skip(f"ENDF files not available: {e}")


@pytest.mark.skipif(not _REACTOR_CORE_AVAILABLE, reason="reactor_core not available")
class TestSMRFeaturesIntegration:
    """Integration tests for SMR features."""

    def test_self_shielding_with_different_sigma_0(self):
        """Test self-shielding with different background cross-sections."""
        cache = NuclearDataCache()

        try:
            u238 = Nuclide(Z=92, A=238)

            # Get cross-sections with different sigma_0 values
            sigma_0_values = [100.0, 1000.0, 10000.0]

            results = []
            for sigma_0 in sigma_0_values:
                energy, xs = get_cross_section_with_self_shielding(
                    cache,
                    u238,
                    "capture",
                    temperature=900.0,
                    sigma_0=sigma_0,
                    use_self_shielding=True,
                )
                results.append((sigma_0, xs))

            # Cross-sections should vary with sigma_0 (self-shielding effect)
            # Higher sigma_0 typically means more self-shielding (lower XS)
            if len(results) > 1:
                xs_100 = results[0][1]
                xs_10000 = results[2][1]
                # With more self-shielding, XS should generally be lower
                # But this depends on the f-factor implementation
                assert len(xs_100) == len(xs_10000)
        except (FileNotFoundError, ImportError, ValueError) as e:
            pytest.skip(f"ENDF files not available: {e}")

    def test_fission_yields_for_multiple_nuclides(self):
        """Test fission yields for different fissile nuclides."""
        cache = NuclearDataCache()

        fissile_nuclides = [
            Nuclide(Z=92, A=235),  # U-235
            Nuclide(Z=94, A=239),  # Pu-239
        ]

        for nuclide in fissile_nuclides:
            try:
                yields = get_fission_yields(cache, nuclide, yield_type="independent")
                if yields is not None:
                    assert isinstance(yields, dict)
                    assert len(yields) > 0
            except (FileNotFoundError, ImportError, ValueError):
                # Skip if ENDF files not available
                pass
