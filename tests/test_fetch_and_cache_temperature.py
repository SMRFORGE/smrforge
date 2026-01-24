"""Tests for _fetch_and_cache temperature broadening paths."""

import numpy as np
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestFetchAndCacheTemperature:
    """Test _fetch_and_cache temperature broadening functionality."""

    @pytest.fixture
    def realistic_endf_file_for_temp(self, temp_dir):
        """Create a realistic ENDF file for temperature testing."""
        endf_path = temp_dir / "U235_temp.endf"
        
        endf_content = """ 1.001000+3 9.991673-1          0          0          0          0 125 1451    1
 9.223500+4 2.350000+2          0          0          0          0 125 1451    2
                                                                   125 1451    0
 1.001000+3 9.991673-1          0          0          0          0 125 3  1    1
 0.000000+0 0.000000+0          0          0          0          6 125 3  1    2
 1.000000+5 1.000000+1 1.000000+6 1.200000+1 5.000000+6 1.500000+1 125 3  1    3
 1.000000+7 1.800000+1 2.000000+7 2.000000+1 5.000000+7 2.200000+1 125 3  1    4
                                                                   125 0  0    0
"""
        endf_path.write_text(endf_content)
        return endf_path

    def test_fetch_and_cache_applies_doppler_broadening(self, temp_dir, realistic_endf_file_for_temp):
        """Test that _fetch_and_cache applies Doppler broadening for non-standard temperatures."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)
        key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/900.0K"
        
        # Mock _ensure_endf_file
        with patch.object(cache, '_ensure_endf_file', return_value=realistic_endf_file_for_temp):
            # Mock _doppler_broaden to verify it's called
            with patch.object(cache, '_doppler_broaden') as mock_doppler:
                # Mock _simple_endf_parse to return test data
                test_energy = np.array([1e5, 1e6, 1e7])
                test_xs = np.array([10.0, 12.0, 15.0])
                broadened_xs = test_xs * 1.1
                
                with patch.object(cache, '_simple_endf_parse', return_value=(test_energy, test_xs)):
                    mock_doppler.return_value = broadened_xs
                    
                    # Mock other backends as unavailable
                    with patch.dict('sys.modules', {'endf_parserpy': None}, clear=False):
                        with patch.dict('sys.modules', {'sandy': None}, clear=False):
                            with patch('smrforge.core.reactor_core.ENDFCompatibility', None, create=True):
                                # Fetch at non-standard temperature (900K)
                                energy, xs = cache._fetch_and_cache(
                                    nuc, "total", 900.0, Library.ENDF_B_VIII, key
                                )
                                
                                # Verify Doppler broadening was called
                                mock_doppler.assert_called_once()
                                call_args = mock_doppler.call_args
                                
                                # Verify arguments: T_old, T_new, A
                                assert call_args[0][2] == 293.6  # T_old
                                assert call_args[0][3] == 900.0  # T_new
                                assert call_args[0][4] == 235  # A (mass number)
                                
                                # Verify returned data exists (simple parser may parse file directly)
                                assert energy is not None
                                assert xs is not None
                                assert len(energy) > 0
                                assert len(xs) == len(energy)

    def test_fetch_and_cache_no_broadening_at_standard_temp(self, temp_dir, realistic_endf_file_for_temp):
        """Test that _fetch_and_cache does not apply broadening at standard temperature."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)
        key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/293.6K"
        
        test_energy = np.array([1e5, 1e6, 1e7])
        test_xs = np.array([10.0, 12.0, 15.0])
        
        with patch.object(cache, '_ensure_endf_file', return_value=realistic_endf_file_for_temp):
            with patch.object(cache, '_simple_endf_parse', return_value=(test_energy, test_xs)):
                # Mock _doppler_broaden to verify it's NOT called
                with patch.object(cache, '_doppler_broaden') as mock_doppler:
                    # Mock other backends as unavailable
                    with patch.dict('sys.modules', {'endf_parserpy': None}, clear=False):
                        with patch.dict('sys.modules', {'sandy': None}, clear=False):
                            with patch('smrforge.core.reactor_core.ENDFCompatibility', None, create=True):
                                # Fetch at standard temperature (293.6K)
                                energy, xs = cache._fetch_and_cache(
                                    nuc, "total", 293.6, Library.ENDF_B_VIII, key
                                )
                                
                                # Verify Doppler broadening was NOT called (within 1K tolerance)
                                mock_doppler.assert_not_called()
                                
                                # Verify returned data exists (simple parser may parse file directly)
                                assert energy is not None
                                assert xs is not None
                                assert len(energy) > 0
                                assert len(xs) == len(energy)

    def test_fetch_and_cache_broadening_tolerance(self, temp_dir, realistic_endf_file_for_temp):
        """Test that _fetch_and_cache uses 1K tolerance for temperature comparison."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)
        
        base_energy = np.logspace(4, 7, 100)
        base_xs = np.ones_like(base_energy) * 10.0
        
        # Test temperatures within 1K of 293.6K (should not broaden)
        test_temps = [292.7, 293.0, 293.5, 293.6, 294.0, 294.5]  # All within ±1K
        
        with patch.object(cache, '_ensure_endf_file', return_value=realistic_endf_file_for_temp):
            with patch.object(cache, '_simple_endf_parse', return_value=(base_energy, base_xs)):
                with patch.object(cache, '_doppler_broaden') as mock_doppler:
                    # Mock other backends as unavailable
                    with patch.dict('sys.modules', {'endf_parserpy': None}, clear=False):
                        with patch.dict('sys.modules', {'sandy': None}, clear=False):
                            with patch('smrforge.core.reactor_core.ENDFCompatibility', None, create=True):
                                for temp in test_temps:
                                    key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/{temp:.1f}K"
                                    cache._fetch_and_cache(
                                        nuc, "total", temp, Library.ENDF_B_VIII, key
                                    )
                                
                                # Should not have been called (all temps within tolerance)
                                mock_doppler.assert_not_called()

    def test_fetch_and_cache_broadening_high_temperature(self, temp_dir, realistic_endf_file_for_temp):
        """Test Doppler broadening at high temperature (HTGR conditions)."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)
        key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/1200.0K"
        
        base_energy = np.logspace(4, 7, 100)
        base_xs = np.ones_like(base_energy) * 10.0
        broadened_xs = base_xs * 1.15  # Simulate broadening
        
        with patch.object(cache, '_ensure_endf_file', return_value=realistic_endf_file_for_temp):
            with patch.object(cache, '_simple_endf_parse', return_value=(base_energy, base_xs)):
                with patch.object(cache, '_doppler_broaden') as mock_doppler:
                    mock_doppler.return_value = broadened_xs
                    with patch.object(cache, '_get_parser', return_value=None):
                        with patch.dict('sys.modules', {'endf_parserpy': None}, clear=False):
                            with patch.dict('sys.modules', {'sandy': None}, clear=False):
                                with patch('smrforge.core.reactor_core.ENDFCompatibility', None, create=True):
                                    energy, xs = cache._fetch_and_cache(
                                        nuc, "total", 1200.0, Library.ENDF_B_VIII, key
                                    )
                    
                    # At least one backend (e.g. simple parser) applies Doppler at 1200K
                    assert mock_doppler.call_count >= 1
                    t_new_calls = [c[0][3] for c in mock_doppler.call_args_list]
                    assert 1200.0 in t_new_calls
                    # Returned xs should be broadened (mock return)
                    assert np.array_equal(xs, broadened_xs)

    def test_fetch_and_cache_broadening_low_temperature(self, temp_dir, realistic_endf_file_for_temp):
        """Test Doppler broadening at low temperature."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)
        key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/100.0K"
        
        base_energy = np.logspace(4, 7, 100)
        base_xs = np.ones_like(base_energy) * 10.0
        narrow_xs = base_xs * 0.95  # Simulate narrowing at low temp
        
        with patch.object(cache, '_ensure_endf_file', return_value=realistic_endf_file_for_temp):
            with patch.object(cache, '_simple_endf_parse', return_value=(base_energy, base_xs)):
                with patch.object(cache, '_doppler_broaden') as mock_doppler:
                    mock_doppler.return_value = narrow_xs
                    with patch.object(cache, '_get_parser', return_value=None):
                        with patch.dict('sys.modules', {'endf_parserpy': None}, clear=False):
                            with patch.dict('sys.modules', {'sandy': None}, clear=False):
                                with patch('smrforge.core.reactor_core.ENDFCompatibility', None, create=True):
                                    energy, xs = cache._fetch_and_cache(
                                        nuc, "total", 100.0, Library.ENDF_B_VIII, key
                                    )
                    
                    assert mock_doppler.call_count >= 1
                    t_new_calls = [c[0][3] for c in mock_doppler.call_args_list]
                    assert 100.0 in t_new_calls
                    assert np.array_equal(xs, narrow_xs)

    def test_fetch_and_cache_broadening_multiple_temperatures(self, temp_dir, realistic_endf_file_for_temp):
        """Test that different temperatures produce different cache entries."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)
        
        base_energy = np.logspace(4, 7, 100)
        base_xs = np.ones_like(base_energy) * 10.0
        
        temperatures = [600.0, 900.0, 1200.0]
        
        with patch.object(cache, '_ensure_endf_file', return_value=realistic_endf_file_for_temp):
            with patch.object(cache, '_simple_endf_parse', return_value=(base_energy, base_xs)):
                with patch.object(cache, '_doppler_broaden') as mock_doppler:
                    # Return different broadened values for each temperature
                    def mock_doppler_side_effect(energy, xs, T_old, T_new, A):
                        # Simple scaling based on temperature ratio
                        scale = np.sqrt(T_new / T_old)
                        return xs * scale
                    
                    mock_doppler.side_effect = mock_doppler_side_effect
                    
                    # Mock other backends as unavailable
                    with patch.dict('sys.modules', {'endf_parserpy': None}, clear=False):
                        with patch.dict('sys.modules', {'sandy': None}, clear=False):
                            with patch('smrforge.core.reactor_core.ENDFCompatibility', None, create=True):
                                # Fetch at different temperatures
                                for temp in temperatures:
                                    key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/{temp:.1f}K"
                                    energy, xs = cache._fetch_and_cache(
                                        nuc, "total", temp, Library.ENDF_B_VIII, key
                                    )
                                
                                # Verify broadening was called for each temperature
                                assert mock_doppler.call_count == len(temperatures)
                                
                                # Verify different cache entries were created
                                assert len(cache._memory_cache) == len(temperatures)

