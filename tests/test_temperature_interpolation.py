"""
Tests for cross-section temperature interpolation.
"""

import importlib
import sys
import typing

import numpy as np
import pytest

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
        cross_sections = np.array([[5.0 + i * 0.1] * 10 for i in range(4)])  # [4, 10]

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

    def test_init_validates_shapes(self):
        temperatures = np.array([293.6, 600.0, 900.0])
        energies = np.logspace(-5, 7, 10)

        with pytest.raises(ValueError, match="Number of temperatures"):
            CrossSectionTemperatureInterpolator(
                temperatures=temperatures,
                energies=energies,
                cross_sections=np.ones((2, 10)),
            )

        with pytest.raises(ValueError, match="Number of energies"):
            CrossSectionTemperatureInterpolator(
                temperatures=temperatures,
                energies=energies,
                cross_sections=np.ones((3, 9)),
            )

    def test_temperature_clamps_and_exact_match_energy_path(self):
        temperatures = np.array([293.6, 600.0, 900.0])
        energies = np.logspace(-5, 7, 10)
        cross_sections = np.array([[5.0] * 10, [6.0] * 10, [7.0] * 10])

        interpolator = CrossSectionTemperatureInterpolator(
            temperatures, energies, cross_sections
        )

        xs_low = interpolator.interpolate(1.0)  # below minimum
        assert xs_low.shape == (10,)

        xs_high = interpolator.interpolate(1e9)  # above maximum
        assert xs_high.shape == (10,)

        # Exact match + energy specified returns a scalar via np.interp()
        xs_value = interpolator.interpolate(600.0, energy=float(energies[3]))
        assert isinstance(xs_value, (float, np.floating))

    def test_unknown_interpolation_method_raises(self):
        temperatures = np.array([293.6, 600.0, 900.0])
        energies = np.logspace(-5, 7, 10)
        cross_sections = np.array([[5.0] * 10, [6.0] * 10, [7.0] * 10])

        interpolator = CrossSectionTemperatureInterpolator(
            temperatures, energies, cross_sections
        )
        interpolator.method = "nope"
        with pytest.raises(ValueError, match="Unknown interpolation method"):
            interpolator.interpolate(750.0)

    def test_internal_duplicate_temperature_guards(self):
        # Exercise dt ~ 0 guard branches by calling the internal methods directly.
        temperatures = np.array([300.0, 300.0, 600.0])
        energies = np.array([1.0, 2.0])
        cross_sections = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])

        interp_lin = CrossSectionTemperatureInterpolator(
            temperatures, energies, cross_sections, method=InterpolationMethod.LINEAR
        )
        xs = interp_lin._interpolate_linear(300.0)
        assert np.array_equal(xs, interp_lin.cross_sections[0, :])

        interp_log_dt0 = CrossSectionTemperatureInterpolator(
            temperatures, energies, cross_sections, method=InterpolationMethod.LOG_LOG
        )
        xs_dt0 = interp_log_dt0._interpolate_log_log(300.0)
        assert np.array_equal(xs_dt0, interp_log_dt0.cross_sections[0, :])

        # Use nearly-equal (but not equal) temperatures to hit the
        # abs(log_temp_high - log_temp_low) < 1e-10 branch.
        temperatures_close = np.array([300.0, 300.0 + 1e-8, 600.0])
        interp_log = CrossSectionTemperatureInterpolator(
            temperatures_close,
            energies,
            cross_sections,
            method=InterpolationMethod.LOG_LOG,
        )
        xs2 = interp_log._interpolate_log_log(300.0)
        assert xs2.shape == (2,)


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

    def test_spline_2d_path(self):
        # Force RectBivariateSpline path: n_temps>=3 and n_energies>10
        temperatures = np.array([293.6, 600.0, 900.0, 1200.0])
        energies = np.logspace(-5, 7, 11)
        cross_sections = np.array([[5.0] * 11, [6.0] * 11, [7.0] * 11, [8.0] * 11])
        interpolator = CrossSectionTemperatureInterpolator(
            temperatures=temperatures,
            energies=energies,
            cross_sections=cross_sections,
            method=InterpolationMethod.SPLINE,
        )
        xs_interp = interpolator.interpolate(750.0)
        assert xs_interp.shape == (11,)

    def test_spline_fallbacks_when_scipy_splines_fail(self, monkeypatch):
        import smrforge.core.temperature_interpolation as ti

        temperatures = np.array([293.6, 600.0, 900.0, 1200.0])
        energies = np.logspace(-5, 7, 11)
        cross_sections = np.array([[5.0] * 11, [6.0] * 11, [7.0] * 11, [8.0] * 11])

        # 2D spline failure -> per-energy fallback
        monkeypatch.setattr(
            ti,
            "RectBivariateSpline",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        interpolator = CrossSectionTemperatureInterpolator(
            temperatures=temperatures,
            energies=energies,
            cross_sections=cross_sections,
            method=InterpolationMethod.SPLINE,
        )
        xs_interp = interpolator.interpolate(750.0)
        assert xs_interp.shape == (11,)

        # Per-energy spline failure -> linear fallback per energy
        monkeypatch.setattr(
            ti,
            "UnivariateSpline",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        energies2 = np.logspace(-5, 7, 10)  # small enough to skip 2D path
        cross_sections2 = np.array([[5.0] * 10, [6.0] * 10, [7.0] * 10, [8.0] * 10])
        interpolator2 = CrossSectionTemperatureInterpolator(
            temperatures=temperatures,
            energies=energies2,
            cross_sections=cross_sections2,
            method=InterpolationMethod.SPLINE,
        )
        xs_interp2 = interpolator2.interpolate(750.0)
        assert xs_interp2.shape == (10,)


@pytest.mark.skipif(
    not _TEMPERATURE_INTERPOLATION_AVAILABLE,
    reason="Temperature interpolation not available",
)
class TestInterpolateCrossSectionTemperature:
    class _Nuclide:
        name = "U-235"

    class _Cache:
        def __init__(self, energy_by_temp, xs_by_temp, fail_temps=frozenset()):
            self.energy_by_temp = dict(energy_by_temp)
            self.xs_by_temp = dict(xs_by_temp)
            self.fail_temps = set(fail_temps)
            self.calls = []

        def get_cross_section(self, nuclide, reaction, temperature, library=None):
            self.calls.append((float(temperature), library))
            if float(temperature) in self.fail_temps:
                raise RuntimeError("no data")
            return (
                self.energy_by_temp[float(temperature)],
                self.xs_by_temp[float(temperature)],
            )

    def test_default_temperatures_and_library_and_skip_failures(self):
        nuclide = self._Nuclide()
        temps = [293.6, 600.0, 900.0, 1200.0]
        energy = np.array([1.0, 2.0, 3.0])
        cache = self._Cache(
            energy_by_temp={t: energy for t in temps},
            xs_by_temp={t: np.array([t, t + 1.0, t + 2.0]) for t in temps},
            fail_temps={600.0},
        )

        e_out, xs_out = interpolate_cross_section_temperature(
            cache=cache,
            nuclide=nuclide,
            reaction="fission",
            target_temperature=900.0,
            available_temperatures=None,
            method=InterpolationMethod.LINEAR,
            library="endfb8.0",
        )
        assert np.array_equal(e_out, energy)
        assert xs_out.shape == (3,)
        assert any(lib == "endfb8.0" for _, lib in cache.calls)

    def test_energy_grid_mismatch_interpolates_to_first_grid(self):
        nuclide = self._Nuclide()
        temps = np.array([300.0, 600.0])

        e0 = np.array([1.0, 2.0, 3.0])
        e1 = np.array([1.0, 2.5, 3.0])
        cache = self._Cache(
            energy_by_temp={300.0: e0, 600.0: e1},
            xs_by_temp={
                300.0: np.array([1.0, 2.0, 3.0]),
                600.0: np.array([2.0, 4.0, 6.0]),
            },
        )

        e_out, xs_out = interpolate_cross_section_temperature(
            cache=cache,
            nuclide=nuclide,
            reaction="capture",
            target_temperature=450.0,
            available_temperatures=temps,
        )
        assert np.array_equal(e_out, e0)
        assert xs_out.shape == (3,)

    def test_raises_when_no_cross_sections_available(self):
        nuclide = self._Nuclide()
        temps = np.array([300.0, 600.0])
        cache = self._Cache(
            energy_by_temp={300.0: np.array([1.0]), 600.0: np.array([1.0])},
            xs_by_temp={300.0: np.array([1.0]), 600.0: np.array([1.0])},
            fail_temps={300.0, 600.0},
        )
        with pytest.raises(ValueError, match="Could not get cross-sections"):
            interpolate_cross_section_temperature(
                cache=cache,
                nuclide=nuclide,
                reaction="fission",
                target_temperature=450.0,
                available_temperatures=temps,
            )


@pytest.mark.skipif(
    not _TEMPERATURE_INTERPOLATION_AVAILABLE,
    reason="Temperature interpolation not available",
)
def test_temperature_interpolation_type_checking_import_branch(monkeypatch):
    """Cover TYPE_CHECKING import branch by re-importing with TYPE_CHECKING=True."""
    orig = typing.TYPE_CHECKING
    typing.TYPE_CHECKING = True
    try:
        sys.modules.pop("smrforge.core.temperature_interpolation", None)
        importlib.import_module("smrforge.core.temperature_interpolation")
    finally:
        typing.TYPE_CHECKING = orig
        sys.modules.pop("smrforge.core.temperature_interpolation", None)
        importlib.import_module("smrforge.core.temperature_interpolation")
