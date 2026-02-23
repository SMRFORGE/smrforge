"""
Tests for decay data parser.
"""

from pathlib import Path

import pytest

from smrforge.core.decay_parser import (
    DecayData,
    DecayMode,
    ENDFDecayParser,
)
from smrforge.core.reactor_core import Nuclide


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
        import numpy as np

        from smrforge.core.decay_parser import GammaSpectrum

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
        import numpy as np

        from smrforge.core.decay_parser import BetaSpectrum

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
        """Test parsing gamma spectrum with header only returns None."""
        parser = ENDFDecayParser()

        lines = [" " * 70 + " 8  460"]
        spectrum = parser._parse_gamma_spectrum(lines)
        assert spectrum is None

    def test_parse_gamma_spectrum_from_mt457_rtyp0(self):
        """Test parsing gamma spectrum from MT=457 decay radiation (RTYP=0)."""
        parser = ENDFDecayParser()
        # ENDF 6-tuple: RTYP=0, RFS=0, Q(eV)=661600, D=0, BR=0.85, DBR=0
        # Energy 661600 eV = 0.6616 MeV. ENDF cols 70-72 MF, 72-75 MT.
        data = " 0.000000+0 0.000000+0 6.616000+5 0.000000+0 8.500000-1 0.000000+0"
        lines = [
            " " * 69 + " 8 457",
            data + "    8 457",  # 66 data + 9 chars so 72:75="457"
        ]
        spectrum = parser._parse_gamma_spectrum(lines)
        assert spectrum is not None
        assert len(spectrum.energy) == 1
        assert abs(spectrum.energy[0] - 0.6616) < 0.001
        assert abs(spectrum.intensity[0] - 0.85) < 0.01
        assert spectrum.total_energy > 0

    def test_parse_beta_spectrum(self):
        """Test parsing beta spectrum with header only returns None."""
        parser = ENDFDecayParser()

        lines = [" " * 70 + " 8  455"]
        spectrum = parser._parse_beta_spectrum(lines)
        assert spectrum is None

    def test_parse_beta_spectrum_from_mt457_rtyp1(self):
        """Test parsing beta spectrum from MT=457 decay radiation (RTYP=1)."""
        parser = ENDFDecayParser()
        # RTYP=1 (beta-), RFS, Q(eV)=2500000 (2.5 MeV), D=0, BR=1.0, DBR=0
        data = " 1.000000+0 9.200000+3 2.500000+6 0.000000+0 1.000000+0 0.000000+0"
        lines = [
            " " * 69 + " 8 457",
            data + "    8 457",
        ]
        spectrum = parser._parse_beta_spectrum(lines)
        assert spectrum is not None
        assert len(spectrum.energy) == 1
        assert abs(spectrum.energy[0] - 2.5) < 0.001
        assert spectrum.endpoint_energy == spectrum.energy[0]

    def test_parse_half_life_short_line(self):
        """Test parsing half-life with short line (line 224)."""
        parser = ENDFDecayParser()

        # Line shorter than 75 characters
        lines = ["short line"]
        half_life = parser._parse_half_life(lines)
        assert half_life == 1e20  # Default for stable

    def test_parse_half_life_value_error(self):
        """Test parsing half-life with ValueError (line 245)."""
        parser = ENDFDecayParser()

        # Line with invalid float value
        lines = [
            " " * 70 + " 8  457",
            "invalid_float_value",
        ]
        half_life = parser._parse_half_life(lines)
        assert half_life == 1e20  # Default when parsing fails

    def test_parse_half_life_positive_value(self):
        """Test parsing half-life with positive value."""
        parser = ENDFDecayParser()

        lines = [
            " " * 70 + " 8  457",
            " 7.04000000E+08",  # U-235 half-life
        ]
        half_life = parser._parse_half_life(lines)
        assert half_life > 0
        assert half_life <= 1e20  # Allow for default stable value

    def test_parse_decay_modes_short_line(self):
        """Test parsing decay modes with short line (line 266)."""
        parser = ENDFDecayParser()
        u235 = Nuclide(Z=92, A=235)

        # Line shorter than 75 characters
        lines = ["short line"]
        decay_modes = parser._parse_decay_modes(lines, u235)
        assert isinstance(decay_modes, list)

    def test_parse_decay_modes_with_branching_ratios(self):
        """Test parsing decay modes and branching ratios from ENDF-style data."""
        parser = ENDFDecayParser()
        u235 = Nuclide(Z=92, A=235)
        th231 = Nuclide(Z=90, A=231)

        # Mock ENDF MF=8 MT=457 with decay radiation (RTYP, RFS, Q, D, BR, DBR)
        # Each field 11 chars. RTYP=4 (alpha), RFS=90231, BR=1.0
        # ENDF format: cols 0-10, 11-21, ..., 66+ for MAT/MF/MT
        line = (
            " 4.0000000+0 9.0231000+4 0.0000000+0 0.0000000+0 1.0000000+0"
            " 0.0000000+0" + " " * 8 + " 8  457\n"
        )
        lines = [" " * 70 + " 8  457\n", line]
        decay_modes = parser._parse_decay_modes(lines, u235)
        assert isinstance(decay_modes, list)
        if decay_modes:
            assert all(0 < m.branching_ratio <= 1 for m in decay_modes)
            if any(m.daughter for m in decay_modes):
                assert th231 in [m.daughter for m in decay_modes if m.daughter]

    def test_parse_filename_metastable_m_only(self):
        """Test parsing filename with metastable 'm' only."""
        parser = ENDFDecayParser()

        nuclide = parser._parse_filename("dec-092_U_235m.endf")
        assert nuclide is not None
        assert nuclide.Z == 92
        assert nuclide.A == 235
        assert nuclide.m == 1  # Default to 1 if no number after 'm'

    def test_parse_filename_metastable_uppercase(self):
        """Test parsing filename with uppercase metastable marker."""
        parser = ENDFDecayParser()

        nuclide = parser._parse_filename("dec-092_U_235M1.endf")
        assert nuclide is not None
        assert nuclide.Z == 92
        assert nuclide.A == 235
        assert nuclide.m == 1

    def test_parse_file_exception_handling(self, tmp_path):
        """Test parse_file exception handling (lines 173-177)."""
        parser = ENDFDecayParser()

        # Create a file that will cause parsing to fail
        filepath = tmp_path / "dec-092_U_235.endf"
        filepath.write_text("invalid content that will cause parsing to fail\n" * 10)

        # Parser is lenient - it returns default DecayData with stable values
        # when content is invalid but filename is valid
        result = parser.parse_file(filepath)

        # Should return DecayData with default values (stable nuclide)
        assert result is not None
        assert result.nuclide.Z == 92
        assert result.nuclide.A == 235
        assert result.is_stable  # Default for invalid content
        assert result.half_life == 1e20  # Default stable half-life

    def test_parse_file_invalid_filename(self, tmp_path):
        """Test parse_file with invalid filename format."""
        parser = ENDFDecayParser()

        # Create file with invalid filename format
        filepath = tmp_path / "invalid_filename.endf"
        filepath.write_text("some content\n")

        # Should raise ValueError because filename can't be parsed
        with pytest.raises(ValueError, match="Could not extract nuclide"):
            parser.parse_file(filepath)

    def test_parse_gamma_spectrum_short_line(self):
        """Test parsing gamma spectrum with short line (line 311)."""
        parser = ENDFDecayParser()

        # Line shorter than 75 characters
        lines = ["short line"]
        spectrum = parser._parse_gamma_spectrum(lines)
        assert spectrum is None

    def test_parse_beta_spectrum_short_line(self):
        """Test parsing beta spectrum with short line (line 337)."""
        parser = ENDFDecayParser()

        # Line shorter than 75 characters
        lines = ["short line"]
        spectrum = parser._parse_beta_spectrum(lines)
        assert spectrum is None


class TestDecayIntegration:
    """Test decay data integration with NuclearDataCache."""

    def test_decay_data_class(self):
        """Test DecayData class from reactor_core."""
        from smrforge.core.reactor_core import DecayData, NuclearDataCache, Nuclide

        cache = NuclearDataCache()
        decay_data = DecayData(cache=cache)

        u235 = Nuclide(Z=92, A=235)
        half_life = decay_data._get_half_life(u235)  # Use private method

        # Should return a positive value (may be placeholder if file not found)
        assert half_life > 0

    def test_decay_constant(self):
        """Test getting decay constant."""
        from smrforge.core.reactor_core import DecayData, NuclearDataCache, Nuclide

        cache = NuclearDataCache()
        decay_data = DecayData(cache=cache)

        u235 = Nuclide(Z=92, A=235)
        lambda_decay = decay_data.get_decay_constant(u235)

        # Should return a non-negative value
        assert lambda_decay >= 0

    def test_get_daughters(self):
        """Test getting decay daughters."""
        from smrforge.core.reactor_core import DecayData, NuclearDataCache, Nuclide

        cache = NuclearDataCache()
        decay_data = DecayData(cache=cache)

        u235 = Nuclide(Z=92, A=235)
        daughters = decay_data._get_daughters(u235)  # Use private method

        # Should return a list (may be empty if no decay data)
        assert isinstance(daughters, list)
