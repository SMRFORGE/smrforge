"""
Tests for _fetch_and_cache method in NuclearDataCache.

This test suite comprehensively tests the _fetch_and_cache method,
covering all backend success paths: endf-parserpy, SANDY, ENDFCompatibility,
and simple parser fallback.
"""

import numpy as np
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


@pytest.fixture
def realistic_endf_file_for_fetch(temp_dir):
    """Create a realistic ENDF file for testing _fetch_and_cache."""
    endf_path = temp_dir / "U235.endf"
    
    # Create ENDF file with proper format
    endf_content = """ 1.001000+3 9.991673-1          0          0          0          0 125 1451    1
 9.223500+4 2.350000+2          0          0          0          0 125 1451    2
                                                                   125 1451    0
 1.001000+3 9.991673-1          0          0          0          0 125 3  1    1
 1.000000+5 1.000000+1 1.000000+6 1.200000+1 5.000000+6 1.500000+1 125 3  1    3
 1.000000+7 1.800000+1 2.000000+7 2.000000+1 5.000000+7 2.200000+1 125 3  1    4
                                                                   125 0  0    0
 1.001000+3 9.991673-1          0          0          0          0 125 3  2    1
 1.000000+5 8.000000+0 1.000000+6 9.000000+0 1.000000+7 1.000000+1 125 3  2    3
                                                                   125 0  0    0
 1.001000+3 9.991673-1          0          0          0          0 125 3 18    1
 1.000000+5 1.500000+0 1.000000+6 2.000000+0 5.000000+6 2.500000+0 125 3 18    3
                                                                   125 0  0    0
 1.001000+3 9.991673-1          0          0          0          0 125 3102    1
 1.000000+5 5.000000-1 1.000000+6 1.000000+0 1.000000+7 1.500000+0 125 3102    3
                                                                   125 0  0    0
                                                                   125 0  0    0
"""
    endf_path.write_text(endf_content)
    return endf_path


class TestFetchAndCacheBackends:
    """Test _fetch_and_cache with different backends."""

    def test_fetch_and_cache_endf_parserpy_success(
        self, temp_dir, realistic_endf_file_for_fetch, mock_requests_get
    ):
        """Test _fetch_and_cache successfully uses endf-parserpy backend."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library
        
        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)
        key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/293.6K"
        
        # Mock endf-parserpy backend (use _get_parser so we bypass Cpp/factory)
        mock_energy = np.array([1.0e5, 1.0e6, 5.0e6])
        mock_xs = np.array([10.0, 12.0, 15.0])
        mock_endf_dict = {
            3: {
                1: {  # MT=1 (total)
                    'E': mock_energy,
                    'XS': mock_xs,
                }
            }
        }
        mock_parser = Mock()
        mock_parser.parsefile.return_value = mock_endf_dict
        
        with patch.object(cache, '_get_parser', return_value=mock_parser):
            with patch.object(cache, '_ensure_endf_file', return_value=realistic_endf_file_for_fetch):
                energy, xs = cache._fetch_and_cache(nuc, "total", 293.6, Library.ENDF_B_VIII, key)
                
                # Verify results
                assert energy is not None
                assert xs is not None
                assert len(energy) == len(mock_energy)
                assert len(xs) == len(mock_xs)
                assert np.allclose(energy, mock_energy)
                assert np.allclose(xs, mock_xs)
                
                # Verify data was cached
                assert key in cache._memory_cache

    def test_fetch_and_cache_sandy_success(
        self, temp_dir, realistic_endf_file_for_fetch, mock_requests_get,
        mock_endf_parserpy_unavailable
    ):
        """Test _fetch_and_cache successfully uses SANDY backend when endf-parserpy unavailable."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library
        import sys
        
        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)
        key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/293.6K"
        
        # Mock SANDY backend
        mock_energy = np.array([1.0e5, 1.0e6, 5.0e6])
        mock_xs = np.array([10.0, 12.0, 15.0])
        
        # Mock sandy module - need to mock the import
        mock_sandy_module = MagicMock()
        mock_endf6 = MagicMock()
        mock_mf3_item = Mock()
        # SANDY uses pandas DataFrames with .values attribute
        mock_mf3_item.data = {
            'E': Mock(values=mock_energy),
            'XS': Mock(values=mock_xs),
        }
        mock_mf3 = [mock_mf3_item]
        mock_endf6.__contains__ = Mock(return_value=True)
        mock_endf6.filter_by = Mock(return_value=mock_mf3)
        mock_sandy_module.Endf6 = MagicMock()
        mock_sandy_module.Endf6.from_file = Mock(return_value=mock_endf6)
        
        # Patch the import inside the method
        with patch.dict('sys.modules', {'sandy': mock_sandy_module}):
            # Mock _ensure_endf_file
            with patch.object(cache, '_ensure_endf_file', return_value=realistic_endf_file_for_fetch):
                energy, xs = cache._fetch_and_cache(nuc, "total", 293.6, Library.ENDF_B_VIII, key)
                
                # Verify results
                assert energy is not None
                assert xs is not None
                assert len(energy) == len(mock_energy)
                assert len(xs) == len(mock_xs)
                assert np.allclose(energy, mock_energy)
                assert np.allclose(xs, mock_xs)
                
                # Verify data was cached
                assert key in cache._memory_cache

    def test_fetch_and_cache_endf_compatibility_success(
        self, temp_dir, realistic_endf_file_for_fetch, mock_requests_get,
        mock_endf_parserpy_unavailable, mock_sandy_unavailable
    ):
        """Test _fetch_and_cache successfully uses ENDFCompatibility backend."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library
        
        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)
        key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/293.6K"
        
        # Mock ENDFCompatibility
        mock_energy = np.array([1.0e5, 1.0e6, 5.0e6])
        mock_xs = np.array([10.0, 12.0, 15.0])
        
        # Create a mock reaction data object with xs dictionary
        mock_rxn_data = Mock()
        mock_rxn_data.xs = {
            "0K": Mock()
        }
        mock_rxn_data.xs["0K"].x = mock_energy
        mock_rxn_data.xs["0K"].y = mock_xs
        
        mock_evaluation = Mock()
        mock_evaluation.__contains__ = Mock(return_value=True)
        mock_evaluation.__getitem__ = Mock(return_value=mock_rxn_data)
        
        with patch('smrforge.core.endf_parser.ENDFCompatibility') as mock_compat:
            mock_compat.return_value = mock_evaluation
            
            # Mock _ensure_endf_file
            with patch.object(cache, '_ensure_endf_file', return_value=realistic_endf_file_for_fetch):
                energy, xs = cache._fetch_and_cache(nuc, "total", 293.6, Library.ENDF_B_VIII, key)
                
                # Verify results
                assert energy is not None
                assert xs is not None
                assert len(energy) == len(mock_energy)
                assert len(xs) == len(mock_xs)
                assert np.allclose(energy, mock_energy)
                assert np.allclose(xs, mock_xs)
                
                # Verify data was cached
                assert key in cache._memory_cache

    def test_fetch_and_cache_simple_parser_success(
        self, temp_dir, realistic_endf_file_for_fetch, mock_requests_get,
        mock_endf_parserpy_unavailable, mock_sandy_unavailable
    ):
        """Test _fetch_and_cache successfully uses simple parser fallback."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library
        
        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)
        key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/293.6K"
        
        # Mock ENDFCompatibility to fail
        mock_compat = MagicMock(side_effect=Exception("ENDFCompatibility failed"))
        
        with patch('smrforge.core.endf_parser.ENDFCompatibility', mock_compat):
            # Mock _ensure_endf_file
            with patch.object(cache, '_ensure_endf_file', return_value=realistic_endf_file_for_fetch):
                # Mock _simple_endf_parse to return data
                mock_energy = np.array([1.0e5, 1.0e6, 5.0e6])
                mock_xs = np.array([10.0, 12.0, 15.0])
                with patch.object(cache, '_simple_endf_parse', return_value=(mock_energy, mock_xs)):
                    energy, xs = cache._fetch_and_cache(nuc, "total", 293.6, Library.ENDF_B_VIII, key)
                    
                    # Verify results
                    assert energy is not None
                    assert xs is not None
                    assert len(energy) == len(mock_energy)
                    assert len(xs) == len(mock_xs)
                    assert np.allclose(energy, mock_energy)
                    assert np.allclose(xs, mock_xs)
                    
                    # Verify data was cached
                    assert key in cache._memory_cache

    def test_fetch_and_cache_doppler_broadening(
        self, temp_dir, realistic_endf_file_for_fetch, mock_requests_get
    ):
        """Test _fetch_and_cache applies Doppler broadening for non-standard temperatures."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library
        
        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)
        key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/600.0K"
        
        mock_energy = np.array([1.0e5, 1.0e6, 5.0e6])
        mock_xs = np.array([10.0, 12.0, 15.0])
        mock_endf_dict = {3: {1: {'E': mock_energy, 'XS': mock_xs}}}
        mock_parser = Mock()
        mock_parser.parsefile.return_value = mock_endf_dict
        
        with patch.object(cache, '_get_parser', return_value=mock_parser):
            with patch.object(cache, '_ensure_endf_file', return_value=realistic_endf_file_for_fetch):
                with patch.object(cache, '_doppler_broaden') as mock_doppler:
                    mock_doppler.return_value = mock_xs * 1.5  # Simulate broadening
                    
                    energy, xs = cache._fetch_and_cache(nuc, "total", 600.0, Library.ENDF_B_VIII, key)
                    
                    mock_doppler.assert_called_once()
                    call_args = mock_doppler.call_args
                    assert np.allclose(call_args[0][0], mock_energy)
                    assert np.allclose(call_args[0][1], mock_xs)
                    assert call_args[0][2] == 293.6
                    assert call_args[0][3] == 600.0
                    assert call_args[0][4] == 235
                    assert np.allclose(xs, mock_xs * 1.5)

    def test_fetch_and_cache_no_doppler_broadening_standard_temp(
        self, temp_dir, realistic_endf_file_for_fetch, mock_requests_get
    ):
        """Test _fetch_and_cache does NOT apply Doppler broadening for standard temperature (293.6K)."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library
        
        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)
        key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/293.6K"
        
        mock_energy = np.array([1.0e5, 1.0e6, 5.0e6])
        mock_xs = np.array([10.0, 12.0, 15.0])
        mock_endf_dict = {3: {1: {'E': mock_energy, 'XS': mock_xs}}}
        mock_parser = Mock()
        mock_parser.parsefile.return_value = mock_endf_dict
        
        with patch.object(cache, '_get_parser', return_value=mock_parser):
            with patch.object(cache, '_ensure_endf_file', return_value=realistic_endf_file_for_fetch):
                with patch.object(cache, '_doppler_broaden') as mock_doppler:
                    energy, xs = cache._fetch_and_cache(nuc, "total", 293.6, Library.ENDF_B_VIII, key)
                    
                    mock_doppler.assert_not_called()
                    assert np.allclose(energy, mock_energy)
                    assert np.allclose(xs, mock_xs)

    def test_fetch_and_cache_saves_to_cache(
        self, temp_dir, realistic_endf_file_for_fetch, mock_requests_get
    ):
        """Test _fetch_and_cache saves data to both memory and zarr cache."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library
        import zarr
        
        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)
        key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/293.6K"
        
        mock_energy = np.array([1.0e5, 1.0e6, 5.0e6])
        mock_xs = np.array([10.0, 12.0, 15.0])
        mock_endf_dict = {3: {1: {'E': mock_energy, 'XS': mock_xs}}}
        mock_parser = Mock()
        mock_parser.parsefile.return_value = mock_endf_dict
        
        with patch.object(cache, '_get_parser', return_value=mock_parser):
            with patch.object(cache, '_ensure_endf_file', return_value=realistic_endf_file_for_fetch):
                with patch.object(cache, '_save_to_cache') as mock_save:
                    energy, xs = cache._fetch_and_cache(nuc, "total", 293.6, Library.ENDF_B_VIII, key)
                    
                    mock_save.assert_called_once()
                    call_args = mock_save.call_args
                    assert call_args[0][0] == key
                    assert np.allclose(call_args[0][1], mock_energy)
                    assert np.allclose(call_args[0][2], mock_xs)

    def test_fetch_and_cache_backend_fallback_chain(
        self, temp_dir, realistic_endf_file_for_fetch, mock_requests_get,
        mock_endf_parserpy_unavailable, mock_sandy_unavailable
    ):
        """Test _fetch_and_cache falls back through backends correctly."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library
        
        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)
        key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/293.6K"
        
        # Mock ENDFCompatibility to fail, simple parser to succeed
        mock_compat = MagicMock(side_effect=Exception("ENDFCompatibility failed"))
        
        mock_energy = np.array([1.0e5, 1.0e6, 5.0e6])
        mock_xs = np.array([10.0, 12.0, 15.0])
        
        with patch('smrforge.core.endf_parser.ENDFCompatibility', mock_compat):
            with patch.object(cache, '_ensure_endf_file', return_value=realistic_endf_file_for_fetch):
                with patch.object(cache, '_simple_endf_parse', return_value=(mock_energy, mock_xs)):
                    energy, xs = cache._fetch_and_cache(nuc, "total", 293.6, Library.ENDF_B_VIII, key)
                    
                    # Verify it eventually succeeded with simple parser
                    assert energy is not None
                    assert xs is not None
                    assert np.allclose(energy, mock_energy)
                    assert np.allclose(xs, mock_xs)

    def test_fetch_and_cache_all_backends_fail(
        self, temp_dir, realistic_endf_file_for_fetch, mock_requests_get,
        mock_endf_parserpy_unavailable, mock_sandy_unavailable
    ):
        """Test _fetch_and_cache raises ImportError when all backends fail."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library
        
        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)
        key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/293.6K"
        
        # Mock all backends to fail
        mock_compat = MagicMock(side_effect=Exception("ENDFCompatibility failed"))
        
        with patch('smrforge.core.endf_parser.ENDFCompatibility', mock_compat):
            with patch.object(cache, '_ensure_endf_file', return_value=realistic_endf_file_for_fetch):
                with patch.object(cache, '_simple_endf_parse', return_value=(None, None)):
                    with pytest.raises(ImportError) as exc_info:
                        cache._fetch_and_cache(nuc, "total", 293.6, Library.ENDF_B_VIII, key)
                    
                    # Verify error message is informative
                    assert "Failed to parse cross-section data" in str(exc_info.value)
                    assert "No suitable backend available" in str(exc_info.value)

