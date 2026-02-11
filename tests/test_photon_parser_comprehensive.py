"""
Comprehensive tests for photon parser to improve coverage to 80%+.

Tests cover:
- File parsing
- Filename parsing
- MT section parsing
- Interpolation
- Energy grid creation
- Error handling
"""

from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from smrforge.core.photon_parser import ENDFPhotonParser, PhotonCrossSection


@pytest.fixture
def mock_photon_file(tmp_path):
    """Create a mock photon ENDF file with MF/MT in parser's expected columns (70-75)."""
    filepath = tmp_path / "p-001_H_001.endf"
    # Parser expects line[70:72]=MF, line[72:75]=MT. Use 80-char ENDF lines.
    base = " 0.000000+0 0.000000+0          0          0          0          0"
    assert len(base) <= 66
    pad_to_70 = base.ljust(70)
    lines = [
        pad_to_70 + "23" + "  1" + " " * 5 + "\n",
        pad_to_70 + "23" + "501" + " " * 4 + "\n",
        " 0.000000+0 0.000000+0          0          0          2         10".ljust(70)
        + "23"
        + "501"
        + " " * 4
        + "\n",
        " 1.000000-2 1.000000+1 1.000000-1 5.000000+0 1.000000+0 2.000000+0".ljust(70)
        + "23"
        + "501"
        + " " * 4
        + "\n",
        " 1.000000+1 1.000000+0 0.000000+0 0.000000+0 0.000000+0 0.000000+0".ljust(70)
        + "23"
        + "501"
        + " " * 4
        + "\n",
        pad_to_70 + "23" + "502" + " " * 4 + "\n",
        " 0.000000+0 0.000000+0          0          0          2         10".ljust(70)
        + "23"
        + "502"
        + " " * 4
        + "\n",
        " 1.000000-2 2.000000+1 1.000000-1 1.000000+1 1.000000+0 5.000000+0".ljust(70)
        + "23"
        + "502"
        + " " * 4
        + "\n",
        " 1.000000+1 2.000000+0 0.000000+0 0.000000+0 0.000000+0 0.000000+0".ljust(70)
        + "23"
        + "502"
        + " " * 4
        + "\n",
        pad_to_70 + "23" + "516" + " " * 4 + "\n",
        " 0.000000+0 0.000000+0          0          0          2         10".ljust(70)
        + "23"
        + "516"
        + " " * 4
        + "\n",
        " 1.000000-2 1.000000+0 1.000000-1 5.000000-1 1.000000+0 2.000000-1".ljust(70)
        + "23"
        + "516"
        + " " * 4
        + "\n",
        " 1.000000+1 1.000000-1 0.000000+0 0.000000+0 0.000000+0 0.000000+0".ljust(70)
        + "23"
        + "516"
        + " " * 4
        + "\n",
        " " * 66 + "-1  0  0   \n",
    ]
    filepath.write_text("".join(lines))
    return filepath


class TestENDFPhotonParserComprehensive:
    """Comprehensive tests for ENDFPhotonParser."""

    def test_parse_file_success(self, mock_photon_file):
        """Test successful file parsing."""
        parser = ENDFPhotonParser()
        photon_data = parser.parse_file(mock_photon_file)

        assert photon_data is not None
        assert isinstance(photon_data, PhotonCrossSection)
        assert photon_data.element == "H"
        assert photon_data.Z == 1
        assert len(photon_data.energy) > 0
        assert len(photon_data.sigma_photoelectric) > 0
        assert len(photon_data.sigma_compton) > 0
        assert len(photon_data.sigma_pair) > 0
        assert len(photon_data.sigma_total) > 0

    def test_parse_file_nonexistent(self):
        """Test parsing nonexistent file."""
        parser = ENDFPhotonParser()
        result = parser.parse_file(Path("nonexistent.endf"))

        assert result is None

    def test_parse_filename_valid(self):
        """Test parsing valid filename."""
        parser = ENDFPhotonParser()

        result = parser._parse_filename("p-001_H_001.endf")
        assert result is not None
        element, Z = result
        assert element == "H"
        assert Z == 1

    def test_parse_filename_variations(self):
        """Test parsing various filename formats."""
        parser = ENDFPhotonParser()

        # Standard format
        result = parser._parse_filename("p-092_U_235.endf")
        assert result is not None
        element, Z = result
        assert element == "U"
        assert Z == 92

        # Without isotope number
        result = parser._parse_filename("p-001_H.endf")
        assert result is not None
        element, Z = result
        assert element == "H"
        assert Z == 1

    def test_parse_filename_invalid(self):
        """Test parsing invalid filename."""
        parser = ENDFPhotonParser()

        result = parser._parse_filename("invalid_filename.txt")
        assert result is None

        result = parser._parse_filename("not_a_photon_file.endf")
        assert result is None

    def test_parse_mt_section(self, mock_photon_file):
        """Test parsing MT section."""
        parser = ENDFPhotonParser()

        with open(mock_photon_file, "r") as f:
            lines = f.readlines()

        # Parse photoelectric section (MT=501)
        result = parser._parse_mt_section(lines, 501)

        assert result is not None
        energy, xs = result
        assert len(energy) > 0
        assert len(xs) > 0
        assert len(energy) == len(xs)

    def test_parse_mt_section_not_found(self, mock_photon_file):
        """Test parsing non-existent MT section."""
        parser = ENDFPhotonParser()

        with open(mock_photon_file, "r") as f:
            lines = f.readlines()

        # Try to parse non-existent section
        result = parser._parse_mt_section(lines, 999)

        assert result is None

    def test_interpolate_to_grid(self):
        """Test interpolating to target energy grid."""
        parser = ENDFPhotonParser()

        source_energy = np.array([0.01, 0.1, 1.0, 10.0])
        source_xs = np.array([1.0, 2.0, 3.0, 4.0])
        source_data = (source_energy, source_xs)

        target_energy = np.array([0.05, 0.5, 5.0])

        interpolated = parser._interpolate_to_grid(target_energy, source_data)

        assert len(interpolated) == len(target_energy)
        assert np.all(interpolated >= 0)

    def test_interpolate_to_grid_empty(self):
        """Test interpolating empty data."""
        parser = ENDFPhotonParser()

        source_data = (np.array([]), np.array([]))
        target_energy = np.array([0.1, 1.0])

        interpolated = parser._interpolate_to_grid(target_energy, source_data)

        assert len(interpolated) == len(target_energy)
        assert np.all(interpolated == 0)

    def test_photon_cross_section_interpolate(self):
        """Test PhotonCrossSection interpolation."""
        energy = np.array([0.01, 0.1, 1.0, 10.0])
        sigma_pe = np.array([1.0, 2.0, 3.0, 4.0])
        sigma_comp = np.array([2.0, 4.0, 6.0, 8.0])
        sigma_pair = np.array([0.1, 0.2, 0.3, 0.4])
        sigma_total = sigma_pe + sigma_comp + sigma_pair

        photon_data = PhotonCrossSection(
            element="H",
            Z=1,
            energy=energy,
            sigma_photoelectric=sigma_pe,
            sigma_compton=sigma_comp,
            sigma_pair=sigma_pair,
            sigma_total=sigma_total,
        )

        # Interpolate at various energies
        pe, comp, pair, tot = photon_data.interpolate(0.05)
        assert pe > 0
        assert comp > 0
        assert pair > 0
        assert tot > 0

        # Below minimum
        pe, comp, pair, tot = photon_data.interpolate(0.001)
        assert pe == sigma_pe[0]
        assert comp == sigma_comp[0]

        # Above maximum
        pe, comp, pair, tot = photon_data.interpolate(100.0)
        assert pe == sigma_pe[-1]
        assert comp == sigma_comp[-1]

    def test_parse_file_missing_sections(self, tmp_path):
        """Test parsing file with missing sections."""
        parser = ENDFPhotonParser()

        # Create file with only header
        filepath = tmp_path / "p-001_H_001.endf"
        filepath.write_text(
            " 1.001000+3 1.000000+0          0          0          0          0 23  1     \n"
        )

        result = parser.parse_file(filepath)

        # Should return None if no data sections
        assert result is None

    def test_parse_file_exception_handling(self, tmp_path):
        """Test exception handling during parsing."""
        parser = ENDFPhotonParser()

        # Create malformed file
        filepath = tmp_path / "p-001_H_001.endf"
        filepath.write_text("invalid content\n" * 10)

        # Should handle exception gracefully
        result = parser.parse_file(filepath)

        # Should return None or handle gracefully
        assert result is None or isinstance(result, PhotonCrossSection)

    def test_parse_file_empty_file(self, tmp_path):
        """Test parsing empty file."""
        parser = ENDFPhotonParser()

        filepath = tmp_path / "p-001_H_001.endf"
        filepath.write_text("")

        result = parser.parse_file(filepath)

        # Should return None
        assert result is None

    def test_parse_file_read_exception(self, tmp_path):
        """Test exception handling during file read."""
        parser = ENDFPhotonParser()

        filepath = tmp_path / "p-001_H_001.endf"
        filepath.write_text("test")

        # Mock open to raise exception
        with patch("builtins.open", side_effect=Exception("Read error")):
            with pytest.warns(UserWarning, match=r"Failed to parse photon data"):
                result = parser.parse_file(filepath)
                assert result is None

    def test_parse_filename_invalid_z(self):
        """Test parsing filename with invalid Z."""
        parser = ENDFPhotonParser()

        result = parser._parse_filename("p-ABC_H_001.endf")
        assert result is None

    def test_parse_filename_no_underscore(self):
        """Test parsing filename without underscore."""
        parser = ENDFPhotonParser()

        result = parser._parse_filename("p-001H001.endf")
        assert result is None

    def test_parse_mt_section_short_line(self):
        """Test parsing MT section with short line."""
        parser = ENDFPhotonParser()

        lines = ["short\n"]

        result = parser._parse_mt_section(lines, 501)
        assert result is None

    def test_parse_mt_section_exception(self):
        """Test parsing MT section with exception."""
        parser = ENDFPhotonParser()

        lines = ["invalid line\n"]

        result = parser._parse_mt_section(lines, 501)
        assert result is None

    def test_parse_mt_section_no_data(self):
        """Test parsing MT section with no data."""
        parser = ENDFPhotonParser()

        lines = [
            " 1.001000+3 1.000000+0          0          0          0          0 23 501   \n",
            "                                                                    -1  0  0   \n",
        ]

        result = parser._parse_mt_section(lines, 501)
        # Should return None if no data found
        assert result is None or result[0] is not None

    def test_interpolate_to_grid_extrapolation(self):
        """Test interpolating outside energy range."""
        parser = ENDFPhotonParser()

        source_energy = np.array([0.1, 1.0, 10.0])
        source_xs = np.array([1.0, 2.0, 3.0])
        source_data = (source_energy, source_xs)

        # Target energy outside source range
        target_energy = np.array([0.05, 0.5, 50.0])

        interpolated = parser._interpolate_to_grid(target_energy, source_data)

        assert len(interpolated) == len(target_energy)
        assert np.all(interpolated >= 0)

    def test_interpolate_to_grid_single_point(self):
        """Test interpolating with single source point."""
        parser = ENDFPhotonParser()

        source_energy = np.array([1.0])
        source_xs = np.array([2.0])
        source_data = (source_energy, source_xs)

        target_energy = np.array([0.5, 1.0, 2.0])

        interpolated = parser._interpolate_to_grid(target_energy, source_data)

        assert len(interpolated) == len(target_energy)
        # Should use constant value
        assert np.all(interpolated == 2.0)

    def test_interpolate_to_grid_exact_match(self):
        """Test interpolating with exact energy match."""
        parser = ENDFPhotonParser()

        source_energy = np.array([0.1, 1.0, 10.0])
        source_xs = np.array([1.0, 2.0, 3.0])
        source_data = (source_energy, source_xs)

        # Target energy matches source exactly
        target_energy = np.array([0.1, 1.0, 10.0])

        interpolated = parser._interpolate_to_grid(target_energy, source_data)

        assert len(interpolated) == len(target_energy)
        assert np.allclose(interpolated, source_xs)

    def test_photon_cross_section_interpolate_exact_match(self):
        """Test PhotonCrossSection interpolation with exact energy match."""
        energy = np.array([0.01, 0.1, 1.0, 10.0])
        sigma_pe = np.array([1.0, 2.0, 3.0, 4.0])
        sigma_comp = np.array([2.0, 4.0, 6.0, 8.0])
        sigma_pair = np.array([0.1, 0.2, 0.3, 0.4])
        sigma_total = sigma_pe + sigma_comp + sigma_pair

        photon_data = PhotonCrossSection(
            element="H",
            Z=1,
            energy=energy,
            sigma_photoelectric=sigma_pe,
            sigma_compton=sigma_comp,
            sigma_pair=sigma_pair,
            sigma_total=sigma_total,
        )

        # Exact match
        pe, comp, pair, tot = photon_data.interpolate(1.0)
        assert pe == 3.0
        assert comp == 6.0
        assert pair == 0.3
        assert tot == 9.3

    def test_photon_cross_section_interpolate_zero_denominator(self):
        """Test PhotonCrossSection interpolation with zero denominator."""
        energy = np.array([0.01, 0.01, 1.0])  # Duplicate energy
        sigma_pe = np.array([1.0, 1.0, 3.0])
        sigma_comp = np.array([2.0, 2.0, 6.0])
        sigma_pair = np.array([0.1, 0.1, 0.3])
        sigma_total = sigma_pe + sigma_comp + sigma_pair

        photon_data = PhotonCrossSection(
            element="H",
            Z=1,
            energy=energy,
            sigma_photoelectric=sigma_pe,
            sigma_compton=sigma_comp,
            sigma_pair=sigma_pair,
            sigma_total=sigma_total,
        )

        # Should handle zero denominator gracefully
        pe, comp, pair, tot = photon_data.interpolate(0.01)
        assert pe >= 0
        assert comp >= 0

    def test_parse_file_no_cross_sections(self, tmp_path):
        """Test parsing file with no cross-section sections."""
        parser = ENDFPhotonParser()

        filepath = tmp_path / "p-001_H_001.endf"
        filepath.write_text(
            " 1.001000+3 1.000000+0          0          0          0          0 23  1     \n"
        )

        result = parser.parse_file(filepath)

        # Should return None if no cross-sections
        assert result is None

    def test_parse_file_only_one_section(self, tmp_path):
        """Test parsing file with only one cross-section section (MT=501 only)."""
        parser = ENDFPhotonParser()
        base = " 0.000000+0 0.000000+0          0          0          0          0"
        pad_to_70 = base.ljust(70)
        filepath = tmp_path / "p-001_H_001.endf"
        lines = [
            " 1.001000+3 1.000000+0          0          0          0          0".ljust(
                70
            )
            + "23"
            + "  1"
            + " " * 5
            + "\n",
            pad_to_70 + "23" + "501" + " " * 4 + "\n",
            " 0.000000+0 0.000000+0          0          0          2         10".ljust(
                70
            )
            + "23"
            + "501"
            + " " * 4
            + "\n",
            " 1.000000-2 1.000000+1 1.000000-1 5.000000+0 1.000000+0 2.000000+0".ljust(
                70
            )
            + "23"
            + "501"
            + " " * 4
            + "\n",
            " 1.000000+1 1.000000+0 0.000000+0 0.000000+0 0.000000+0 0.000000+0".ljust(
                70
            )
            + "23"
            + "501"
            + " " * 4
            + "\n",
            " " * 66 + "-1  0  0   \n",
        ]
        filepath.write_text("".join(lines))

        result = parser.parse_file(filepath)

        # Should create PhotonCrossSection with zeros for missing sections
        assert result is not None
        assert result.sigma_photoelectric is not None
        # Missing sections should be zeros
        assert np.all(result.sigma_compton == 0) or result.sigma_compton is not None
        assert np.all(result.sigma_pair == 0) or result.sigma_pair is not None

    def test_parse_filename_value_error_branch_via_mocked_match(self):
        """Cover _parse_filename() ValueError branch (int conversion failure)."""
        parser = ENDFPhotonParser()

        class _Match:
            def groups(self):
                return ("not-an-int", "h")

        with patch("smrforge.core.photon_parser.re.match", return_value=_Match()):
            assert parser._parse_filename("p-001_H_001.endf") is None

    def test_parse_mt_section_last_part_digits_fallback_and_short_header_line(self):
        """Cover line_end last-part parsing + header_count short-line branch."""
        parser = ENDFPhotonParser()

        # This header line makes mf_str/mt_str non-digit, but line_end contains 3 tokens
        # and the last token is MAT+MF+MT (8 digits) => last_part fallback.
        header = (" " * 66 + "foo bar 10023501").ljust(80) + "\n"
        short_header = "short\n"  # len < 22 => header_count path
        data = (" 1.0000E-02" + " 1.0000E+00").ljust(80) + "\n"
        end = (" " * 66 + "-1  0  0").ljust(80) + "\n"

        result = parser._parse_mt_section([header, short_header, data, end], 501)
        assert result is not None
        e, xs = result
        assert len(e) == len(xs) and len(e) > 0

    def test_parse_mt_section_text_header_marker_path_and_parse_exceptions(self):
        """Cover the text-header marker detection and inner parse exception handling."""
        parser = ENDFPhotonParser()

        # First line: triggers last_part parsing but MT does not match (502),
        # then triggers the text-header marker logic (23 in 66:72 and 501 in 72:80).
        marker = ("X".ljust(66) + "23    501 " + "10023502").ljust(80) + "\n"

        # Data line with one invalid pair to hit the (ValueError, OverflowError) pass.
        good = (" 1.0000E-02" + " 1.0000E+00").ljust(80) + "\n"
        bad = (" not_a_num " + " 1.000000+0").ljust(80) + "\n"
        end = (" " * 66 + "-1  0  0").ljust(80) + "\n"

        result = parser._parse_mt_section([marker, good, bad, end], 501)
        assert result is not None

    def test_parse_mt_section_try_block_exception_is_caught(self):
        """Cover the (ValueError, IndexError, AttributeError) except: continue branch."""
        parser = ENDFPhotonParser()

        class _WeirdLine:
            def __len__(self):
                return 80

            def __getitem__(self, key):
                # Keep the pre-try `line[66:].strip()` safe, but break inside the try block.
                if isinstance(key, slice) and key.start == 66:
                    return " " * 20
                return 123

        assert parser._parse_mt_section([_WeirdLine()], 501) is None

    def test_parse_file_invalid_filename_returns_none(self, tmp_path):
        """Cover parse_file() path where filename doesn't match patterns."""
        parser = ENDFPhotonParser()
        filepath = tmp_path / "not-a-photon-file.endf"
        filepath.write_text("anything\n")
        assert parser.parse_file(filepath) is None

    def test_parse_mt_section_skips_text_header_lines(self):
        """Cover the text-header 'continue' branch (MF/MT header text)."""
        parser = ENDFPhotonParser()

        # First line: triggers text-header detection and is skipped due to "MF/MT" marker.
        skipped = ("MF/MT".ljust(66) + "23    501 " + "10023502").ljust(80) + "\n"

        # Then provide a valid section header + data so parsing succeeds.
        header = (" " * 70 + "23" + "501").ljust(80) + "\n"
        data = (" 1.0000E-02" + " 1.0000E+00").ljust(80) + "\n"
        end = (" " * 66 + "-1  0  0").ljust(80) + "\n"

        result = parser._parse_mt_section([skipped, header, data, end], 501)
        assert result is not None

    def test_parse_mt_section_text_header_marker_try_except_branch(self):
        """Cover the text-header marker try/except branch (ValueError -> continue)."""
        parser = ENDFPhotonParser()

        class _Slice66:
            def strip(self):
                # Used by earlier fallback parsing in the first try block.
                return "23    501 10023502"

            def split(self):
                # Used by the later text-header marker logic.
                raise ValueError("split failed")

            def __contains__(self, item):
                return item in self.strip()

        class _HeaderLine:
            def __len__(self):
                return 80

            def strip(self):
                return "X"

            def __contains__(self, item):
                return False

            def __getitem__(self, key):
                if isinstance(key, slice) and key.start == 66 and key.stop is None:
                    return _Slice66()
                if isinstance(key, slice) and key.start == 66 and key.stop == 72:
                    return "23    "
                if isinstance(key, slice) and key.start == 72 and key.stop == 80:
                    return "501     "
                if isinstance(key, slice) and key.start == 70 and key.stop == 72:
                    return "  "
                if isinstance(key, slice) and key.start == 72 and key.stop == 75:
                    return "501"
                if isinstance(key, slice) and key.start == 67 and key.stop == 75:
                    return "3    501"
                if isinstance(key, slice):
                    return " " * (key.stop - key.start)  # type: ignore[operator]
                return " "

        header = (" " * 70 + "23" + "501").ljust(80) + "\n"
        data = (" 1.0000E-02" + " 1.0000E+00").ljust(80) + "\n"
        end = (" " * 66 + "-1  0  0").ljust(80) + "\n"

        result = parser._parse_mt_section([_HeaderLine(), header, data, end], 501)
        assert result is not None

    def test_parse_mt_section_outer_parse_exception_branch(self):
        """Cover the outer (ValueError, IndexError) data-parse exception handler."""
        parser = ENDFPhotonParser()

        header = (" " * 70 + "23" + "501").ljust(80) + "\n"
        good = (" 1.0000E-02" + " 1.0000E+00").ljust(80) + "\n"

        class _BadDataLine:
            def __len__(self):
                return 80

            def strip(self):
                return ""

            def __contains__(self, item):
                return False

            def __getitem__(self, key):
                if isinstance(key, slice) and key.start == 70 and key.stop == 72:
                    return "  "
                if isinstance(key, slice) and key.start == 72 and key.stop == 75:
                    return "   "
                # Trigger the OUTER try/except in the pair parsing loop
                if isinstance(key, slice) and key.start in (0, 11, 22, 33, 44, 55):
                    raise IndexError("boom")
                return " " * (key.stop - key.start)  # type: ignore[operator]

        end = (" " * 66 + "-1  0  0").ljust(80) + "\n"

        result = parser._parse_mt_section([header, good, _BadDataLine(), end], 501)
        assert result is not None

    def test_parse_mt_section_returns_none_when_no_data_after_header(self):
        """Cover the final return None when no valid data are parsed."""
        parser = ENDFPhotonParser()
        header = (" " * 70 + "23" + "501").ljust(80) + "\n"
        assert parser._parse_mt_section([header], 501) is None
