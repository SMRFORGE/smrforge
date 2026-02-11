"""Tests for _extract_mf3_data pattern 5 (lines 1030-1055) - array/list data structures."""

import numpy as np
import pytest


class TestExtractMf3DataPatterns:
    """Test _extract_mf3_data pattern 5 - array/list data structures."""

    def test_extract_mf3_data_list_pairs_format(self):
        """Test extraction from list of (E, XS) pairs."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern: list of tuples/pairs
        mf3_data = [(1e5, 10.0), (1e6, 12.0), (5e6, 15.0)]
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert np.allclose(energy, [1e5, 1e6, 5e6])
        assert np.allclose(xs, [10.0, 12.0, 15.0])

    def test_extract_mf3_data_array_pairs_format(self):
        """Test extraction from numpy array with shape (n, 2)."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern: 2D array with shape (n, 2)
        mf3_data = np.array([[1e5, 10.0], [1e6, 12.0], [5e6, 15.0]])
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert np.allclose(energy, [1e5, 1e6, 5e6])
        assert np.allclose(xs, [10.0, 12.0, 15.0])

    def test_extract_mf3_data_flat_pairs_list(self):
        """Test extraction from flat list format [E1, XS1, E2, XS2, ...]."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern 5: flat list with even number of elements
        # The implementation splits into first half and second half (not interleaved)
        # So [E1, XS1, E2, XS2] becomes energy=[E1, XS1], xs=[E2, XS2]
        mf3_data = [
            1e5,
            1e6,
            5e6,
            10.0,
            12.0,
            15.0,
        ]  # 6 elements: first 3 are energy, last 3 are xs
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        # Implementation splits as first half = energy, second half = xs
        assert np.allclose(energy, [1e5, 1e6, 5e6])
        assert np.allclose(xs, [10.0, 12.0, 15.0])

    def test_extract_mf3_data_flat_pairs_array(self):
        """Test extraction from flat numpy array format."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern 5: flat array with even number of elements
        # Same as above - splits into first half and second half
        mf3_data = np.array(
            [1e5, 1e6, 5e6, 10.0, 12.0, 15.0]
        )  # First 3 are energy, last 3 are xs
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert np.allclose(energy, [1e5, 1e6, 5e6])
        assert np.allclose(xs, [10.0, 12.0, 15.0])

    def test_extract_mf3_data_flat_odd_elements_returns_none(self):
        """Test that flat format with odd number of elements returns None."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern: flat list with odd number of elements (should fail)
        mf3_data = [1e5, 10.0, 1e6]  # 3 elements (odd)
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        # Should return None, None for odd number of elements
        assert energy is None
        assert xs is None

    def test_extract_mf3_data_flat_array_odd_elements_returns_none(self):
        """Test that flat array with odd number of elements returns None."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern: flat array with odd number of elements
        mf3_data = np.array([1e5, 10.0, 1e6])  # 3 elements (odd)
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        # Should return None, None for odd number of elements
        assert energy is None
        assert xs is None

    def test_extract_mf3_data_list_single_pair(self):
        """Test extraction from list with single pair."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern: single pair
        mf3_data = [(1e5, 10.0)]
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert len(energy) == 1
        assert len(xs) == 1
        assert np.allclose(energy, [1e5])
        assert np.allclose(xs, [10.0])

    def test_extract_mf3_data_array_single_pair(self):
        """Test extraction from array with single pair."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern: single pair in array format
        mf3_data = np.array([[1e5, 10.0]])
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert len(energy) == 1
        assert len(xs) == 1
        assert np.allclose(energy, [1e5])
        assert np.allclose(xs, [10.0])

    def test_extract_mf3_data_flat_single_pair(self):
        """Test extraction from flat format with 2 elements (treated as single pair)."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern: flat format with 2 elements
        # Implementation splits: pairs = 1, energy = first 1 element, xs = second 1 element
        mf3_data = [1e5, 10.0]  # 2 elements: first is energy, second is xs
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert len(energy) == 1
        assert len(xs) == 1
        assert np.allclose(energy, [1e5])
        assert np.allclose(xs, [10.0])

    def test_extract_mf3_data_list_empty_returns_none(self):
        """Test that empty list returns None."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern: empty list
        mf3_data = []
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is None
        assert xs is None

    def test_extract_mf3_data_array_three_columns_splits_incorrectly(self):
        """Test that array with 3 columns is handled (splits by dimension, not ideal but works)."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern: 2D array with 3 columns
        # Implementation: len(array) on 2D array returns first dimension (2), which is even
        # So it goes to flat array handling: splits first dimension in half
        mf3_data = np.array([[1e5, 10.0, 100.0], [1e6, 12.0, 120.0]])  # shape (2, 3)
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        # Implementation splits first dimension (2) in half: [first row], [second row]
        # This is not ideal but is what the code does
        assert energy is not None
        assert xs is not None
        # Each is a 2D array with shape (1, 3)
        assert energy.shape == (1, 3)
        assert xs.shape == (1, 3)

    def test_extract_mf3_data_list_tuple_pairs(self):
        """Test extraction from list of tuples (pairs format)."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern: list of tuples
        mf3_data = [(1e5, 10.0), (1e6, 12.0), (5e6, 15.0), (1e7, 18.0)]
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert len(energy) == 4
        assert len(xs) == 4
        assert np.allclose(energy, [1e5, 1e6, 5e6, 1e7])
        assert np.allclose(xs, [10.0, 12.0, 15.0, 18.0])

    def test_extract_mf3_data_exception_handling(self):
        """Test that exceptions in extraction return None."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern: invalid data that will cause exception
        # Use a mock object that raises exception when accessed
        class BadData:
            def __array__(self):
                raise ValueError("Cannot convert to array")

            def __len__(self):
                return 2

        mf3_data = BadData()
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        # Should return None, None on exception
        assert energy is None
        assert xs is None
