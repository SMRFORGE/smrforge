"""
Tests for decay data parser.
"""

import pytest
from pathlib import Path

from smrforge.core.reactor_core import Nuclide
from smrforge.core.decay_parser import (
    ENDFDecayParser,
    DecayData,
    DecayMode,
)


class TestDecayData:
    """Test DecayData dataclass."""

    def test_decay_data_creation(self):
        """Test creating DecayData."""
        u235 = Nuclide(Z=92, A=235)
        u236 = Nuclide(Z=92, A=236)
        
        decay_modes = [
            DecayMode(
                mode="α",
                daughter=u236,
                branching_ratio=0.5,
            )
        ]

        data = DecayData(
            nuclide=u235,
            half_life=7.04e8,  # seconds (~22.3 years)
            decay_constant=0.0,  # Will be calculated
            is_stable=False,
            decay_modes=decay_modes,
            daughters={},
        )

        assert data.nuclide == u235
        assert data.half_life == 7.04e8
        assert len(data.decay_modes) == 1
        assert data.decay_constant > 0  # Should be calculated

    def test_decay_constant_calculation(self):
        """Test decay constant is calculated from half-life."""
        u235 = Nuclide(Z=92, A=235)
        
        data = DecayData(
            nuclide=u235,
            half_life=7.04e8,  # seconds
            decay_constant=0.0,
            is_stable=False,
            decay_modes=[],
            daughters={},
        )

        # Decay constant = ln(2) / half_life
        expected = 0.693147 / 7.04e8
        assert abs(data.decay_constant - expected) < 1e-10
    
    def test_decay_data_stable(self):
        """Test DecayData for stable nuclide."""
        u238 = Nuclide(Z=92, A=238)
        
        data = DecayData(
            nuclide=u238,
            half_life=1e21,  # Very long half-life (effectively stable)
            decay_constant=0.0,
            is_stable=True,
            decay_modes=[],
            daughters={},
        )
        
        assert data.is_stable
        assert data.decay_constant == 0.0
    
    def test_decay_data_gamma_spectrum(self):
        """Test DecayData with gamma spectrum."""
        from smrforge.core.decay_parser import GammaSpectrum
        import numpy as np
        
        u235 = Nuclide(Z=92, A=235)
        gamma_spec = GammaSpectrum(
            energy=np.array([0.5, 1.0, 1.5]),
            intensity=np.array([0.3, 0.5, 0.2]),
            total_energy=1.2,
        )
        
        data = DecayData(
            nuclide=u235,
            half_life=7.04e8,
            decay_constant=0.0,
            is_stable=False,
            decay_modes=[],
            daughters={},
            gamma_spectrum=gamma_spec,
        )
        
        assert data.gamma_spectrum is not None
        assert data.get_total_gamma_energy() == 1.2
        energy, intensity = data.gamma_spectrum.get_energy_spectrum()
        assert len(energy) == 3
    
    def test_decay_data_beta_spectrum(self):
        """Test DecayData with beta spectrum."""
        from smrforge.core.decay_parser import BetaSpectrum
        import numpy as np
        
        u235 = Nuclide(Z=92, A=235)
        beta_spec = BetaSpectrum(
            energy=np.array([0.5, 1.0]),
            intensity=np.array([0.6, 0.4]),
            endpoint_energy=1.0,
            average_energy=0.8,
        )
        
        data = DecayData(
            nuclide=u235,
            half_life=7.04e8,
            decay_constant=0.0,
            is_stable=False,
            decay_modes=[],
            daughters={},
            beta_spectrum=beta_spec,
        )
        
        assert data.beta_spectrum is not None
        assert data.get_total_beta_energy() == 0.8
        energy, intensity = data.beta_spectrum.get_energy_spectrum()
        assert len(energy) == 2


class TestENDFDecayParser:
    """Test ENDFDecayParser."""

    def test_parser_initialization(self):
        """Test parser can be initialized."""
        parser = ENDFDecayParser()
        assert parser is not None

    def test_parse_filename(self):
        """Test filename parsing."""
        parser = ENDFDecayParser()
        
        # Test standard format
        nuclide = parser._parse_filename("dec-092_U_235.endf")
        assert nuclide is not None
        assert nuclide.Z == 92
        assert nuclide.A == 235

    def test_parse_file_nonexistent(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        parser = ENDFDecayParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("nonexistent.endf"))
    
    def test_parse_filename_with_metastable(self):
        """Test parsing filename with metastable state."""
        parser = ENDFDecayParser()
        
        nuclide = parser._parse_filename("dec-092_U_235m1.endf")
        assert nuclide is not None
        assert nuclide.Z == 92
        assert nuclide.A == 235
        assert nuclide.m == 1
    
    def test_parse_filename_invalid(self):
        """Test parsing invalid filename."""
        parser = ENDFDecayParser()
        
        nuclide = parser._parse_filename("invalid.endf")
        assert nuclide is None
    
    def test_parse_half_life_with_zero(self):
        """Test parsing half-life with zero value."""
        parser = ENDFDecayParser()
        
        # Test with zero half-life (should return 1e20 for stable)
        lines = [
            " " * 70 + " 8  457",
            " 0.00000000E+00",
        ]
        half_life = parser._parse_half_life(lines)
        assert half_life == 1e20
    
    def test_parse_half_life_not_found(self):
        """Test parsing half-life when section not found."""
        parser = ENDFDecayParser()
        
        lines = [" " * 50]
        half_life = parser._parse_half_life(lines)
        assert half_life == 1e20  # Default for stable
    
    def test_build_daughters_dict(self):
        """Test building daughters dictionary."""
        parser = ENDFDecayParser()
        u235 = Nuclide(Z=92, A=235)
        u236 = Nuclide(Z=92, A=236)
        u237 = Nuclide(Z=92, A=237)
        
        decay_modes = [
            DecayMode(mode="α", daughter=u236, branching_ratio=0.3),
            DecayMode(mode="β⁻", daughter=u236, branching_ratio=0.2),  # Same daughter
            DecayMode(mode="α", daughter=u237, branching_ratio=0.5),
            DecayMode(mode="SF", daughter=None, branching_ratio=0.0),  # No daughter
        ]
        
        daughters = parser._build_daughters_dict(decay_modes)
        
        assert u236 in daughters
        assert daughters[u236] == 0.5  # 0.3 + 0.2
        assert u237 in daughters
        assert daughters[u237] == 0.5
    
    def test_parse_gamma_spectrum(self):
        """Test parsing gamma spectrum."""
        parser = ENDFDecayParser()
        
        lines = [" " * 70 + " 8  460"]
        spectrum = parser._parse_gamma_spectrum(lines)
        assert spectrum is None  # Simplified parser returns None
    
    def test_parse_beta_spectrum(self):
        """Test parsing beta spectrum."""
        parser = ENDFDecayParser()
        
        lines = [" " * 70 + " 8  455"]
        spectrum = parser._parse_beta_spectrum(lines)
        assert spectrum is None  # Simplified parser returns None


class TestDecayIntegration:
    """Test decay data integration with NuclearDataCache."""

    def test_decay_data_class(self):
        """Test DecayData class from reactor_core."""
        from smrforge.core.reactor_core import DecayData, Nuclide, NuclearDataCache

        cache = NuclearDataCache()
        decay_data = DecayData(cache=cache)
        
        u235 = Nuclide(Z=92, A=235)
        half_life = decay_data._get_half_life(u235)  # Use private method
        
        # Should return a positive value (may be placeholder if file not found)
        assert half_life > 0

    def test_decay_constant(self):
        """Test getting decay constant."""
        from smrforge.core.reactor_core import DecayData, Nuclide, NuclearDataCache

        cache = NuclearDataCache()
        decay_data = DecayData(cache=cache)
        
        u235 = Nuclide(Z=92, A=235)
        lambda_decay = decay_data.get_decay_constant(u235)
        
        # Should return a non-negative value
        assert lambda_decay >= 0

    def test_get_daughters(self):
        """Test getting decay daughters."""
        from smrforge.core.reactor_core import DecayData, Nuclide, NuclearDataCache

        cache = NuclearDataCache()
        decay_data = DecayData(cache=cache)
        
        u235 = Nuclide(Z=92, A=235)
        daughters = decay_data._get_daughters(u235)  # Use private method
        
        # Should return a list (may be empty if no decay data)
        assert isinstance(daughters, list)

