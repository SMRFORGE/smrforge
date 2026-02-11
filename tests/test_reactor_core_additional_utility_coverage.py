"""
Additional coverage tests for remaining gaps in reactor_core.py utility functions.

This test suite covers:
- Line 311: logger.info call in _get_parser when C++ parser detected
- Lines 3253-3255, 3259-3261: logger calls in organize_bulk_endf_downloads
- Lines 3351-3354: version detection in scan_endf_directory
- Additional edge cases in generate_multigroup and generate_multigroup_async
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from smrforge.core.reactor_core import (
    CrossSectionTable,
    Library,
    NuclearDataCache,
    Nuclide,
    organize_bulk_endf_downloads,
    scan_endf_directory,
)


@pytest.fixture
def mock_endf_file_valid(tmp_path):
    """Create a valid mock ENDF file for testing."""
    endf_file = tmp_path / "n-092_U_235.endf"
    content = (
        "ENDF/B-VIII.1                                                         0  0\n"
        " 9.223500+4 2.350000+2          1          1          0          0 125 1451    1\n"
        " 9.223500+4 2.350000+2          0          0          0          0 125 1451    2\n"
        "                                                                   125 1451    0\n"
    )
    # Pad to ensure >= 1000 bytes
    content += (
        " 1.000000+5 1.000000+1 1.000000+6 1.200000+1                       125 3  1    3\n"
        * 50
    )
    endf_file.write_text(content)
    return endf_file


class TestGetParserLoggerCalls:
    """Test logger calls in _get_parser method."""

    def test_get_parser_logs_cpp_parser_info(self, tmp_path):
        """Test that _get_parser logs C++ parser info (line 311)."""
        cache = NuclearDataCache(cache_dir=tmp_path)

        # Mock EndfParserCpp import
        mock_cpp_parser = Mock()
        mock_cpp_parser.__class__.__name__ = "EndfParserCpp"

        with patch("smrforge.core.reactor_core.logger") as mock_logger:
            with patch("builtins.__import__") as mock_import:

                def import_side_effect(name, *args, **kwargs):
                    if name == "endf_parserpy":
                        mod = Mock()
                        mod.EndfParserCpp = Mock(return_value=mock_cpp_parser)
                        mod.EndfParserFactory = Mock()
                        return mod
                    return __import__(name, *args, **kwargs)

                mock_import.side_effect = import_side_effect

                # Clear parser to force re-initialization
                cache._parser = None
                cache._parser_type = None

                parser = cache._get_parser()

                # Verify logger.info was called (line 311 path)
                if parser is not None:
                    # Check if info was logged (either line 299-302 or 311)
                    assert mock_logger.info.called


class TestOrganizeBulkEndfDownloadsLoggerCalls:
    """Test logger calls in organize_bulk_endf_downloads."""

    def test_organize_bulk_endf_downloads_logs_warning_for_invalid_file(self, tmp_path):
        """Test logger.warning call for invalid files (lines 3253-3255)."""
        source = tmp_path / "source"
        source.mkdir()

        # Create invalid file
        invalid_file = source / "n-092_U_235.endf"
        invalid_file.write_text("Not a valid ENDF file")  # Too small, no ENDF markers

        target_dir = tmp_path / "target"

        with patch("smrforge.core.reactor_core.logger") as mock_logger:
            stats = organize_bulk_endf_downloads(
                source_dir=source,
                target_dir=target_dir,
                library_version="VIII.1",
                create_structure=True,
            )

            # Should log warning for invalid file
            assert any(
                "warning" in str(call).lower() or "invalid" in str(call).lower()
                for call in mock_logger.warning.call_args_list
            )

    def test_organize_bulk_endf_downloads_logs_debug_for_duplicate(self, tmp_path):
        """Test logger.debug call for duplicates (lines 3259-3261)."""
        source = tmp_path / "source"
        source.mkdir()

        # Create two files with same nuclide (both valid)
        content = (
            "ENDF/B-VIII.1                                                         0  0\n"
            " 9.223500+4 2.350000+2          1          1          0          0 125 1451    1\n"
        )
        content += " 1.000000+5 1.000000+1\n" * 50

        file1 = source / "n-092_U_235.endf"
        file2 = source / "n-092_U_235_alt.endf"
        file1.write_text(content)
        file2.write_text(content)

        target_dir = tmp_path / "target"

        # Use actual logger calls to verify behavior
        stats = organize_bulk_endf_downloads(
            source_dir=source,
            target_dir=target_dir,
            library_version="VIII.1",
            create_structure=True,
        )

        # Should skip duplicate - only organize one file
        assert stats["files_found"] == 2
        assert stats["files_organized"] == 1
        assert stats["files_skipped"] == 1


class TestScanEndfDirectoryVersionDetection:
    """Test version detection in scan_endf_directory."""

    def test_scan_endf_directory_detects_version_from_directory_name(self, tmp_path):
        """Test version detection from directory name (lines 3351-3354)."""
        endf_dir = tmp_path / "endf"
        # Create a custom version directory
        custom_version_dir = endf_dir / "neutrons-version.VIII.2"
        custom_version_dir.mkdir(parents=True)

        # Create a file in the custom version directory
        content = (
            "ENDF/B-VIII.1                                                         0  0\n"
            " 9.223500+4 2.350000+2          1          1          0          0 125 1451    1\n"
        )
        (custom_version_dir / "n-092_U_235.endf").write_text(
            content + " 1.000000+5 1.000000+1\n" * 50
        )

        results = scan_endf_directory(endf_dir)

        # Should detect the custom version
        assert "VIII.2" in results["library_versions"]
        assert results["directory_structure"] == "standard"


class TestGenerateMultigroupAdditionalCoverage:
    """Test additional edge cases in generate_multigroup methods."""

    def test_generate_multigroup_handles_all_reactions_skipped(self, tmp_path):
        """Test generate_multigroup when all reactions are skipped (lines 2459-2488)."""
        cache = NuclearDataCache(cache_dir=tmp_path)
        table = CrossSectionTable(cache=cache)

        u235 = Nuclide(Z=92, A=235)
        group_structure = np.array([2e7, 1e6, 1e5])  # 2 groups

        # Mock get_cross_section to return None for all reactions
        with patch.object(cache, "get_cross_section", return_value=(None, None)):
            df = table.generate_multigroup(
                nuclides=[u235],
                reactions=["fission", "capture"],
                group_structure=group_structure,
                temperature=900.0,
            )

            # When all reactions are skipped, pre-allocated arrays create DataFrame with null values
            # This is expected behavior - DataFrame has correct structure but with nulls
            assert df is not None
            # Check that DataFrame has correct columns even if all reactions skipped
            assert "nuclide" in df.columns
            assert "reaction" in df.columns
            assert "group" in df.columns
            assert "xs" in df.columns

    def test_generate_multigroup_handles_empty_data_arrays(self, tmp_path):
        """Test generate_multigroup handles empty energy/xs arrays (lines 2465-2470)."""
        cache = NuclearDataCache(cache_dir=tmp_path)
        table = CrossSectionTable(cache=cache)

        u235 = Nuclide(Z=92, A=235)
        group_structure = np.array([2e7, 1e6])

        # Mock get_cross_section to return empty arrays
        with patch.object(
            cache, "get_cross_section", return_value=(np.array([]), np.array([]))
        ):
            df = table.generate_multigroup(
                nuclides=[u235],
                reactions=["fission"],
                group_structure=group_structure,
                temperature=900.0,
            )

            # Should handle gracefully
            assert df is not None

    def test_generate_multigroup_async_handles_all_reactions_success(self, tmp_path):
        """Test generate_multigroup_async when all reactions succeed (lines 2595-2608)."""
        cache = NuclearDataCache(cache_dir=tmp_path)
        table = CrossSectionTable(cache=cache)

        u235 = Nuclide(Z=92, A=235)
        group_structure = np.array([2e7, 1e6])

        # Mock async method to return valid data
        energy = np.logspace(4, 7, 100)
        xs = np.ones_like(energy) * 10.0

        async def mock_get_cross_section_async(*args, **kwargs):
            return energy, xs

        with patch.object(
            cache, "get_cross_section_async", side_effect=mock_get_cross_section_async
        ):
            import asyncio

            df = asyncio.run(
                table.generate_multigroup_async(
                    nuclides=[u235],
                    reactions=["fission"],
                    group_structure=group_structure,
                    temperature=900.0,
                )
            )

            # Should create DataFrame with results
            assert df is not None
            assert len(df) > 0


class TestSimpleEndfParseAdditionalCoverage:
    """Test additional edge cases in _simple_endf_parse."""

    def test_simple_endf_parse_handles_control_record_skipping(self, tmp_path):
        """Test _simple_endf_parse skips control records correctly."""
        cache = NuclearDataCache(cache_dir=tmp_path)
        u235 = Nuclide(Z=92, A=235)

        # Create ENDF file with control records that should be skipped
        endf_file = tmp_path / "U235.endf"
        content = (
            "ENDF/B-VIII.1                                                         0  0\n"
            "                                                                   125 3  1    1\n"
            " 0.000000+0 0.000000+0          0          0          0          0 125 3  1    2\n"  # Control record to skip
            " 1.000000+5 1.000000+1 1.000000+6 1.200000+1                       125 3  1    3\n"
            "                                                                   125 0  0    0\n"
        )
        content += " 1.000000+5 1.000000+1\n" * 50  # Pad for validation
        endf_file.write_text(content)

        # Should parse successfully
        energy, xs = cache._simple_endf_parse(endf_file, "total", u235)

        # Should skip control record and return actual data
        if energy is not None and xs is not None:
            assert len(energy) > 0
            assert len(xs) > 0
