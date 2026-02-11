"""
Tests to reach high coverage for smrforge.decay_heat.calculator.

Covers:
- Lines 55, 57, 64-66: get_decay_heat_at_time (idx beyond, idx zero, interpolation, t2<=t1)
- Lines 115-118: __init__ TypeError fallback (DecayData without cache)
- Lines 147, 152, 162: calculate_decay_heat continues (N0<=0, decay_info None, lambda<=0)
- Line 171: beta_energy_per_decay == 0 -> _estimate_beta_energy
- Lines 209-244: _get_decay_data fallback path (no decay file)
- Lines 265-279, 289: _get_gamma_energy_per_decay (fission spectrum, except, _estimate)
- Lines 321, 326, 330, 340-341, 375: calculate_gamma_source branches
"""

import types
from unittest.mock import Mock, patch

import numpy as np
import pytest

from smrforge.core.decay_parser import DecayData, GammaSpectrum
from smrforge.core.reactor_core import NuclearDataCache, Nuclide
from smrforge.decay_heat import DecayHeatCalculator, DecayHeatResult


def test_get_decay_heat_at_time_idx_beyond_last():
    """Cover line 55: return last value when time >= max(times)."""
    times = np.array([0.0, 100.0, 200.0])
    total_decay_heat = np.array([10.0, 5.0, 2.0])
    result = DecayHeatResult(
        times=times,
        total_decay_heat=total_decay_heat,
        gamma_decay_heat=np.zeros_like(times),
        beta_decay_heat=np.zeros_like(times),
        nuclide_contributions={},
    )
    heat = result.get_decay_heat_at_time(500.0)
    assert heat == 2.0


def test_get_decay_heat_at_time_idx_zero():
    """Cover line 57: return first value when time <= min(times)."""
    times = np.array([100.0, 200.0, 300.0])
    total_decay_heat = np.array([10.0, 5.0, 2.0])
    result = DecayHeatResult(
        times=times,
        total_decay_heat=total_decay_heat,
        gamma_decay_heat=np.zeros_like(times),
        beta_decay_heat=np.zeros_like(times),
        nuclide_contributions={},
    )
    heat = result.get_decay_heat_at_time(0.0)
    assert heat == 10.0


def test_get_decay_heat_at_time_interpolation():
    """Cover lines 64-65: linear interpolation when t2 > t1."""
    times = np.array([0.0, 100.0, 200.0])
    total_decay_heat = np.array([10.0, 5.0, 2.0])
    result = DecayHeatResult(
        times=times,
        total_decay_heat=total_decay_heat,
        gamma_decay_heat=np.zeros_like(times),
        beta_decay_heat=np.zeros_like(times),
        nuclide_contributions={},
    )
    heat = result.get_decay_heat_at_time(50.0)  # Midpoint between 0 and 100
    expected = 10.0 + 0.5 * (5.0 - 10.0)  # h1 + frac * (h2 - h1), frac=0.5
    assert abs(heat - expected) < 1e-9


def test_get_decay_heat_at_time_t2_eq_t1_returns_h1():
    """Cover line 66: return h1 when t2 <= t1 (avoid div-by-zero)."""
    times = np.array([0.0, 50.0, 50.0, 100.0])
    total_decay_heat = np.array([10.0, 5.0, 5.0, 2.0])
    result = DecayHeatResult(
        times=times,
        total_decay_heat=total_decay_heat,
        gamma_decay_heat=np.zeros_like(times),
        beta_decay_heat=np.zeros_like(times),
        nuclide_contributions={},
    )
    # Mock searchsorted to return 2 so idx=2 -> t1=times[1]=50, t2=times[2]=50 -> t2<=t1
    with patch("smrforge.decay_heat.calculator.np.searchsorted", return_value=2):
        heat = result.get_decay_heat_at_time(100.0)
    assert heat == 5.0  # h1 = total_decay_heat[1]


def test_init_decay_data_typeerror_fallback():
    """Cover lines 115-118: DecayData(cache=...) raises TypeError, use fallback."""
    mock_cache = Mock(spec=NuclearDataCache)

    with patch("smrforge.decay_heat.calculator.DecayData") as mock_decay_cls:
        # First call raises TypeError (no cache param), second returns instance
        mock_instance = Mock()
        mock_instance._cache = None
        mock_decay_cls.side_effect = [TypeError("unexpected keyword"), mock_instance]

        calc = DecayHeatCalculator(cache=mock_cache)

        assert mock_decay_cls.call_count == 2
        assert calc.decay_data._cache is mock_cache


def test_calculate_decay_heat_n0_zero_continue():
    """Cover line 147: continue when N0 <= 0."""
    mock_cache = Mock(spec=NuclearDataCache)
    u235 = Nuclide(Z=92, A=235)
    decay_data = types.SimpleNamespace(
        decay_constant=np.log(2) / 7.04e8,
        get_total_gamma_energy=lambda: 1.5,
        get_total_beta_energy=lambda: 0.5,
    )
    concentrations = {u235: 0.0}  # N0 <= 0
    times = np.array([0.0, 3600.0])
    calc = DecayHeatCalculator(cache=mock_cache)
    with patch.object(calc, "_get_decay_data", return_value=decay_data):
        result = calc.calculate_decay_heat(concentrations, times)
    assert np.all(result.total_decay_heat == 0)


def test_calculate_decay_heat_decay_info_none_continue():
    """Cover line 152: continue when _get_decay_data returns None."""
    mock_cache = Mock(spec=NuclearDataCache)
    u235 = Nuclide(Z=92, A=235)
    cs137 = Nuclide(Z=55, A=137)
    concentrations = {u235: 1e20, cs137: 1e19}
    times = np.array([0.0, 3600.0])
    decay_data = types.SimpleNamespace(
        decay_constant=np.log(2) / 7.04e8,
        get_total_gamma_energy=lambda: 1.5,
        get_total_beta_energy=lambda: 0.5,
    )

    def get_decay(nuclide):
        return None if nuclide == cs137 else decay_data

    calc = DecayHeatCalculator(cache=mock_cache)
    with patch.object(calc, "_get_decay_data", side_effect=get_decay):
        result = calc.calculate_decay_heat(concentrations, times)
    assert np.any(result.total_decay_heat > 0)
    assert cs137 not in result.nuclide_contributions


def test_calculate_decay_heat_lambda_decay_zero_continue():
    """Cover line 162: continue when lambda_decay <= 0."""
    mock_cache = Mock(spec=NuclearDataCache)
    u235 = Nuclide(Z=92, A=235)
    cs137 = Nuclide(Z=55, A=137)
    concentrations = {u235: 1e20, cs137: 1e19}
    times = np.array([0.0, 3600.0])

    def get_decay(nuclide):
        if nuclide == cs137:
            return types.SimpleNamespace(
                decay_constant=0.0,
                get_total_gamma_energy=lambda: 0.0,
                get_total_beta_energy=lambda: 0.0,
            )
        return types.SimpleNamespace(
            decay_constant=np.log(2) / 7.04e8,
            get_total_gamma_energy=lambda: 1.5,
            get_total_beta_energy=lambda: 0.5,
        )

    calc = DecayHeatCalculator(cache=mock_cache)
    with patch.object(calc, "_get_decay_data", side_effect=get_decay):
        result = calc.calculate_decay_heat(concentrations, times)
    assert np.any(result.total_decay_heat > 0)
    assert cs137 not in result.nuclide_contributions


def test_get_gamma_energy_per_decay_fission_spectrum_path():
    """Cover lines 265-274: gamma_prod_data fission spectrum total_energy path."""
    from smrforge.core.gamma_production_parser import GammaProductionSpectrum

    decay_data = types.SimpleNamespace(
        decay_constant=np.log(2) / 7.04e8,
        get_total_gamma_energy=lambda: 0.0,  # Force try block
        get_total_beta_energy=lambda: 0.5,
    )
    fission_spec = GammaProductionSpectrum(
        reaction="fission",
        energy=np.array([0.5, 1.0]),
        intensity=np.array([0.5, 0.5]),
        total_yield=1.0,
        prompt=True,
    )
    mock_gamma_prod = types.SimpleNamespace(prompt_spectra={"fission": fission_spec})
    mock_cache = Mock(spec=NuclearDataCache)
    mock_cache.get_gamma_production_data.return_value = mock_gamma_prod
    u235 = Nuclide(Z=92, A=235)
    concentrations = {u235: 1e20}
    times = np.array([0.0, 3600.0])
    calc = DecayHeatCalculator(cache=mock_cache)
    with patch.object(calc, "_get_decay_data", return_value=decay_data):
        result = calc.calculate_decay_heat(concentrations, times)
    assert np.any(result.total_decay_heat > 0)


def test_get_gamma_energy_per_decay_exception_and_estimate_fallback():
    """Cover lines 275-279, 289: except when get_gamma_production_data raises; _estimate_gamma_energy."""
    decay_data = types.SimpleNamespace(
        decay_constant=np.log(2) / 7.04e8,
        get_total_gamma_energy=lambda: 0.0,  # Force try block
        get_total_beta_energy=lambda: 0.5,
    )
    mock_cache = Mock(spec=NuclearDataCache)
    mock_cache.get_gamma_production_data.side_effect = RuntimeError("no gamma data")
    u235 = Nuclide(Z=92, A=235)
    concentrations = {u235: 1e20}
    times = np.array([0.0, 3600.0])
    calc = DecayHeatCalculator(cache=mock_cache)
    with patch.object(calc, "_get_decay_data", return_value=decay_data):
        result = calc.calculate_decay_heat(concentrations, times)
    assert np.any(result.total_decay_heat > 0)


def test_get_decay_data_fallback_path():
    """Cover lines 209-244: _get_decay_data fallback when no decay file found."""
    mock_cache = Mock(spec=NuclearDataCache)
    mock_cache._find_local_decay_file.return_value = None  # No file -> fallback
    u235 = Nuclide(Z=92, A=235)
    concentrations = {u235: 1e20}
    times = np.array([0.0, 3600.0])
    calc = DecayHeatCalculator(cache=mock_cache)
    # Do NOT patch _get_decay_data - let it run and hit fallback path
    result = calc.calculate_decay_heat(concentrations, times)
    assert np.any(result.total_decay_heat > 0)
    assert u235 in result.nuclide_contributions


def test_calculate_decay_heat_beta_energy_estimate_branch():
    """Cover line 171: beta_energy_per_decay == 0 -> _estimate_beta_energy."""
    mock_cache = Mock(spec=NuclearDataCache)
    decay_data = Mock(spec=DecayData)
    decay_data.decay_constant = np.log(2) / 7.04e8
    decay_data.get_total_gamma_energy.return_value = 1.5
    decay_data.get_total_beta_energy.return_value = 0.0  # Forces _estimate_beta_energy
    decay_data.gamma_spectrum = None

    u235 = Nuclide(Z=92, A=235)
    concentrations = {u235: 1e20}
    times = np.array([0.0, 3600.0])

    calc = DecayHeatCalculator(cache=mock_cache)
    with patch.object(calc, "_get_decay_data", return_value=decay_data):
        result = calc.calculate_decay_heat(concentrations, times)

    assert np.all(result.total_decay_heat >= 0)
    assert np.any(result.beta_decay_heat > 0)  # From _estimate_beta_energy


def test_calculate_gamma_source_n0_zero_continue():
    """Cover line 321: continue when N0 <= 0."""
    mock_cache = Mock(spec=NuclearDataCache)
    u235 = Nuclide(Z=92, A=235)
    cs137 = Nuclide(Z=55, A=137)
    # Include nuclide with N0=0 to hit the continue branch
    concentrations = {u235: 1e20, cs137: 0.0}
    times = np.array([0.0, 3600.0])
    energy_groups = np.array([0.1, 0.5, 1.0, 1.5, 2.0])

    decay_data = types.SimpleNamespace(
        decay_constant=np.log(2) / 7.04e8,
        gamma_spectrum=None,
        get_total_gamma_energy=lambda: 1.2,
    )

    calc = DecayHeatCalculator(cache=mock_cache)
    with patch.object(calc, "_get_decay_data", return_value=decay_data):
        gamma_source = calc.calculate_gamma_source(concentrations, times, energy_groups)
    assert gamma_source.shape == (2, 4)
    assert np.any(gamma_source > 0)  # u235 contributes; cs137 skipped


def test_calculate_gamma_source_lambda_decay_zero_continue():
    """Cover line 330: continue when lambda_decay <= 0."""
    mock_cache = Mock(spec=NuclearDataCache)
    u235 = Nuclide(Z=92, A=235)
    cs137 = Nuclide(Z=55, A=137)
    concentrations = {u235: 1e20, cs137: 1e19}
    times = np.array([0.0, 3600.0])
    energy_groups = np.array([0.1, 0.5, 1.0, 1.5, 2.0])

    def get_decay_data(nuclide):
        if nuclide == cs137:
            return types.SimpleNamespace(
                decay_constant=0.0,
                gamma_spectrum=None,
                get_total_gamma_energy=lambda: 0.0,
            )
        return types.SimpleNamespace(
            decay_constant=np.log(2) / 7.04e8,
            gamma_spectrum=None,
            get_total_gamma_energy=lambda: 1.2,
        )

    calc = DecayHeatCalculator(cache=mock_cache)
    with patch.object(calc, "_get_decay_data", side_effect=get_decay_data):
        gamma_source = calc.calculate_gamma_source(concentrations, times, energy_groups)
    assert gamma_source.shape == (2, 4)
    assert np.any(gamma_source > 0)


def test_calculate_gamma_source_decay_info_none_continue():
    """Cover line 325-326: continue when _get_decay_data returns None."""
    from smrforge.core.gamma_production_parser import GammaProductionSpectrum

    mock_cache = Mock(spec=NuclearDataCache)
    u235 = Nuclide(Z=92, A=235)
    cs137 = Nuclide(Z=55, A=137)
    concentrations = {u235: 1e20, cs137: 1e19}
    times = np.array([0.0, 3600.0])
    energy_groups = np.array([0.1, 0.5, 1.0, 1.5, 2.0])

    def get_decay_data(nuclide):
        if nuclide == cs137:
            return None  # Line 321: continue
        decay = types.SimpleNamespace(
            decay_constant=np.log(2) / 7.04e8,
            gamma_spectrum=None,
            get_total_gamma_energy=lambda: 1.2,
        )
        return decay

    calc = DecayHeatCalculator(cache=mock_cache)
    with patch.object(calc, "_get_decay_data", side_effect=get_decay_data):
        gamma_source = calc.calculate_gamma_source(concentrations, times, energy_groups)
    assert gamma_source.shape == (2, 4)
    assert np.any(gamma_source > 0)  # u235 contributes


def test_calculate_gamma_source_fission_spectrum_path():
    """Cover line 326: gamma_spectrum from gamma_prod_data.prompt_spectra['fission']."""
    from smrforge.core.gamma_production_parser import GammaProductionSpectrum

    u235 = Nuclide(Z=92, A=235)
    fission_spec = GammaProductionSpectrum(
        reaction="fission",
        energy=np.array([0.5, 1.0, 1.5]),
        intensity=np.array([0.3, 0.5, 0.2]),
        total_yield=1.0,
        prompt=True,
    )
    mock_gamma_prod = types.SimpleNamespace(prompt_spectra={"fission": fission_spec})
    mock_cache = Mock(spec=NuclearDataCache)
    mock_cache.get_gamma_production_data.return_value = mock_gamma_prod

    decay_data = types.SimpleNamespace(
        decay_constant=np.log(2) / 7.04e8,
        gamma_spectrum=None,
        get_total_gamma_energy=lambda: 0.0,
    )

    calc = DecayHeatCalculator(cache=mock_cache)
    concentrations = {u235: 1e20}
    times = np.array([0.0, 3600.0])
    energy_groups = np.array([0.1, 0.5, 1.0, 1.5, 2.0])

    with patch.object(calc, "_get_decay_data", return_value=decay_data):
        gamma_source = calc.calculate_gamma_source(concentrations, times, energy_groups)
    assert gamma_source.shape == (2, 4)
    assert np.any(gamma_source > 0)


def test_calculate_gamma_source_get_gamma_production_exception_pass():
    """Cover line 340-341: except Exception pass when get_gamma_production_data raises."""
    gamma_spec = GammaSpectrum(
        energy=np.array([0.5, 1.0, 1.5]),
        intensity=np.array([0.3, 0.5, 0.2]),
        total_energy=1.2,
    )
    decay_data = types.SimpleNamespace(
        decay_constant=np.log(2) / 7.04e8,
        gamma_spectrum=gamma_spec,
        get_total_gamma_energy=lambda: 1.2,
    )

    class RaisingCache:
        """Cache that raises on get_gamma_production_data to trigger except block."""

        def get_gamma_production_data(self, nuclide):
            raise RuntimeError("no data")

    u235 = Nuclide(Z=92, A=235)
    concentrations = {u235: 1e20}
    times = np.array([0.0, 3600.0])
    energy_groups = np.array([0.1, 0.5, 1.0, 1.5, 2.0])

    calc = DecayHeatCalculator(cache=RaisingCache())
    with patch.object(calc, "_get_decay_data", return_value=decay_data):
        gamma_source = calc.calculate_gamma_source(concentrations, times, energy_groups)
    assert gamma_source.shape == (2, 4)
    assert np.any(gamma_source > 0)


def test_calculate_gamma_source_gamma_yield_zero_default():
    """Cover line 375: gamma_yield = 1.0 when get_total_gamma_energy returns 0."""
    mock_cache = Mock(spec=NuclearDataCache)
    mock_cache.get_gamma_production_data.return_value = None

    decay_data = types.SimpleNamespace(
        decay_constant=np.log(2) / 7.04e8,
        gamma_spectrum=None,
        get_total_gamma_energy=lambda: 0.0,  # Forces gamma_yield = 1.0 default
    )

    u235 = Nuclide(Z=92, A=235)
    concentrations = {u235: 1e20}
    times = np.array([0.0, 3600.0])
    energy_groups = np.array([0.1, 0.5, 1.0, 1.5, 2.0])

    calc = DecayHeatCalculator(cache=mock_cache)
    with patch.object(calc, "_get_decay_data", return_value=decay_data):
        gamma_source = calc.calculate_gamma_source(concentrations, times, energy_groups)
    assert gamma_source.shape == (2, 4)
    assert np.any(gamma_source > 0)
