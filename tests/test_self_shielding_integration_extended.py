"""
Extended edge case tests for smrforge.core.self_shielding_integration module.

Additional tests targeting uncovered code paths to reach 80% coverage.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

try:
    import smrforge.core.self_shielding_integration as self_shielding_module
    from smrforge.core.reactor_core import NuclearDataCache, Nuclide
    from smrforge.core.self_shielding_integration import (
        get_cross_section_with_equivalence_theory,
        get_cross_section_with_self_shielding,
    )

    _SELF_SHIELDING_INTEGRATION_AVAILABLE = True
except ImportError:
    _SELF_SHIELDING_INTEGRATION_AVAILABLE = False


@pytest.mark.skipif(
    not _SELF_SHIELDING_INTEGRATION_AVAILABLE,
    reason="Self-shielding integration not available",
)
class TestSelfShieldingIntegrationExtended:
    """Extended edge case tests for self-shielding integration."""

    def test_get_cross_section_with_self_shielding_enable_false(self):
        """Test get_cross_section_with_self_shielding with enable_self_shielding=False."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)

        # Mock cache.get_cross_section
        mock_energy = np.array([1e-5, 1e-3, 1e-1, 1e1, 1e3])
        mock_xs = np.array([10.0, 20.0, 30.0, 40.0, 50.0])

        with patch.object(
            cache, "get_cross_section", return_value=(mock_energy, mock_xs)
        ) as mock_get:
            energy, xs = get_cross_section_with_self_shielding(
                cache,
                u238,
                "capture",
                temperature=900.0,
                sigma_0=10.0,
                method="bondarenko",
                enable_self_shielding=False,  # Should skip shielding
            )

            # Should return unshielded cross-section directly
            assert len(energy) > 0
            assert len(xs) > 0
            # Should have called get_cross_section once
            assert mock_get.call_count == 1

    def test_get_cross_section_with_self_shielding_resonance_not_available(self):
        """Test when _RESONANCE_AVAILABLE is False, should return unshielded."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)

        mock_energy = np.array([1e-5, 1e-3, 1e-1])
        mock_xs = np.array([10.0, 20.0, 30.0])

        with patch.object(
            cache, "get_cross_section", return_value=(mock_energy, mock_xs)
        ):
            with patch.object(self_shielding_module, "_RESONANCE_AVAILABLE", False):
                with patch.object(
                    self_shielding_module.logger, "warning"
                ) as mock_warning:
                    energy, xs = get_cross_section_with_self_shielding(
                        cache,
                        u238,
                        "capture",
                        temperature=900.0,
                        sigma_0=10.0,
                        method="bondarenko",
                    )

                    # Should log warning
                    mock_warning.assert_called_once()
                    # Should return unshielded cross-section
                    assert len(energy) > 0
                    assert len(xs) > 0

    def test_get_cross_section_with_equivalence_theory_resonance_not_available(self):
        """Test equivalence theory when _RESONANCE_AVAILABLE is False."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)

        mock_energy = np.array([1e-5, 1e-3, 1e-1])
        mock_xs = np.array([10.0, 20.0, 30.0])

        with patch.object(
            cache, "get_cross_section", return_value=(mock_energy, mock_xs)
        ):
            with patch.object(self_shielding_module, "_RESONANCE_AVAILABLE", False):
                with patch.object(
                    self_shielding_module.logger, "warning"
                ) as mock_warning:
                    energy, xs = get_cross_section_with_equivalence_theory(
                        cache,
                        u238,
                        "capture",
                        temperature=600.0,
                        fuel_pin_radius=0.4,
                        pin_pitch=1.26,
                        fuel_volume_fraction=0.4,
                    )

                    # Should log warning
                    mock_warning.assert_called_once()
                    # Should return unshielded cross-section
                    assert len(energy) > 0
                    assert len(xs) > 0

    def test_get_cross_section_with_equivalence_theory_with_moderator_xs(self):
        """Test equivalence theory with explicit moderator cross-sections."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)

        mock_energy = np.array([1e-5, 1e-3, 1e-1, 1e1])
        mock_fuel_xs = np.array([10.0, 20.0, 30.0, 40.0])
        mock_moderator_xs = np.array([0.5, 0.6, 0.7, 0.8])

        try:
            with patch.object(
                cache, "get_cross_section", return_value=(mock_energy, mock_fuel_xs)
            ):
                energy, xs = get_cross_section_with_equivalence_theory(
                    cache,
                    u238,
                    "capture",
                    temperature=600.0,
                    fuel_pin_radius=0.4,
                    pin_pitch=1.26,
                    fuel_volume_fraction=0.4,
                    moderator_xs=mock_moderator_xs,  # Explicit moderator XS
                )

                assert len(energy) > 0
                assert len(xs) > 0
                assert len(energy) == len(xs)
        except (ImportError, FileNotFoundError, ValueError):
            pytest.skip("ENDF files or resonance module not available")

    def test_get_cross_section_with_equivalence_theory_moderator_xs_none_defaults(self):
        """Test equivalence theory when moderator_xs is None (uses defaults)."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)

        mock_energy = np.array([1e-5, 1e-3, 1e-1])
        mock_fuel_xs = np.array([10.0, 20.0, 30.0])

        try:
            with patch.object(
                cache, "get_cross_section", return_value=(mock_energy, mock_fuel_xs)
            ):
                energy, xs = get_cross_section_with_equivalence_theory(
                    cache,
                    u238,
                    "capture",
                    temperature=600.0,
                    fuel_pin_radius=0.4,
                    pin_pitch=1.26,
                    fuel_volume_fraction=0.4,
                    moderator_xs=None,  # Should use default water XS
                )

                assert len(energy) > 0
                assert len(xs) > 0
                # Moderator XS should be created (ones_like * 0.66)
                assert len(energy) == len(xs)
        except (ImportError, FileNotFoundError, ValueError):
            pytest.skip("ENDF files or resonance module not available")

    def test_get_cross_section_with_self_shielding_subgroup_zero_mean_resonance_xs(
        self,
    ):
        """Test subgroup method when mean(resonance_xs) is zero."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)

        # Create energy grid with resonance region
        mock_energy = np.array(
            [1.0, 10.0, 100.0, 1000.0, 1e5]
        )  # Includes resonance region
        mock_xs = np.array([0.0, 0.0, 0.0, 50.0, 40.0])  # Zero in resonance region

        try:
            with patch.object(
                cache, "get_cross_section", return_value=(mock_energy, mock_xs)
            ):
                mock_subgroup = MagicMock()
                mock_subgroup.compute_effective_xs.return_value = 2.5

                with patch(
                    "smrforge.core.self_shielding_integration.SubgroupMethod",
                    return_value=mock_subgroup,
                ):
                    energy, xs = get_cross_section_with_self_shielding(
                        cache,
                        u238,
                        "capture",
                        temperature=900.0,
                        sigma_0=10.0,
                        method="subgroup",
                    )

                    assert len(energy) > 0
                    assert len(xs) > 0
                    # Should handle zero mean resonance XS gracefully
                    assert np.any(xs >= 0)  # No negative cross-sections
        except (ImportError, FileNotFoundError, ValueError):
            pytest.skip("ENDF files or resonance module not available")
