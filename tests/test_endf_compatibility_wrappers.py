"""
Tests for ENDFCompatibility wrapper methods.

This test suite comprehensively tests the wrapper methods in ENDFCompatibility:
- __contains__: Checking if reactions exist
- __getitem__: Getting reaction data with ReactionWrapper
- to_polars: Exporting reactions as Polars DataFrame
- get_reactions_dataframe: Getting summary DataFrame
"""

import numpy as np
import pytest
from pathlib import Path


@pytest.fixture
def endf_compatibility_class():
    """Get the ENDFCompatibility class."""
    try:
        from smrforge.core.endf_parser import ENDFCompatibility
        return ENDFCompatibility
    except ImportError:
        pytest.skip("ENDF parser not available")


@pytest.fixture
def complete_endf_file_with_reactions(temp_dir):
    """Create a complete ENDF file with header and multiple reactions for testing."""
    endf_path = temp_dir / "U235_complete.endf"
    
    # Create ENDF file with proper format including header and multiple reactions
    endf_content = """ 1.001000+3 9.991673-1          0          0          0          0 125 1451    1
 9.223500+4 2.350000+2          0          0          0          0 125 1451    2
                                                                   125 1451    0
 1.001000+3 9.991673-1          0          0          0          0 125 3  1    1
 1.000000+5 1.000000+1 1.000000+6 1.200000+1 5.000000+6 1.500000+1 125 3  1    3
 1.000000+7 1.800000+1 2.000000+7 2.000000+1 5.000000+7 2.200000+1 125 3  1    4
                                                                   125 0  0    0
 1.001000+3 9.991673-1          0          0          0          0 125 3  2    1
 1.000000+5 8.000000+0 1.000000+6 9.000000+0 1.000000+7 1.000000+1 125 3  2    3
                                                                   125 0  0    0
 1.001000+3 9.991673-1          0          0          0          0 125 3 18    1
 1.000000+5 1.500000+0 1.000000+6 2.000000+0 5.000000+6 2.500000+0 125 3 18    3
                                                                   125 0  0    0
 1.001000+3 9.991673-1          0          0          0          0 125 3102    1
 1.000000+5 5.000000-1 1.000000+6 1.000000+0 1.000000+7 1.500000+0 125 3102    3
                                                                   125 0  0    0
                                                                   125 0  0    0
"""
    endf_path.write_text(endf_content)
    return endf_path


class TestENDFCompatibilityContains:
    """Test ENDFCompatibility.__contains__ method."""

    def test_contains_existing_reaction(self, endf_compatibility_class, complete_endf_file_with_reactions):
        """Test __contains__ returns True for existing reactions."""
        evaluation = endf_compatibility_class(complete_endf_file_with_reactions)
        
        # Should contain MT=1 (total)
        assert 1 in evaluation
        
        # Should contain MT=2 (elastic)
        assert 2 in evaluation
        
        # Should contain MT=18 (fission)
        assert 18 in evaluation
        
        # Should contain MT=102 (capture)
        assert 102 in evaluation

    def test_contains_nonexistent_reaction(self, endf_compatibility_class, complete_endf_file_with_reactions):
        """Test __contains__ returns False for nonexistent reactions."""
        evaluation = endf_compatibility_class(complete_endf_file_with_reactions)
        
        # Should not contain MT=999 (nonexistent)
        assert 999 not in evaluation
        
        # Should not contain MT=0 (invalid)
        assert 0 not in evaluation
        
        # Should not contain negative MT
        assert -1 not in evaluation

    def test_contains_delegates_to_evaluation(self, endf_compatibility_class, complete_endf_file_with_reactions):
        """Test that __contains__ properly delegates to underlying ENDFEvaluation."""
        evaluation = endf_compatibility_class(complete_endf_file_with_reactions)
        
        # Verify it checks the underlying evaluation
        assert hasattr(evaluation, "_evaluation")
        
        # Should match the underlying evaluation's reactions
        for mt in [1, 2, 18, 102]:
            assert mt in evaluation
            assert mt in evaluation._evaluation.reactions


class TestENDFCompatibilityGetItem:
    """Test ENDFCompatibility.__getitem__ method and ReactionWrapper."""

    def test_getitem_returns_reaction_wrapper(self, endf_compatibility_class, complete_endf_file_with_reactions):
        """Test __getitem__ returns ReactionWrapper with extended interface."""
        evaluation = endf_compatibility_class(complete_endf_file_with_reactions)
        
        # Get reaction data
        rxn_data = evaluation[1]  # MT=1 (total)
        
        # Should have ReactionWrapper attributes
        assert hasattr(rxn_data, "energy")
        assert hasattr(rxn_data, "cross_section")
        assert hasattr(rxn_data, "xs")
        assert hasattr(rxn_data, "_data")

    def test_getitem_energy_attribute(self, endf_compatibility_class, complete_endf_file_with_reactions):
        """Test ReactionWrapper.energy attribute matches underlying data."""
        evaluation = endf_compatibility_class(complete_endf_file_with_reactions)
        
        rxn_data = evaluation[1]  # MT=1 (total)
        
        # Energy should be accessible
        assert rxn_data.energy is not None
        assert isinstance(rxn_data.energy, np.ndarray)
        assert len(rxn_data.energy) > 0
        
        # Should match underlying ReactionData
        assert np.array_equal(rxn_data.energy, rxn_data._data.energy)

    def test_getitem_cross_section_attribute(self, endf_compatibility_class, complete_endf_file_with_reactions):
        """Test ReactionWrapper.cross_section attribute matches underlying data."""
        evaluation = endf_compatibility_class(complete_endf_file_with_reactions)
        
        rxn_data = evaluation[1]  # MT=1 (total)
        
        # Cross section should be accessible
        assert rxn_data.cross_section is not None
        assert isinstance(rxn_data.cross_section, np.ndarray)
        assert len(rxn_data.cross_section) > 0
        assert len(rxn_data.cross_section) == len(rxn_data.energy)
        
        # Should match underlying ReactionData
        assert np.array_equal(rxn_data.cross_section, rxn_data._data.cross_section)

    def test_getitem_xs_dictionary_structure(self, endf_compatibility_class, complete_endf_file_with_reactions):
        """Test ReactionWrapper.xs dictionary provides temperature data structure."""
        evaluation = endf_compatibility_class(complete_endf_file_with_reactions)
        
        rxn_data = evaluation[1]  # MT=1 (total)
        
        # xs should be a dictionary
        assert isinstance(rxn_data.xs, dict)
        
        # Should have "0K" key
        assert "0K" in rxn_data.xs
        
        # The value should be an object with x and y attributes
        xs_0k = rxn_data.xs["0K"]
        assert hasattr(xs_0k, "x")
        assert hasattr(xs_0k, "y")
        
        # x should be energy array
        assert np.array_equal(xs_0k.x, rxn_data.energy)
        
        # y should be cross section array
        assert np.array_equal(xs_0k.y, rxn_data.cross_section)

    def test_getitem_multiple_reactions(self, endf_compatibility_class, complete_endf_file_with_reactions):
        """Test __getitem__ works with multiple different reactions."""
        evaluation = endf_compatibility_class(complete_endf_file_with_reactions)
        
        # Get different reactions
        total = evaluation[1]
        elastic = evaluation[2]
        fission = evaluation[18]
        capture = evaluation[102]
        
        # Each should have proper structure
        for rxn in [total, elastic, fission, capture]:
            assert hasattr(rxn, "energy")
            assert hasattr(rxn, "cross_section")
            assert hasattr(rxn, "xs")
            assert len(rxn.energy) > 0
            assert len(rxn.cross_section) == len(rxn.energy)

    def test_getitem_raises_keyerror_for_missing(self, endf_compatibility_class, complete_endf_file_with_reactions):
        """Test __getitem__ raises KeyError for missing reactions."""
        evaluation = endf_compatibility_class(complete_endf_file_with_reactions)
        
        # Should raise KeyError for nonexistent reaction
        with pytest.raises(KeyError):
            _ = evaluation[999]
        
        with pytest.raises(KeyError):
            _ = evaluation[0]


class TestENDFCompatibilityToPolars:
    """Test ENDFCompatibility.to_polars method."""

    def test_to_polars_returns_dataframe(self, endf_compatibility_class, complete_endf_file_with_reactions):
        """Test to_polars returns Polars DataFrame with correct structure."""
        try:
            import polars as pl
        except ImportError:
            pytest.skip("Polars not available")
        
        evaluation = endf_compatibility_class(complete_endf_file_with_reactions)
        
        df = evaluation.to_polars()
        
        # Should return DataFrame (not None if Polars available)
        if df is not None:
            assert isinstance(df, pl.DataFrame)
            
            # Should have correct columns
            expected_columns = {"mt_number", "reaction_name", "energy", "cross_section"}
            assert set(df.columns) == expected_columns
            
            # Should have rows (one per energy point across all reactions)
            assert len(df) > 0

    def test_to_polars_contains_all_reactions(self, endf_compatibility_class, complete_endf_file_with_reactions):
        """Test to_polars includes all reactions."""
        try:
            import polars as pl
        except ImportError:
            pytest.skip("Polars not available")
        
        evaluation = endf_compatibility_class(complete_endf_file_with_reactions)
        
        df = evaluation.to_polars()
        
        if df is not None:
            # Should contain all reaction MT numbers
            mt_numbers = set(df["mt_number"].unique())
            assert 1 in mt_numbers  # total
            assert 2 in mt_numbers  # elastic
            assert 18 in mt_numbers  # fission
            assert 102 in mt_numbers  # capture

    def test_to_polars_data_correctness(self, endf_compatibility_class, complete_endf_file_with_reactions):
        """Test to_polars data matches underlying reaction data."""
        try:
            import polars as pl
        except ImportError:
            pytest.skip("Polars not available")
        
        evaluation = endf_compatibility_class(complete_endf_file_with_reactions)
        
        df = evaluation.to_polars()
        
        if df is not None:
            # Get reaction directly
            rxn_data = evaluation[1]
            
            # Filter DataFrame for MT=1
            mt1_df = df.filter(df["mt_number"] == 1)
            
            # Check that energy and cross_section match
            assert len(mt1_df) == len(rxn_data.energy)
            
            # Check a few values match
            energies_from_df = mt1_df["energy"].to_numpy()
            xs_from_df = mt1_df["cross_section"].to_numpy()
            
            # Should match (may need to sort if order differs)
            assert np.allclose(np.sort(energies_from_df), np.sort(rxn_data.energy))
            # Cross sections may need to be sorted in same order as energies
            sort_idx_df = np.argsort(energies_from_df)
            sort_idx_rxn = np.argsort(rxn_data.energy)
            assert np.allclose(xs_from_df[sort_idx_df], rxn_data.cross_section[sort_idx_rxn])


class TestENDFCompatibilityGetReactionsDataframe:
    """Test ENDFCompatibility.get_reactions_dataframe method."""

    def test_get_reactions_dataframe_returns_summary(self, endf_compatibility_class, complete_endf_file_with_reactions):
        """Test get_reactions_dataframe returns summary DataFrame."""
        try:
            import polars as pl
        except ImportError:
            pytest.skip("Polars not available")
        
        evaluation = endf_compatibility_class(complete_endf_file_with_reactions)
        
        df = evaluation.get_reactions_dataframe()
        
        # Should return DataFrame (not None if Polars available)
        if df is not None:
            assert isinstance(df, pl.DataFrame)
            
            # Should have one row per reaction
            assert len(df) >= 4  # At least 4 reactions (MT=1, 2, 18, 102)
            
            # Should have summary columns (checking for expected ones, allowing extra like xs_mean)
            required_columns = {"mt_number", "reaction_name", "n_points", 
                              "energy_min", "energy_max", "xs_min", "xs_max"}
            assert required_columns.issubset(set(df.columns))

    def test_get_reactions_dataframe_contains_all_reactions(self, endf_compatibility_class, complete_endf_file_with_reactions):
        """Test get_reactions_dataframe includes all reactions."""
        try:
            import polars as pl
        except ImportError:
            pytest.skip("Polars not available")
        
        evaluation = endf_compatibility_class(complete_endf_file_with_reactions)
        
        df = evaluation.get_reactions_dataframe()
        
        if df is not None:
            # Should contain all reaction MT numbers
            mt_numbers = set(df["mt_number"].unique())
            assert 1 in mt_numbers  # total
            assert 2 in mt_numbers  # elastic
            assert 18 in mt_numbers  # fission
            assert 102 in mt_numbers  # capture

    def test_get_reactions_dataframe_summary_statistics(self, endf_compatibility_class, complete_endf_file_with_reactions):
        """Test get_reactions_dataframe summary statistics are correct."""
        try:
            import polars as pl
        except ImportError:
            pytest.skip("Polars not available")
        
        evaluation = endf_compatibility_class(complete_endf_file_with_reactions)
        
        df = evaluation.get_reactions_dataframe()
        
        if df is not None:
            # Get MT=1 row
            mt1_row = df.filter(df["mt_number"] == 1)
            assert len(mt1_row) == 1
            
            # Get the actual reaction data for comparison
            rxn_data = evaluation[1]
            
            # Check summary statistics match
            assert mt1_row["n_points"][0] == len(rxn_data.energy)
            assert np.isclose(mt1_row["energy_min"][0], np.min(rxn_data.energy))
            assert np.isclose(mt1_row["energy_max"][0], np.max(rxn_data.energy))
            assert np.isclose(mt1_row["xs_min"][0], np.min(rxn_data.cross_section))
            assert np.isclose(mt1_row["xs_max"][0], np.max(rxn_data.cross_section))

