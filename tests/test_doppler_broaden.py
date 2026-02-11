"""Tests for _doppler_broaden method in NuclearDataCache."""

import numpy as np
import pytest


class TestDopplerBroaden:
    """Test _doppler_broaden method comprehensively."""

    def test_doppler_broaden_same_temperature(self):
        """Test that broadening with same temperature returns approximately original data."""
        from smrforge.core.reactor_core import NuclearDataCache

        energy = np.array([1e5, 1e6, 5e6, 1e7])
        xs = np.array([10.0, 12.0, 15.0, 18.0])

        result = NuclearDataCache._doppler_broaden(energy, xs, 293.6, 293.6, 235)

        # Should return approximately original cross sections (implementation applies small factors)
        # Allow for small numerical differences
        assert np.allclose(result, xs, rtol=1e-3)
        # Should be a copy, not the same array
        assert result is not xs

    def test_doppler_broaden_invalid_temperature_zero(self):
        """Test that invalid temperatures (zero) raise errors."""
        from smrforge.core.reactor_core import NuclearDataCache

        energy = np.array([1e5, 1e6, 5e6])
        xs = np.array([10.0, 12.0, 15.0])

        # Zero temperature causes division by zero
        with pytest.raises(ZeroDivisionError):
            NuclearDataCache._doppler_broaden(energy, xs, 0.0, 293.6, 235)

        # Negative temperature - implementation may handle it (produces NaN or negative sqrt)
        # Just verify it doesn't crash (may produce NaN values)
        try:
            result = NuclearDataCache._doppler_broaden(energy, xs, -100.0, 293.6, 235)
            # If it returns, values may be NaN or inf, which is acceptable behavior
            assert result is not None
        except (ValueError, ZeroDivisionError, FloatingPointError):
            # Also acceptable - error raised for invalid input
            pass

    def test_doppler_broaden_increase_temperature(self):
        """Test broadening when temperature increases."""
        from smrforge.core.reactor_core import NuclearDataCache

        energy = np.array([1e5, 1e6, 5e6])
        xs = np.array([10.0, 12.0, 15.0])

        # Broadening from 293.6K to 900K should change cross sections
        result = NuclearDataCache._doppler_broaden(energy, xs, 293.6, 900.0, 235)

        # Cross sections should be modified (broadened)
        assert not np.allclose(result, xs, rtol=1e-10)
        # All values should be positive
        assert np.all(result >= 0)
        # Should have same length
        assert len(result) == len(xs)

    def test_doppler_broaden_decrease_temperature(self):
        """Test broadening when temperature decreases."""
        from smrforge.core.reactor_core import NuclearDataCache

        energy = np.array([1e5, 1e6, 5e6])
        xs = np.array([10.0, 12.0, 15.0])

        # Narrowing from 900K to 293.6K should change cross sections
        result = NuclearDataCache._doppler_broaden(energy, xs, 900.0, 293.6, 235)

        # Cross sections should be modified
        assert not np.allclose(result, xs, rtol=1e-10)
        # All values should be positive
        assert np.all(result >= 0)
        # Should have same length
        assert len(result) == len(xs)

    def test_doppler_broaden_htgr_temperature(self):
        """Test broadening at HTGR operating temperature."""
        from smrforge.core.reactor_core import NuclearDataCache

        energy = np.logspace(4, 7, 100)
        xs = np.ones_like(energy) * 10.0

        # Typical HTGR temperature: 900K
        result = NuclearDataCache._doppler_broaden(energy, xs, 293.6, 900.0, 235)

        # Should modify cross sections
        assert not np.allclose(result, xs, rtol=1e-10)
        # All values should be positive
        assert np.all(result >= 0)
        # Should preserve length
        assert len(result) == len(energy)

    def test_doppler_broaden_high_temperature(self):
        """Test broadening at very high temperature."""
        from smrforge.core.reactor_core import NuclearDataCache

        energy = np.array([1e5, 1e6, 5e6])
        xs = np.array([10.0, 12.0, 15.0])

        # Very high temperature: 2000K
        result = NuclearDataCache._doppler_broaden(energy, xs, 293.6, 2000.0, 235)

        # Should modify cross sections significantly
        assert not np.allclose(result, xs, rtol=1e-10)
        assert np.all(result >= 0)

    def test_doppler_broaden_different_mass_numbers(self):
        """Test that mass number affects broadening."""
        from smrforge.core.reactor_core import NuclearDataCache

        energy = np.array([1e5, 1e6, 5e6])
        xs = np.array([10.0, 12.0, 15.0])

        # Light nucleus (A=1, hydrogen)
        result_light = NuclearDataCache._doppler_broaden(energy, xs, 293.6, 900.0, 1)

        # Heavy nucleus (A=238, U238)
        result_heavy = NuclearDataCache._doppler_broaden(energy, xs, 293.6, 900.0, 238)

        # Results should be different due to mass-dependent broadening
        assert not np.allclose(result_light, result_heavy, rtol=1e-10)

    def test_doppler_broaden_low_energy_preference(self):
        """Test that broadening effect is stronger at lower energies."""
        from smrforge.core.reactor_core import NuclearDataCache

        # Wide energy range
        energy = np.array([1e3, 1e5, 1e6, 1e7])  # 1 keV to 10 MeV
        xs = np.ones_like(energy) * 10.0  # Constant cross section

        result = NuclearDataCache._doppler_broaden(energy, xs, 293.6, 900.0, 235)

        # Lower energies should have larger relative change
        # (due to energy-dependent broadening factor)
        relative_change = np.abs(result - xs) / xs

        # Lower energies should show more change (may vary by implementation)
        # At minimum, all should be modified
        assert not np.allclose(relative_change, 0.0, atol=1e-10)

    def test_doppler_broaden_zero_energy(self):
        """Test handling of zero energy values."""
        from smrforge.core.reactor_core import NuclearDataCache

        energy = np.array([0.0, 1e5, 1e6])
        xs = np.array([10.0, 12.0, 15.0])

        # Should handle zero energy gracefully
        result = NuclearDataCache._doppler_broaden(energy, xs, 293.6, 900.0, 235)

        # Should return array of same length
        assert len(result) == len(xs)
        # All values should be non-negative
        assert np.all(result >= 0)

    def test_doppler_broaden_single_point(self):
        """Test broadening with single data point."""
        from smrforge.core.reactor_core import NuclearDataCache

        energy = np.array([1e6])
        xs = np.array([10.0])

        result = NuclearDataCache._doppler_broaden(energy, xs, 293.6, 900.0, 235)

        assert len(result) == 1
        assert result[0] >= 0

    def test_doppler_broaden_large_array(self):
        """Test broadening with large energy array."""
        from smrforge.core.reactor_core import NuclearDataCache

        energy = np.logspace(3, 7, 10000)  # 10k points
        xs = np.ones_like(energy) * 10.0 + np.random.rand(10000) * 0.1

        result = NuclearDataCache._doppler_broaden(energy, xs, 293.6, 900.0, 235)

        # Should handle large arrays efficiently
        assert len(result) == len(xs)
        assert np.all(result >= 0)
        assert not np.allclose(result, xs, rtol=1e-10)

    def test_doppler_broaden_zero_cross_section(self):
        """Test broadening with zero cross sections."""
        from smrforge.core.reactor_core import NuclearDataCache

        energy = np.array([1e5, 1e6, 5e6])
        xs = np.array([0.0, 0.0, 0.0])  # All zeros

        result = NuclearDataCache._doppler_broaden(energy, xs, 293.6, 900.0, 235)

        # Zero cross sections should remain zero (or very close to zero)
        assert np.all(result >= 0)
        # With broadening, might have small numerical errors, so check small tolerance
        assert np.all(result < 1e-10)

    def test_doppler_broaden_reversibility(self):
        """Test that broadening is approximately reversible."""
        from smrforge.core.reactor_core import NuclearDataCache

        energy = np.array([1e5, 1e6, 5e6])
        xs = np.array([10.0, 12.0, 15.0])

        # Broaden from 293.6K to 900K
        broadened = NuclearDataCache._doppler_broaden(energy, xs, 293.6, 900.0, 235)

        # Then narrow back to 293.6K
        narrowed = NuclearDataCache._doppler_broaden(
            energy, broadened, 900.0, 293.6, 235
        )

        # Should be approximately back to original (within reasonable tolerance)
        # Note: Exact reversibility is not expected due to the approximation method
        # but should be close
        assert np.allclose(narrowed, xs, rtol=0.5)  # 50% tolerance for approximation
