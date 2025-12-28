"""Tests for _save_to_cache method in NuclearDataCache."""

import numpy as np
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestSaveToCache:
    """Test _save_to_cache method comprehensively."""

    def test_save_to_cache_basic(self, temp_dir):
        """Test basic _save_to_cache functionality."""
        from smrforge.core.reactor_core import NuclearDataCache

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        
        key = "test_lib/U235/total/293.6K"
        energy = np.array([1e5, 1e6, 5e6, 1e7])
        xs = np.array([10.0, 12.0, 15.0, 18.0])
        
        # Save to cache
        cache._save_to_cache(key, energy, xs)
        
        # Verify data was added to memory cache
        assert key in cache._memory_cache
        cached_energy, cached_xs = cache._memory_cache[key]
        assert np.array_equal(cached_energy, energy)
        assert np.array_equal(cached_xs, xs)
        
        # Verify data was saved to zarr cache
        group = cache.root[key]
        zarr_energy = group["energy"][:]
        zarr_xs = group["xs"][:]
        
        assert np.array_equal(zarr_energy, energy)
        assert np.array_equal(zarr_xs, xs)

    def test_save_to_cache_overwrite(self, temp_dir):
        """Test that _save_to_cache overwrites existing cache entries."""
        from smrforge.core.reactor_core import NuclearDataCache

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        
        key = "test_lib/U235/total/293.6K"
        energy1 = np.array([1e5, 1e6])
        xs1 = np.array([10.0, 12.0])
        
        # Save first set of data
        cache._save_to_cache(key, energy1, xs1)
        
        # Save different data with same key
        energy2 = np.array([1e5, 1e6, 5e6])
        xs2 = np.array([20.0, 22.0, 25.0])
        cache._save_to_cache(key, energy2, xs2)
        
        # Verify memory cache was updated
        cached_energy, cached_xs = cache._memory_cache[key]
        assert np.array_equal(cached_energy, energy2)
        assert np.array_equal(cached_xs, xs2)
        
        # Verify zarr cache was updated
        group = cache.root[key]
        zarr_energy = group["energy"][:]
        zarr_xs = group["xs"][:]
        assert np.array_equal(zarr_energy, energy2)
        assert np.array_equal(zarr_xs, xs2)

    def test_save_to_cache_large_arrays(self, temp_dir):
        """Test _save_to_cache with large arrays."""
        from smrforge.core.reactor_core import NuclearDataCache

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        
        key = "test_lib/U235/total/293.6K"
        # Create large arrays (10k points)
        energy = np.logspace(4, 7, 10000)
        xs = np.ones_like(energy) * 10.0 + np.random.rand(10000) * 0.1
        
        # Save to cache
        cache._save_to_cache(key, energy, xs)
        
        # Verify data integrity
        cached_energy, cached_xs = cache._memory_cache[key]
        assert len(cached_energy) == 10000
        assert len(cached_xs) == 10000
        assert np.allclose(cached_energy, energy)
        assert np.allclose(cached_xs, xs)
        
        # Verify zarr cache
        group = cache.root[key]
        zarr_energy = group["energy"][:]
        zarr_xs = group["xs"][:]
        assert len(zarr_energy) == 10000
        assert len(zarr_xs) == 10000

    def test_save_to_cache_single_point(self, temp_dir):
        """Test _save_to_cache with single data point."""
        from smrforge.core.reactor_core import NuclearDataCache

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        
        key = "test_lib/U235/total/293.6K"
        energy = np.array([1e6])
        xs = np.array([10.0])
        
        # Save to cache
        cache._save_to_cache(key, energy, xs)
        
        # Verify data
        cached_energy, cached_xs = cache._memory_cache[key]
        assert len(cached_energy) == 1
        assert len(cached_xs) == 1
        assert cached_energy[0] == 1e6
        assert cached_xs[0] == 10.0
        
        # Verify zarr cache
        group = cache.root[key]
        zarr_energy = group["energy"][:]
        zarr_xs = group["xs"][:]
        assert len(zarr_energy) == 1
        assert len(zarr_xs) == 1

    def test_save_to_cache_different_keys(self, temp_dir):
        """Test _save_to_cache with multiple different keys."""
        from smrforge.core.reactor_core import NuclearDataCache

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        
        keys_and_data = [
            ("test_lib/U235/total/293.6K", np.array([1e5, 1e6]), np.array([10.0, 12.0])),
            ("test_lib/U235/fission/293.6K", np.array([1e5, 1e6]), np.array([5.0, 6.0])),
            ("test_lib/U238/total/900.0K", np.array([1e5, 1e6]), np.array([8.0, 9.0])),
        ]
        
        # Save all data
        for key, energy, xs in keys_and_data:
            cache._save_to_cache(key, energy, xs)
        
        # Verify all keys are in memory cache
        assert len(cache._memory_cache) == 3
        for key, energy, xs in keys_and_data:
            assert key in cache._memory_cache
            cached_energy, cached_xs = cache._memory_cache[key]
            assert np.array_equal(cached_energy, energy)
            assert np.array_equal(cached_xs, xs)
            
            # Verify zarr cache
            group = cache.root[key]
            zarr_energy = group["energy"][:]
            zarr_xs = group["xs"][:]
            assert np.array_equal(zarr_energy, energy)
            assert np.array_equal(zarr_xs, xs)

    def test_save_to_cache_retrieval_after_save(self, temp_dir):
        """Test that saved cache can be retrieved via get_cross_section."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)
        
        key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/293.6K"
        energy = np.array([1e5, 1e6, 5e6])
        xs = np.array([10.0, 12.0, 15.0])
        
        # Save to cache
        cache._save_to_cache(key, energy, xs)
        
        # Clear memory cache to test zarr retrieval
        cache._memory_cache.clear()
        
        # Retrieve via get_cross_section (should hit zarr cache)
        retrieved_energy, retrieved_xs = cache.get_cross_section(nuc, "total", 293.6, Library.ENDF_B_VIII)
        
        assert np.array_equal(retrieved_energy, energy)
        assert np.array_equal(retrieved_xs, xs)
        
        # Verify memory cache was repopulated
        assert key in cache._memory_cache

    def test_save_to_cache_zero_values(self, temp_dir):
        """Test _save_to_cache with zero cross-section values."""
        from smrforge.core.reactor_core import NuclearDataCache

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        
        key = "test_lib/U235/total/293.6K"
        energy = np.array([1e5, 1e6, 5e6])
        xs = np.array([0.0, 0.0, 0.0])  # All zeros
        
        # Save to cache
        cache._save_to_cache(key, energy, xs)
        
        # Verify data
        cached_energy, cached_xs = cache._memory_cache[key]
        assert np.allclose(cached_xs, 0.0)
        
        # Verify zarr cache
        group = cache.root[key]
        zarr_xs = group["xs"][:]
        assert np.allclose(zarr_xs, 0.0)

    def test_save_to_cache_negative_energy_values(self, temp_dir):
        """Test _save_to_cache with negative energy values (should handle gracefully)."""
        from smrforge.core.reactor_core import NuclearDataCache

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        
        key = "test_lib/U235/total/293.6K"
        # Note: Negative energies are unphysical, but the cache should handle them
        energy = np.array([-1e5, 1e5, 1e6])  # Include negative value
        xs = np.array([10.0, 12.0, 15.0])
        
        # Save to cache (should work, even if unphysical)
        cache._save_to_cache(key, energy, xs)
        
        # Verify data was stored as-is
        cached_energy, cached_xs = cache._memory_cache[key]
        assert np.array_equal(cached_energy, energy)
        assert cached_energy[0] < 0  # Negative value preserved
        
        # Verify zarr cache
        group = cache.root[key]
        zarr_energy = group["energy"][:]
        assert np.array_equal(zarr_energy, energy)

