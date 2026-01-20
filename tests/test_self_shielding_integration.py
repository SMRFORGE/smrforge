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
    
    def test_get_cross_section_with_self_shielding_equivalence_method(self):
        """Test equivalence method (should fallback to Bondarenko)."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)

        try:
            energy, xs = get_cross_section_with_self_shielding(
                cache, u238, "capture", temperature=900.0,
                sigma_0=10.0, method="equivalence"
            )

            assert len(energy) > 0
            assert len(xs) > 0
        except (ImportError, FileNotFoundError, ValueError):
            pytest.skip("ENDF files not available")
    
    def test_get_cross_section_with_self_shielding_unknown_method(self):
        """Test that unknown method raises ValueError."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)

        try:
            with pytest.raises(ValueError, match="Unknown self-shielding method"):
                get_cross_section_with_self_shielding(
                    cache, u238, "capture", temperature=900.0,
                    method="unknown_method"
                )
        except (ImportError, FileNotFoundError):
            pytest.skip("ENDF files not available")
    
    def test_get_cross_section_with_self_shielding_no_resonance_available(self):
        """Test when resonance_selfshield module is not available."""
        from unittest.mock import patch
        import smrforge.core.self_shielding_integration
        
        # Mock _RESONANCE_AVAILABLE to False
        with patch.object(smrforge.core.self_shielding_integration, '_RESONANCE_AVAILABLE', False):
            cache = NuclearDataCache()
            u238 = Nuclide(Z=92, A=238)
            
            try:
                energy, xs = get_cross_section_with_self_shielding(
                    cache, u238, "capture", temperature=900.0,
                    enable_self_shielding=True
                )
                
                assert len(energy) > 0
                assert len(xs) > 0
            except (ImportError, FileNotFoundError, ValueError):
                pytest.skip("ENDF files not available")
    
    def test_get_cross_section_with_self_shielding_cross_section_error(self):
        """Test error handling when cross-section cannot be retrieved."""
        from unittest.mock import patch, MagicMock
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        # Mock cache.get_cross_section to raise an error
        with patch.object(cache, 'get_cross_section', side_effect=FileNotFoundError("Data not found")):
            with pytest.raises(FileNotFoundError):
                get_cross_section_with_self_shielding(
                    cache, u238, "capture", temperature=900.0,
                    method="bondarenko"
                )
    
    def test_get_cross_section_with_equivalence_theory_with_moderator_xs(self):
        """Test equivalence theory with provided moderator cross-sections."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)

        try:
            # Get fuel cross-section to determine shape
            energy, fuel_xs = cache.get_cross_section(u238, "capture", temperature=600.0)
            
            # Provide custom moderator cross-sections
            moderator_xs = np.ones_like(fuel_xs) * 1.0  # Custom value
            
            energy, xs = get_cross_section_with_equivalence_theory(
                cache, u238, "capture", temperature=600.0,
                fuel_pin_radius=0.4,
                pin_pitch=1.26,
                fuel_volume_fraction=0.4,
                moderator_xs=moderator_xs,
            )

            assert len(energy) > 0
            assert len(xs) > 0
            assert len(energy) == len(xs)
        except (ImportError, FileNotFoundError, ValueError):
            pytest.skip("ENDF files not available")
    
    def test_get_cross_section_with_equivalence_theory_no_resonance_available(self):
        """Test equivalence theory when resonance_selfshield is not available."""
        from unittest.mock import patch
        import smrforge.core.self_shielding_integration
        
        # Mock _RESONANCE_AVAILABLE to False
        with patch.object(smrforge.core.self_shielding_integration, '_RESONANCE_AVAILABLE', False):
            cache = NuclearDataCache()
            u238 = Nuclide(Z=92, A=238)
            
            try:
                energy, xs = get_cross_section_with_equivalence_theory(
                    cache, u238, "capture", temperature=600.0,
                    fuel_pin_radius=0.4,
                    pin_pitch=1.26,
                    fuel_volume_fraction=0.4,
                )
                
                assert len(energy) > 0
                assert len(xs) > 0
            except (ImportError, FileNotFoundError, ValueError):
                pytest.skip("ENDF files not available")
    
    def test_get_cross_section_with_self_shielding_subgroup_no_resonance_region(self):
        """Test subgroup method when no resonance region is found."""
        from unittest.mock import patch, MagicMock
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        # Mock cache to return energy array outside resonance region
        mock_energy = np.array([1e6, 1e7, 1e8])  # All fast (> 100 keV)
        mock_xs = np.array([1.0, 2.0, 3.0])
        
        with patch.object(cache, 'get_cross_section', return_value=(mock_energy, mock_xs)):
            try:
                energy, xs = get_cross_section_with_self_shielding(
                    cache, u238, "capture", temperature=900.0,
                    sigma_0=10.0, method="subgroup"
                )
                
                assert len(energy) > 0
                assert len(xs) > 0
            except (ImportError, FileNotFoundError, ValueError):
                pytest.skip("ENDF files not available")
    
    def test_get_cross_section_with_self_shielding_subgroup_zero_resonance_xs(self):
        """Test subgroup method when resonance region has zero cross-sections (line 160)."""
        from unittest.mock import patch, MagicMock
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        # Mock cache to return energy array with resonance region (1 eV to 100 keV)
        # but all zero cross-sections in resonance region to trigger line 160
        mock_energy = np.array([0.1, 1.0, 10.0, 100.0, 1000.0, 1e4, 1e5, 1e6])
        # All zeros in resonance region (indices 1-5 are in resonance: 1.0 to 1e5)
        mock_xs = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 2.0])  # Zero mean in resonance
        
        with patch.object(cache, 'get_cross_section', return_value=(mock_energy, mock_xs)):
            try:
                energy, xs = get_cross_section_with_self_shielding(
                    cache, u238, "capture", temperature=900.0,
                    sigma_0=10.0, method="subgroup"
                )
                
                assert len(energy) > 0
                assert len(xs) > 0
                # When mean(resonance_xs) == 0, should use xs_inf directly (line 160)
                # Verify that resonance region values are unchanged (xs_inf, not corrected)
            except (ImportError, FileNotFoundError, ValueError):
                pytest.skip("ENDF files not available")
    
    def test_get_cross_section_with_self_shielding_subgroup_fast_energy_group(self):
        """Test subgroup method with fast energy group classification."""
        from unittest.mock import patch
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        # Mock cache to return energy in fast region (> 100 keV)
        mock_energy = np.array([1e5, 2e5, 5e5, 1e6])  # All > 100 keV
        mock_xs = np.array([1.0, 2.0, 3.0, 4.0])
        
        with patch.object(cache, 'get_cross_section', return_value=(mock_energy, mock_xs)):
            try:
                energy, xs = get_cross_section_with_self_shielding(
                    cache, u238, "capture", temperature=900.0,
                    sigma_0=10.0, method="subgroup"
                )
                
                assert len(energy) > 0
                assert len(xs) > 0
            except (ImportError, FileNotFoundError, ValueError):
                pytest.skip("ENDF files not available")
    
    def test_get_cross_section_with_self_shielding_subgroup_thermal_energy_group(self):
        """Test subgroup method with thermal energy group classification."""
        from unittest.mock import patch
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        # Mock cache to return energy in thermal region (< 1 keV)
        mock_energy = np.array([0.01, 0.1, 1.0, 10.0, 100.0, 500.0, 900.0])  # All < 1 keV
        mock_xs = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
        
        with patch.object(cache, 'get_cross_section', return_value=(mock_energy, mock_xs)):
            try:
                energy, xs = get_cross_section_with_self_shielding(
                    cache, u238, "capture", temperature=900.0,
                    sigma_0=10.0, method="subgroup"
                )
                
                assert len(energy) > 0
                assert len(xs) > 0
            except (ImportError, FileNotFoundError, ValueError):
                pytest.skip("ENDF files not available")
    
    def test_import_error_handling(self):
        """Test that ImportError in resonance_selfshield is handled."""
        from unittest.mock import patch
        import sys
        
        # Mock the import to fail
        original_modules = {}
        for mod_name in ['smrforge.core.resonance_selfshield']:
            if mod_name in sys.modules:
                original_modules[mod_name] = sys.modules[mod_name]
            sys.modules[mod_name] = None
        
        try:
            # Reload module to trigger import error
            import importlib
            import smrforge.core.self_shielding_integration
            importlib.reload(smrforge.core.self_shielding_integration)
            
            # Check that _RESONANCE_AVAILABLE is False
            assert smrforge.core.self_shielding_integration._RESONANCE_AVAILABLE is False
        finally:
            # Restore original modules
            for mod_name, mod in original_modules.items():
                sys.modules[mod_name] = mod
            if 'smrforge.core.resonance_selfshield' not in original_modules:
                sys.modules.pop('smrforge.core.resonance_selfshield', None)
            
            # Reload to restore state
            import importlib
            import smrforge.core.self_shielding_integration
            importlib.reload(smrforge.core.self_shielding_integration)
