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
                daughter=u236,
                branching_ratio=0.5,
                decay_type="alpha",
            )
        ]

        data = DecayData(
            nuclide=u235,
            half_life=7.04e8,  # seconds (~22.3 years)
            decay_constant=0.0,  # Will be calculated
            decay_modes=decay_modes,
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
            decay_modes=[],
        )

        # Decay constant = ln(2) / half_life
        expected = 0.693147 / 7.04e8
        assert abs(data.decay_constant - expected) < 1e-10


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
        """Test parsing non-existent file returns None."""
        parser = ENDFDecayParser()
        result = parser.parse_file(Path("nonexistent.endf"))
        assert result is None


class TestDecayIntegration:
    """Test decay data integration with NuclearDataCache."""

    def test_decay_data_class(self):
        """Test DecayData class from reactor_core."""
        from smrforge.core.reactor_core import DecayData, Nuclide, NuclearDataCache

        cache = NuclearDataCache()
        decay_data = DecayData(cache=cache)
        
        u235 = Nuclide(Z=92, A=235)
        half_life = decay_data.get_half_life(u235)
        
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
        daughters = decay_data.get_daughters(u235)
        
        # Should return a list of (daughter, branching_ratio) tuples
        assert isinstance(daughters, list)

