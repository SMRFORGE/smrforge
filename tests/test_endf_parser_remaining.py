"""
Tests for remaining uncovered methods in endf_parser.py.

This test suite covers:
- _mt_to_reaction_name static method (all MT number mappings and unknown MTs)
- ENDFEvaluation.__getitem__ KeyError path
"""

from pathlib import Path

import pytest


@pytest.fixture
def endf_evaluation_class():
    """Get the ENDFEvaluation class."""
    try:
        from smrforge.core.endf_parser import ENDFEvaluation

        return ENDFEvaluation
    except ImportError:
        pytest.skip("ENDF parser not available")


@pytest.fixture
def empty_endf_file(temp_dir):
    """Create an empty ENDF file for testing."""
    endf_path = temp_dir / "empty_test.endf"

    # Minimal ENDF file structure (just header, no reactions)
    endf_content = """ 1.001000+3 9.991673-1          0          0          0          0 125 1451    1
 9.223500+4 2.350000+2          0          0          0          0 125 1451    2
                                                                   125 1451    0
                                                                   125 0  0    0
"""
    endf_path.write_text(endf_content)
    return endf_path


class TestMtToReactionName:
    """Test _mt_to_reaction_name static method."""

    def test_mt_to_reaction_name_total(self, endf_evaluation_class):
        """Test MT=1 maps to 'total'."""
        result = endf_evaluation_class._mt_to_reaction_name(1)
        assert result == "total"

    def test_mt_to_reaction_name_elastic(self, endf_evaluation_class):
        """Test MT=2 maps to 'elastic'."""
        result = endf_evaluation_class._mt_to_reaction_name(2)
        assert result == "elastic"

    def test_mt_to_reaction_name_non_elastic(self, endf_evaluation_class):
        """Test MT=3 maps to 'non-elastic'."""
        result = endf_evaluation_class._mt_to_reaction_name(3)
        assert result == "non-elastic"

    def test_mt_to_reaction_name_inelastic(self, endf_evaluation_class):
        """Test MT=4 maps to 'inelastic'."""
        result = endf_evaluation_class._mt_to_reaction_name(4)
        assert result == "inelastic"

    def test_mt_to_reaction_name_n2n(self, endf_evaluation_class):
        """Test MT=16 maps to 'n,2n'."""
        result = endf_evaluation_class._mt_to_reaction_name(16)
        assert result == "n,2n"

    def test_mt_to_reaction_name_n3n(self, endf_evaluation_class):
        """Test MT=17 maps to 'n,3n'."""
        result = endf_evaluation_class._mt_to_reaction_name(17)
        assert result == "n,3n"

    def test_mt_to_reaction_name_fission(self, endf_evaluation_class):
        """Test MT=18 maps to 'fission'."""
        result = endf_evaluation_class._mt_to_reaction_name(18)
        assert result == "fission"

    def test_mt_to_reaction_name_fission_first_chance(self, endf_evaluation_class):
        """Test MT=19 maps to 'fission (first chance)'."""
        result = endf_evaluation_class._mt_to_reaction_name(19)
        assert result == "fission (first chance)"

    def test_mt_to_reaction_name_fission_second_chance(self, endf_evaluation_class):
        """Test MT=20 maps to 'fission (second chance)'."""
        result = endf_evaluation_class._mt_to_reaction_name(20)
        assert result == "fission (second chance)"

    def test_mt_to_reaction_name_fission_third_chance(self, endf_evaluation_class):
        """Test MT=21 maps to 'fission (third chance)'."""
        result = endf_evaluation_class._mt_to_reaction_name(21)
        assert result == "fission (third chance)"

    def test_mt_to_reaction_name_nn_alpha(self, endf_evaluation_class):
        """Test MT=22 maps to 'n,n'alpha'."""
        result = endf_evaluation_class._mt_to_reaction_name(22)
        assert result == "n,n'alpha"

    def test_mt_to_reaction_name_nn_p(self, endf_evaluation_class):
        """Test MT=28 maps to 'n,n'p'."""
        result = endf_evaluation_class._mt_to_reaction_name(28)
        assert result == "n,n'p"

    def test_mt_to_reaction_name_capture(self, endf_evaluation_class):
        """Test MT=102 maps to 'capture'."""
        result = endf_evaluation_class._mt_to_reaction_name(102)
        assert result == "capture"

    def test_mt_to_reaction_name_ngamma(self, endf_evaluation_class):
        """Test MT=103 maps to 'n,gamma'."""
        result = endf_evaluation_class._mt_to_reaction_name(103)
        assert result == "n,gamma"

    def test_mt_to_reaction_name_nalpha(self, endf_evaluation_class):
        """Test MT=107 maps to 'n,alpha'."""
        result = endf_evaluation_class._mt_to_reaction_name(107)
        assert result == "n,alpha"

    def test_mt_to_reaction_name_n2alpha(self, endf_evaluation_class):
        """Test MT=111 maps to 'n,2alpha'."""
        result = endf_evaluation_class._mt_to_reaction_name(111)
        assert result == "n,2alpha"

    def test_mt_to_reaction_name_n3alpha(self, endf_evaluation_class):
        """Test MT=112 maps to 'n,3alpha'."""
        result = endf_evaluation_class._mt_to_reaction_name(112)
        assert result == "n,3alpha"

    def test_mt_to_reaction_name_unknown_returns_mt_format(self, endf_evaluation_class):
        """Test unknown MT numbers return 'MT{number}' format."""
        # Test various unknown MT numbers
        assert endf_evaluation_class._mt_to_reaction_name(0) == "MT0"
        assert endf_evaluation_class._mt_to_reaction_name(5) == "MT5"
        assert endf_evaluation_class._mt_to_reaction_name(10) == "MT10"
        assert endf_evaluation_class._mt_to_reaction_name(50) == "MT50"
        assert endf_evaluation_class._mt_to_reaction_name(200) == "MT200"
        assert endf_evaluation_class._mt_to_reaction_name(999) == "MT999"

    def test_mt_to_reaction_name_negative_number(self, endf_evaluation_class):
        """Test negative MT numbers return 'MT{number}' format."""
        result = endf_evaluation_class._mt_to_reaction_name(-1)
        assert result == "MT-1"

    def test_mt_to_reaction_name_large_number(self, endf_evaluation_class):
        """Test large MT numbers return 'MT{number}' format."""
        result = endf_evaluation_class._mt_to_reaction_name(9999)
        assert result == "MT9999"

    def test_mt_to_reaction_name_all_known_mappings(self, endf_evaluation_class):
        """Test all known MT number mappings in one comprehensive test."""
        known_mappings = {
            1: "total",
            2: "elastic",
            3: "non-elastic",
            4: "inelastic",
            16: "n,2n",
            17: "n,3n",
            18: "fission",
            19: "fission (first chance)",
            20: "fission (second chance)",
            21: "fission (third chance)",
            22: "n,n'alpha",
            28: "n,n'p",
            102: "capture",
            103: "n,gamma",
            107: "n,alpha",
            111: "n,2alpha",
            112: "n,3alpha",
        }

        for mt, expected_name in known_mappings.items():
            result = endf_evaluation_class._mt_to_reaction_name(mt)
            assert (
                result == expected_name
            ), f"MT={mt} should map to '{expected_name}', got '{result}'"

    def test_mt_to_reaction_name_is_static_method(self, endf_evaluation_class):
        """Test that _mt_to_reaction_name can be called without an instance."""
        # Should be callable on the class itself (static method)
        result = endf_evaluation_class._mt_to_reaction_name(1)
        assert result == "total"


class TestENDFEvaluationGetItemKeyError:
    """Test ENDFEvaluation.__getitem__ KeyError path."""

    def test_getitem_raises_keyerror_for_missing_reaction(
        self, endf_evaluation_class, empty_endf_file
    ):
        """Test __getitem__ raises KeyError when reaction MT number is not found."""
        evaluation = endf_evaluation_class(empty_endf_file)

        # Should raise KeyError for nonexistent reaction
        with pytest.raises(KeyError) as exc_info:
            _ = evaluation[1]  # MT=1 (total) - should not exist in empty file

        # Verify error message contains useful information
        error_msg = str(exc_info.value)
        assert "MT=1" in error_msg or "1" in error_msg
        assert "not found" in error_msg.lower() or "not found" in error_msg

    def test_getitem_keyerror_for_multiple_missing_reactions(
        self, endf_evaluation_class, empty_endf_file
    ):
        """Test __getitem__ raises KeyError for various missing reactions."""
        evaluation = endf_evaluation_class(empty_endf_file)

        # Test various missing MT numbers
        for mt in [1, 2, 18, 102, 999]:
            with pytest.raises(KeyError) as exc_info:
                _ = evaluation[mt]

            # Verify error message mentions the MT number
            error_msg = str(exc_info.value)
            assert str(mt) in error_msg

    def test_getitem_keyerror_message_includes_filename(
        self, endf_evaluation_class, empty_endf_file
    ):
        """Test KeyError message includes filename for debugging."""
        evaluation = endf_evaluation_class(empty_endf_file)

        with pytest.raises(KeyError) as exc_info:
            _ = evaluation[1]

        error_msg = str(exc_info.value)
        # Should mention the filename (at least part of it)
        assert (
            "endf" in error_msg.lower()
            or str(empty_endf_file.name) in error_msg
            or str(empty_endf_file) in error_msg
        )

    def test_getitem_keyerror_format(self, endf_evaluation_class, empty_endf_file):
        """Test KeyError has expected format."""
        evaluation = endf_evaluation_class(empty_endf_file)

        with pytest.raises(KeyError) as exc_info:
            _ = evaluation[18]  # MT=18 (fission)

        # KeyError should be raised (not ValueError, AttributeError, etc.)
        assert isinstance(exc_info.value, KeyError)

        # Should have a message
        error_msg = str(exc_info.value)
        assert len(error_msg) > 0

    def test_getitem_keyerror_vs_contains(self, endf_evaluation_class, empty_endf_file):
        """Test that __getitem__ raises KeyError only for reactions not in __contains__."""
        evaluation = endf_evaluation_class(empty_endf_file)

        # Verify reaction is not in evaluation
        assert 1 not in evaluation

        # Getting it should raise KeyError
        with pytest.raises(KeyError):
            _ = evaluation[1]
