"""Tests for _extract_mf3_data static method."""

import numpy as np
import pytest

from smrforge.core.reactor_core import NuclearDataCache


class TestExtractMf3Data:
    """Test _extract_mf3_data static method comprehensively."""

    def test_extract_mf3_data_pattern1_E_XS_keys(self):
        """Test _extract_mf3_data with Pattern 1: 'E' and 'XS' keys."""
        mf3_data = {"E": [1e5, 1e6, 1e7], "XS": [10.0, 12.0, 15.0]}

        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert isinstance(energy, np.ndarray)
        assert isinstance(xs, np.ndarray)
        assert len(energy) == 3
        assert len(xs) == 3
        assert np.array_equal(energy, [1e5, 1e6, 1e7])
        assert np.array_equal(xs, [10.0, 12.0, 15.0])

    def test_extract_mf3_data_pattern2_energy_cross_section_keys(self):
        """Test _extract_mf3_data with Pattern 2: 'energy' and 'cross_section' keys."""
        mf3_data = {
            "energy": np.array([1e4, 1e5, 1e6]),
            "cross_section": np.array([8.0, 9.0, 10.0]),
        }

        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert len(energy) == 3
        assert len(xs) == 3
        assert np.allclose(energy, [1e4, 1e5, 1e6])
        assert np.allclose(xs, [8.0, 9.0, 10.0])

    def test_extract_mf3_data_pattern3_data_field_with_pairs(self):
        """Test _extract_mf3_data with Pattern 3: 'data' field with (E, XS) pairs."""
        mf3_data = {"data": [(1e5, 10.0), (1e6, 12.0), (1e7, 15.0)]}

        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert len(energy) == 3
        assert len(xs) == 3
        assert np.allclose(energy, [1e5, 1e6, 1e7])
        assert np.allclose(xs, [10.0, 12.0, 15.0])

    def test_extract_mf3_data_pattern4_data_field_with_array_pairs(self):
        """Test _extract_mf3_data with Pattern 4: 'data' field with array pairs."""
        mf3_data = {"data": np.array([(1e5, 10.0), (1e6, 12.0), (1e7, 15.0)])}

        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert len(energy) == 3
        assert len(xs) == 3

    def test_extract_mf3_data_pattern5_xy_keys(self):
        """Test _extract_mf3_data with Pattern 5: 'x' and 'y' keys (not directly supported)."""
        # Note: Pattern 5 (x/y keys) is not explicitly supported in the current implementation
        # The method uses Pattern 4 which searches for keys containing 'E' or 'ENERGY'
        # So 'x' and 'y' keys without 'E' or 'ENERGY' won't match
        mf3_data = {"x": [1e5, 1e6, 1e7], "y": [10.0, 12.0, 15.0]}

        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        # Pattern 5 is not directly supported - returns None
        assert energy is None
        assert xs is None

    def test_extract_mf3_data_empty_data_returns_none(self):
        """Test _extract_mf3_data with empty data returns None."""
        mf3_data = {"E": [], "XS": []}

        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is None
        assert xs is None

    def test_extract_mf3_data_mismatched_lengths_returns_none(self):
        """Test _extract_mf3_data with mismatched array lengths returns None."""
        mf3_data = {"E": [1e5, 1e6, 1e7], "XS": [10.0, 12.0]}  # Different length

        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is None
        assert xs is None

    def test_extract_mf3_data_none_input_returns_none(self):
        """Test _extract_mf3_data with None input returns None."""
        energy, xs = NuclearDataCache._extract_mf3_data(None)

        assert energy is None
        assert xs is None

    def test_extract_mf3_data_non_dict_input_returns_none(self):
        """Test _extract_mf3_data with non-dict input returns None."""
        energy, xs = NuclearDataCache._extract_mf3_data("not a dict")

        assert energy is None
        assert xs is None

    def test_extract_mf3_data_dict_without_matching_keys_returns_none(self):
        """Test _extract_mf3_data with dict without matching keys returns None."""
        mf3_data = {"unrelated_key1": [1, 2, 3], "unrelated_key2": [4, 5, 6]}

        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is None
        assert xs is None

    def test_extract_mf3_data_large_array(self):
        """Test _extract_mf3_data with large arrays."""
        n_points = 10000
        energies = np.logspace(1, 7, n_points)
        xs_values = np.ones(n_points) * 10.0

        mf3_data = {"E": energies, "XS": xs_values}

        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert len(energy) == n_points
        assert len(xs) == n_points
        assert np.allclose(energy, energies)
        assert np.allclose(xs, xs_values)

    def test_extract_mf3_data_single_point(self):
        """Test _extract_mf3_data with single data point."""
        mf3_data = {"E": [1e6], "XS": [10.0]}

        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert len(energy) == 1
        assert len(xs) == 1
        assert energy[0] == 1e6
        assert xs[0] == 10.0

    def test_extract_mf3_data_with_numpy_arrays(self):
        """Test _extract_mf3_data with numpy arrays as values."""
        mf3_data = {"E": np.array([1e5, 1e6, 1e7]), "XS": np.array([10.0, 12.0, 15.0])}

        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert isinstance(energy, np.ndarray)
        assert isinstance(xs, np.ndarray)
        assert len(energy) == 3
        assert len(xs) == 3

    def test_extract_mf3_data_with_lists(self):
        """Test _extract_mf3_data with lists as values."""
        mf3_data = {"E": [1e5, 1e6, 1e7], "XS": [10.0, 12.0, 15.0]}

        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert isinstance(energy, np.ndarray)
        assert isinstance(xs, np.ndarray)

    def test_extract_mf3_data_data_field_with_list_of_tuples(self):
        """Test _extract_mf3_data with 'data' field containing list of tuples."""
        mf3_data = {"data": [(1e5, 10.0), (1e6, 12.0), (1e7, 15.0), (1e8, 18.0)]}

        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert len(energy) == 4
        assert len(xs) == 4
        assert np.allclose(energy, [1e5, 1e6, 1e7, 1e8])
        assert np.allclose(xs, [10.0, 12.0, 15.0, 18.0])

    def test_extract_mf3_data_data_field_with_empty_list(self):
        """Test _extract_mf3_data with 'data' field containing empty list."""
        mf3_data = {"data": []}

        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is None
        assert xs is None

    def test_extract_mf3_data_data_field_with_single_tuple(self):
        """Test _extract_mf3_data with 'data' field containing single tuple."""
        mf3_data = {"data": [(1e6, 10.0)]}

        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert len(energy) == 1
        assert len(xs) == 1

    def test_extract_mf3_data_prefers_pattern1_over_pattern2(self):
        """Test that Pattern 1 ('E', 'XS') is preferred over Pattern 2 when both exist."""
        mf3_data = {
            "E": [1e5, 1e6],
            "XS": [10.0, 12.0],
            "energy": [1e7, 1e8],  # Should be ignored
            "cross_section": [15.0, 18.0],  # Should be ignored
        }

        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        # Should use Pattern 1 (E, XS)
        assert energy is not None
        assert xs is not None
        assert len(energy) == 2
        assert np.allclose(energy, [1e5, 1e6])
        assert np.allclose(xs, [10.0, 12.0])
