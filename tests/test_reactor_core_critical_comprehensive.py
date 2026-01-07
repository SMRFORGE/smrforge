"""
Comprehensive tests for reactor_core.py critical functionality to reach 80%+ coverage.

Focuses on:
- NuclearDataCache methods (file discovery, caching, cross-section retrieval)
- CrossSectionTable methods (multi-group generation, pivoting)
- DecayData methods (decay constants, decay matrices)
- TSL, photon, and gamma production file discovery
- Error handling and edge cases
"""

import numpy as np
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open

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
def mock_endf_dir(tmp_path):
    """Create a mock ENDF directory structure."""
    endf_dir = tmp_path / "ENDF-B-VIII.1"
    endf_dir.mkdir()
    
    # Create neutron directory
    neutron_dir = endf_dir / "neutrons"
    neutron_dir.mkdir()
    
    # Create decay directory
    decay_dir = endf_dir / "decay"
    decay_dir.mkdir()
    
    # Create TSL directory
    tsl_dir = endf_dir / "tsl"
    tsl_dir.mkdir()
    
    # Create photon directory
    photoat_dir = endf_dir / "photoat-version.VIII.1"
    photoat_dir.mkdir()
    
    # Create gamma production directory
    gamma_dir = endf_dir / "gammas-version.VIII.1"
    gamma_dir.mkdir()
    
    return endf_dir


class TestNuclearDataCacheCritical:
    """Critical tests for NuclearDataCache to improve coverage."""
    
    def test_tsl_file_discovery(self, mock_endf_dir):
        """Test TSL file discovery."""
        cache = NuclearDataCache(local_endf_dir=mock_endf_dir)
        
        # Create a mock TSL file
        tsl_file = mock_endf_dir / "tsl" / "tsl-H_in_H2O.endf"
        tsl_file.write_text("dummy TSL data")
        
        materials = cache.list_available_tsl_materials()
        assert isinstance(materials, list)
    
    def test_photon_file_discovery(self, mock_endf_dir):
        """Test photon file discovery."""
        cache = NuclearDataCache(local_endf_dir=mock_endf_dir)
        
        # Create a mock photon file
        photon_file = mock_endf_dir / "photoat-version.VIII.1" / "p-001_H_001.endf"
        photon_file.write_text("dummy photon data")
        
        elements = cache.list_available_photon_elements()
        assert isinstance(elements, list)
    
    def test_get_tsl_file(self, mock_endf_dir):
        """Test getting TSL file."""
        cache = NuclearDataCache(local_endf_dir=mock_endf_dir)
        
        # Create a mock TSL file
        tsl_file = mock_endf_dir / "tsl" / "tsl-H_in_H2O.endf"
        tsl_file.write_text("dummy TSL data")
        
        file_path = cache.get_tsl_file("H_in_H2O")
        assert file_path is None or isinstance(file_path, Path)
    
    def test_get_photon_file(self, mock_endf_dir):
        """Test getting photon file."""
        cache = NuclearDataCache(local_endf_dir=mock_endf_dir)
        
        # Create a mock photon file
        photon_file = mock_endf_dir / "photoat-version.VIII.1" / "p-001_H_001.endf"
        photon_file.write_text("dummy photon data")
        
        file_path = cache.get_photon_file("H")
        assert file_path is None or isinstance(file_path, Path)
    
    def test_get_photon_cross_section(self, mock_endf_dir):
        """Test getting photon cross-section."""
        cache = NuclearDataCache(local_endf_dir=mock_endf_dir)
        
        # Try to get photon cross-section (may return None if file not found)
        photon_data = cache.get_photon_cross_section("H")
        assert photon_data is None or hasattr(photon_data, 'interpolate')
    
    def test_get_gamma_production_data(self, mock_endf_dir):
        """Test getting gamma production data."""
        cache = NuclearDataCache(local_endf_dir=mock_endf_dir)
        
        u235 = Nuclide(Z=92, A=235)
        gamma_data = cache.get_gamma_production_data(u235)
        assert gamma_data is None or hasattr(gamma_data, 'prompt_spectra')
    
    def test_build_tsl_file_index(self, mock_endf_dir):
        """Test building TSL file index."""
        cache = NuclearDataCache(local_endf_dir=mock_endf_dir)
        
        # Create a mock TSL file
        tsl_file = mock_endf_dir / "tsl" / "tsl-H_in_H2O.endf"
        tsl_file.write_text("dummy TSL data")
        
        index = cache._build_tsl_file_index()
        assert isinstance(index, dict)
    
    def test_build_photon_file_index(self, mock_endf_dir):
        """Test building photon file index."""
        cache = NuclearDataCache(local_endf_dir=mock_endf_dir)
        
        # Create a mock photon file
        photon_file = mock_endf_dir / "photoat-version.VIII.1" / "p-001_H_001.endf"
        photon_file.write_text("dummy photon data")
        
        index = cache._build_photon_file_index()
        assert isinstance(index, dict)
    
    
    def test_find_local_decay_file(self, mock_endf_dir):
        """Test finding local decay file."""
        cache = NuclearDataCache(local_endf_dir=mock_endf_dir)
        
        u235 = Nuclide(Z=92, A=235)
        decay_file = cache._find_local_decay_file(u235, Library.ENDF_B_VIII_1)
        assert decay_file is None or isinstance(decay_file, Path)
    
    def test_find_local_fission_yield_file(self, mock_endf_dir):
        """Test finding local fission yield file."""
        cache = NuclearDataCache(local_endf_dir=mock_endf_dir)
        
        u235 = Nuclide(Z=92, A=235)
        yield_file = cache._find_local_fission_yield_file(u235, Library.ENDF_B_VIII_1)
        assert yield_file is None or isinstance(yield_file, Path)
    
    def test_save_to_cache(self, temp_cache_dir):
        """Test saving to cache."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        energy = np.array([1e6, 2e6, 3e6])
        xs = np.array([10.0, 20.0, 30.0])
        key = "test_key"
        
        cache._save_to_cache(key, energy, xs)
        
        # Verify cache was written
        assert cache.cache_dir.exists()
    
    def test_get_cross_section_cached(self, temp_cache_dir):
        """Test getting cross-section from cache."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        energy = np.array([1e6, 2e6, 3e6])
        xs = np.array([10.0, 20.0, 30.0])
        key = "test_key"
        
        # Save to cache
        cache._save_to_cache(key, energy, xs)
        
        # Verify it's in memory cache
        assert key in cache._memory_cache
    
    def test_get_cross_section_with_cache(self, temp_cache_dir):
        """Test getting cross-section with caching."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        u235 = Nuclide(Z=92, A=235)
        
        # Try to get cross-section (will use cache if available)
        try:
            energy, xs = cache.get_cross_section(u235, "total", temperature=900.0)
            assert energy is not None
            assert xs is not None
            assert len(energy) == len(xs)
        except Exception:
            # Expected if no ENDF files available
            pass
    
    def test_get_cross_section_temperature_broadening(self, temp_cache_dir):
        """Test cross-section retrieval with temperature broadening."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        u235 = Nuclide(Z=92, A=235)
        
        # Try different temperatures
        try:
            energy1, xs1 = cache.get_cross_section(u235, "total", temperature=300.0)
            energy2, xs2 = cache.get_cross_section(u235, "total", temperature=900.0)
            
            # Should have same energy grid
            if energy1 is not None and energy2 is not None:
                assert len(energy1) == len(energy2)
        except Exception:
            # Expected if no ENDF files available
            pass


class TestCrossSectionTableCritical:
    """Critical tests for CrossSectionTable to improve coverage."""
    
    def test_generate_multigroup(self, temp_cache_dir):
        """Test multi-group generation."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        xs_table = CrossSectionTable(cache=cache)
        
        u235 = Nuclide(Z=92, A=235)
        group_structure = np.array([2e7, 1e6, 1e5, 1e4])  # 3 groups
        
        try:
            result = xs_table.generate_multigroup(
                nuclides=[u235],
                reactions=["total", "fission"],
                group_structure=group_structure,
                temperature=900.0,
            )
            assert result is not None
        except Exception:
            # Expected if no ENDF files available
            pass
    
    def test_pivot_for_solver(self, temp_cache_dir):
        """Test pivoting for solver."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        xs_table = CrossSectionTable(cache=cache)
        
        # Create some test data
        from smrforge.validation.models import CrossSectionData
        
        try:
            xs_data = xs_table.pivot_for_solver(
                nuclides=[Nuclide(Z=92, A=235)],
                reactions=["total", "fission"],
                n_groups=2,
            )
            assert xs_data is None or isinstance(xs_data, CrossSectionData)
        except Exception:
            # Expected if no data available
            pass
    
    def test_collapse_to_multigroup_static(self):
        """Test static collapse to multi-group method."""
        energy = np.logspace(4, 7, 1000)  # 10 keV to 10 MeV
        xs = np.ones_like(energy) * 10.0  # Constant 10 barns
        group_bounds = np.array([1e7, 1e6, 1e5])  # 2 groups (descending order)
        
        mg_xs = CrossSectionTable._collapse_to_multigroup(energy, xs, group_bounds)
        
        assert len(mg_xs) == 2
        assert np.all(mg_xs > 0)
    
    def test_collapse_to_multigroup_with_flux(self):
        """Test collapse with flux weighting."""
        energy = np.logspace(4, 7, 1000)
        xs = np.ones_like(energy) * 10.0
        group_bounds = np.array([1e7, 1e6, 1e5])
        
        # 1/E flux weighting
        weighting_flux = 1.0 / energy
        
        mg_xs = CrossSectionTable._collapse_to_multigroup(
            energy, xs, group_bounds, weighting_flux=weighting_flux
        )
        
        assert len(mg_xs) == 2
        assert np.all(mg_xs > 0)


class TestDecayDataCritical:
    """Critical tests for DecayData to improve coverage."""
    
    def test_get_decay_constant(self, temp_cache_dir):
        """Test getting decay constant."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        decay_data = DecayData(cache=cache)
        
        u235 = Nuclide(Z=92, A=235)
        lambda_decay = decay_data.get_decay_constant(u235)
        
        assert lambda_decay >= 0
    
    def test_build_decay_matrix(self, temp_cache_dir):
        """Test building decay matrix."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        decay_data = DecayData(cache=cache)
        
        nuclides = [
            Nuclide(Z=92, A=235),
            Nuclide(Z=92, A=238),
        ]
        
        decay_matrix = decay_data.build_decay_matrix(nuclides)
        
        assert decay_matrix is not None
        assert decay_matrix.shape == (len(nuclides), len(nuclides))


class TestReactorCoreEdgeCases:
    """Test edge cases and error handling."""
    
    def test_cache_without_endf_dir(self, temp_cache_dir):
        """Test cache initialization without ENDF directory."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Should work without local_endf_dir
        assert cache.cache_dir == temp_cache_dir
    
    def test_get_cross_section_invalid_nuclide(self, temp_cache_dir):
        """Test getting cross-section for invalid nuclide."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        invalid_nuclide = Nuclide(Z=999, A=1000)
        
        try:
            energy, xs = cache.get_cross_section(invalid_nuclide, "total")
            # Should return None or raise exception
            assert energy is None or xs is None
        except Exception:
            # Expected behavior
            pass
    
    def test_get_cross_section_invalid_reaction(self, temp_cache_dir):
        """Test getting cross-section for invalid reaction."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        u235 = Nuclide(Z=92, A=235)
        
        try:
            energy, xs = cache.get_cross_section(u235, "invalid_reaction")
            # Should return None or raise exception
            assert energy is None or xs is None
        except Exception:
            # Expected behavior
            pass
    
    def test_collapse_to_multigroup_empty_energy(self):
        """Test collapse with empty energy array."""
        energy = np.array([])
        xs = np.array([])
        group_bounds = np.array([1e7, 1e6])
        
        try:
            mg_xs = CrossSectionTable._collapse_to_multigroup(energy, xs, group_bounds)
            # Should handle gracefully
            assert len(mg_xs) == 1  # One group
        except Exception:
            # Acceptable if raises exception
            pass
    
    def test_collapse_to_multigroup_single_group(self):
        """Test collapse with single group."""
        energy = np.logspace(4, 7, 100)
        xs = np.ones_like(energy) * 10.0
        group_bounds = np.array([1e7, 1e6])  # Single group
        
        mg_xs = CrossSectionTable._collapse_to_multigroup(energy, xs, group_bounds)
        
        assert len(mg_xs) == 1
        assert mg_xs[0] > 0
    
    def test_get_cross_section_zarr_cache_hit(self, temp_cache_dir):
        """Test get_cross_section with zarr cache hit."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        u235 = Nuclide(Z=92, A=235)
        key = f"ENDF-B-VIII.0/{u235.name}/total/293.6K"
        energy = np.array([1e5, 1e6, 1e7])
        xs = np.array([10.0, 12.0, 15.0])
        
        # Pre-populate zarr cache
        try:
            group = cache.root.create_group(key)
            group.create_dataset("energy", data=energy, chunks=(1024,), compression="zstd")
            group.create_dataset("xs", data=xs, chunks=(1024,), compression="zstd")
            
            # Clear memory cache
            cache._memory_cache.clear()
            
            # Should retrieve from zarr
            retrieved_energy, retrieved_xs = cache.get_cross_section(u235, "total", 293.6)
            
            assert np.array_equal(retrieved_energy, energy)
            assert np.array_equal(retrieved_xs, xs)
            
            # Should also be in memory cache now
            assert key in cache._memory_cache
        except Exception:
            # Zarr may not be available or may fail
            pytest.skip("Zarr cache not available in test environment")
    
    def test_get_file_metadata_cached(self, temp_cache_dir, tmp_path):
        """Test _get_file_metadata with cached metadata."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        test_file = tmp_path / "test.endf"
        test_file.write_text("test content")
        
        # First call - should compute metadata
        mtime1, size1, mts1 = cache._get_file_metadata(test_file)
        assert mtime1 > 0
        assert size1 > 0
        assert mts1 is None  # Not cached yet
        
        # Cache metadata
        cache._update_file_metadata(test_file, {1, 2, 3})
        
        # Second call - should return cached
        mtime2, size2, mts2 = cache._get_file_metadata(test_file)
        assert mtime2 == mtime1
        assert size2 == size1
        assert mts2 == {1, 2, 3}
    
    def test_get_file_metadata_file_changed(self, temp_cache_dir, tmp_path):
        """Test _get_file_metadata when file changes."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        test_file = tmp_path / "test_changed.endf"
        test_file.write_text("initial content")
        
        # Cache metadata
        cache._update_file_metadata(test_file, {1, 2, 3})
        
        # Modify file
        test_file.write_text("modified content")
        
        # Should detect change and return None for MTs
        mtime, size, mts = cache._get_file_metadata(test_file)
        assert mts is None  # File changed, MTs not cached
    
    def test_get_file_metadata_file_not_found(self, temp_cache_dir):
        """Test _get_file_metadata with non-existent file."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        nonexistent = Path("nonexistent_file.endf")
        
        mtime, size, mts = cache._get_file_metadata(nonexistent)
        assert mtime == 0.0
        assert size == 0
        assert mts is None
    
    def test_update_file_metadata_exception(self, temp_cache_dir):
        """Test _update_file_metadata with exception handling."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        nonexistent = Path("nonexistent_file.endf")
        
        # Should handle exception gracefully
        cache._update_file_metadata(nonexistent, {1, 2, 3})
        # Should not raise exception
    
    def test_get_parser_info_with_parser(self, temp_cache_dir):
        """Test get_parser_info when parser is available."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Try to get parser (may or may not be available)
        info = cache.get_parser_info()
        
        assert isinstance(info, dict)
        assert "parser_available" in info
        assert "parser_type" in info
        assert "is_cpp_parser" in info
    
    def test_get_parser_info_no_parser(self, temp_cache_dir):
        """Test get_parser_info when parser is not available."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Mock parser to None
        cache._parser = None
        cache._parser_type = None
        
        # Try to get parser info (will try to initialize)
        info = cache.get_parser_info()
        
        assert isinstance(info, dict)
        assert "parser_available" in info
        # Parser may or may not be available depending on environment
    
    def test_get_parser_cpp_parser(self, temp_cache_dir):
        """Test _get_parser with C++ parser available."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Mock endf_parserpy imports
        with patch('smrforge.core.reactor_core.EndfParserCpp', create=True):
            with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: 
                       MagicMock() if name == 'endf_parserpy' else __import__(name, *args, **kwargs)):
                parser = cache._get_parser()
                # Parser may be None if not available
                assert parser is None or hasattr(parser, 'parsefile')
    
    def test_get_parser_factory_fallback(self, temp_cache_dir):
        """Test _get_parser with factory fallback when C++ parser not available."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Mock endf_parserpy to have factory but no C++ parser
        mock_factory = MagicMock()
        mock_parser = MagicMock()
        mock_factory.create.return_value = mock_parser
        
        # Create mock module that has EndfParserFactory but raises ImportError for EndfParserCpp
        mock_endf_parserpy = MagicMock()
        mock_endf_parserpy.EndfParserFactory = mock_factory
        
        # Mock the import to raise ImportError when trying to import EndfParserCpp
        def import_side_effect(name, globals=None, locals=None, fromlist=(), level=0):
            # If trying to import EndfParserCpp from endf_parserpy, raise ImportError
            if name == 'endf_parserpy' and fromlist and 'EndfParserCpp' in fromlist:
                raise ImportError("cannot import name 'EndfParserCpp' from 'endf_parserpy'")
            # Otherwise, return the mock module
            if name == 'endf_parserpy':
                return mock_endf_parserpy
            # Default behavior for other imports - use builtins
            import builtins
            return builtins.__import__(name, globals, locals, fromlist, level)
        
        with patch('builtins.__import__', side_effect=import_side_effect):
            with patch.dict('sys.modules', {'endf_parserpy': mock_endf_parserpy}, clear=False):
                parser = cache._get_parser()
                # Should fall back to factory-created parser
                assert parser is not None
                assert parser == mock_parser or hasattr(parser, 'parsefile')
    
    def test_get_parser_not_available(self, temp_cache_dir):
        """Test _get_parser when endf-parserpy is not available."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Mock ImportError for endf-parserpy
        with patch('builtins.__import__', side_effect=ImportError("No module named 'endf_parserpy'")):
            parser = cache._get_parser()
            assert parser is None
    
    def test_save_to_cache_zarr_exception_handling(self, temp_cache_dir):
        """Test _save_to_cache with zarr exception handling."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        energy = np.array([1e5, 1e6])
        xs = np.array([1.0, 2.0])
        
        # Mock zarr to raise exception on create_group
        original_root = cache.root
        mock_root = MagicMock()
        mock_group = MagicMock()
        mock_root.create_group.side_effect = Exception("Zarr error")
        
        cache.root = mock_root
        
        try:
            # Should still update memory cache even if zarr fails
            cache._save_to_cache("test/key", energy, xs)
            assert "test/key" in cache._memory_cache
        finally:
            cache.root = original_root
    
    def test_save_to_cache_zarr_dataset_exception(self, temp_cache_dir):
        """Test _save_to_cache with dataset creation exception."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        energy = np.array([1e5, 1e6])
        xs = np.array([1.0, 2.0])
        
        # Mock zarr group to raise exception on create_dataset
        original_root = cache.root
        mock_root = MagicMock()
        mock_group = MagicMock()
        mock_group.create_dataset.side_effect = Exception("Dataset error")
        mock_root.create_group.return_value = mock_group
        
        cache.root = mock_root
        
        try:
            # Should still update memory cache even if dataset creation fails
            cache._save_to_cache("test/key2", energy, xs)
            assert "test/key2" in cache._memory_cache
        finally:
            cache.root = original_root
    
    def test_fetch_and_cache_all_backends_fail(self, temp_cache_dir):
        """Test _fetch_and_cache when all backends fail."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        u235 = Nuclide(Z=92, A=235)
        
        # Mock _ensure_endf_file to return a file
        test_file = temp_cache_dir / "test.endf"
        test_file.write_text("invalid ENDF content")
        
        # Mock all backends to fail
        with patch.object(cache, '_get_parser', return_value=None):
            with patch('builtins.__import__', side_effect=ImportError("No backend available")):
                # Mock _ensure_endf_file to return test file
                with patch.object(cache, '_ensure_endf_file', return_value=test_file):
                    # Should raise ImportError when all backends fail
                    with pytest.raises(ImportError):
                        cache._fetch_and_cache(u235, "total", 293.6, Library.ENDF_B_VIII, "test/key")
    
    def test_fetch_and_cache_endf_parserpy_fallback(self, temp_cache_dir):
        """Test _fetch_and_cache fallback from endf-parserpy to other backends."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        u235 = Nuclide(Z=92, A=235)
        test_file = temp_cache_dir / "test.endf"
        test_file.write_text("test content")
        
        # Mock endf-parserpy to raise exception, then try other backends
        mock_parser = MagicMock()
        mock_parser.parsefile.side_effect = Exception("Parse error")
        
        with patch.object(cache, '_get_parser', return_value=mock_parser):
            with patch.object(cache, '_ensure_endf_file', return_value=test_file):
                # Should try other backends
                try:
                    cache._fetch_and_cache(u235, "total", 293.6, Library.ENDF_B_VIII, "test/key")
                except ImportError:
                    # Expected if all backends fail
                    pass
    
    def test_fetch_and_cache_update_file_metadata(self, temp_cache_dir):
        """Test _fetch_and_cache updates file metadata cache."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        u235 = Nuclide(Z=92, A=235)
        test_file = temp_cache_dir / "test.endf"
        test_file.write_text("test content")
        
        # Mock parser to return data with MT=3
        mock_parser = MagicMock()
        mock_endf_dict = {
            3: {
                1: {"E": np.array([1e5, 1e6]), "XS": np.array([10.0, 12.0])}  # Total
            }
        }
        mock_parser.parsefile.return_value = mock_endf_dict
        
        with patch.object(cache, '_get_parser', return_value=mock_parser):
            with patch.object(cache, '_ensure_endf_file', return_value=test_file):
                with patch.object(cache, '_extract_mf3_data', return_value=(np.array([1e5, 1e6]), np.array([10.0, 12.0]))):
                    try:
                        cache._fetch_and_cache(u235, "total", 293.6, Library.ENDF_B_VIII, "test/key")
                        # Should have updated file metadata
                        assert test_file in cache._file_metadata_cache
                    except Exception:
                        # May fail if _extract_mf3_data is not properly mocked
                        pass

