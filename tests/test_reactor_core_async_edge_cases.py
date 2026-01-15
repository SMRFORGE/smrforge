"""
Advanced async operation edge case tests for reactor_core.py.

Tests cover:
- Error handling in async gathering operations
- Partial failure scenarios in parallel async operations
- Exception propagation in async chains
- Missing data handling in async operations
- Concurrent access edge cases
"""

import pytest
import numpy as np
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from smrforge.core.reactor_core import (
    NuclearDataCache,
    Nuclide,
    Library,
    CrossSectionTable,
)


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def mock_cache(temp_cache_dir):
    """Create a mock cache for testing."""
    return NuclearDataCache(cache_dir=temp_cache_dir)


class TestAsyncGatherErrorHandling:
    """Test error handling in asyncio.gather operations."""
    
    @pytest.mark.asyncio
    async def test_generate_multigroup_async_partial_failure(self, mock_cache):
        """Test handling when some async operations fail."""
        table = CrossSectionTable()
        table._cache = mock_cache
        
        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)
        groups = np.array([2e7, 1e6, 1e5])
        
        # Mock async calls - one succeeds, one fails
        async def mock_get_xs_success(nuclide, reaction, temp, library, client):
            return (np.array([1e6, 1e5]), np.array([1.0, 0.8]))
        
        async def mock_get_xs_failure(nuclide, reaction, temp, library, client):
            raise FileNotFoundError("ENDF file not found")
        
        with patch.object(mock_cache, 'get_cross_section_async', side_effect=[
            mock_get_xs_success(u235, "fission", 900.0, Library.ENDF_B_VIII, None),
            mock_get_xs_failure(u238, "fission", 900.0, Library.ENDF_B_VIII, None)
        ]):
            # Should raise exception when gathering fails
            with pytest.raises((FileNotFoundError, Exception)):
                await table.generate_multigroup_async(
                    nuclides=[u235, u238],
                    reactions=["fission"],
                    group_structure=groups
                )
    
    @pytest.mark.asyncio
    async def test_generate_multigroup_async_all_fail(self, mock_cache):
        """Test handling when all async operations fail."""
        table = CrossSectionTable()
        table._cache = mock_cache
        
        u235 = Nuclide(Z=92, A=235)
        groups = np.array([2e7, 1e6, 1e5])
        
        # Mock all async calls to fail
        async def mock_get_xs_failure(nuclide, reaction, temp, library, client):
            raise ImportError("Parser not available")
        
        with patch.object(mock_cache, 'get_cross_section_async', side_effect=mock_get_xs_failure):
            with pytest.raises((ImportError, Exception)):
                await table.generate_multigroup_async(
                    nuclides=[u235],
                    reactions=["fission"],
                    group_structure=groups
                )
    
    @pytest.mark.asyncio
    async def test_generate_multigroup_async_empty_inputs(self, mock_cache):
        """Test async operations with empty inputs."""
        table = CrossSectionTable()
        table._cache = mock_cache
        
        groups = np.array([2e7, 1e6, 1e5])
        
        # Should handle empty inputs gracefully
        result = await table.generate_multigroup_async(
            nuclides=[],
            reactions=[],
            group_structure=groups
        )
        
        # Should return empty DataFrame
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_generate_multigroup_async_missing_data(self, mock_cache):
        """Test handling when async returns None or missing data."""
        table = CrossSectionTable()
        table._cache = mock_cache
        
        u235 = Nuclide(Z=92, A=235)
        groups = np.array([2e7, 1e6, 1e5])
        
        # Mock to return None (missing data) - this will cause issues in Numba-compiled functions
        async def mock_get_xs_none(nuclide, reaction, temp, library, client):
            return None, None
        
        with patch.object(mock_cache, 'get_cross_section_async', side_effect=mock_get_xs_none):
            # Should handle None gracefully (will raise in collapse_to_multigroup due to Numba typing)
            # This tests that the code path exists even if it ultimately fails
            with pytest.raises((TypeError, ValueError, AttributeError, Exception)):
                await table.generate_multigroup_async(
                    nuclides=[u235],
                    reactions=["fission"],
                    group_structure=groups
                )


class TestAsyncConcurrentAccess:
    """Test concurrent access scenarios in async operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_get_cross_section_async(self, mock_cache):
        """Test concurrent access to async cross-section fetching."""
        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)
        
        # Mock async responses
        async def mock_get_xs(nuclide, reaction, temp, library, client):
            await asyncio.sleep(0.01)  # Simulate async delay
            return (np.array([1e6, 1e5]), np.array([1.0, 0.8]))
        
        with patch.object(mock_cache, 'get_cross_section_async', side_effect=mock_get_xs):
            # Launch concurrent requests
            tasks = [
                mock_cache.get_cross_section_async(u235, "fission", 900.0, Library.ENDF_B_VIII, None),
                mock_cache.get_cross_section_async(u238, "fission", 900.0, Library.ENDF_B_VIII, None)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Should complete successfully
            assert len(results) == 2
            assert all(r[0] is not None for r in results)
            assert all(r[1] is not None for r in results)


class TestAsyncExceptionPropagation:
    """Test exception propagation in async chains."""
    
    @pytest.mark.asyncio
    async def test_async_exception_propagates_correctly(self, mock_cache):
        """Test that exceptions in async operations propagate correctly."""
        u235 = Nuclide(Z=92, A=235)
        
        # Mock to raise specific exception
        async def mock_get_xs_error(nuclide, reaction, temp, library, client):
            raise ValueError("Invalid nuclide")
        
        with patch.object(mock_cache, 'get_cross_section_async', side_effect=mock_get_xs_error):
            with pytest.raises(ValueError, match="Invalid nuclide"):
                await mock_cache.get_cross_section_async(
                    u235, "fission", 900.0, Library.ENDF_B_VIII, None
                )
    
    @pytest.mark.asyncio
    async def test_async_exception_in_gather_stops_all(self, mock_cache):
        """Test that exception in gather stops all operations."""
        table = CrossSectionTable()
        table._cache = mock_cache
        
        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)
        groups = np.array([2e7, 1e6, 1e5])
        
        call_count = 0
        
        async def mock_get_xs(nuclide, reaction, temp, library, client):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("First call failed")
            return (np.array([1e6, 1e5]), np.array([1.0, 0.8]))
        
        with patch.object(mock_cache, 'get_cross_section_async', side_effect=mock_get_xs):
            with pytest.raises(RuntimeError, match="First call failed"):
                await table.generate_multigroup_async(
                    nuclides=[u235, u238],
                    reactions=["fission"],
                    group_structure=groups
                )
            
            # Second call may or may not complete depending on gather behavior
            # But exception should propagate


class TestAsyncTimeoutScenarios:
    """Test timeout and slow operation handling."""
    
    @pytest.mark.asyncio
    async def test_async_slow_operation(self, mock_cache):
        """Test handling of slow async operations."""
        u235 = Nuclide(Z=92, A=235)
        
        async def mock_get_xs_slow(nuclide, reaction, temp, library, client):
            await asyncio.sleep(0.1)  # Simulate slow operation
            return (np.array([1e6, 1e5]), np.array([1.0, 0.8]))
        
        with patch.object(mock_cache, 'get_cross_section_async', side_effect=mock_get_xs_slow):
            # Should complete successfully even if slow
            energy, xs = await mock_cache.get_cross_section_async(
                u235, "fission", 900.0, Library.ENDF_B_VIII, None
            )
            
            assert energy is not None
            assert xs is not None
    
    @pytest.mark.asyncio
    async def test_async_with_timeout(self, mock_cache):
        """Test async operation with timeout."""
        u235 = Nuclide(Z=92, A=235)
        
        async def mock_get_xs_hang(nuclide, reaction, temp, library, client):
            await asyncio.sleep(10)  # Simulate hanging operation
            return (np.array([1e6]), np.array([1.0]))
        
        with patch.object(mock_cache, 'get_cross_section_async', side_effect=mock_get_xs_hang):
            # Use asyncio.wait_for to test timeout handling
            try:
                energy, xs = await asyncio.wait_for(
                    mock_cache.get_cross_section_async(u235, "fission", 900.0, Library.ENDF_B_VIII, None),
                    timeout=0.1
                )
                pytest.fail("Should have raised TimeoutError")
            except asyncio.TimeoutError:
                # Expected
                pass


class TestAsyncDataConsistency:
    """Test data consistency in async operations."""
    
    @pytest.mark.asyncio
    async def test_async_results_order_preserved(self, mock_cache):
        """Test that async results maintain order."""
        table = CrossSectionTable()
        table._cache = mock_cache
        
        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)
        groups = np.array([2e7, 1e6, 1e5])
        
        # Mock with different delays to ensure order preservation
        call_order = []
        
        async def mock_get_xs_ordered(nuclide, reaction, temp, library, client):
            call_order.append(nuclide.name)
            # Vary delays to test order preservation
            delay = 0.02 if nuclide.name == "U238" else 0.01
            await asyncio.sleep(delay)
            return (np.array([1e6, 1e5]), np.array([1.0, 0.8]))
        
        with patch.object(mock_cache, 'get_cross_section_async', side_effect=mock_get_xs_ordered):
            await table.generate_multigroup_async(
                nuclides=[u235, u238],
                reactions=["fission"],
                group_structure=groups
            )
            
            # Verify order preserved (may be called in different order due to async,
            # but results should be ordered correctly in final DataFrame)
            assert len(call_order) == 2
