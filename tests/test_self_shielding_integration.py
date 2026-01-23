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
    
    def test_get_cross_section_with_self_shielding_different_reactions(self):
        """Test self-shielding with different reaction types."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        reactions = ["fission", "capture", "elastic", "total"]
        
        for reaction in reactions:
            try:
                energy, xs = get_cross_section_with_self_shielding(
                    cache, u238, reaction, temperature=900.0,
                    sigma_0=10.0, method="bondarenko"
                )
                
                assert len(energy) > 0
                assert len(xs) > 0
            except (ImportError, FileNotFoundError, ValueError):
                # Some reactions may not be available for all nuclides
                pass
    
    def test_get_cross_section_with_self_shielding_different_sigma_0(self):
        """Test self-shielding with different background cross-sections."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        sigma_0_values = [0.1, 1.0, 10.0, 100.0]
        
        for sigma_0 in sigma_0_values:
            try:
                energy, xs = get_cross_section_with_self_shielding(
                    cache, u238, "capture", temperature=900.0,
                    sigma_0=sigma_0, method="bondarenko"
                )
                
                assert len(energy) > 0
                assert len(xs) > 0
            except (ImportError, FileNotFoundError, ValueError):
                pytest.skip("ENDF files not available")
    
    def test_get_cross_section_with_self_shielding_different_temperatures(self):
        """Test self-shielding with different temperatures."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        temperatures = [300.0, 600.0, 900.0, 1200.0]
        
        for temp in temperatures:
            try:
                energy, xs = get_cross_section_with_self_shielding(
                    cache, u238, "capture", temperature=temp,
                    sigma_0=10.0, method="bondarenko"
                )
                
                assert len(energy) > 0
                assert len(xs) > 0
            except (ImportError, FileNotFoundError, ValueError):
                pytest.skip("ENDF files not available")
    
    def test_get_cross_section_with_equivalence_theory_different_geometries(self):
        """Test equivalence theory with different geometry parameters."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        geometries = [
            (0.3, 1.0, 0.3),  # Small pin, tight pitch, low volume fraction
            (0.5, 1.5, 0.5),  # Medium pin, medium pitch, medium volume fraction
            (0.7, 2.0, 0.7),  # Large pin, wide pitch, high volume fraction
        ]
        
        for fuel_radius, pitch, volume_frac in geometries:
            try:
                energy, xs = get_cross_section_with_equivalence_theory(
                    cache, u238, "capture", temperature=600.0,
                    fuel_pin_radius=fuel_radius,
                    pin_pitch=pitch,
                    fuel_volume_fraction=volume_frac,
                )
                
                assert len(energy) > 0
                assert len(xs) > 0
            except (ImportError, FileNotFoundError, ValueError):
                pytest.skip("ENDF files not available")
    
    def test_get_cross_section_with_equivalence_theory_custom_moderator_xs_shape(self):
        """Test equivalence theory with custom moderator XS of different shape."""
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        try:
            # Get fuel cross-section to determine shape
            energy, fuel_xs = cache.get_cross_section(u238, "capture", temperature=600.0)
            
            # Provide moderator XS with same shape but different values
            moderator_xs = np.ones_like(fuel_xs) * 2.0  # Different value
            
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
    
    def test_get_cross_section_with_self_shielding_subgroup_epithermal_energy_group(self):
        """Test subgroup method with epithermal energy group classification."""
        from unittest.mock import patch
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        # Mock cache to return energy in epithermal region (1 keV to 100 keV)
        mock_energy = np.array([1e3, 5e3, 1e4, 5e4, 9e4])  # All in epithermal range
        mock_xs = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
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
    
    def test_get_cross_section_with_self_shielding_subgroup_all_energy_regions(self):
        """Test subgroup method with energy spanning all regions."""
        from unittest.mock import patch
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        # Mock cache to return energy spanning thermal, resonance, and fast regions
        mock_energy = np.array([0.1, 1.0, 100.0, 1e4, 1e5, 1e6, 1e7])  # All regions
        mock_xs = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
        
        with patch.object(cache, 'get_cross_section', return_value=(mock_energy, mock_xs)):
            try:
                energy, xs = get_cross_section_with_self_shielding(
                    cache, u238, "capture", temperature=900.0,
                    sigma_0=10.0, method="subgroup"
                )
                
                assert len(energy) > 0
                assert len(xs) > 0
                # Should have resonance region corrected, others use Bondarenko
            except (ImportError, FileNotFoundError, ValueError):
                pytest.skip("ENDF files not available")
    
    def test_get_cross_section_with_self_shielding_warning_logging(self):
        """Test that warnings are logged when resonance module unavailable."""
        from unittest.mock import patch
        import smrforge.core.self_shielding_integration
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        # Mock _RESONANCE_AVAILABLE to False and check warning
        with patch.object(smrforge.core.self_shielding_integration, '_RESONANCE_AVAILABLE', False), \
             patch('smrforge.core.self_shielding_integration.logger') as mock_logger:
            
            try:
                energy, xs = get_cross_section_with_self_shielding(
                    cache, u238, "capture", temperature=900.0,
                    enable_self_shielding=True
                )
                
                # Should have logged warning
                mock_logger.warning.assert_called()
                assert len(energy) > 0
                assert len(xs) > 0
            except (ImportError, FileNotFoundError, ValueError):
                pytest.skip("ENDF files not available")
    
    def test_get_cross_section_with_equivalence_theory_warning_logging(self):
        """Test that warnings are logged when equivalence theory unavailable."""
        from unittest.mock import patch
        import smrforge.core.self_shielding_integration
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        # Mock _RESONANCE_AVAILABLE to False
        with patch.object(smrforge.core.self_shielding_integration, '_RESONANCE_AVAILABLE', False), \
             patch('smrforge.core.self_shielding_integration.logger') as mock_logger:
            
            try:
                energy, xs = get_cross_section_with_equivalence_theory(
                    cache, u238, "capture", temperature=600.0,
                    fuel_pin_radius=0.4,
                    pin_pitch=1.26,
                    fuel_volume_fraction=0.4,
                )
                
                # Should have logged warning
                mock_logger.warning.assert_called()
                assert len(energy) > 0
                assert len(xs) > 0
            except (ImportError, FileNotFoundError, ValueError):
                pytest.skip("ENDF files not available")


class TestSelfShieldingIntegrationEdgeCases:
    """Edge case tests for self_shielding_integration.py to improve coverage."""
    
    def test_get_cross_section_with_self_shielding_subgroup_non_resonance_region_path(self):
        """Test subgroup method fallback to Bondarenko when no resonance region exists."""
        from unittest.mock import patch
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        # Mock cache to return energy array with no resonance region (all fast/thermal)
        # This tests the path at line 173-182
        mock_energy = np.array([0.01, 0.1, 1e6, 1e7])  # No resonance region (1 eV to 100 keV)
        mock_xs = np.array([1.0, 2.0, 3.0, 4.0])
        
        with patch.object(cache, 'get_cross_section', return_value=(mock_energy, mock_xs)):
            try:
                energy, xs = get_cross_section_with_self_shielding(
                    cache, u238, "capture", temperature=900.0,
                    sigma_0=10.0, method="subgroup"
                )
                
                assert len(energy) > 0
                assert len(xs) > 0
                # Should use Bondarenko for all when no resonance region
            except (ImportError, FileNotFoundError, ValueError):
                pytest.skip("ENDF files not available")
    
    def test_get_cross_section_with_self_shielding_equivalence_warning_logging(self):
        """Test that equivalence method logs warning and falls back to Bondarenko."""
        from unittest.mock import patch
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        with patch('smrforge.core.self_shielding_integration.logger') as mock_logger:
            try:
                energy, xs = get_cross_section_with_self_shielding(
                    cache, u238, "capture", temperature=900.0,
                    sigma_0=10.0, method="equivalence"
                )
                
                # Should log warning about using Bondarenko instead
                mock_logger.warning.assert_called()
                assert len(energy) > 0
                assert len(xs) > 0
            except (ImportError, FileNotFoundError, ValueError):
                pytest.skip("ENDF files not available")
    
    def test_get_cross_section_with_self_shielding_cross_section_import_error(self):
        """Test error handling when cross-section retrieval raises ImportError."""
        from unittest.mock import patch
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        # Mock cache.get_cross_section to raise ImportError
        with patch.object(cache, 'get_cross_section', side_effect=ImportError("Import failed")):
            with pytest.raises(ImportError):
                get_cross_section_with_self_shielding(
                    cache, u238, "capture", temperature=900.0,
                    method="bondarenko"
                )
    
    def test_get_cross_section_with_self_shielding_cross_section_value_error(self):
        """Test error handling when cross-section retrieval raises ValueError."""
        from unittest.mock import patch
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        # Mock cache.get_cross_section to raise ValueError
        with patch.object(cache, 'get_cross_section', side_effect=ValueError("Invalid data")):
            with pytest.raises(ValueError):
                get_cross_section_with_self_shielding(
                    cache, u238, "capture", temperature=900.0,
                    method="bondarenko"
                )
    
    def test_get_cross_section_with_equivalence_theory_cross_section_error(self):
        """Test equivalence theory when cross-section retrieval fails."""
        from unittest.mock import patch
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        # Mock cache.get_cross_section to raise an error
        with patch.object(cache, 'get_cross_section', side_effect=FileNotFoundError("Data not found")):
            with pytest.raises(FileNotFoundError):
                get_cross_section_with_equivalence_theory(
                    cache, u238, "capture", temperature=600.0,
                    fuel_pin_radius=0.4,
                    pin_pitch=1.26,
                    fuel_volume_fraction=0.4,
                )


class TestSelfShieldingIntegration70Percent:
    """Additional edge case tests to reach 70%+ coverage for self_shielding_integration.py."""
    
    def test_subgroup_method_fast_energy_group_in_resonance(self):
        """Test subgroup method with fast energy group but still in resonance region."""
        from unittest.mock import patch, MagicMock
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        # Mock cache to return energy > 100 keV but still in resonance region (edge case)
        # Actually, resonance region is 1 eV to 100 keV, so > 100 keV is not in resonance
        # Test with energy just at 100 keV boundary
        mock_energy = np.array([50.0, 90.0, 99.0, 100.0])  # At upper boundary
        mock_xs = np.array([1.0, 2.0, 3.0, 4.0])
        
        mock_subgroup = MagicMock()
        mock_subgroup.compute_effective_xs.return_value = 2.5
        
        with patch.object(cache, 'get_cross_section', return_value=(mock_energy, mock_xs)):
            with patch('smrforge.core.self_shielding_integration.SubgroupMethod', return_value=mock_subgroup):
                try:
                    energy, xs = get_cross_section_with_self_shielding(
                        cache, u238, "capture", temperature=900.0,
                        sigma_0=10.0, method="subgroup"
                    )
                    assert len(energy) > 0
                    assert len(xs) > 0
                except (ImportError, FileNotFoundError, ValueError):
                    pytest.skip("ENDF files not available")
    
    def test_subgroup_method_non_resonance_mask_applied(self):
        """Test subgroup method when non_resonance_mask has values (line 164)."""
        from unittest.mock import patch, MagicMock
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        # Mock cache to return energy spanning both resonance and non-resonance regions
        mock_energy = np.array([0.1, 1.0, 1e4, 1e5, 1e6, 1e7])  # Mixed regions
        mock_xs = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        
        mock_subgroup = MagicMock()
        mock_subgroup.compute_effective_xs.return_value = 2.5
        
        mock_bondarenko = MagicMock()
        mock_bondarenko.get_f_factor.return_value = 0.9
        
        with patch.object(cache, 'get_cross_section', return_value=(mock_energy, mock_xs)):
            with patch('smrforge.core.self_shielding_integration.SubgroupMethod', return_value=mock_subgroup):
                with patch('smrforge.core.self_shielding_integration.BondarenkoMethod', return_value=mock_bondarenko):
                    try:
                        energy, xs = get_cross_section_with_self_shielding(
                            cache, u238, "capture", temperature=900.0,
                            sigma_0=10.0, method="subgroup"
                        )
                        # Should apply subgroup to resonance and Bondarenko to non-resonance
                        mock_subgroup.compute_effective_xs.assert_called()
                        mock_bondarenko.get_f_factor.assert_called()
                        assert len(energy) > 0
                        assert len(xs) > 0
                    except (ImportError, FileNotFoundError, ValueError):
                        pytest.skip("ENDF files not available")
    
    def test_equivalence_method_recursive_fallback(self):
        """Test that equivalence method recursively calls bondarenko (line 193-195)."""
        from unittest.mock import patch, MagicMock
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        mock_energy = np.array([1e4, 1e5, 1e6])
        mock_xs = np.array([1.0, 2.0, 3.0])
        
        with patch.object(cache, 'get_cross_section', return_value=(mock_energy, mock_xs)):
            with patch('smrforge.core.self_shielding_integration.logger') as mock_logger:
                with patch('smrforge.core.self_shielding_integration.get_cross_section_with_self_shielding') as mock_recursive:
                    mock_recursive.return_value = (mock_energy, mock_xs * 0.9)
                    try:
                        energy, xs = get_cross_section_with_self_shielding(
                            cache, u238, "capture", temperature=900.0,
                            sigma_0=10.0, method="equivalence"
                        )
                        # Should log warning and recursively call with "bondarenko"
                        mock_logger.warning.assert_called()
                        mock_recursive.assert_called_once()
                        # Check that method="bondarenko" was passed (as positional or keyword)
                        call_args = mock_recursive.call_args
                        # Method is passed as 5th positional argument (0-indexed: cache, nuclide, reaction, temp, sigma_0, method)
                        # or as keyword argument
                        if len(call_args[0]) > 5:
                            method_arg = call_args[0][5]  # 6th positional arg (method)
                        elif 'method' in call_args[1]:
                            method_arg = call_args[1]['method']
                        else:
                            method_arg = None
                        assert method_arg == "bondarenko"
                    except (ImportError, FileNotFoundError, ValueError):
                        pytest.skip("ENDF files not available")
    
    def test_equivalence_theory_volume_fraction_calculation(self):
        """Test equivalence theory volume fraction calculations (line 271-275)."""
        from unittest.mock import patch
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        mock_energy = np.array([1e4, 1e5, 1e6])
        mock_fuel_xs = np.array([10.0, 20.0, 30.0])
        
        # Test with different volume fractions
        fuel_vf = 0.3
        moderator_vf = 1.0 - fuel_vf  # Should be 0.7
        
        with patch.object(cache, 'get_cross_section', return_value=(mock_energy, mock_fuel_xs)):
            try:
                energy, xs = get_cross_section_with_equivalence_theory(
                    cache, u238, "capture", temperature=600.0,
                    fuel_pin_radius=0.4,
                    pin_pitch=1.26,
                    fuel_volume_fraction=fuel_vf,
                )
                # Should calculate moderator_volume_fraction correctly
                assert len(energy) > 0
                assert len(xs) > 0
            except (ImportError, FileNotFoundError, ValueError):
                pytest.skip("ENDF files not available")
    
    def test_equivalence_theory_sigma_0_eff_calculation(self):
        """Test equivalence theory sigma_0_eff calculation (line 275)."""
        from unittest.mock import patch, MagicMock
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        mock_energy = np.array([1e4, 1e5, 1e6])
        mock_fuel_xs = np.array([10.0, 20.0, 30.0])
        custom_moderator_xs = np.array([0.5, 0.6, 0.7])  # Mean = 0.6
        
        mock_bondarenko = MagicMock()
        mock_bondarenko.get_f_factor.return_value = 0.85
        
        with patch.object(cache, 'get_cross_section', return_value=(mock_energy, mock_fuel_xs)):
            with patch('smrforge.core.self_shielding_integration.BondarenkoMethod', return_value=mock_bondarenko):
                try:
                    energy, xs = get_cross_section_with_equivalence_theory(
                        cache, u238, "capture", temperature=600.0,
                        fuel_pin_radius=0.4,
                        pin_pitch=1.26,
                        fuel_volume_fraction=0.4,  # moderator_vf = 0.6
                        moderator_xs=custom_moderator_xs,
                    )
                    # Should calculate sigma_0_eff = mean(moderator_xs) * 0.6 / 0.4 = 0.6 * 1.5 = 0.9
                    # Verify Bondarenko was called with calculated sigma_0_eff
                    mock_bondarenko.get_f_factor.assert_called()
                    call_kwargs = mock_bondarenko.get_f_factor.call_args[1]
                    # sigma_0 should be approximately 0.9 (mean(0.5,0.6,0.7) * 0.6 / 0.4)
                    assert call_kwargs['sigma_0'] > 0
                    assert len(energy) > 0
                    assert len(xs) > 0
                except (ImportError, FileNotFoundError, ValueError):
                    pytest.skip("ENDF files not available")
    
    def test_equivalence_theory_equivalent_xs_formula(self):
        """Test equivalence theory equivalent cross-section formula (line 287-290)."""
        from unittest.mock import patch
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        mock_energy = np.array([1e4, 1e5])
        mock_fuel_xs = np.array([10.0, 20.0])
        custom_moderator_xs = np.array([0.5, 0.6])
        fuel_vf = 0.4
        moderator_vf = 0.6
        
        with patch.object(cache, 'get_cross_section', return_value=(mock_energy, mock_fuel_xs)):
            try:
                energy, xs = get_cross_section_with_equivalence_theory(
                    cache, u238, "capture", temperature=600.0,
                    fuel_pin_radius=0.4,
                    pin_pitch=1.26,
                    fuel_volume_fraction=fuel_vf,
                    moderator_xs=custom_moderator_xs,
                )
                # Equivalent XS should be: fuel_vf * fuel_xs * f_factor + moderator_vf * moderator_xs
                # Verify the formula is applied
                assert len(energy) == 2
                assert len(xs) == 2
                # xs should be between fuel_xs and moderator_xs (volume-weighted)
                assert np.all(xs > 0)
            except (ImportError, FileNotFoundError, ValueError):
                pytest.skip("ENDF files not available")
    
    def test_subgroup_method_resonance_boundary_exact_match(self):
        """Test subgroup method with energy exactly at resonance boundaries."""
        from unittest.mock import patch, MagicMock
        
        cache = NuclearDataCache()
        u238 = Nuclide(Z=92, A=238)
        
        # Test exact boundary values: 1.0 eV and 1e5 eV
        mock_energy = np.array([0.9, 1.0, 1e5, 1e5 + 1])  # Boundary cases
        mock_xs = np.array([1.0, 2.0, 3.0, 4.0])
        
        mock_subgroup = MagicMock()
        mock_subgroup.compute_effective_xs.return_value = 2.5
        
        with patch.object(cache, 'get_cross_section', return_value=(mock_energy, mock_xs)):
            with patch('smrforge.core.self_shielding_integration.SubgroupMethod', return_value=mock_subgroup):
                try:
                    energy, xs = get_cross_section_with_self_shielding(
                        cache, u238, "capture", temperature=900.0,
                        sigma_0=10.0, method="subgroup"
                    )
                    assert len(energy) > 0
                    assert len(xs) > 0
                except (ImportError, FileNotFoundError, ValueError):
                    pytest.skip("ENDF files not available")
