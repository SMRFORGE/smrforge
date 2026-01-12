"""
Tests for cross-section temperature interpolation.
"""

import pytest
import numpy as np

try:
    from smrforge.core.temperature_interpolation import (
        CrossSectionTemperatureInterpolator,
        InterpolationMethod,
        interpolate_cross_section_temperature,
    )

    _TEMPERATURE_INTERPOLATION_AVAILABLE = True
except ImportError:
    _TEMPERATURE_INTERPOLATION_AVAILABLE = False


@pytest.mark.skipif(
    not _TEMPERATURE_INTERPOLATION_AVAILABLE,
    reason="Temperature interpolation not available",
)
class TestCrossSectionTemperatureInterpolator:
    """Tests for CrossSectionTemperatureInterpolator class."""

    def test_interpolator_creation(self):
        """Test creating temperature interpolator."""
        temperatures = np.array([293.6, 600.0, 900.0, 1200.0])
        energies = np.logspace(-5, 7, 100)  # 100 energy points
        cross_sections = np.ones((4, 100)) * 5.0  # 5 barns at all temps

        interpolator = CrossSectionTemperatureInterpolator(
            temperatures=temperatures,
            energies=energies,
            cross_sections=cross_sections,
            method=InterpolationMethod.LINEAR,
        )

        assert len(interpolator.temperatures) == 4
        assert len(interpolator.energies) == 100

    def test_interpolate_linear(self):
        """Test linear interpolation."""
        temperatures = np.array([293.6, 600.0, 900.0, 1200.0])
        energies = np.logspace(-5, 7, 10)
        # Cross-section increases with temperature
        cross_sections = np.array(
            [[5.0 + i * 0.1] * 10 for i in range(4)]
        )  # [4, 10]

        interpolator = CrossSectionTemperatureInterpolator(
            temperatures=temperatures,
            energies=energies,
            cross_sections=cross_sections,
            method=InterpolationMethod.LINEAR,
        )

        # Interpolate at 750 K (between 600 and 900)
        xs_interp = interpolator.interpolate(750.0)

        assert len(xs_interp) == 10
        assert np.all(xs_interp > 5.0)

    def test_interpolate_log_log(self):
        """Test log-log interpolation."""
        temperatures = np.array([293.6, 600.0, 900.0])
        energies = np.logspace(-5, 7, 10)
        cross_sections = np.array([[5.0] * 10, [6.0] * 10, [7.0] * 10])

        interpolator = CrossSectionTemperatureInterpolator(
            temperatures=temperatures,
            energies=energies,
            cross_sections=cross_sections,
            method=InterpolationMethod.LOG_LOG,
        )

        xs_interp = interpolator.interpolate(750.0)
        assert len(xs_interp) == 10

    def test_interpolate_spline(self):
        """Test spline interpolation."""
        temperatures = np.array([293.6, 600.0, 900.0, 1200.0])
        energies = np.logspace(-5, 7, 10)
        cross_sections = np.array([[5.0] * 10, [6.0] * 10, [7.0] * 10, [8.0] * 10])

        interpolator = CrossSectionTemperatureInterpolator(
            temperatures=temperatures,
            energies=energies,
            cross_sections=cross_sections,
            method=InterpolationMethod.SPLINE,
        )

        xs_interp = interpolator.interpolate(750.0)
        assert len(xs_interp) == 10

    def test_interpolate_at_exact_temperature(self):
        """Test interpolation at exact temperature point."""
        temperatures = np.array([293.6, 600.0, 900.0])
        energies = np.logspace(-5, 7, 10)
        cross_sections = np.array([[5.0] * 10, [6.0] * 10, [7.0] * 10])

        interpolator = CrossSectionTemperatureInterpolator(
            temperatures=temperatures,
            energies=energies,
            cross_sections=cross_sections,
        )

        # Interpolate at exact temperature
        xs_interp = interpolator.interpolate(600.0)
        assert np.allclose(xs_interp, 6.0)

    def test_interpolate_at_specific_energy(self):
        """Test interpolation at specific energy point."""
        temperatures = np.array([293.6, 600.0, 900.0])
        energies = np.logspace(-5, 7, 10)
        cross_sections = np.array([[5.0] * 10, [6.0] * 10, [7.0] * 10])

        interpolator = CrossSectionTemperatureInterpolator(
            temperatures=temperatures,
            energies=energies,
            cross_sections=cross_sections,
        )

        # Interpolate at specific energy
        xs_value = interpolator.interpolate(750.0, energy=1e6)  # 1 MeV
        assert isinstance(xs_value, (float, np.floating))
        assert xs_value > 0


@pytest.mark.skipif(
    not _TEMPERATURE_INTERPOLATION_AVAILABLE,
    reason="Temperature interpolation not available",
)
class TestInterpolationMethods:
    """Tests for different interpolation methods."""

    def test_linear_vs_log_log(self):
        """Test that linear and log-log give different results."""
        temperatures = np.array([293.6, 1200.0])
        energies = np.logspace(-5, 7, 10)
        cross_sections = np.array([[5.0] * 10, [10.0] * 10])

        interp_linear = CrossSectionTemperatureInterpolator(
            temperatures, energies, cross_sections, InterpolationMethod.LINEAR
        )
        interp_log = CrossSectionTemperatureInterpolator(
            temperatures, energies, cross_sections, InterpolationMethod.LOG_LOG
        )

        xs_linear = interp_linear.interpolate(750.0)
        xs_log = interp_log.interpolate(750.0)

        # Results should be different
        assert not np.allclose(xs_linear, xs_log, rtol=1e-3)
