"""
Tests for advanced control rod worth calculations.

Tests worth profiles, flux-weighted worth, and worth interpolation.
"""

import pytest
import numpy as np

try:
    from smrforge.core.control_rod_worth import (
        ControlRodWorthCalculator,
        WorthProfile,
        calculate_rod_worth_from_neutronics,
        calculate_rod_worth_pcm,
        calculate_worth_profile_from_neutronics,
    )

    _CONTROL_ROD_WORTH_AVAILABLE = True
except ImportError:
    _CONTROL_ROD_WORTH_AVAILABLE = False


@pytest.mark.skipif(
    not _CONTROL_ROD_WORTH_AVAILABLE,
    reason="Control rod worth module not available",
)
class TestWorthProfile:
    """Tests for WorthProfile class."""

    def test_uniform_profile(self):
        """Test uniform worth profile."""
        profile = WorthProfile.uniform(n_points=10)

        assert len(profile.positions) == 10
        assert len(profile.worth_fractions) == 10
        assert profile.profile_type == "uniform"
        assert np.allclose(profile.worth_fractions, 1.0)

    def test_cosine_profile(self):
        """Test cosine worth profile."""
        profile = WorthProfile.cosine(n_points=20, peak_position=0.5)

        assert len(profile.positions) == 20
        assert len(profile.worth_fractions) == 20
        assert profile.profile_type == "cosine"
        # Peak should be at center (position 0.5)
        peak_idx = np.argmax(profile.worth_fractions)
        assert abs(profile.positions[peak_idx] - 0.5) < 0.1

    def test_parabolic_profile(self):
        """Test parabolic worth profile."""
        profile = WorthProfile.parabolic(n_points=20, peak_position=0.5)

        assert len(profile.positions) == 20
        assert profile.profile_type == "parabolic"
        # Peak should be at center
        peak_idx = np.argmax(profile.worth_fractions)
        assert abs(profile.positions[peak_idx] - 0.5) < 0.1

    def test_get_worth_fraction(self):
        """Test getting worth fraction at position."""
        profile = WorthProfile.uniform(n_points=10)

        # Should return 1.0 for uniform profile
        assert profile.get_worth_fraction(0.0) == pytest.approx(1.0)
        assert profile.get_worth_fraction(0.5) == pytest.approx(1.0)
        assert profile.get_worth_fraction(1.0) == pytest.approx(1.0)

    def test_get_worth_fraction_cosine(self):
        """Test getting worth fraction from cosine profile."""
        profile = WorthProfile.cosine(n_points=20, peak_position=0.5)

        # Center should have higher worth than edges
        center_worth = profile.get_worth_fraction(0.5)
        edge_worth = profile.get_worth_fraction(0.0)

        assert center_worth > edge_worth


@pytest.mark.skipif(
    not _CONTROL_ROD_WORTH_AVAILABLE,
    reason="Control rod worth module not available",
)
class TestControlRodWorthCalculator:
    """Tests for ControlRodWorthCalculator class."""

    def test_calculator_creation(self):
        """Test creating a worth calculator."""
        calculator = ControlRodWorthCalculator(max_worth=1000.0)  # 1000 pcm

        assert calculator.max_worth == 1000.0
        assert calculator.worth_profile is not None
        assert calculator.worth_interpolation == "linear"

    def test_calculate_worth_uniform(self):
        """Test worth calculation with uniform profile."""
        calculator = ControlRodWorthCalculator(
            max_worth=1000.0, worth_profile=WorthProfile.uniform()
        )

        # Fully withdrawn
        worth = calculator.calculate_worth(insertion=0.0)
        assert worth == pytest.approx(0.0)

        # Half inserted
        worth = calculator.calculate_worth(insertion=0.5)
        assert worth == pytest.approx(500.0)  # 50% of max

        # Fully inserted
        worth = calculator.calculate_worth(insertion=1.0)
        assert worth == pytest.approx(1000.0)

    def test_calculate_worth_cosine(self):
        """Test worth calculation with cosine profile."""
        calculator = ControlRodWorthCalculator(
            max_worth=1000.0, worth_profile=WorthProfile.cosine()
        )

        # Fully withdrawn
        worth = calculator.calculate_worth(insertion=0.0)
        assert worth == pytest.approx(0.0)

        # Partially inserted (should be less than uniform due to profile)
        worth = calculator.calculate_worth(insertion=0.5)
        assert 0.0 < worth < 500.0  # Less than uniform due to cosine shape

    def test_calculate_flux_weighted_worth(self):
        """Test flux-weighted worth calculation."""
        calculator = ControlRodWorthCalculator(max_worth=1000.0)

        # Create flux distribution (higher in center)
        n_axial = 20
        axial_positions = np.linspace(0, 365.76, n_axial)  # cm
        flux = np.cos(np.pi * np.linspace(0, 1, n_axial)) + 1.0  # Cosine shape

        # Calculate worth at 50% insertion
        worth = calculator.calculate_worth(
            insertion=0.5, flux=flux, axial_positions=axial_positions
        )

        assert worth > 0.0
        assert worth <= 1000.0

    def test_calculate_worth_gradient(self):
        """Test worth gradient calculation."""
        calculator = ControlRodWorthCalculator(max_worth=1000.0)

        # Gradient should be positive (worth increases with insertion)
        gradient = calculator.calculate_worth_gradient(insertion=0.5)

        assert gradient > 0.0

    def test_interpolate_worth(self):
        """Test worth interpolation."""
        calculator = ControlRodWorthCalculator(max_worth=1000.0)

        # Create some calculated worths
        insertions = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        calculated_worths = np.array([0.0, 250.0, 500.0, 750.0, 1000.0])

        # Interpolate at 0.3
        worth = calculator.interpolate_worth(insertions, calculated_worths, 0.3)

        assert 250.0 < worth < 500.0  # Should be between 0.25 and 0.5


@pytest.mark.skipif(
    not _CONTROL_ROD_WORTH_AVAILABLE,
    reason="Control rod worth module not available",
)
class TestWorthFromNeutronics:
    """Tests for worth calculation from neutronics results."""

    def test_calculate_rod_worth_from_neutronics(self):
        """Test worth calculation from k-eff values."""
        k_eff_without = 1.0
        k_eff_with = 0.99

        worth = calculate_rod_worth_from_neutronics(k_eff_without, k_eff_with)

        # Should be 0.01 dk/k
        assert worth == pytest.approx(0.01)

    def test_calculate_rod_worth_pcm(self):
        """Test worth calculation in pcm."""
        k_eff_without = 1.0
        k_eff_with = 0.99

        worth_pcm = calculate_rod_worth_pcm(k_eff_without, k_eff_with)

        # Should be 1000 pcm (0.01 * 1e5)
        assert worth_pcm == pytest.approx(1000.0)

    def test_calculate_worth_profile_from_neutronics(self):
        """Test worth profile calculation from neutronics."""
        insertions = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        k_eff_values = np.array([1.0, 0.9975, 0.995, 0.9925, 0.99])

        worths, profile = calculate_worth_profile_from_neutronics(
            insertions, k_eff_values, k_eff_critical=1.0
        )

        assert len(worths) == len(insertions)
        assert len(profile.positions) == len(insertions)
        assert len(profile.worth_fractions) == len(insertions)

        # Worth should increase with insertion
        assert worths[-1] > worths[0]

    def test_worth_profile_normalization(self):
        """Test that worth profile is normalized correctly."""
        insertions = np.array([0.0, 0.5, 1.0])
        k_eff_values = np.array([1.0, 0.995, 0.99])

        worths, profile = calculate_worth_profile_from_neutronics(
            insertions, k_eff_values
        )

        # Worth fractions should be normalized to 0-1
        assert np.all(profile.worth_fractions >= 0.0)
        assert np.all(profile.worth_fractions <= 1.0)
        # Maximum should be 1.0
        assert np.max(profile.worth_fractions) == pytest.approx(1.0)
