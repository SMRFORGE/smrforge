"""
Tests for ReactionData.interpolate method.

This test suite comprehensively tests the interpolate method in ReactionData,
covering boundary conditions, interpolation accuracy, edge cases, and various
energy/cross-section array configurations.
"""

import numpy as np
import pytest


@pytest.fixture
def reaction_data_class():
    """Get the ReactionData class."""
    try:
        from smrforge.core.endf_parser import ReactionData
        return ReactionData
    except ImportError:
        pytest.skip("ENDF parser not available")


@pytest.fixture
def simple_reaction_data(reaction_data_class):
    """Create a simple ReactionData instance for testing."""
    energy = np.array([1.0e5, 1.0e6, 1.0e7])
    cross_section = np.array([10.0, 20.0, 30.0])
    return reaction_data_class(
        energy=energy,
        cross_section=cross_section,
        mt_number=1,
        reaction_name="total"
    )


@pytest.fixture
def non_monotonic_reaction_data(reaction_data_class):
    """Create ReactionData with non-monotonic energy (should still work for interpolation)."""
    energy = np.array([1.0e5, 5.0e5, 1.0e6, 2.0e6, 1.0e7])
    cross_section = np.array([10.0, 15.0, 20.0, 25.0, 30.0])
    return reaction_data_class(
        energy=energy,
        cross_section=cross_section,
        mt_number=2,
        reaction_name="elastic"
    )


@pytest.fixture
def constant_cross_section(reaction_data_class):
    """Create ReactionData with constant cross section."""
    energy = np.array([1.0e5, 1.0e6, 1.0e7])
    cross_section = np.array([15.0, 15.0, 15.0])
    return reaction_data_class(
        energy=energy,
        cross_section=cross_section,
        mt_number=102,
        reaction_name="capture"
    )


class TestReactionDataInterpolate:
    """Test ReactionData.interpolate method comprehensively."""

    def test_interpolate_at_lower_boundary(self, simple_reaction_data):
        """Test interpolation at lower energy boundary."""
        # Energy exactly at minimum
        result = simple_reaction_data.interpolate(1.0e5)
        assert result == 10.0
        assert isinstance(result, (float, np.floating))

    def test_interpolate_below_lower_boundary(self, simple_reaction_data):
        """Test interpolation below lower energy boundary (should return first value)."""
        # Energy below minimum
        result = simple_reaction_data.interpolate(1.0e4)
        assert result == 10.0
        assert isinstance(result, (float, np.floating))

    def test_interpolate_at_upper_boundary(self, simple_reaction_data):
        """Test interpolation at upper energy boundary."""
        # Energy exactly at maximum
        result = simple_reaction_data.interpolate(1.0e7)
        assert result == 30.0
        assert isinstance(result, (float, np.floating))

    def test_interpolate_above_upper_boundary(self, simple_reaction_data):
        """Test interpolation above upper energy boundary (should return last value)."""
        # Energy above maximum
        result = simple_reaction_data.interpolate(1.0e8)
        assert result == 30.0
        assert isinstance(result, (float, np.floating))

    def test_interpolate_at_exact_grid_point(self, simple_reaction_data):
        """Test interpolation at exact grid point (middle value)."""
        # Energy at exact grid point
        result = simple_reaction_data.interpolate(1.0e6)
        assert result == 20.0
        assert isinstance(result, (float, np.floating))

    def test_interpolate_between_points_midpoint(self, simple_reaction_data):
        """Test interpolation at midpoint between two grid points."""
        # Energy at midpoint between 1e5 and 1e6
        energy_interp = 5.5e5  # Midpoint
        result = simple_reaction_data.interpolate(energy_interp)
        
        # Should be midpoint between cross sections: (10.0 + 20.0) / 2 = 15.0
        expected = 15.0
        assert np.isclose(result, expected, rtol=1e-10)
        assert isinstance(result, (float, np.floating))

    def test_interpolate_between_points_quarter(self, simple_reaction_data):
        """Test interpolation at quarter point between two grid points."""
        # Energy at 25% from first to second point
        energy_interp = 3.25e5  # 25% of way from 1e5 to 1e6
        result = simple_reaction_data.interpolate(energy_interp)
        
        # Linear interpolation: xs1 + f * (xs2 - xs1)
        # f = (3.25e5 - 1e5) / (1e6 - 1e5) = 0.25
        # result = 10.0 + 0.25 * (20.0 - 10.0) = 12.5
        expected = 12.5
        assert np.isclose(result, expected, rtol=1e-10)

    def test_interpolate_between_upper_points(self, simple_reaction_data):
        """Test interpolation between upper two grid points."""
        # Energy between 1e6 and 1e7
        energy_interp = 5.5e6  # Midpoint
        result = simple_reaction_data.interpolate(energy_interp)
        
        # Should be midpoint: (20.0 + 30.0) / 2 = 25.0
        expected = 25.0
        assert np.isclose(result, expected, rtol=1e-10)

    def test_interpolate_with_non_monotonic_energy(self, non_monotonic_reaction_data):
        """Test interpolation works with properly sorted energy arrays."""
        # Should work fine since energy is already sorted
        result = non_monotonic_reaction_data.interpolate(7.5e5)
        # Between 5e5 (xs=15.0) and 1e6 (xs=20.0)
        # f = (7.5e5 - 5e5) / (1e6 - 5e5) = 2.5e5 / 5e5 = 0.5
        # At 50% of way: 15.0 + 0.5 * (20.0 - 15.0) = 17.5
        expected = 17.5
        assert np.isclose(result, expected, rtol=1e-10)

    def test_interpolate_with_constant_cross_section(self, constant_cross_section):
        """Test interpolation with constant cross section."""
        # Should return constant value regardless of energy
        result1 = constant_cross_section.interpolate(5.0e5)
        result2 = constant_cross_section.interpolate(5.0e6)
        result3 = constant_cross_section.interpolate(5.0e7)
        
        assert result1 == 15.0
        assert result2 == 15.0
        assert result3 == 15.0

    def test_interpolate_handles_negative_energy(self, simple_reaction_data):
        """Test interpolation handles negative energy (below boundary)."""
        # Negative energy should return first cross section
        result = simple_reaction_data.interpolate(-1.0e5)
        assert result == 10.0

    def test_interpolate_with_single_point_array(self, reaction_data_class):
        """Test interpolation with single point energy array."""
        energy = np.array([1.0e6])
        cross_section = np.array([25.0])
        rxn_data = reaction_data_class(
            energy=energy,
            cross_section=cross_section,
            mt_number=18,
            reaction_name="fission"
        )
        
        # Should return the single value for any energy
        assert rxn_data.interpolate(1.0e5) == 25.0
        assert rxn_data.interpolate(1.0e6) == 25.0
        assert rxn_data.interpolate(1.0e7) == 25.0

    def test_interpolate_with_two_points(self, reaction_data_class):
        """Test interpolation with two-point energy array."""
        energy = np.array([1.0e5, 1.0e6])
        cross_section = np.array([10.0, 20.0])
        rxn_data = reaction_data_class(
            energy=energy,
            cross_section=cross_section,
            mt_number=1,
            reaction_name="total"
        )
        
        # At boundaries
        assert rxn_data.interpolate(1.0e5) == 10.0
        assert rxn_data.interpolate(1.0e6) == 20.0
        
        # Between points
        result = rxn_data.interpolate(5.5e5)
        assert np.isclose(result, 15.0, rtol=1e-10)

    def test_interpolate_with_large_energy_range(self, reaction_data_class):
        """Test interpolation with large energy range (eV to MeV)."""
        # Wide energy range from thermal to fast
        energy = np.logspace(0, 7, 100)  # 1 eV to 10 MeV
        cross_section = 10.0 / np.sqrt(energy)  # 1/v behavior
        rxn_data = reaction_data_class(
            energy=energy,
            cross_section=cross_section,
            mt_number=2,
            reaction_name="elastic"
        )
        
        # Test interpolation at various points
        result1 = rxn_data.interpolate(1.0)  # 1 eV
        result2 = rxn_data.interpolate(1.0e3)  # 1 keV
        result3 = rxn_data.interpolate(1.0e6)  # 1 MeV
        
        # All should be finite and positive
        assert np.isfinite(result1)
        assert np.isfinite(result2)
        assert np.isfinite(result3)
        assert result1 > 0
        assert result2 > 0
        assert result3 > 0
        
        # Should follow 1/v trend (decreasing with energy)
        assert result1 > result2
        assert result2 > result3

    def test_interpolate_handles_identical_energy_points(self, reaction_data_class):
        """Test interpolation handles duplicate energy points (edge case)."""
        # Create data with duplicate energies (should still work)
        energy = np.array([1.0e5, 1.0e5, 1.0e6, 1.0e7])
        cross_section = np.array([10.0, 12.0, 20.0, 30.0])
        rxn_data = reaction_data_class(
            energy=energy,
            cross_section=cross_section,
            mt_number=1,
            reaction_name="total"
        )
        
        # Should handle gracefully (will use searchsorted behavior)
        result = rxn_data.interpolate(5.5e5)
        assert np.isfinite(result)
        assert result > 0

    def test_interpolate_accuracy_linear_function(self, reaction_data_class):
        """Test interpolation accuracy with known linear function."""
        # Create linear cross section
        energy = np.array([1.0e5, 5.0e5, 1.0e6, 5.0e6, 1.0e7])
        cross_section = np.array([10.0, 12.0, 14.0, 16.0, 18.0])
        rxn_data = reaction_data_class(
            energy=energy,
            cross_section=cross_section,
            mt_number=1,
            reaction_name="total"
        )
        
        # Interpolate at 2.5e5
        result = rxn_data.interpolate(2.5e5)
        # Between 1e5 (xs=10.0) and 5e5 (xs=12.0)
        # f = (2.5e5 - 1e5) / (5e5 - 1e5) = 1.5e5 / 4e5 = 0.375
        # Should be: 10.0 + 0.375 * (12.0 - 10.0) = 10.75
        expected = 10.75
        assert np.isclose(result, expected, rtol=1e-10)

    def test_interpolate_returns_float(self, simple_reaction_data):
        """Test that interpolate always returns a float (not array)."""
        result = simple_reaction_data.interpolate(5.0e5)
        assert isinstance(result, (float, np.floating))
        assert not isinstance(result, np.ndarray)
        assert result.ndim == 0 if isinstance(result, np.ndarray) else True

    def test_interpolate_very_small_energy_difference(self, reaction_data_class):
        """Test interpolation with very small energy differences."""
        # Very closely spaced energy points
        energy = np.array([1.0e5, 1.00001e5, 1.0e6])
        cross_section = np.array([10.0, 10.0001, 20.0])
        rxn_data = reaction_data_class(
            energy=energy,
            cross_section=cross_section,
            mt_number=1,
            reaction_name="total"
        )
        
        # Should handle small differences without numerical issues
        result = rxn_data.interpolate(1.000005e5)
        assert np.isfinite(result)
        # Should handle division by small number correctly (code has check for e2 != e1)

