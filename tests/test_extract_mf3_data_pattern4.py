"""Tests for _extract_mf3_data Pattern 4 - ENDF variable names (lines 1002-1024)."""

import numpy as np
import pytest


class TestExtractMf3DataPattern4:
    """Test _extract_mf3_data Pattern 4 - ENDF variable names with various key patterns."""

    def test_extract_mf3_data_pattern4_energy_cross_section_keys(self):
        """Test Pattern 4: Keys containing 'ENERGY' and 'CROSS'."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern 4: Keys with ENERGY and CROSS (but not E/XS which would match Pattern 1/2)
        mf3_data = {
            "ENERGY_VALUES": [1e5, 1e6, 1e7],
            "CROSS_SECTION_VALUES": [10.0, 12.0, 15.0],
        }
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert np.allclose(energy, [1e5, 1e6, 1e7])
        assert np.allclose(xs, [10.0, 12.0, 15.0])

    def test_extract_mf3_data_pattern4_sigma_key(self):
        """Test Pattern 4: Keys containing 'ENERGY' and 'SIGMA'."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern 4: Keys with ENERGY and SIGMA
        mf3_data = {
            "ENERGY": np.array([1e5, 1e6, 5e6]),
            "SIGMA": np.array([10.0, 12.0, 15.0]),
        }
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert np.allclose(energy, [1e5, 1e6, 5e6])
        assert np.allclose(xs, [10.0, 12.0, 15.0])

    def test_extract_mf3_data_pattern4_lowercase_keys(self):
        """Test Pattern 4: Lowercase keys with energy/cross patterns."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern 4: Lowercase keys
        mf3_data = {"energy_array": [1e5, 1e6], "sigma_array": [10.0, 12.0]}
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert np.allclose(energy, [1e5, 1e6])
        assert np.allclose(xs, [10.0, 12.0])

    def test_extract_mf3_data_pattern4_mixed_case_keys(self):
        """Test Pattern 4: Mixed case keys."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern 4: Mixed case
        mf3_data = {"EnergyValues": [1e5, 1e6, 5e6], "CrossSection": [10.0, 12.0, 15.0]}
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert np.allclose(energy, [1e5, 1e6, 5e6])
        assert np.allclose(xs, [10.0, 12.0, 15.0])

    def test_extract_mf3_data_pattern4_excludes_xs_in_key(self):
        """Test Pattern 4: Keys with 'E' but also 'XS' are excluded from energy match."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern 4: Key with 'E' but also 'XS' should not match as energy
        # But should match as cross-section
        mf3_data = {
            "ENERGY": [1e5, 1e6],
            "XS_VALUES": [10.0, 12.0],  # Has XS, should match as cross-section
        }
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert np.allclose(energy, [1e5, 1e6])
        assert np.allclose(xs, [10.0, 12.0])

    def test_extract_mf3_data_pattern4_list_values(self):
        """Test Pattern 4: List values (not just arrays)."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern 4: List values
        mf3_data = {"ENERGY": [1e5, 1e6, 5e6], "CROSS_SECTION": [10.0, 12.0, 15.0]}
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert isinstance(energy, np.ndarray)
        assert isinstance(xs, np.ndarray)
        assert np.allclose(energy, [1e5, 1e6, 5e6])
        assert np.allclose(xs, [10.0, 12.0, 15.0])

    def test_extract_mf3_data_pattern4_array_values(self):
        """Test Pattern 4: Array values (already arrays)."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern 4: Already arrays
        mf3_data = {
            "ENERGY": np.array([1e5, 1e6]),
            "CROSS_SECTION": np.array([10.0, 12.0]),
        }
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert isinstance(energy, np.ndarray)
        assert isinstance(xs, np.ndarray)
        assert np.allclose(energy, [1e5, 1e6])
        assert np.allclose(xs, [10.0, 12.0])

    def test_extract_mf3_data_pattern4_string_values_excluded(self):
        """Test Pattern 4: String values are excluded (not iterable in the right way)."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern 4: Strings are explicitly excluded
        mf3_data = {
            "ENERGY": "1e5,1e6,1e7",  # String, should be excluded
            "CROSS_SECTION": "10.0,12.0,15.0",
        }
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        # Strings are excluded, so should return None
        assert energy is None
        assert xs is None

    def test_extract_mf3_data_pattern4_mismatched_lengths_returns_none(self):
        """Test Pattern 4: Mismatched lengths return None."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern 4: Different lengths
        mf3_data = {
            "ENERGY": [1e5, 1e6, 5e6],
            "CROSS_SECTION": [10.0, 12.0],  # Different length
        }
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        # Should return None due to length mismatch
        assert energy is None
        assert xs is None

    def test_extract_mf3_data_pattern4_empty_arrays_returns_none(self):
        """Test Pattern 4: Empty arrays return None."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern 4: Empty arrays
        mf3_data = {"ENERGY": [], "CROSS_SECTION": []}
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        # Should return None due to empty arrays
        assert energy is None
        assert xs is None

    def test_extract_mf3_data_pattern4_single_point(self):
        """Test Pattern 4: Single data point."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Pattern 4: Single point
        mf3_data = {"ENERGY": [1e6], "CROSS_SECTION": [10.0]}
        energy, xs = NuclearDataCache._extract_mf3_data(mf3_data)

        assert energy is not None
        assert xs is not None
        assert len(energy) == 1
        assert len(xs) == 1
        assert np.allclose(energy, [1e6])
        assert np.allclose(xs, [10.0])
