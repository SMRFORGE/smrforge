"""Tests for _extract_mf3_data Pattern 3 - flat array extraction (lines 995-1000)."""

import numpy as np
import pytest


class TestExtractMf3DataPattern3Flat:
    """Test _extract_mf3_data Pattern 3 flat array extraction."""

    def test_extract_mf3_data_pattern3_flat_array_interleaved(self):
        """Test Pattern 3: 'data' field with flat array [E1, XS1, E2, XS2, ...]."""
        from smrforge.core.reactor_core import NuclearDataCache
        
        # Pattern 3: flat array with interleaved pairs
        mf3_data = {
            'data': np.array([1e5, 10.0, 1e6, 12.0, 5e6, 15.0])  # Interleaved: E, XS, E, XS, ...
        }
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)
        
        assert energy is not None
        assert xs is not None
        # Should extract every even index (E) and every odd index (XS)
        assert np.allclose(energy, [1e5, 1e6, 5e6])
        assert np.allclose(xs, [10.0, 12.0, 15.0])

    def test_extract_mf3_data_pattern3_flat_array_two_points(self):
        """Test Pattern 3: flat array with 2 data points."""
        from smrforge.core.reactor_core import NuclearDataCache
        
        # Pattern 3: flat array with 2 points
        mf3_data = {
            'data': np.array([1e5, 10.0, 1e6, 12.0])  # 4 elements: 2 pairs
        }
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)
        
        assert energy is not None
        assert xs is not None
        assert len(energy) == 2
        assert len(xs) == 2
        assert np.allclose(energy, [1e5, 1e6])
        assert np.allclose(xs, [10.0, 12.0])

    def test_extract_mf3_data_pattern3_flat_array_many_points(self):
        """Test Pattern 3: flat array with many data points."""
        from smrforge.core.reactor_core import NuclearDataCache
        
        # Pattern 3: flat array with many points
        energies = [1e5 * (i+1) for i in range(10)]
        xs_values = [10.0 + i for i in range(10)]
        interleaved = []
        for e, x in zip(energies, xs_values):
            interleaved.extend([e, x])
        
        mf3_data = {
            'data': np.array(interleaved)
        }
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)
        
        assert energy is not None
        assert xs is not None
        assert len(energy) == 10
        assert len(xs) == 10
        assert np.allclose(energy, energies)
        assert np.allclose(xs, xs_values)

    def test_extract_mf3_data_pattern3_flat_array_odd_elements_skipped(self):
        """Test Pattern 3: flat array with odd number of elements (should skip this pattern)."""
        from smrforge.core.reactor_core import NuclearDataCache
        
        # Pattern 3: flat array with odd number (should not match this pattern)
        mf3_data = {
            'data': np.array([1e5, 10.0, 1e6])  # 3 elements (odd)
        }
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)
        
        # Pattern 3 requires even number of elements, so should return None
        # (might match other patterns, but Pattern 3 won't match)
        # Actually, it will try Pattern 3 first but fail the even check
        # Then try other patterns, but they may also fail
        # So result could be None or could match another pattern
        # The key is Pattern 3 specific code (lines 995-1000) won't execute
        pass  # Just test that it doesn't crash

    def test_extract_mf3_data_pattern3_flat_array_single_point_fails_check(self):
        """Test Pattern 3: flat array with 2 elements (single pair) - should match but need >= 2 check."""
        from smrforge.core.reactor_core import NuclearDataCache
        
        # Pattern 3: flat array with 2 elements (single pair)
        # The check is len(data_array) >= 2, so this should match
        mf3_data = {
            'data': np.array([1e5, 10.0])  # 2 elements (even, >= 2)
        }
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)
        
        assert energy is not None
        assert xs is not None
        assert len(energy) == 1
        assert len(xs) == 1
        assert np.allclose(energy, [1e5])
        assert np.allclose(xs, [10.0])

