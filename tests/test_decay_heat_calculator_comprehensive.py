"""
Comprehensive tests for decay heat calculator to improve coverage to 80%+.

Tests cover:
- Decay heat calculation
- Gamma source calculation
- Energy estimation
- Time-dependent calculations
- Nuclide contributions
"""

import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock

from smrforge.decay_heat import DecayHeatCalculator, DecayHeatResult
from smrforge.core.reactor_core import Nuclide, NuclearDataCache
from smrforge.core.decay_parser import DecayData, GammaSpectrum, BetaSpectrum


@pytest.fixture
def mock_cache():
    """Create a mock cache for testing."""
    cache = Mock(spec=NuclearDataCache)
    return cache


@pytest.fixture
def mock_decay_data():
    """Create mock decay data."""
    u235 = Nuclide(Z=92, A=235)
    decay_data = Mock(spec=DecayData)
    decay_data.nuclide = u235
    decay_data.half_life = 7.04e8  # seconds
    decay_data.decay_constant = np.log(2) / 7.04e8
    decay_data.get_total_gamma_energy.return_value = 1.5  # MeV
    decay_data.get_total_beta_energy.return_value = 0.5  # MeV
    decay_data.gamma_spectrum = None
    decay_data.beta_spectrum = None
    return decay_data


class TestDecayHeatCalculatorComprehensive:
    """Comprehensive tests for DecayHeatCalculator."""
    
    def test_calculate_decay_heat_basic(self, mock_cache, mock_decay_data):
        """Test basic decay heat calculation."""
        calculator = DecayHeatCalculator(cache=mock_cache)
        
        u235 = Nuclide(Z=92, A=235)
        concentrations = {u235: 1e20}  # atoms/cm³
        times = np.array([0, 3600, 86400])  # 0, 1h, 1d
        
        # Mock decay data retrieval
        with patch.object(calculator, '_get_decay_data', return_value=mock_decay_data):
            result = calculator.calculate_decay_heat(concentrations, times)
        
        assert isinstance(result, DecayHeatResult)
        assert len(result.times) == len(times)
        assert len(result.total_decay_heat) == len(times)
        assert np.all(result.total_decay_heat >= 0)
        assert np.all(result.gamma_decay_heat >= 0)
        assert np.all(result.beta_decay_heat >= 0)
    
    def test_calculate_decay_heat_multiple_nuclides(self, mock_cache, mock_decay_data):
        """Test decay heat with multiple nuclides."""
        calculator = DecayHeatCalculator(cache=mock_cache)
        
        u235 = Nuclide(Z=92, A=235)
        cs137 = Nuclide(Z=55, A=137)
        
        concentrations = {
            u235: 1e20,
            cs137: 1e19,
        }
        times = np.array([0, 86400, 604800])  # 0, 1d, 1w
        
        # Mock decay data
        cs137_decay = Mock(spec=DecayData)
        cs137_decay.decay_constant = 7.3e-10  # Cs-137 half-life
        cs137_decay.get_total_gamma_energy.return_value = 0.662  # MeV (Cs-137 gamma)
        cs137_decay.get_total_beta_energy.return_value = 1.176  # MeV
        
        def get_decay_data(nuclide):
            if nuclide == u235:
                return mock_decay_data
            elif nuclide == cs137:
                return cs137_decay
            return None
        
        with patch.object(calculator, '_get_decay_data', side_effect=get_decay_data):
            result = calculator.calculate_decay_heat(concentrations, times)
        
        assert len(result.nuclide_contributions) == 2
        assert u235 in result.nuclide_contributions
        assert cs137 in result.nuclide_contributions
    
    def test_calculate_decay_heat_with_gamma_spectrum(self, mock_cache, mock_decay_data):
        """Test decay heat with gamma spectrum."""
        calculator = DecayHeatCalculator(cache=mock_cache)
        
        u235 = Nuclide(Z=92, A=235)
        concentrations = {u235: 1e20}
        times = np.array([0, 3600])
        
        # Add gamma spectrum to decay data
        gamma_spec = GammaSpectrum(
            energy=np.array([0.5, 1.0, 1.5]),
            intensity=np.array([0.3, 0.5, 0.2]),
            total_energy=1.2,
        )
        mock_decay_data.gamma_spectrum = gamma_spec
        mock_decay_data.get_total_gamma_energy.return_value = 1.2
        
        with patch.object(calculator, '_get_decay_data', return_value=mock_decay_data):
            result = calculator.calculate_decay_heat(concentrations, times)
        
        assert result.gamma_decay_heat[0] > 0
    
    def test_calculate_decay_heat_with_beta_spectrum(self, mock_cache, mock_decay_data):
        """Test decay heat with beta spectrum."""
        calculator = DecayHeatCalculator(cache=mock_cache)
        
        u235 = Nuclide(Z=92, A=235)
        concentrations = {u235: 1e20}
        times = np.array([0, 3600])
        
        # Add beta spectrum
        beta_spec = BetaSpectrum(
            energy=np.array([0.5, 1.0]),
            intensity=np.array([0.6, 0.4]),
            total_energy=0.8,
        )
        mock_decay_data.beta_spectrum = beta_spec
        mock_decay_data.get_total_beta_energy.return_value = 0.8
        
        with patch.object(calculator, '_get_decay_data', return_value=mock_decay_data):
            result = calculator.calculate_decay_heat(concentrations, times)
        
        assert result.beta_decay_heat[0] > 0
    
    def test_calculate_gamma_source(self, mock_cache, mock_decay_data):
        """Test gamma source calculation."""
        calculator = DecayHeatCalculator(cache=mock_cache)
        
        u235 = Nuclide(Z=92, A=235)
        concentrations = {u235: 1e20}
        times = np.array([0, 3600, 86400])
        energy_groups = np.logspace(-2, 1, 21)  # 20 groups
        
        with patch.object(calculator, '_get_decay_data', return_value=mock_decay_data):
            gamma_source = calculator.calculate_gamma_source(
                concentrations, times, energy_groups
            )
        
        assert gamma_source.shape == (len(times), len(energy_groups) - 1)
        assert np.all(gamma_source >= 0)
    
    def test_calculate_gamma_source_with_spectrum(self, mock_cache, mock_decay_data):
        """Test gamma source with gamma production spectrum."""
        calculator = DecayHeatCalculator(cache=mock_cache)
        
        u235 = Nuclide(Z=92, A=235)
        concentrations = {u235: 1e20}
        times = np.array([0, 3600])
        energy_groups = np.logspace(-2, 1, 11)  # 10 groups
        
        # Mock gamma production data
        from smrforge.core.gamma_production_parser import GammaProductionSpectrum
        gamma_spec = GammaProductionSpectrum(
            reaction="fission",
            energy=np.array([0.5, 1.0, 1.5]),
            intensity=np.array([0.3, 0.5, 0.2]),
            total_yield=1.0,
            prompt=True,
        )
        
        mock_gamma_prod = Mock()
        mock_gamma_prod.prompt_spectra = {"fission": gamma_spec}
        mock_cache.get_gamma_production_data.return_value = mock_gamma_prod
        
        with patch.object(calculator, '_get_decay_data', return_value=mock_decay_data):
            gamma_source = calculator.calculate_gamma_source(
                concentrations, times, energy_groups
            )
        
        assert gamma_source.shape == (len(times), len(energy_groups) - 1)
    
    def test_get_gamma_energy_per_decay(self, mock_cache, mock_decay_data):
        """Test getting gamma energy per decay."""
        calculator = DecayHeatCalculator(cache=mock_cache)
        
        u235 = Nuclide(Z=92, A=235)
        
        # Test with decay data
        gamma_energy = calculator._get_gamma_energy_per_decay(u235, mock_decay_data)
        assert gamma_energy > 0
        
        # Test with gamma production data
        mock_gamma_prod = Mock()
        gamma_spec = Mock()
        gamma_spec.energy = np.array([0.5, 1.0])
        gamma_spec.intensity = np.array([0.5, 0.5])
        mock_gamma_prod.prompt_spectra = {"fission": gamma_spec}
        mock_cache.get_gamma_production_data.return_value = mock_gamma_prod
        
        gamma_energy = calculator._get_gamma_energy_per_decay(u235, mock_decay_data)
        assert gamma_energy >= 0
    
    def test_estimate_gamma_energy(self, mock_cache):
        """Test gamma energy estimation."""
        calculator = DecayHeatCalculator(cache=mock_cache)
        
        u235 = Nuclide(Z=92, A=235)
        gamma_energy = calculator._estimate_gamma_energy(u235)
        
        assert gamma_energy > 0
        assert gamma_energy == 1.5  # Default estimate
    
    def test_estimate_beta_energy(self, mock_cache):
        """Test beta energy estimation."""
        calculator = DecayHeatCalculator(cache=mock_cache)
        
        u235 = Nuclide(Z=92, A=235)
        beta_energy = calculator._estimate_beta_energy(u235)
        
        assert beta_energy > 0
    
    def test_decay_heat_result_get_heat_at_time(self, mock_cache, mock_decay_data):
        """Test getting decay heat at specific time."""
        calculator = DecayHeatCalculator(cache=mock_cache)
        
        u235 = Nuclide(Z=92, A=235)
        concentrations = {u235: 1e20}
        times = np.array([0, 3600, 86400, 604800])
        
        with patch.object(calculator, '_get_decay_data', return_value=mock_decay_data):
            result = calculator.calculate_decay_heat(concentrations, times)
        
        # Get heat at specific time
        heat_1day = result.get_decay_heat_at_time(86400)
        assert heat_1day >= 0
        
        # Test interpolation
        heat_12h = result.get_decay_heat_at_time(43200)
        assert heat_12h >= 0
        
        # Test extrapolation (before first time)
        heat_before = result.get_decay_heat_at_time(-1000)
        assert heat_before >= 0
        
        # Test extrapolation (after last time)
        heat_after = result.get_decay_heat_at_time(1e6)
        assert heat_after >= 0
    
    def test_zero_concentration(self, mock_cache, mock_decay_data):
        """Test handling zero concentrations."""
        calculator = DecayHeatCalculator(cache=mock_cache)
        
        u235 = Nuclide(Z=92, A=235)
        concentrations = {u235: 0.0}  # Zero concentration
        times = np.array([0, 3600])
        
        with patch.object(calculator, '_get_decay_data', return_value=mock_decay_data):
            result = calculator.calculate_decay_heat(concentrations, times)
        
        assert np.all(result.total_decay_heat == 0)
    
    def test_no_decay_data(self, mock_cache):
        """Test handling nuclides without decay data."""
        calculator = DecayHeatCalculator(cache=mock_cache)
        
        unknown = Nuclide(Z=999, A=1000)  # Non-existent nuclide
        concentrations = {unknown: 1e20}
        times = np.array([0, 3600])
        
        with patch.object(calculator, '_get_decay_data', return_value=None):
            result = calculator.calculate_decay_heat(concentrations, times)
        
        assert np.all(result.total_decay_heat == 0)
    
    def test_stable_nuclide(self, mock_cache):
        """Test handling stable nuclides (zero decay constant)."""
        calculator = DecayHeatCalculator(cache=mock_cache)
        
        u235 = Nuclide(Z=92, A=235)
        stable_decay = Mock(spec=DecayData)
        stable_decay.decay_constant = 0.0  # Stable
        stable_decay.get_total_gamma_energy.return_value = 0.0
        stable_decay.get_total_beta_energy.return_value = 0.0
        
        concentrations = {u235: 1e20}
        times = np.array([0, 3600])
        
        with patch.object(calculator, '_get_decay_data', return_value=stable_decay):
            result = calculator.calculate_decay_heat(concentrations, times)
        
        assert np.all(result.total_decay_heat == 0)
    
    def test_initial_time_offset(self, mock_cache, mock_decay_data):
        """Test decay heat with non-zero initial time."""
        calculator = DecayHeatCalculator(cache=mock_cache)
        
        u235 = Nuclide(Z=92, A=235)
        concentrations = {u235: 1e20}
        times = np.array([3600, 7200, 10800])  # Starting at 1h
        initial_time = 3600.0
        
        with patch.object(calculator, '_get_decay_data', return_value=mock_decay_data):
            result = calculator.calculate_decay_heat(concentrations, times, initial_time=initial_time)
        
        assert len(result.times) == len(times)
        assert np.all(result.total_decay_heat >= 0)

