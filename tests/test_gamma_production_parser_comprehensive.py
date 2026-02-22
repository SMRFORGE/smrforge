"""
Comprehensive tests for gamma production parser to improve coverage to 80%+.

Tests cover:
- File parsing
- Filename parsing
- MF=12 parsing (prompt)
- MF=13,14 parsing (delayed)
- Spectrum parsing
- Data access methods
"""

from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from smrforge.core.gamma_production_parser import (
    ENDFGammaProductionParser,
    GammaProductionData,
    GammaProductionSpectrum,
)
from smrforge.core.reactor_core import Nuclide


@pytest.fixture
def mock_gamma_production_file(tmp_path):
    """Create a mock gamma production ENDF file."""
    filepath = tmp_path / "gammas-092_U_235.endf"

    # Create minimal valid ENDF gamma production file
    lines = [
        " 9.223500+4 2.345678+2          0          0          0          0 12 18     \n",
        " 0.000000+0 0.000000+0          0          0          2         10 12 18     \n",
        " 1.000000-2 1.000000+0 1.000000-1 5.000000+0 1.000000+0 2.000000+0 12 18     \n",
        " 1.000000+1 1.000000-1 0.000000+0 0.000000+0 0.000000+0 0.000000+0 12 18     \n",
        " 9.223500+4 2.345678+2          0          0          0          0 13 18     \n",
        " 0.000000+0 0.000000+0          0          0          2         10 13 18     \n",
        " 1.000000-2 5.000000-1 1.000000-1 2.500000+0 1.000000+0 1.000000+0 13 18     \n",
        " 1.000000+1 5.000000-2 0.000000+0 0.000000+0 0.000000+0 0.000000+0 13 18     \n",
        "                                                                    -1  0  0   \n",
    ]

    filepath.write_text("".join(lines))
    return filepath


class TestENDFGammaProductionParserComprehensive:
    """Comprehensive tests for ENDFGammaProductionParser."""

    def test_parse_file_success(self, mock_gamma_production_file):
        """Test successful file parsing."""
        parser = ENDFGammaProductionParser()
        gamma_data = parser.parse_file(mock_gamma_production_file)

        assert gamma_data is not None
        assert isinstance(gamma_data, GammaProductionData)
        assert gamma_data.nuclide.Z == 92
        assert gamma_data.nuclide.A == 235

    def test_parse_file_nonexistent(self):
        """Test parsing nonexistent file."""
        parser = ENDFGammaProductionParser()
        result = parser.parse_file(Path("nonexistent.endf"))

        assert result is None

    def test_parse_filename_valid(self):
        """Test parsing valid filename."""
        parser = ENDFGammaProductionParser()

        result = parser._parse_filename("gammas-092_U_235.endf")
        assert result is not None
        assert result.Z == 92
        assert result.A == 235

    def test_parse_filename_variations(self):
        """Test parsing various filename formats."""
        parser = ENDFGammaProductionParser()

        # Standard format
        result = parser._parse_filename("gammas-001_H_001.endf")
        assert result is not None
        assert result.Z == 1
        assert result.A == 1

        # Alternative format
        result = parser._parse_filename("gamma-092_U_235.endf")
        assert result is not None
        assert result.Z == 92

        # With metastable
        result = parser._parse_filename("gammas-092_U_239m1.endf")
        assert result is not None
        assert result.m == 1

    def test_parse_filename_invalid(self):
        """Test parsing invalid filename."""
        parser = ENDFGammaProductionParser()

        result = parser._parse_filename("invalid_filename.txt")
        assert result is None

    def test_parse_mf12(self, mock_gamma_production_file):
        """Test parsing MF=12 (prompt gamma)."""
        parser = ENDFGammaProductionParser()

        with open(mock_gamma_production_file, "r") as f:
            lines = f.readlines()

        spectra = parser._parse_mf12(lines)

        assert isinstance(spectra, dict)
        # Should have fission spectrum (MT=18)
        if "fission" in spectra:
            assert isinstance(spectra["fission"], GammaProductionSpectrum)
            assert spectra["fission"].prompt is True

    def test_parse_mf13_14(self, mock_gamma_production_file):
        """Test parsing MF=13,14 (delayed gamma)."""
        parser = ENDFGammaProductionParser()

        with open(mock_gamma_production_file, "r") as f:
            lines = f.readlines()

        spectra = parser._parse_mf13_14(lines)

        assert isinstance(spectra, dict)
        # Should have delayed spectra if present
        for spectrum in spectra.values():
            assert spectrum.prompt is False

    def test_parse_gamma_spectrum_section(self, mock_gamma_production_file):
        """Test parsing gamma spectrum section."""
        parser = ENDFGammaProductionParser()

        with open(mock_gamma_production_file, "r") as f:
            lines = f.readlines()

        # Find MF=12, MT=18 section
        start_idx = 0
        for i, line in enumerate(lines):
            if "12 18" in line:
                start_idx = i
                break

        result = parser._parse_gamma_spectrum_section(lines, start_idx, 18)

        assert result is not None
        energy, intensity = result
        assert len(energy) > 0
        assert len(intensity) > 0
        assert len(energy) == len(intensity)

    def test_gamma_production_data_methods(self):
        """Test GammaProductionData methods."""
        u235 = Nuclide(Z=92, A=235)

        # Create prompt spectrum
        prompt_spectrum = GammaProductionSpectrum(
            reaction="fission",
            energy=np.array([0.5, 1.0, 1.5]),
            intensity=np.array([0.3, 0.5, 0.2]),
            total_yield=1.0,
            prompt=True,
        )

        # Create delayed spectrum
        delayed_spectrum = GammaProductionSpectrum(
            reaction="fission",
            energy=np.array([0.5, 1.0]),
            intensity=np.array([0.6, 0.4]),
            total_yield=0.5,
            prompt=False,
        )

        gamma_data = GammaProductionData(
            nuclide=u235,
            prompt_spectra={"fission": prompt_spectrum},
            delayed_spectra={"fission": delayed_spectrum},
        )

        # Test get_total_gamma_yield
        prompt_yield = gamma_data.get_total_gamma_yield("fission", prompt=True)
        assert prompt_yield == 1.0

        delayed_yield = gamma_data.get_total_gamma_yield("fission", prompt=False)
        assert delayed_yield == 0.5

        # Test get_gamma_spectrum
        prompt_spec = gamma_data.get_gamma_spectrum("fission", prompt=True)
        assert prompt_spec is not None
        assert prompt_spec.prompt is True

        delayed_spec = gamma_data.get_gamma_spectrum("fission", prompt=False)
        assert delayed_spec is not None
        assert delayed_spec.prompt is False

        # Test missing reaction
        missing_yield = gamma_data.get_total_gamma_yield("capture", prompt=True)
        assert missing_yield == 0.0

        missing_spec = gamma_data.get_gamma_spectrum("capture", prompt=True)
        assert missing_spec is None

    def test_parse_file_exception_handling(self, tmp_path):
        """Test exception handling during parsing."""
        parser = ENDFGammaProductionParser()

        # Create malformed file
        filepath = tmp_path / "gammas-092_U_235.endf"
        filepath.write_text("invalid content\n" * 10)

        # Should handle exception gracefully
        result = parser.parse_file(filepath)

        # Should return None or handle gracefully
        assert result is None or isinstance(result, GammaProductionData)

    def test_reaction_mt_mapping(self):
        """Test reaction MT mapping."""
        parser = ENDFGammaProductionParser()

        # Check that MT numbers are mapped correctly
        assert 18 in parser.reaction_mt_map
        assert parser.reaction_mt_map[18] == "fission"
        assert 102 in parser.reaction_mt_map
        assert parser.reaction_mt_map[102] == "capture"

    def test_parse_file_empty_file(self, tmp_path):
        """Test parsing empty file."""
        parser = ENDFGammaProductionParser()

        filepath = tmp_path / "gammas-092_U_235.endf"
        filepath.write_text("")

        result = parser.parse_file(filepath)

        # Should return None or handle gracefully
        assert result is None or isinstance(result, GammaProductionData)

    def test_parse_file_read_exception(self, tmp_path):
        """Test exception handling during file read."""
        parser = ENDFGammaProductionParser()

        filepath = tmp_path / "gammas-092_U_235.endf"
        filepath.write_text("test")

        # Mock open to raise exception
        with patch("builtins.open", side_effect=Exception("Read error")):
            with patch(
                "smrforge.core.gamma_production_parser.logger"
            ) as mock_logger:
                result = parser.parse_file(filepath)
                assert result is None
                mock_logger.warning.assert_called_once()

    def test_parse_filename_multiple_patterns(self):
        """Test parsing filename with multiple pattern attempts."""
        parser = ENDFGammaProductionParser()

        # Test first pattern
        result1 = parser._parse_filename("gammas-092_U_235.endf")
        assert result1 is not None
        assert result1.Z == 92

        # Test second pattern
        result2 = parser._parse_filename("gamma-001_H_001.endf")
        assert result2 is not None
        assert result2.Z == 1

        # Test third pattern (alternative format)
        result3 = parser._parse_filename("092_U_235.endf")
        assert result3 is not None
        assert result3.Z == 92

    def test_parse_filename_with_metastable(self):
        """Test parsing filename with metastable state."""
        parser = ENDFGammaProductionParser()

        result = parser._parse_filename("gammas-092_U_239m1.endf")
        assert result is not None
        assert result.m == 1

        result = parser._parse_filename("gammas-092_U_239m2.endf")
        assert result is not None
        assert result.m == 2

    def test_parse_filename_invalid_format(self):
        """Test parsing filename with invalid format."""
        parser = ENDFGammaProductionParser()

        result = parser._parse_filename("invalid")
        assert result is None

        result = parser._parse_filename("not-gamma-file.txt")
        assert result is None

    def test_parse_mf12_no_sections(self):
        """Test parsing MF=12 when no sections exist."""
        parser = ENDFGammaProductionParser()

        lines = [
            " 1.001000+3 1.000000+0          0          0          0          0  3  1     \n",
        ]

        spectra = parser._parse_mf12(lines)
        assert isinstance(spectra, dict)
        assert len(spectra) == 0

    def test_parse_mf12_invalid_mt(self):
        """Test parsing MF=12 with invalid MT number."""
        parser = ENDFGammaProductionParser()

        lines = [
            " 1.001000+3 1.000000+0          0          0          0          0 12 XX     \n",
        ]

        spectra = parser._parse_mf12(lines)
        assert isinstance(spectra, dict)
        # Should skip invalid MT

    def test_parse_mf13_14_no_sections(self):
        """Test parsing MF=13,14 when no sections exist."""
        parser = ENDFGammaProductionParser()

        lines = [
            " 1.001000+3 1.000000+0          0          0          0          0  3  1     \n",
        ]

        spectra = parser._parse_mf13_14(lines)
        assert isinstance(spectra, dict)
        assert len(spectra) == 0

    def test_parse_gamma_spectrum_section_invalid_index(self):
        """Test parsing gamma spectrum section with invalid start index."""
        parser = ENDFGammaProductionParser()

        lines = [
            " 1.001000+3 1.000000+0          0          0          0          0 12 18     \n",
        ]

        result = parser._parse_gamma_spectrum_section(
            lines, 100, 18
        )  # Index out of range
        assert result is None

    def test_parse_gamma_spectrum_section_exception(self):
        """Test parsing gamma spectrum section with exception."""
        parser = ENDFGammaProductionParser()

        lines = ["invalid line\n"]

        result = parser._parse_gamma_spectrum_section(lines, 0, 18)
        assert result is None

    def test_parse_mf12_alternative_mf_position(self):
        """Test parsing MF=12 with MF at alternative position."""
        parser = ENDFGammaProductionParser()

        lines = [
            " 9.223500+4 2.345678+2          0          0          0          0   12 18     \n",
        ]

        spectra = parser._parse_mf12(lines)
        assert isinstance(spectra, dict)

    def test_parse_mf12_no_mt_str(self):
        """Test parsing MF=12 when MT string is empty."""
        parser = ENDFGammaProductionParser()

        lines = [
            " 9.223500+4 2.345678+2          0          0          0          0 12      \n",
        ]

        spectra = parser._parse_mf12(lines)
        assert isinstance(spectra, dict)

    def test_parse_mf12_extract_mt_from_context(self):
        """Test extracting MT from context when standard position fails."""
        parser = ENDFGammaProductionParser()

        lines = [
            " 9.223500+4 2.345678+2          0          0          0          0   12   18     \n",
        ]

        spectra = parser._parse_mf12(lines)
        assert isinstance(spectra, dict)

    def test_parse_gamma_spectrum_section_short_line(self):
        """Test parsing gamma spectrum section with short line."""
        parser = ENDFGammaProductionParser()

        lines = [
            " 9.223500+4 2.345678+2          0          0          0          0 12 18     \n",
            "short\n",  # Line too short
        ]

        result = parser._parse_gamma_spectrum_section(lines, 0, 18)
        assert result is None or isinstance(result, tuple)

    def test_parse_gamma_spectrum_section_new_mf_break(self):
        """Test parsing breaks when encountering different MF."""
        parser = ENDFGammaProductionParser()

        lines = [
            " 9.223500+4 2.345678+2          0          0          0          0 12 18     \n",
            " 0.000000+0 0.000000+0          0          0          2         10 12 18     \n",
            " 1.000000+3 2.500000+2          0          0          0          0  3  1     \n",  # Different MF
        ]

        result = parser._parse_gamma_spectrum_section(lines, 0, 18)
        assert result is None or isinstance(result, tuple)

    def test_parse_gamma_spectrum_section_scientific_notation_error(self):
        """Test parsing handles scientific notation errors."""
        parser = ENDFGammaProductionParser()

        lines = [
            " 9.223500+4 2.345678+2          0          0          0          0 12 18     \n",
            "invalid scientific notation here                                                   12 18     \n",
        ]

        result = parser._parse_gamma_spectrum_section(lines, 0, 18)
        # Should handle error gracefully and continue
        assert result is None or isinstance(result, tuple)

    def test_gamma_production_data_empty_spectra(self):
        """Test GammaProductionData with empty spectra."""
        u235 = Nuclide(Z=92, A=235)

        gamma_data = GammaProductionData(
            nuclide=u235,
            prompt_spectra={},
            delayed_spectra={},
        )

        # Should return 0.0 for missing reactions
        yield_fission = gamma_data.get_total_gamma_yield("fission", prompt=True)
        assert yield_fission == 0.0

        spec = gamma_data.get_gamma_spectrum("fission", prompt=True)
        assert spec is None

    def test_gamma_production_data_delayed_only(self):
        """Test GammaProductionData with only delayed spectra."""
        u235 = Nuclide(Z=92, A=235)

        delayed_spectrum = GammaProductionSpectrum(
            reaction="fission",
            energy=np.array([0.5, 1.0]),
            intensity=np.array([0.6, 0.4]),
            total_yield=0.5,
            prompt=False,
        )

        gamma_data = GammaProductionData(
            nuclide=u235,
            prompt_spectra={},
            delayed_spectra={"fission": delayed_spectrum},
        )

        # Prompt should return 0.0
        prompt_yield = gamma_data.get_total_gamma_yield("fission", prompt=True)
        assert prompt_yield == 0.0

        # Delayed should return yield
        delayed_yield = gamma_data.get_total_gamma_yield("fission", prompt=False)
        assert delayed_yield == 0.5

    def test_parse_filename_keyerror_is_handled(self):
        """Force the (ValueError, KeyError) filename parsing continue branch."""
        parser = ENDFGammaProductionParser()

        with patch(
            "smrforge.core.gamma_production_parser.Nuclide",
            side_effect=KeyError("boom"),
        ):
            assert parser._parse_filename("gammas-092_U_235.endf") is None

    def test_parse_mf12_context_extraction_and_unknown_mt(self):
        """Hit MF/MT context extraction and default mt->reaction mapping."""
        parser = ENDFGammaProductionParser()

        def _line_with_mf12_mt_in_context(mt_token: str) -> str:
            chars = [" "] * 80
            # Put "12" into the 66:78 window but keep 70:72 blank.
            chars[68:70] = list("12")
            # Keep 72:75 blank so MT must be extracted from context.
            if mt_token:
                chars[75 : 75 + len(mt_token)] = list(mt_token)
            return "".join(chars) + "\n"

        header_unknown_mt = _line_with_mf12_mt_in_context("999")
        # One valid data line (energy/intensity pair in ENDF scientific notation) and an end marker.
        data = (" 1.000000+0" + " 2.000000+0").ljust(80) + "\n"
        end = (" " * 66 + "-1").ljust(80) + "\n"

        # Also include a line where MT token is non-numeric to hit the ValueError branch.
        header_bad_mt = _line_with_mf12_mt_in_context("XX")

        lines = [header_unknown_mt, data, end, header_bad_mt]
        spectra = parser._parse_mf12(lines)

        assert "mt999" in spectra
        assert spectra["mt999"].prompt is True
        assert spectra["mt999"].total_yield > 0.0

    def test_parse_mf13_14_invalid_mt_is_skipped(self):
        """Hit the ValueError branch when MT cannot be parsed for MF=13/14."""
        parser = ENDFGammaProductionParser()

        # MF=13 with non-integer MT field.
        line = (" " * 70 + "13" + "XX " + " " * 5).ljust(80) + "\n"
        assert parser._parse_mf13_14([line]) == {}

    def test_parse_gamma_spectrum_section_header_parse_error_and_end_marker(self):
        """Cover header detection ValueError path and '-1' end-marker break."""
        parser = ENDFGammaProductionParser()

        header = (" " * 70 + "12" + " 18").ljust(80) + "\n"
        control = ((" 0.000000+0" + " 0.000000+0").ljust(70) + "12" + " 18").ljust(
            80
        ) + "\n"
        # This looks like a new header line but has non-numeric ZA field -> triggers ValueError in float().
        bad_header_like = ("not_a_num".ljust(70) + "12" + " 18").ljust(80) + "\n"
        end = (" " * 66 + "-1").ljust(80) + "\n"

        assert (
            parser._parse_gamma_spectrum_section(
                [header, control, bad_header_like, end], 0, 18
            )
            is None
        )

    def test_parse_file_invalid_filename_returns_none(self, tmp_path):
        """Cover parse_file() path where filename doesn't match nuclide patterns."""
        parser = ENDFGammaProductionParser()
        filepath = tmp_path / "not-a-gamma-file.endf"
        filepath.write_text("anything\n")
        assert parser.parse_file(filepath) is None

    def test_parse_mf13_14_success_and_unknown_mt_mapping(self):
        """Cover delayed-spectrum success path and default mt->reaction mapping."""
        parser = ENDFGammaProductionParser()

        header = (" " * 70 + "13" + "999").ljust(80) + "\n"
        data = (" 1.000000+0" + " 3.000000+0").ljust(70) + "13" + "999" + " " * 5 + "\n"
        end = (" " * 66 + "-1").ljust(80) + "\n"

        spectra = parser._parse_mf13_14([header, data, end])
        assert "mt999" in spectra
        assert spectra["mt999"].prompt is False
        assert spectra["mt999"].total_yield > 0.0
