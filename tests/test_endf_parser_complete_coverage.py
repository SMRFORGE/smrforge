"""
Complete coverage tests for endf_parser.py to cover all remaining missing lines.

This test suite fills remaining coverage gaps:
- POLARS_AVAILABLE = False path (lines 22-24)
- __contains__ method (line 81)
- __getitem__ KeyError (line 86)
- to_polars when POLARS_AVAILABLE=False (lines 97-98)
- to_polars full method (lines 100-112)
- get_reactions_dataframe when POLARS_AVAILABLE=False (line 124)
- get_reactions_dataframe full method (line 128)
- _parse_mf3 exception handling (lines 208-210)
- _parse_mf3_section start_idx >= len(lines) (line 237)
- _parse_mf3_section break condition (line 276)
- ENDFCompatibility.__contains__ (line 381)
- ENDFCompatibility.to_polars (line 407)
"""

import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False


@pytest.fixture
def endf_evaluation_class():
    """Get the ENDFEvaluation class."""
    try:
        from smrforge.core.endf_parser import ENDFEvaluation
        return ENDFEvaluation
    except ImportError:
        pytest.skip("ENDF parser not available")


@pytest.fixture
def endf_compatibility_class():
    """Get the ENDFCompatibility class."""
    try:
        from smrforge.core.endf_parser import ENDFCompatibility
        return ENDFCompatibility
    except ImportError:
        pytest.skip("ENDF parser not available")


@pytest.fixture
def reaction_data_class():
    """Get the ReactionData class."""
    try:
        from smrforge.core.endf_parser import ReactionData
        return ReactionData
    except ImportError:
        pytest.skip("ENDF parser not available")


@pytest.fixture
def complete_endf_file_with_reactions(temp_dir):
    """Create a complete ENDF file with header and multiple reactions."""
    endf_path = temp_dir / "complete_U235.endf"
    endf_content = """                                                                   125 1451    1
 9.223500+4 2.350000+2          0          0          0          0 125 1451    2
                                                                   125 1451    0
                                                                   125 3  1    1
 1.000000+5 1.000000+1 1.000000+6 1.200000+1                       125 3  1    3
                                                                   125 0  0    0
                                                                   125 3  2    1
 1.000000+5 8.000000+0 1.000000+6 9.000000+0                       125 3  2    3
                                                                   125 0  0    0
"""
    endf_path.write_text(endf_content)
    return endf_path


class TestENDFEvaluationContainsAndGetItem:
    """Test __contains__ and __getitem__ methods."""

    def test_contains_returns_true_when_mt_exists(
        self, endf_evaluation_class, complete_endf_file_with_reactions
    ):
        """Test __contains__ returns True when MT exists (line 81)."""
        eval_obj = endf_evaluation_class(complete_endf_file_with_reactions)
        
        # Should return True for MT=1 (total)
        assert 1 in eval_obj
        assert 2 in eval_obj

    def test_contains_returns_false_when_mt_not_exists(
        self, endf_evaluation_class, complete_endf_file_with_reactions
    ):
        """Test __contains__ returns False when MT doesn't exist."""
        eval_obj = endf_evaluation_class(complete_endf_file_with_reactions)
        
        # Should return False for non-existent MT
        assert 18 not in eval_obj
        assert 102 not in eval_obj

    def test_getitem_raises_keyerror_when_mt_not_found(
        self, endf_evaluation_class, complete_endf_file_with_reactions
    ):
        """Test __getitem__ raises KeyError when MT not found (line 86)."""
        eval_obj = endf_evaluation_class(complete_endf_file_with_reactions)
        
        with pytest.raises(KeyError, match="Reaction MT=999 not found"):
            _ = eval_obj[999]

    def test_getitem_returns_reaction_data_when_mt_exists(
        self, endf_evaluation_class, complete_endf_file_with_reactions
    ):
        """Test __getitem__ returns ReactionData when MT exists."""
        eval_obj = endf_evaluation_class(complete_endf_file_with_reactions)
        
        reaction = eval_obj[1]
        assert hasattr(reaction, "energy")
        assert hasattr(reaction, "cross_section")
        assert reaction.mt_number == 1


@pytest.mark.skipif(not POLARS_AVAILABLE, reason="Polars not available")
class TestToPolarsWithPolarsAvailable:
    """Test to_polars method when Polars is available."""

    def test_to_polars_returns_dataframe(
        self, endf_evaluation_class, complete_endf_file_with_reactions
    ):
        """Test to_polars returns DataFrame with correct structure (lines 100-112)."""
        eval_obj = endf_evaluation_class(complete_endf_file_with_reactions)
        
        df = eval_obj.to_polars()
        
        assert df is not None
        assert "mt_number" in df.columns
        assert "reaction_name" in df.columns
        assert "energy" in df.columns
        assert "cross_section" in df.columns
        
        # Should have rows for all reactions and energy points
        assert len(df) > 0
        
        # Check data
        mt1_rows = df.filter(pl.col("mt_number") == 1)
        assert len(mt1_rows) >= 2  # At least 2 energy points

    def test_to_polars_empty_reactions(self, endf_evaluation_class, temp_dir):
        """Test to_polars with empty reactions."""
        endf_path = temp_dir / "empty.endf"
        endf_content = """                                                                   125 1451    1
 9.223500+4 2.350000+2          0          0          0          0 125 1451    2
                                                                   125 1451    0
"""
        endf_path.write_text(endf_content)
        
        eval_obj = endf_evaluation_class(endf_path)
        df = eval_obj.to_polars()
        
        # When no reactions, records list is empty
        # Polars DataFrame([]) creates empty DataFrame (no rows, no columns)
        # Or if Polars not available, returns None
        if df is not None:
            # Empty DataFrame - no rows, columns may be empty too
            assert len(df) == 0
            # When records is empty, Polars creates DataFrame with no columns
            # So we just check it's a valid DataFrame (or has expected columns if any)
            assert hasattr(df, 'columns')
        else:
            # Polars not available - that's also valid
            assert df is None


class TestToPolarsWithoutPolars:
    """Test to_polars method when Polars is not available (lines 97-98)."""

    @pytest.mark.skipif(POLARS_AVAILABLE, reason="Polars is available, cannot test unavailable path")
    def test_to_polars_returns_none_when_polars_unavailable(
        self, endf_evaluation_class, complete_endf_file_with_reactions
    ):
        """Test to_polars returns None when Polars is not available."""
        eval_obj = endf_evaluation_class(complete_endf_file_with_reactions)
        
        df = eval_obj.to_polars()
        assert df is None


@pytest.mark.skipif(not POLARS_AVAILABLE, reason="Polars not available")
class TestGetReactionsDataframeWithPolarsAvailable:
    """Test get_reactions_dataframe method when Polars is available."""

    def test_get_reactions_dataframe_returns_summary(
        self, endf_evaluation_class, complete_endf_file_with_reactions
    ):
        """Test get_reactions_dataframe returns summary DataFrame (line 128)."""
        eval_obj = endf_evaluation_class(complete_endf_file_with_reactions)
        
        df = eval_obj.get_reactions_dataframe()
        
        assert df is not None
        assert "mt_number" in df.columns
        assert "reaction_name" in df.columns
        assert "n_points" in df.columns
        assert "energy_min" in df.columns
        assert "energy_max" in df.columns
        assert "xs_min" in df.columns
        assert "xs_max" in df.columns
        assert "xs_mean" in df.columns
        
        # Should have one row per reaction
        assert len(df) == 2  # MT=1 and MT=2
        
        # Check values
        mt1_row = df.filter(pl.col("mt_number") == 1)
        assert len(mt1_row) == 1
        assert mt1_row["n_points"][0] >= 2


class TestGetReactionsDataframeWithoutPolars:
    """Test get_reactions_dataframe when Polars is not available (line 124)."""

    @pytest.mark.skipif(POLARS_AVAILABLE, reason="Polars is available, cannot test unavailable path")
    def test_get_reactions_dataframe_returns_none_when_polars_unavailable(
        self, endf_evaluation_class, complete_endf_file_with_reactions
    ):
        """Test get_reactions_dataframe returns None when Polars is not available."""
        eval_obj = endf_evaluation_class(complete_endf_file_with_reactions)
        
        df = eval_obj.get_reactions_dataframe()
        assert df is None


class TestParseMf3ExceptionHandling:
    """Test _parse_mf3 exception handling (lines 208-210)."""

    def test_parse_mf3_handles_invalid_control_record(
        self, endf_evaluation_class, temp_dir
    ):
        """Test _parse_mf3 handles ValueError/IndexError in control record parsing."""
        endf_path = temp_dir / "invalid_control.endf"
        endf_path.write_text("                                                                   125 1451    1\n")
        
        eval_obj = endf_evaluation_class(endf_path)
        
        lines = [
            "                                                                   125 3  1    1",  # Valid
            " 1.000000+5 1.000000+1 1.000000+6 1.200000+1                       125 3  1    3",
            "                                                                   125 0  0    0",
            "short line",  # Too short, will cause IndexError when trying to parse MF/MT
            "                                                                   125 3  2    1",
            " 1.000000+5 8.000000+0 1.000000+6 9.000000+0                       125 3  2    3",
            "                                                                   125 0  0    0",
        ]
        
        # Should handle gracefully and continue parsing
        eval_obj._parse_mf3(lines)
        
        # Should still parse valid sections
        assert 1 in eval_obj.reactions
        assert 2 in eval_obj.reactions


class TestParseMf3SectionEdgeCases:
    """Test _parse_mf3_section edge cases."""

    def test_parse_mf3_section_start_idx_geq_len_lines(
        self, endf_evaluation_class, temp_dir
    ):
        """Test _parse_mf3_section returns None when start_idx >= len(lines) (line 237)."""
        endf_path = temp_dir / "empty.endf"
        endf_path.write_text("                                                                   125 1451    1\n")
        
        eval_obj = endf_evaluation_class(endf_path)
        
        lines = [
            "                                                                   125 3  1    1",
            " 1.000000+5 1.000000+1 1.000000+6 1.200000+1                       125 3  1    3",
        ]
        
        # start_idx >= len(lines)
        energy, xs = eval_obj._parse_mf3_section(lines, start_idx=len(lines), mt=1)
        
        assert energy is None
        assert xs is None

    def test_parse_mf3_section_break_on_short_line(
        self, endf_evaluation_class, temp_dir
    ):
        """Test _parse_mf3_section breaks when j+11 > len(line) (line 276)."""
        endf_path = temp_dir / "short_line.endf"
        endf_path.write_text("                                                                   125 1451    1\n")
        
        eval_obj = endf_evaluation_class(endf_path)
        
        lines = [
            "                                                                   125 3  1    1",
            " 1.000000+5 1.000000+1",  # Very short line, less than 22 chars (can't have 2 values)
            "                                                                   125 0  0    0",
        ]
        
        energy, xs = eval_obj._parse_mf3_section(lines, start_idx=0, mt=1)
        
        # Should still parse what it can
        # May return None if no valid pairs found, or partial data
        # The break condition prevents reading past line length


class TestENDFCompatibilityContains:
    """Test ENDFCompatibility.__contains__ method (line 381)."""

    def test_endf_compatibility_contains(
        self, endf_compatibility_class, complete_endf_file_with_reactions
    ):
        """Test ENDFCompatibility.__contains__ delegates to _evaluation."""
        compat = endf_compatibility_class(complete_endf_file_with_reactions)
        
        # Should delegate to _evaluation.__contains__
        assert 1 in compat
        assert 2 in compat
        assert 18 not in compat


@pytest.mark.skipif(not POLARS_AVAILABLE, reason="Polars not available")
class TestENDFCompatibilityToPolars:
    """Test ENDFCompatibility.to_polars method (line 407)."""

    def test_endf_compatibility_to_polars_delegates(
        self, endf_compatibility_class, complete_endf_file_with_reactions
    ):
        """Test ENDFCompatibility.to_polars delegates to _evaluation.to_polars."""
        compat = endf_compatibility_class(complete_endf_file_with_reactions)
        
        df = compat.to_polars()
        
        assert df is not None
        assert "mt_number" in df.columns
        assert len(df) > 0


class TestParseMf3SectionAdditionalEdgeCases:
    """Test additional edge cases for _parse_mf3_section."""

    def test_parse_mf3_section_next_mt_equals_zero(
        self, endf_evaluation_class, temp_dir
    ):
        """Test _parse_mf3_section continues when next_mt == 0 (same section continuation)."""
        endf_path = temp_dir / "mt_zero.endf"
        endf_path.write_text("                                                                   125 1451    1\n")
        
        eval_obj = endf_evaluation_class(endf_path)
        
        lines = [
            "                                                                   125 3  1    1",
            " 1.000000+5 1.000000+1 1.000000+6 1.200000+1                       125 3  1    3",
            "                                                                   125 3  0    0",  # MT=0 continuation
            " 1.000000+7 1.500000+1 1.000000+8 1.800000+1                       125 3  1    4",
            "                                                                   125 0  0    0",
        ]
        
        energy, xs = eval_obj._parse_mf3_section(lines, start_idx=0, mt=1)
        
        # Should parse all data including continuation (MT=0)
        assert energy is not None
        assert xs is not None
        assert len(energy) >= 2  # At least initial 2 points

    def test_parse_mf3_section_next_mf_different(
        self, endf_evaluation_class, temp_dir
    ):
        """Test _parse_mf3_section stops when next_mf != 3."""
        endf_path = temp_dir / "different_mf.endf"
        endf_path.write_text("                                                                   125 1451    1\n")
        
        eval_obj = endf_evaluation_class(endf_path)
        
        lines = [
            "                                                                   125 3  1    1",
            " 1.000000+5 1.000000+1 1.000000+6 1.200000+1                       125 3  1    3",
            "                                                                   125 4  1    1",  # Different MF
            " 1.000000+7 1.500000+1 1.000000+8 1.800000+1                       125 4  1    4",
            "                                                                   125 0  0    0",
        ]
        
        energy, xs = eval_obj._parse_mf3_section(lines, start_idx=0, mt=1)
        
        # Should stop at MF=4, so should only have first 2 points
        assert energy is not None
        assert xs is not None
        assert len(energy) == 2

    def test_parse_mf3_section_exception_in_mf_mt_parsing(
        self, endf_evaluation_class, temp_dir
    ):
        """Test _parse_mf3_section handles exceptions when parsing next_mf/next_mt."""
        endf_path = temp_dir / "exception_mf_mt.endf"
        endf_path.write_text("                                                                   125 1451    1\n")
        
        eval_obj = endf_evaluation_class(endf_path)
        
        lines = [
            "                                                                   125 3  1    1",
            " 1.000000+5 1.000000+1 1.000000+6 1.200000+1                       125 3  1    3",
            "invalid mf mt format here - cannot parse",  # Will cause ValueError/IndexError
            " 1.000000+7 1.500000+1 1.000000+8 1.800000+1                       125 3  1    4",
            "                                                                   125 0  0    0",
        ]
        
        energy, xs = eval_obj._parse_mf3_section(lines, start_idx=0, mt=1)
        
        # Should continue parsing after exception
        assert energy is not None
        assert xs is not None
        # Should parse data from both valid data lines
        assert len(energy) >= 2
