"""Comprehensive tests for _reaction_to_mt static method."""

import pytest

from smrforge.core.reactor_core import NuclearDataCache


class TestReactionToMt:
    """Test _reaction_to_mt static method comprehensively."""

    def test_reaction_to_mt_total(self):
        """Test _reaction_to_mt with 'total' reaction."""
        assert NuclearDataCache._reaction_to_mt("total") == 1
        assert NuclearDataCache._reaction_to_mt("TOTAL") == 1
        assert NuclearDataCache._reaction_to_mt("Total") == 1

    def test_reaction_to_mt_elastic(self):
        """Test _reaction_to_mt with 'elastic' reaction."""
        assert NuclearDataCache._reaction_to_mt("elastic") == 2
        assert NuclearDataCache._reaction_to_mt("ELASTIC") == 2
        assert NuclearDataCache._reaction_to_mt("Elastic") == 2

    def test_reaction_to_mt_fission(self):
        """Test _reaction_to_mt with 'fission' reaction."""
        assert NuclearDataCache._reaction_to_mt("fission") == 18
        assert NuclearDataCache._reaction_to_mt("FISSION") == 18
        assert NuclearDataCache._reaction_to_mt("Fission") == 18

    def test_reaction_to_mt_capture(self):
        """Test _reaction_to_mt with 'capture' reaction."""
        assert NuclearDataCache._reaction_to_mt("capture") == 102
        assert NuclearDataCache._reaction_to_mt("CAPTURE") == 102
        assert NuclearDataCache._reaction_to_mt("Capture") == 102

    def test_reaction_to_mt_n_gamma(self):
        """Test _reaction_to_mt with 'n,gamma' reaction (capture)."""
        assert NuclearDataCache._reaction_to_mt("n,gamma") == 102
        assert NuclearDataCache._reaction_to_mt("N,GAMMA") == 102
        assert NuclearDataCache._reaction_to_mt("N,Gamma") == 102
        assert NuclearDataCache._reaction_to_mt("n,GAMMA") == 102

    def test_reaction_to_mt_n_2n(self):
        """Test _reaction_to_mt with 'n,2n' reaction."""
        assert NuclearDataCache._reaction_to_mt("n,2n") == 16
        assert NuclearDataCache._reaction_to_mt("N,2N") == 16
        assert NuclearDataCache._reaction_to_mt("N,2n") == 16

    def test_reaction_to_mt_n_alpha(self):
        """Test _reaction_to_mt with 'n,alpha' reaction."""
        assert NuclearDataCache._reaction_to_mt("n,alpha") == 107
        assert NuclearDataCache._reaction_to_mt("N,ALPHA") == 107
        assert NuclearDataCache._reaction_to_mt("N,Alpha") == 107

    def test_reaction_to_mt_unknown_reaction_defaults_to_total(self):
        """Test _reaction_to_mt with unknown reaction defaults to MT=1 (total)."""
        assert NuclearDataCache._reaction_to_mt("unknown_reaction") == 1
        assert NuclearDataCache._reaction_to_mt("not_a_reaction") == 1
        assert NuclearDataCache._reaction_to_mt("") == 1
        assert NuclearDataCache._reaction_to_mt("invalid") == 1

    def test_reaction_to_mt_case_insensitive(self):
        """Test that _reaction_to_mt is case-insensitive for all reactions."""
        reactions = {
            "total": 1,
            "elastic": 2,
            "fission": 18,
            "capture": 102,
            "n,gamma": 102,
            "n,2n": 16,
            "n,alpha": 107,
        }

        for reaction, expected_mt in reactions.items():
            # Test lowercase
            assert NuclearDataCache._reaction_to_mt(reaction.lower()) == expected_mt
            # Test uppercase
            assert NuclearDataCache._reaction_to_mt(reaction.upper()) == expected_mt
            # Test mixed case
            if len(reaction) > 1:
                mixed_case = reaction[0].upper() + reaction[1:].lower()
                assert NuclearDataCache._reaction_to_mt(mixed_case) == expected_mt

    def test_reaction_to_mt_with_whitespace(self):
        """Test _reaction_to_mt handles whitespace (should not trim, but .lower() handles it)."""
        # Note: The method uses .lower() but doesn't strip, so whitespace will still be in the key
        # This means "total " won't match "total", so it should default to 1
        assert (
            NuclearDataCache._reaction_to_mt("total ") == 1
        )  # Whitespace causes mismatch
        assert NuclearDataCache._reaction_to_mt(" total") == 1
        assert NuclearDataCache._reaction_to_mt("total\t") == 1

    def test_reaction_to_mt_all_supported_reactions(self):
        """Test _reaction_to_mt with all supported reactions in one test."""
        reaction_mt_map = {
            "total": 1,
            "elastic": 2,
            "fission": 18,
            "capture": 102,
            "n,gamma": 102,  # Alternative name for capture
            "n,2n": 16,
            "n,alpha": 107,
        }

        for reaction, expected_mt in reaction_mt_map.items():
            result = NuclearDataCache._reaction_to_mt(reaction)
            assert (
                result == expected_mt
            ), f"Reaction '{reaction}' should map to MT={expected_mt}, got MT={result}"

    def test_reaction_to_mt_empty_string(self):
        """Test _reaction_to_mt with empty string defaults to MT=1."""
        assert NuclearDataCache._reaction_to_mt("") == 1

    def test_reaction_to_mt_numeric_string(self):
        """Test _reaction_to_mt with numeric string defaults to MT=1."""
        assert NuclearDataCache._reaction_to_mt("123") == 1
        assert (
            NuclearDataCache._reaction_to_mt("18") == 1
        )  # Even if it matches an MT number

    def test_reaction_to_mt_special_characters(self):
        """Test _reaction_to_mt with special characters defaults to MT=1."""
        assert NuclearDataCache._reaction_to_mt("!@#$%") == 1
        assert NuclearDataCache._reaction_to_mt("reaction@name") == 1

    def test_reaction_to_mt_unicode(self):
        """Test _reaction_to_mt with unicode characters defaults to MT=1."""
        assert NuclearDataCache._reaction_to_mt("réaction") == 1
        assert NuclearDataCache._reaction_to_mt("反応") == 1

    def test_reaction_to_mt_capture_and_n_gamma_equivalent(self):
        """Test that 'capture' and 'n,gamma' both map to MT=102."""
        assert NuclearDataCache._reaction_to_mt(
            "capture"
        ) == NuclearDataCache._reaction_to_mt("n,gamma")
        assert NuclearDataCache._reaction_to_mt("capture") == 102
        assert NuclearDataCache._reaction_to_mt("n,gamma") == 102

    def test_reaction_to_mt_variations(self):
        """Test _reaction_to_mt with common variations that should still work."""
        # These variations should still default to MT=1 since they're not exact matches
        assert NuclearDataCache._reaction_to_mt("fissions") == 1  # Plural
        assert NuclearDataCache._reaction_to_mt("total_xs") == 1  # With suffix
        assert (
            NuclearDataCache._reaction_to_mt("elastic_scattering") == 1
        )  # Extended name

    def test_reaction_to_mt_none_input(self):
        """Test _reaction_to_mt with None input raises AttributeError."""
        with pytest.raises(AttributeError):
            NuclearDataCache._reaction_to_mt(None)
