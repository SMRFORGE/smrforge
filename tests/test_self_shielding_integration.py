"""
Tests for self-shielding integration.

Tests integration of SubgroupMethod and EquivalenceTheory into reactor_core.
"""

import pytest
import numpy as np

try:
    from smrforge.core.self_shielding_integration import (
        get_cross_section_with_equivalence_theory,
        get_cross_section_with_self_shielding,
    )
    from smrforge.core.reactor_core import Nuclide, NuclearDataCache

    _SELF_SHIELDING_INTEGRATION_AVAILABLE = True
except ImportError:
    _SELF_SHIELDING_INTEGRATION_AVAILABLE = False


@pytest.mark.skipif(
    not _SELF_SHIELDING_INTEGRATION_AVAILABLE,
    reason="Self-shielding integration not available",
)
class TestSelfShieldingIntegration:
    """Tests for self-shielding integration functions."""

    def test_get_cross_section_with_self_shielding_bondarenko(self):
        """Test Bondarenko method integration."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)

        try:
            energy, xs = get_cross_section_with_self_shielding(
                cache, u238, "capture", temperature=900.0,
                sigma_0=10.0, method="bondarenko"
            )

            assert len(energy) > 0
            assert len(xs) > 0
            assert len(energy) == len(xs)
        except (ImportError, FileNotFoundError, ValueError):
            pytest.skip("ENDF files not available")

    def test_get_cross_section_with_self_shielding_subgroup(self):
        """Test Subgroup method integration."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)

        try:
            energy, xs = get_cross_section_with_self_shielding(
                cache, u238, "capture", temperature=900.0,
                sigma_0=10.0, method="subgroup"
            )

            assert len(energy) > 0
            assert len(xs) > 0
        except (ImportError, FileNotFoundError, ValueError):
            pytest.skip("ENDF files not available")

    def test_get_cross_section_with_equivalence_theory(self):
        """Test Equivalence theory integration."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)

        try:
            energy, xs = get_cross_section_with_equivalence_theory(
                cache, u238, "capture", temperature=600.0,
                fuel_pin_radius=0.4,  # cm
                pin_pitch=1.26,  # cm
                fuel_volume_fraction=0.4,
            )

            assert len(energy) > 0
            assert len(xs) > 0
        except (ImportError, FileNotFoundError, ValueError):
            pytest.skip("ENDF files not available")

    def test_disable_self_shielding(self):
        """Test disabling self-shielding."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)

        try:
            energy, xs = get_cross_section_with_self_shielding(
                cache, u238, "capture", temperature=900.0,
                enable_self_shielding=False
            )

            assert len(energy) > 0
            assert len(xs) > 0
        except (ImportError, FileNotFoundError, ValueError):
            pytest.skip("ENDF files not available")
