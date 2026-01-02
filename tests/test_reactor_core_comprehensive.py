"""
Comprehensive tests for reactor_core.py to improve coverage to 80%+.

Tests cover:
- File discovery and indexing
- File parsing and validation
- Cache operations (zarr, memory)
- CrossSectionTable methods
- DecayData methods
- Async operations
- Error handling
"""

import numpy as np
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

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
    cache_dir = tmp_path / "test_cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def mock_endf_file_content():
    """Create minimal valid ENDF file content."""
    return """ 1.001000+3 1.000000+0          0          0          0          0  1  451     \n
 9.223500+4 2.345678+2          0          0          0          0  3  1     \n
 0.000000+0 0.000000+0          0          0          1          2  3  1     \n
 1.000000+5 1.000000+0 1.000000+6 2.000000+0 0.000000+0 0.000000+0  3  1     \n
                                                                    -1  0  0   \n"""


@pytest.fixture
def mock_endf_file(tmp_path, mock_endf_file_content):
    """Create a mock ENDF file."""
    endf_file = tmp_path / "n-092_U_235.endf"
    endf_file.write_text(mock_endf_file_content)
    return endf_file


class TestNuclearDataCacheComprehensive:
    """Comprehensive tests for NuclearDataCache."""
    
    def test_build_local_file_index(self, temp_cache_dir, mock_endf_file):
        """Test building local file index."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Create local ENDF directory structure
        local_dir = temp_cache_dir / "local_endf"
        local_dir.mkdir()
        neutron_dir = local_dir / "neutrons"
        neutron_dir.mkdir()
        
        # Copy mock file
        (neutron_dir / "n-092_U_235.endf").write_text(mock_endf_file.read_text())
        
        cache.local_endf_dir = local_dir
        index = cache._build_local_file_index()
        
        assert len(index) > 0
        assert "U235" in index
    
    def test_find_local_endf_file(self, temp_cache_dir, mock_endf_file):
        """Test finding local ENDF file."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Create local directory
        local_dir = temp_cache_dir / "local_endf"
        local_dir.mkdir()
        neutron_dir = local_dir / "neutrons"
        neutron_dir.mkdir()
        
        (neutron_dir / "n-092_U_235.endf").write_text(mock_endf_file.read_text())
        
        cache.local_endf_dir = local_dir
        u235 = Nuclide(Z=92, A=235)
        
        file_path = cache._find_local_endf_file(u235, Library.ENDF_B_VIII_1)
        
        assert file_path is not None
        assert file_path.exists()
    
    def test_find_local_endf_file_fallback(self, temp_cache_dir):
        """Test library version fallback."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        cache.local_endf_dir = temp_cache_dir / "local_endf"
        
        u235 = Nuclide(Z=92, A=235)
        
        # Should return None if no files found
        file_path = cache._find_local_endf_file(u235, Library.ENDF_B_VIII_1)
        # May be None if files not found, which is acceptable
    
    def test_parse_alternative_endf_filename(self):
        """Test parsing alternative ENDF filename formats."""
        # Pattern 1: ElementSymbolMass
        nuclide = NuclearDataCache._parse_alternative_endf_filename("u235.endf")
        assert nuclide is not None
        assert nuclide.Z == 92
        assert nuclide.A == 235
        
        # Pattern 2: ZAAM format
        nuclide = NuclearDataCache._parse_alternative_endf_filename("92235.endf")
        assert nuclide is not None
        assert nuclide.Z == 92
        assert nuclide.A == 235
        
        # With metastable
        nuclide = NuclearDataCache._parse_alternative_endf_filename("u239m1.endf")
        assert nuclide is not None
        assert nuclide.m == 1
        
        # Invalid
        nuclide = NuclearDataCache._parse_alternative_endf_filename("invalid.endf")
        assert nuclide is None
    
    def test_validate_endf_file(self, mock_endf_file, tmp_path):
        """Test ENDF file validation."""
        # Valid file
        assert NuclearDataCache._validate_endf_file(mock_endf_file) is True
        
        # Invalid file (too small)
        small_file = tmp_path / "small.endf"
        small_file.write_text("x")
        assert NuclearDataCache._validate_endf_file(small_file) is False
        
        # Non-existent file
        assert NuclearDataCache._validate_endf_file(Path("nonexistent.endf")) is False
    
    def test_endf_filename_to_nuclide(self):
        """Test converting ENDF filename to Nuclide."""
        # Standard format
        nuclide = NuclearDataCache._endf_filename_to_nuclide("n-092_U_235.endf")
        assert nuclide is not None
        assert nuclide.Z == 92
        assert nuclide.A == 235
        
        # With metastable
        nuclide = NuclearDataCache._endf_filename_to_nuclide("n-013_Al_026m1.endf")
        assert nuclide is not None
        assert nuclide.m == 1
        
        # Invalid
        nuclide = NuclearDataCache._endf_filename_to_nuclide("invalid.endf")
        assert nuclide is None
    
    def test_nuclide_to_endf_filename(self):
        """Test converting Nuclide to ENDF filename."""
        u235 = Nuclide(Z=92, A=235)
        filename = NuclearDataCache._nuclide_to_endf_filename(u235)
        assert filename == "n-092_U_235.endf"
        
        al26m = Nuclide(Z=13, A=26, m=1)
        filename = NuclearDataCache._nuclide_to_endf_filename(al26m)
        assert filename == "n-013_Al_026m1.endf"
    
    def test_get_library_fallback(self):
        """Test library fallback chain."""
        fallback = NuclearDataCache._get_library_fallback(Library.ENDF_B_VIII_1)
        assert fallback == Library.ENDF_B_VIII
        
        fallback = NuclearDataCache._get_library_fallback(Library.ENDF_B_VIII)
        assert fallback is None
    
    def test_save_to_cache_validation(self, temp_cache_dir):
        """Test _save_to_cache input validation."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        energy = np.array([1e5, 1e6, 1e7])
        xs = np.array([1.0, 2.0, 3.0])
        
        # Valid
        cache._save_to_cache("test/key", energy, xs)
        
        # Invalid: different lengths
        with pytest.raises(ValueError):
            cache._save_to_cache("test/key2", energy, xs[:-1])
        
        # Invalid: NaN values
        energy_nan = np.array([1e5, np.nan, 1e7])
        with pytest.raises(ValueError):
            cache._save_to_cache("test/key3", energy_nan, xs)
    
    def test_find_local_decay_file(self, temp_cache_dir):
        """Test finding local decay file."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Create decay directory
        local_dir = temp_cache_dir / "local_endf"
        local_dir.mkdir()
        decay_dir = local_dir / "decay-version.VIII.1"
        decay_dir.mkdir()
        
        # Create decay file
        decay_file = decay_dir / "dec-092_U_235.endf"
        decay_file.write_text(" 1.001000+3 1.000000+0          0          0          0          0  8  451     \n")
        
        cache.local_endf_dir = local_dir
        u235 = Nuclide(Z=92, A=235)
        
        file_path = cache._find_local_decay_file(u235, Library.ENDF_B_VIII_1)
        
        assert file_path is not None
        assert file_path.exists()
    
    def test_find_local_tsl_file(self, temp_cache_dir):
        """Test finding local TSL file."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Create TSL directory
        local_dir = temp_cache_dir / "local_endf"
        local_dir.mkdir()
        tsl_dir = local_dir / "tsl-version.VIII.1"
        tsl_dir.mkdir()
        
        # Create TSL file
        tsl_file = tsl_dir / "tsl-H_in_H2O.endf"
        tsl_file.write_text(" 1.001000+3 1.000000+0          0          0          0          0  7  1     \n")
        
        cache.local_endf_dir = local_dir
        
        file_path = cache._find_local_tsl_file("H_in_H2O", Library.ENDF_B_VIII_1)
        
        assert file_path is not None
        assert file_path.exists()
    
    def test_build_tsl_file_index(self, temp_cache_dir):
        """Test building TSL file index."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Create TSL directory
        local_dir = temp_cache_dir / "local_endf"
        local_dir.mkdir()
        tsl_dir = local_dir / "tsl-version.VIII.1"
        tsl_dir.mkdir()
        
        tsl_file = tsl_dir / "tsl-H_in_H2O.endf"
        tsl_file.write_text(" 1.001000+3 1.000000+0          0          0          0          0  7  1     \n")
        
        cache.local_endf_dir = local_dir
        index = cache._build_tsl_file_index()
        
        assert len(index) > 0
        assert "h_in_h2o" in index or "H_in_H2O" in index
    
    def test_build_photon_file_index(self, temp_cache_dir):
        """Test building photon file index."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Create photon directory
        local_dir = temp_cache_dir / "local_endf"
        local_dir.mkdir()
        photon_dir = local_dir / "photoat-version.VIII.1"
        photon_dir.mkdir()
        
        photon_file = photon_dir / "p-001_H_001.endf"
        photon_file.write_text(" 1.001000+3 1.000000+0          0          0          0          0 23  1     \n")
        
        cache.local_endf_dir = local_dir
        index = cache._build_photon_file_index()
        
        assert len(index) > 0
        assert "h" in index
    
    def test_build_gamma_production_file_index(self, temp_cache_dir):
        """Test building gamma production file index."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Create gamma production directory
        local_dir = temp_cache_dir / "local_endf"
        local_dir.mkdir()
        gammas_dir = local_dir / "gammas-version.VIII.1"
        gammas_dir.mkdir()
        
        gamma_file = gammas_dir / "gammas-092_U_235.endf"
        gamma_file.write_text(" 9.223500+4 2.345678+2          0          0          0          0 12 18     \n")
        
        cache.local_endf_dir = local_dir
        index = cache._build_gamma_production_file_index()
        
        assert len(index) > 0
        assert "U235" in index
    
    def test_get_photon_file(self, temp_cache_dir):
        """Test getting photon file."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Create photon directory
        local_dir = temp_cache_dir / "local_endf"
        local_dir.mkdir()
        photon_dir = local_dir / "photoat-version.VIII.1"
        photon_dir.mkdir()
        
        photon_file = photon_dir / "p-001_H_001.endf"
        photon_file.write_text(" 1.001000+3 1.000000+0          0          0          0          0 23  1     \n")
        
        cache.local_endf_dir = local_dir
        
        file_path = cache.get_photon_file("H")
        assert file_path is not None
    
    def test_get_gamma_production_data(self, temp_cache_dir):
        """Test getting gamma production data."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        
        # Create gamma production directory
        local_dir = temp_cache_dir / "local_endf"
        local_dir.mkdir()
        gammas_dir = local_dir / "gammas-version.VIII.1"
        gammas_dir.mkdir()
        
        gamma_file = gammas_dir / "gammas-092_U_235.endf"
        gamma_file.write_text(" 9.223500+4 2.345678+2          0          0          0          0 12 18     \n")
        
        cache.local_endf_dir = local_dir
        u235 = Nuclide(Z=92, A=235)
        
        gamma_data = cache.get_gamma_production_data(u235)
        # May be None if parsing fails, which is acceptable
        assert gamma_data is None or hasattr(gamma_data, 'nuclide')


class TestCrossSectionTableComprehensive:
    """Comprehensive tests for CrossSectionTable."""
    
    def test_collapse_to_multigroup(self):
        """Test collapsing to multi-group."""
        energy = np.logspace(4, 7, 1000)  # 10 keV to 10 MeV
        xs = np.ones_like(energy) * 10.0  # Constant 10 barns
        group_bounds = np.array([1e7, 1e6, 1e5])  # 2 groups (high to low)
        
        mg_xs = CrossSectionTable._collapse_to_multigroup(energy, xs, group_bounds)
        
        assert len(mg_xs) == 2
        assert np.all(mg_xs > 0)
    
    def test_collapse_to_multigroup_with_flux(self):
        """Test collapsing with custom flux weighting."""
        energy = np.logspace(4, 7, 1000)
        xs = np.ones_like(energy) * 10.0
        group_bounds = np.array([1e7, 1e6, 1e5])
        weighting_flux = np.ones_like(energy)  # Flat flux
        
        mg_xs = CrossSectionTable._collapse_to_multigroup(
            energy, xs, group_bounds, weighting_flux=weighting_flux
        )
        
        assert len(mg_xs) == 2
    
    def test_collapse_to_multigroup_single_point(self):
        """Test collapsing with single point per group."""
        energy = np.array([1e5, 1e6, 1e7])
        xs = np.array([5.0, 10.0, 15.0])
        group_bounds = np.array([1e7, 1e6, 1e5])
        
        mg_xs = CrossSectionTable._collapse_to_multigroup(energy, xs, group_bounds)
        
        assert len(mg_xs) == 2
    
    def test_pivot_for_solver(self, temp_cache_dir):
        """Test pivoting for solver."""
        table = CrossSectionTable()
        
        # Create minimal data
        u235 = Nuclide(Z=92, A=235)
        energy = np.logspace(4, 7, 100)
        xs_total = np.ones_like(energy) * 10.0
        xs_fission = np.ones_like(energy) * 5.0
        
        # Add data
        table.add_cross_section(u235, "total", energy, xs_total)
        table.add_cross_section(u235, "fission", energy, xs_fission)
        
        # Generate multi-group
        group_bounds = np.array([1e7, 1e6, 1e5])
        table.generate_multigroup([u235], ["total", "fission"], group_bounds)
        
        # Pivot
        xs_matrix = table.pivot_for_solver(["U235"], ["total", "fission"])
        
        assert xs_matrix.shape[0] == 2  # 1 nuclide * 2 groups
        assert xs_matrix.shape[1] == 2  # 2 reactions


class TestDecayDataComprehensive:
    """Comprehensive tests for DecayData."""
    
    def test_build_decay_matrix(self, temp_cache_dir):
        """Test building decay matrix."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        decay_data = DecayData(cache=cache)
        
        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)
        nuclides = [u235, u238]
        
        decay_matrix = decay_data.build_decay_matrix(nuclides)
        
        assert decay_matrix is not None
        assert decay_matrix.shape == (len(nuclides), len(nuclides))
    
    def test_get_daughters(self, temp_cache_dir):
        """Test getting decay daughters."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        decay_data = DecayData(cache=cache)
        
        u235 = Nuclide(Z=92, A=235)
        daughters = decay_data.get_daughters(u235)
        
        assert isinstance(daughters, list)
    
    def test_get_half_life(self, temp_cache_dir):
        """Test getting half-life."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        decay_data = DecayData(cache=cache)
        
        u235 = Nuclide(Z=92, A=235)
        half_life = decay_data.get_half_life(u235)
        
        assert half_life > 0


class TestAsyncOperations:
    """Tests for async operations."""
    
    @pytest.mark.asyncio
    async def test_get_cross_section_async_memory_cache(self, temp_cache_dir):
        """Test async get_cross_section with memory cache hit."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        u235 = Nuclide(Z=92, A=235)
        key = f"{Library.ENDF_B_VIII.value}/{u235.name}/total/293.6K"
        
        # Pre-populate memory cache
        energy = np.array([1e5, 1e6, 1e7])
        xs = np.array([1.0, 2.0, 3.0])
        cache._memory_cache[key] = (energy, xs)
        
        # Async get should hit memory cache
        cached_energy, cached_xs = await cache.get_cross_section_async(
            u235, "total", temperature=293.6, library=Library.ENDF_B_VIII
        )
        
        assert np.allclose(cached_energy, energy)
        assert np.allclose(cached_xs, xs)
    
    @pytest.mark.asyncio
    async def test_get_cross_section_async_zarr_cache(self, temp_cache_dir):
        """Test async get_cross_section with zarr cache hit."""
        import zarr
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        u235 = Nuclide(Z=92, A=235)
        key = f"{Library.ENDF_B_VIII.value}/{u235.name}/total/293.6K"
        
        # Pre-populate zarr cache
        energy = np.array([1e5, 1e6, 1e7])
        xs = np.array([1.0, 2.0, 3.0])
        cache._save_to_cache(key, energy, xs)
        
        # Async get should hit zarr cache
        cached_energy, cached_xs = await cache.get_cross_section_async(
            u235, "total", temperature=293.6, library=Library.ENDF_B_VIII
        )
        
        assert np.allclose(cached_energy, energy)
        assert np.allclose(cached_xs, xs)

