"""
Tests for endf_parser.py when Polars is not available.

This test suite tests the behavior when POLARS_AVAILABLE is False,
ensuring that to_polars and get_reactions_dataframe return None gracefully.
"""

import pytest
from pathlib import Path
from unittest.mock import patch


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
def complete_endf_file(temp_dir):
    """Create a complete mock ENDF file with header and reactions."""
    endf_path = temp_dir / "test_complete.endf"
    endf_content = """                                                                   125 1451    1
 9.223500+4 2.350000+2          0          0          0          0 125 1451    2
                                                                   125 1451    0
                                                                   125 3  1    1
 1.000000+5 1.000000+1 1.000000+6 1.200000+1                       125 3  1    3
                                                                   125 0  0    0
                                                                   125 3  2    1
 1.000000+5 8.000000+0 1.000000+6 9.000000+0                       125 3  2    3
                                                                   125 0  0    0
                                                                   125 318    1
 1.000000+5 1.500000+0 1.000000+6 2.000000+0                       125 318    3
                                                                   125 0  0    0
                                                                   125 3102    1
 1.000000+5 2.000000+0 1.000000+6 2.500000+0                       125 3102    3
                                                                   125 0  0    0
"""
    endf_path.write_text(endf_content)
    return endf_path


class TestENDFEvaluationPolarsUnavailable:
    """Test ENDFEvaluation methods when Polars is not available."""

    @patch('smrforge.core.endf_parser.POLARS_AVAILABLE', False)
    @patch('smrforge.core.endf_parser.pl', None)
    def test_to_polars_returns_none_when_polars_unavailable(self, endf_evaluation_class, complete_endf_file):
        """Test that to_polars returns None when Polars is not available."""
        eval_obj = endf_evaluation_class(complete_endf_file)
        
        result = eval_obj.to_polars()
        
        assert result is None

    @patch('smrforge.core.endf_parser.POLARS_AVAILABLE', False)
    @patch('smrforge.core.endf_parser.pl', None)
    def test_get_reactions_dataframe_returns_none_when_polars_unavailable(
        self, endf_evaluation_class, complete_endf_file
    ):
        """Test that get_reactions_dataframe returns None when Polars is not available."""
        eval_obj = endf_evaluation_class(complete_endf_file)
        
        result = eval_obj.get_reactions_dataframe()
        
        assert result is None

    @patch('smrforge.core.endf_parser.POLARS_AVAILABLE', False)
    @patch('smrforge.core.endf_parser.pl', None)
    def test_to_polars_with_no_reactions_returns_none(self, endf_evaluation_class, temp_dir):
        """Test that to_polars returns None when Polars unavailable, even with no reactions."""
        # Create minimal ENDF file with no reactions
        endf_path = temp_dir / "no_reactions.endf"
        endf_content = """                                                                   125 1451    1
 9.223500+4 2.350000+2          0          0          0          0 125 1451    2
                                                                   125 1451    0
"""
        endf_path.write_text(endf_content)
        
        eval_obj = endf_evaluation_class(endf_path)
        
        result = eval_obj.to_polars()
        
        assert result is None

    @patch('smrforge.core.endf_parser.POLARS_AVAILABLE', False)
    @patch('smrforge.core.endf_parser.pl', None)
    def test_get_reactions_dataframe_with_no_reactions_returns_none(
        self, endf_evaluation_class, temp_dir
    ):
        """Test that get_reactions_dataframe returns None when Polars unavailable, even with no reactions."""
        # Create minimal ENDF file with no reactions
        endf_path = temp_dir / "no_reactions2.endf"
        endf_content = """                                                                   125 1451    1
 9.223500+4 2.350000+2          0          0          0          0 125 1451    2
                                                                   125 1451    0
"""
        endf_path.write_text(endf_content)
        
        eval_obj = endf_evaluation_class(endf_path)
        
        result = eval_obj.get_reactions_dataframe()
        
        assert result is None


class TestENDFCompatibilityPolarsUnavailable:
    """Test ENDFCompatibility methods when Polars is not available."""

    @patch('smrforge.core.endf_parser.POLARS_AVAILABLE', False)
    @patch('smrforge.core.endf_parser.pl', None)
    def test_compatibility_to_polars_returns_none_when_polars_unavailable(
        self, endf_compatibility_class, complete_endf_file
    ):
        """Test that ENDFCompatibility.to_polars returns None when Polars is not available."""
        compat = endf_compatibility_class(complete_endf_file)
        
        result = compat.to_polars()
        
        assert result is None

    @patch('smrforge.core.endf_parser.POLARS_AVAILABLE', False)
    @patch('smrforge.core.endf_parser.pl', None)
    def test_compatibility_get_reactions_dataframe_returns_none_when_polars_unavailable(
        self, endf_compatibility_class, complete_endf_file
    ):
        """Test that ENDFCompatibility.get_reactions_dataframe returns None when Polars is not available."""
        compat = endf_compatibility_class(complete_endf_file)
        
        result = compat.get_reactions_dataframe()
        
        assert result is None

    @patch('smrforge.core.endf_parser.POLARS_AVAILABLE', False)
    @patch('smrforge.core.endf_parser.pl', None)
    def test_compatibility_other_methods_work_when_polars_unavailable(
        self, endf_compatibility_class, complete_endf_file
    ):
        """Test that other ENDFCompatibility methods work normally even when Polars is unavailable."""
        compat = endf_compatibility_class(complete_endf_file)
        
        # These methods should work regardless of Polars availability
        assert 1 in compat  # __contains__
        reaction = compat[1]  # __getitem__
        assert reaction is not None
        assert hasattr(reaction, 'energy')
        assert hasattr(reaction, 'cross_section')
        assert hasattr(reaction, 'xs')
        
        # Polars methods should return None
        assert compat.to_polars() is None
        assert compat.get_reactions_dataframe() is None

