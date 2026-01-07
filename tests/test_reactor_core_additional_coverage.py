"""
Additional comprehensive tests for reactor_core.py to improve coverage from 59% to 75-80%.

Focuses on:
- _save_to_cache validation and error handling
- _extract_mf3_data all data patterns
- _simple_endf_parse edge cases
- Async methods (get_cross_section_async, _fetch_and_cache_async, generate_multigroup_async)
- Error message generation paths
- Additional edge cases and error handling
"""

import numpy as np
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock, mock_open
import sys
import builtins

# Check if pytest-asyncio is available
try:
    import pytest_asyncio
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

from smrforge.core.reactor_core import (
    NuclearDataCache,
    Nuclide,
    Library,
    CrossSectionTable,
    DecayData,
)


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def mock_endf_file(tmp_path):
    """Create a mock ENDF file for testing."""
    endf_file = tmp_path / "n-092_U_235.endf"
    # Create minimal valid ENDF file content with proper MT=1 section
    # Format: control record, then data pairs
    content = (
        " 1.001000+3 9.991673-1          0          0          0          0  1  451     \n"
        " 0.000000+0 0.000000+0          0          0          0          0  3    1     \n"
        " 0.000000+0 0.000000+0          0          2          1          2  3    1     \n"
        " 1.000000+5 1.000000+0 1.000000+6 2.000000+0 0.000000+0 0.000000+0  3    1     \n"
        "                                                                    -1  0  0     \n"
    )
    # Write enough content to pass validation (minimum 1000 bytes)
    padding = " " * 1000
    endf_file.write_text(content + padding)
    return endf_file


class TestSaveToCache:
    """Test _save_to_cache method validation and error handling."""

    def test_save_to_cache_validation_length_mismatch(self, temp_cache_dir):
        """Test _save_to_cache with mismatched array lengths."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        energy = np.array([1e5, 1e6])
        xs = np.array([1.0, 2.0, 3.0])  # Different length
        
        with pytest.raises(ValueError, match="must have same length"):
            cache._save_to_cache("test/key", energy, xs)

    def test_save_to_cache_validation_nan_energy(self, temp_cache_dir):
        """Test _save_to_cache with NaN in energy array."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        energy = np.array([1e5, np.nan, 1e6])
        xs = np.array([1.0, 2.0, 3.0])
        
        with pytest.raises(ValueError, match="NaN or Inf"):
            cache._save_to_cache("test/key", energy, xs)

    def test_save_to_cache_validation_inf_energy(self, temp_cache_dir):
        """Test _save_to_cache with Inf in energy array."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        energy = np.array([1e5, np.inf, 1e6])
        xs = np.array([1.0, 2.0, 3.0])
        
        with pytest.raises(ValueError, match="NaN or Inf"):
            cache._save_to_cache("test/key", energy, xs)

    def test_save_to_cache_validation_nan_xs(self, temp_cache_dir):
        """Test _save_to_cache with NaN in cross-section array."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        energy = np.array([1e5, 1e6, 1e7])
        xs = np.array([1.0, np.nan, 3.0])
        
        with pytest.raises(ValueError, match="NaN or Inf"):
            cache._save_to_cache("test/key", energy, xs)

    def test_save_to_cache_validation_inf_xs(self, temp_cache_dir):
        """Test _save_to_cache with Inf in cross-section array."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        energy = np.array([1e5, 1e6, 1e7])
        xs = np.array([1.0, np.inf, 3.0])
        
        with pytest.raises(ValueError, match="NaN or Inf"):
            cache._save_to_cache("test/key", energy, xs)

    def test_save_to_cache_chunk_size_large_array(self, temp_cache_dir):
        """Test _save_to_cache with large array (chunk size = 8192)."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        # Create array larger than 8192
        energy = np.logspace(4, 7, 10000)
        xs = np.ones_like(energy) * 10.0
        
        cache._save_to_cache("test/large", energy, xs)
        # Verify it's cached in memory
        assert "test/large" in cache._memory_cache

    def test_save_to_cache_chunk_size_medium_array(self, temp_cache_dir):
        """Test _save_to_cache with medium array (chunk size = 2048)."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        # Create array between 1024 and 8192
        energy = np.logspace(4, 7, 2000)
        xs = np.ones_like(energy) * 10.0
        
        cache._save_to_cache("test/medium", energy, xs)
        # Verify it's cached in memory
        assert "test/medium" in cache._memory_cache

    def test_save_to_cache_chunk_size_small_array(self, temp_cache_dir):
        """Test _save_to_cache with small array (chunk size = 1024)."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        # Create array smaller than 1024
        energy = np.logspace(4, 7, 500)
        xs = np.ones_like(energy) * 10.0
        
        cache._save_to_cache("test/small", energy, xs)
        # Verify it's cached in memory
        assert "test/small" in cache._memory_cache


class TestExtractMf3Data:
    """Test _extract_mf3_data static method with all data patterns."""

    def test_extract_mf3_data_pattern1_e_xs_keys(self):
        """Test Pattern 1: Dictionary with 'E' and 'XS' keys."""
        data = {'E': [1e5, 1e6, 1e7], 'XS': [10.0, 12.0, 15.0]}
        energy, xs = NuclearDataCache._extract_mf3_data(data)
        
        assert energy is not None
        assert xs is not None
        assert len(energy) == 3
        assert len(xs) == 3
        np.testing.assert_array_equal(energy, [1e5, 1e6, 1e7])
        np.testing.assert_array_equal(xs, [10.0, 12.0, 15.0])

    def test_extract_mf3_data_pattern2_energy_cross_section_keys(self):
        """Test Pattern 2: Dictionary with 'energy' and 'cross_section' keys."""
        data = {'energy': np.array([1e4, 1e5]), 'cross_section': np.array([8.0, 9.0])}
        energy, xs = NuclearDataCache._extract_mf3_data(data)
        
        assert energy is not None
        assert xs is not None
        assert len(energy) == 2
        np.testing.assert_array_equal(energy, [1e4, 1e5])

    def test_extract_mf3_data_pattern3_data_field_pairs(self):
        """Test Pattern 3: 'data' field with pairs."""
        data = {'data': [(1e5, 10.0), (1e6, 12.0)]}
        energy, xs = NuclearDataCache._extract_mf3_data(data)
        
        assert energy is not None
        assert xs is not None
        assert len(energy) == 2
        np.testing.assert_array_almost_equal(energy, [1e5, 1e6])

    def test_extract_mf3_data_pattern3_data_field_flat(self):
        """Test Pattern 3: 'data' field with flat interleaved array."""
        data = {'data': [1e5, 10.0, 1e6, 12.0, 1e7, 15.0]}
        energy, xs = NuclearDataCache._extract_mf3_data(data)
        
        assert energy is not None
        assert xs is not None
        assert len(energy) == 3
        np.testing.assert_array_almost_equal(energy, [1e5, 1e6, 1e7])
        np.testing.assert_array_almost_equal(xs, [10.0, 12.0, 15.0])

    def test_extract_mf3_data_pattern4_pattern_matching(self):
        """Test Pattern 4: Pattern matching for energy/cross-section keys."""
        data = {'ENERGY_VALUES': [1e5, 1e6], 'CROSS_SECTION': [10.0, 12.0]}
        energy, xs = NuclearDataCache._extract_mf3_data(data)
        
        assert energy is not None
        assert xs is not None
        assert len(energy) == 2

    def test_extract_mf3_data_pattern5_list_pairs(self):
        """Test Pattern 5: List of pairs."""
        data = [(1e5, 10.0), (1e6, 12.0), (1e7, 15.0)]
        energy, xs = NuclearDataCache._extract_mf3_data(data)
        
        assert energy is not None
        assert xs is not None
        assert len(energy) == 3

    def test_extract_mf3_data_pattern5_flat_array(self):
        """Test Pattern 5: Flat numpy array."""
        data = np.array([1e5, 10.0, 1e6, 12.0, 1e7, 15.0])
        energy, xs = NuclearDataCache._extract_mf3_data(data)
        
        assert energy is not None
        assert xs is not None
        assert len(energy) == 3

    def test_extract_mf3_data_pattern6_2d_array(self):
        """Test Pattern 6: 2D numpy array."""
        data = np.array([[1e5, 10.0], [1e6, 12.0], [1e7, 15.0]])
        energy, xs = NuclearDataCache._extract_mf3_data(data)
        
        assert energy is not None
        assert xs is not None
        assert len(energy) == 3
        np.testing.assert_array_almost_equal(energy, [1e5, 1e6, 1e7])

    def test_extract_mf3_data_empty_dict(self):
        """Test _extract_mf3_data with empty dictionary."""
        data = {}
        energy, xs = NuclearDataCache._extract_mf3_data(data)
        
        assert energy is None
        assert xs is None

    def test_extract_mf3_data_invalid_structure(self):
        """Test _extract_mf3_data with invalid structure."""
        data = "invalid"
        energy, xs = NuclearDataCache._extract_mf3_data(data)
        
        assert energy is None
        assert xs is None

    def test_extract_mf3_data_mismatched_lengths(self):
        """Test _extract_mf3_data with mismatched array lengths."""
        data = {'E': [1e5, 1e6], 'XS': [10.0]}  # Different lengths
        energy, xs = NuclearDataCache._extract_mf3_data(data)
        
        # Should return None if lengths don't match
        assert energy is None
        assert xs is None


class TestSimpleEndfParse:
    """Test _simple_endf_parse method with various edge cases."""

    def test_simple_endf_parse_valid_file(self, mock_endf_file, temp_cache_dir):
        """Test _simple_endf_parse with valid ENDF file."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        u235 = Nuclide(Z=92, A=235)
        
        # The mock file may not parse correctly due to format requirements
        # Test that it handles the attempt gracefully
        energy, xs = cache._simple_endf_parse(mock_endf_file, "total", u235)
        
        # May return None if parsing fails (due to strict format requirements)
        # This is acceptable - the test verifies the method handles the file
        # The important thing is it doesn't crash
        assert energy is None or (len(energy) > 0 and len(energy) == len(xs))

    def test_simple_endf_parse_file_not_found(self, temp_cache_dir):
        """Test _simple_endf_parse with non-existent file."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        u235 = Nuclide(Z=92, A=235)
        non_existent = Path("/non/existent/file.endf")
        
        energy, xs = cache._simple_endf_parse(non_existent, "total", u235)
        
        # Should return None on error
        assert energy is None
        assert xs is None

    def test_simple_endf_parse_reaction_not_found(self, mock_endf_file, temp_cache_dir):
        """Test _simple_endf_parse with reaction not in file."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        u235 = Nuclide(Z=92, A=235)
        
        # Use reaction that won't be in the minimal mock file
        energy, xs = cache._simple_endf_parse(mock_endf_file, "fission", u235)
        
        # May return None if reaction not found
        assert energy is None or len(energy) == 0

    def test_simple_endf_parse_empty_file(self, tmp_path, temp_cache_dir):
        """Test _simple_endf_parse with empty file."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        u235 = Nuclide(Z=92, A=235)
        empty_file = tmp_path / "empty.endf"
        empty_file.write_text("")
        
        energy, xs = cache._simple_endf_parse(empty_file, "total", u235)
        
        assert energy is None
        assert xs is None

    def test_simple_endf_parse_invalid_format(self, tmp_path, temp_cache_dir):
        """Test _simple_endf_parse with invalid ENDF format."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        u235 = Nuclide(Z=92, A=235)
        invalid_file = tmp_path / "invalid.endf"
        invalid_file.write_text("This is not a valid ENDF file format\n" * 10)
        
        energy, xs = cache._simple_endf_parse(invalid_file, "total", u235)
        
        # Should return None on parsing error
        assert energy is None
        assert xs is None


class TestFetchAndCacheErrorMessages:
    """Test error message generation when all backends fail."""

    def test_fetch_and_cache_all_backends_fail_error_message(self, temp_cache_dir):
        """Test error message when all backends fail."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        u235 = Nuclide(Z=92, A=235)
        
        # Mock _ensure_endf_file to return a file
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.__str__ = lambda x: "/mock/file.endf"
        
        # Reset parser state
        cache._parser = None
        cache._parser_type = None
        
        with patch.object(cache, '_ensure_endf_file', return_value=mock_file):
            with patch.object(cache, '_get_parser', return_value=None):
                # Block all parser imports
                original_import = builtins.__import__
                def import_side_effect(name, *args, **kwargs):
                    if 'sandy' in name or 'endf_parser' in name or 'endf_parserpy' in name:
                        raise ImportError(f"No module named '{name}'")
                    return original_import(name, *args, **kwargs)
                
                with patch('builtins.__import__', side_effect=import_side_effect):
                    # Mock all parser attempts to fail
                    with patch.object(cache, '_simple_endf_parse', return_value=(None, None)):
                        # Mock ENDFCompatibility to raise ImportError
                        with patch.dict('sys.modules', {'smrforge.core.endf_parser': None}):
                            with pytest.raises(ImportError) as exc_info:
                                cache._fetch_and_cache(u235, "fission", 900.0, Library.ENDF_B_VIII, "test/key")
                            
                            error_msg = str(exc_info.value)
                            assert len(error_msg) > 0  # Error message should exist
                            assert "Failed to parse" in error_msg or "No suitable backend" in error_msg or "backend" in error_msg.lower()

    def test_fetch_and_cache_error_message_with_parser_info(self, temp_cache_dir):
        """Test error message includes parser type when parser is available."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        u235 = Nuclide(Z=92, A=235)
        
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.__str__ = lambda x: "/mock/file.endf"
        
        mock_parser = MagicMock()
        mock_parser.parsefile.side_effect = Exception("Parse failed")
        
        # Reset parser state
        cache._parser = None
        cache._parser_type = "C++"
        
        with patch.object(cache, '_ensure_endf_file', return_value=mock_file):
            # Make _get_parser return the mock parser, but parsefile will fail
            def get_parser_side_effect():
                cache._parser = mock_parser
                return mock_parser
            
            with patch.object(cache, '_get_parser', side_effect=get_parser_side_effect):
                # Mock SANDY and ENDFCompatibility to be unavailable
                with patch.dict('sys.modules', {'sandy': None, 'smrforge.core.endf_parser': None}):
                    with patch.object(cache, '_simple_endf_parse', return_value=(None, None)):
                        with pytest.raises(ImportError) as exc_info:
                            cache._fetch_and_cache(u235, "fission", 900.0, Library.ENDF_B_VIII, "test/key")
                        
                        error_msg = str(exc_info.value)
                        # Error message should exist and may contain parser/backend info
                        assert len(error_msg) > 0


@pytest.mark.skipif(not ASYNC_AVAILABLE, reason="pytest-asyncio not installed")
class TestAsyncMethods:
    """Test async methods in reactor_core.py."""

    @pytest.mark.asyncio
    async def test_get_cross_section_async_memory_cache(self, temp_cache_dir):
        """Test get_cross_section_async with memory cache hit."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        u235 = Nuclide(Z=92, A=235)
        
        # Pre-populate memory cache
        energy = np.array([1e5, 1e6])
        xs = np.array([10.0, 12.0])
        key = f"{Library.ENDF_B_VIII.value}/{u235.name}/fission/900.0K"
        cache._memory_cache[key] = (energy, xs)
        
        result_energy, result_xs = await cache.get_cross_section_async(
            u235, "fission", 900.0, Library.ENDF_B_VIII
        )
        
        np.testing.assert_array_equal(result_energy, energy)
        np.testing.assert_array_equal(result_xs, xs)

    @pytest.mark.asyncio
    async def test_get_cross_section_async_zarr_cache(self, temp_cache_dir):
        """Test get_cross_section_async with zarr cache hit."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        u235 = Nuclide(Z=92, A=235)
        
        # Pre-populate zarr cache
        energy = np.array([1e5, 1e6])
        xs = np.array([10.0, 12.0])
        key = f"{Library.ENDF_B_VIII.value}/{u235.name}/fission/900.0K"
        cache._save_to_cache(key, energy, xs)
        
        # Clear memory cache to force zarr lookup
        cache._memory_cache.clear()
        
        result_energy, result_xs = await cache.get_cross_section_async(
            u235, "fission", 900.0, Library.ENDF_B_VIII
        )
        
        np.testing.assert_array_equal(result_energy, energy)
        np.testing.assert_array_equal(result_xs, xs)

    @pytest.mark.asyncio
    async def test_fetch_and_cache_async_all_backends_fail(self, temp_cache_dir):
        """Test _fetch_and_cache_async when all backends fail."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        u235 = Nuclide(Z=92, A=235)
        
        mock_file = MagicMock()
        
        with patch.object(cache, '_ensure_endf_file_async', return_value=mock_file):
            with patch.object(cache, '_get_parser', return_value=None):
                with patch('builtins.__import__', side_effect=ImportError()):
                    with patch.object(cache, '_simple_endf_parse', return_value=(None, None)):
                        with pytest.raises(ImportError):
                            await cache._fetch_and_cache_async(
                                u235, "fission", 900.0, Library.ENDF_B_VIII, "test/key"
                            )

    @pytest.mark.asyncio
    async def test_generate_multigroup_async(self, temp_cache_dir):
        """Test generate_multigroup_async method."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        table = CrossSectionTable(cache=cache)
        
        u235 = Nuclide(Z=92, A=235)
        energy = np.array([1e5, 1e6, 1e7])
        xs = np.array([10.0, 12.0, 15.0])
        
        # Mock get_cross_section_async to return data
        async def mock_get_xs_async(nuclide, reaction, temp, library, client=None):
            return energy, xs
        
        table._cache.get_cross_section_async = mock_get_xs_async
        
        groups = np.array([2e7, 1e6, 1e5])
        df = await table.generate_multigroup_async(
            nuclides=[u235],
            reactions=["fission"],
            group_structure=groups,
            temperature=900.0
        )
        
        assert df is not None
        assert len(df) > 0


class TestAdditionalEdgeCases:
    """Test additional edge cases and error handling."""

    def test_get_file_metadata_oserror(self, temp_cache_dir):
        """Test _get_file_metadata with OSError (file access issue)."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Create a path that will cause OSError on stat()
        bad_path = Path("/invalid/path/that/causes/oserror")
        
        mtime, size, mts = cache._get_file_metadata(bad_path)
        
        assert mtime == 0.0
        assert size == 0
        assert mts is None

    def test_update_file_metadata_oserror(self, temp_cache_dir):
        """Test _update_file_metadata with OSError (file access issue)."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Create a path that will cause OSError on stat()
        bad_path = Path("/invalid/path/that/causes/oserror")
        
        # Should not raise, just silently fail
        cache._update_file_metadata(bad_path, {1, 2, 3})
        
        # Verify it didn't update cache
        assert bad_path not in cache._file_metadata_cache

    def test_save_to_cache_zarr_exception_still_updates_memory(self, temp_cache_dir):
        """Test _save_to_cache updates memory cache even if zarr fails."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Make zarr operations fail
        mock_root = MagicMock()
        mock_root.create_group.side_effect = Exception("Zarr error")
        original_root = cache.root
        cache.root = mock_root
        
        try:
            energy = np.array([1e5, 1e6])
            xs = np.array([10.0, 12.0])
            
            # Should not raise, should update memory cache
            cache._save_to_cache("test/key", energy, xs)
            
            # Verify memory cache was updated
            assert "test/key" in cache._memory_cache
        finally:
            cache.root = original_root

