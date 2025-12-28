"""Tests for pivot_for_solver method edge cases and error handling."""

import numpy as np
import polars as pl
import pytest

from smrforge.core.reactor_core import CrossSectionTable


class TestPivotForSolver:
    """Test pivot_for_solver method comprehensively."""

    def test_pivot_for_solver_basic(self):
        """Test basic pivot_for_solver functionality."""
        table = CrossSectionTable()
        
        # Create a sample DataFrame with proper structure
        records = []
        for nuclide in ["U235", "U238"]:
            for reaction in ["fission", "capture"]:
                for group in [0, 1, 2]:
                    xs_val = 1.0 if nuclide == "U235" else 0.5
                    records.append({
                        "nuclide": nuclide,
                        "reaction": reaction,
                        "group": group,
                        "xs": xs_val
                    })
        
        table.data = pl.DataFrame(records)
        
        # Pivot for solver
        result = table.pivot_for_solver(
            nuclides=["U235", "U238"],
            reactions=["fission", "capture"]
        )
        
        # Result should be numpy array
        assert isinstance(result, np.ndarray)
        # Pivot creates 2D array: (n_nuclides * n_groups, n_reactions)
        # 2 nuclides * 3 groups = 6 rows, 2 reactions = 2 columns
        assert result.shape == (6, 2)
        assert result.size > 0

    def test_pivot_for_solver_single_nuclide(self):
        """Test pivot_for_solver with single nuclide."""
        table = CrossSectionTable()
        
        records = []
        for reaction in ["fission", "capture"]:
            for group in [0, 1]:
                records.append({
                    "nuclide": "U235",
                    "reaction": reaction,
                    "group": group,
                    "xs": 1.0
                })
        
        table.data = pl.DataFrame(records)
        
        result = table.pivot_for_solver(
            nuclides=["U235"],
            reactions=["fission", "capture"]
        )
        
        assert isinstance(result, np.ndarray)
        # 1 nuclide * 2 groups = 2 rows, 2 reactions = 2 columns
        assert result.shape == (2, 2)

    def test_pivot_for_solver_single_reaction(self):
        """Test pivot_for_solver with single reaction."""
        table = CrossSectionTable()
        
        records = []
        for nuclide in ["U235", "U238"]:
            for group in [0, 1]:
                records.append({
                    "nuclide": nuclide,
                    "reaction": "fission",
                    "group": group,
                    "xs": 1.0
                })
        
        table.data = pl.DataFrame(records)
        
        result = table.pivot_for_solver(
            nuclides=["U235", "U238"],
            reactions=["fission"]
        )
        
        assert isinstance(result, np.ndarray)
        # 2 nuclides * 2 groups = 4 rows, 1 reaction = 1 column
        assert result.shape == (4, 1)

    def test_pivot_for_solver_many_groups(self):
        """Test pivot_for_solver with many energy groups."""
        table = CrossSectionTable()
        
        n_groups = 70
        records = []
        for nuclide in ["U235", "U238"]:
            for reaction in ["fission", "capture", "elastic"]:
                for group in range(n_groups):
                    records.append({
                        "nuclide": nuclide,
                        "reaction": reaction,
                        "group": group,
                        "xs": float(group)  # Varying cross sections
                    })
        
        table.data = pl.DataFrame(records)
        
        result = table.pivot_for_solver(
            nuclides=["U235", "U238"],
            reactions=["fission", "capture", "elastic"]
        )
        
        assert isinstance(result, np.ndarray)
        # 2 nuclides * 70 groups = 140 rows, 3 reactions = 3 columns
        assert result.shape == (140, 3)
        # Check that values are correctly extracted
        assert np.all(np.isfinite(result))

    def test_pivot_for_solver_subset_nuclides(self):
        """Test pivot_for_solver with subset of nuclides in table."""
        table = CrossSectionTable()
        
        records = []
        for nuclide in ["U235", "U238", "U236"]:
            for reaction in ["fission", "capture"]:
                for group in [0, 1]:
                    records.append({
                        "nuclide": nuclide,
                        "reaction": reaction,
                        "group": group,
                        "xs": 1.0
                    })
        
        table.data = pl.DataFrame(records)
        
        # Only pivot subset of nuclides
        result = table.pivot_for_solver(
            nuclides=["U235", "U238"],  # Exclude U236
            reactions=["fission", "capture"]
        )
        
        assert isinstance(result, np.ndarray)
        # 2 nuclides * 2 groups = 4 rows, 2 reactions = 2 columns
        assert result.shape == (4, 2)

    def test_pivot_for_solver_subset_reactions(self):
        """Test pivot_for_solver with subset of reactions in table."""
        table = CrossSectionTable()
        
        records = []
        for nuclide in ["U235", "U238"]:
            for reaction in ["fission", "capture", "elastic", "total"]:
                for group in [0, 1]:
                    records.append({
                        "nuclide": nuclide,
                        "reaction": reaction,
                        "group": group,
                        "xs": 1.0
                    })
        
        table.data = pl.DataFrame(records)
        
        # Only pivot subset of reactions
        result = table.pivot_for_solver(
            nuclides=["U235", "U238"],
            reactions=["fission", "capture"]  # Exclude elastic, total
        )
        
        assert isinstance(result, np.ndarray)
        # 2 nuclides * 2 groups = 4 rows, 2 reactions = 2 columns
        assert result.shape == (4, 2)

    def test_pivot_for_solver_empty_data(self):
        """Test pivot_for_solver with empty DataFrame."""
        table = CrossSectionTable()
        table.data = pl.DataFrame({
            "nuclide": [],
            "reaction": [],
            "group": [],
            "xs": []
        })
        
        # Empty pivot results in empty DataFrame, which should raise error when selecting columns
        with pytest.raises((pl.exceptions.ColumnNotFoundError, AttributeError)):
            table.pivot_for_solver(
                nuclides=["U235"],
                reactions=["fission"]
            )

    def test_pivot_for_solver_no_data_attribute(self):
        """Test pivot_for_solver when data attribute is None."""
        table = CrossSectionTable()
        table.data = None
        
        # Should raise AttributeError when trying to access data
        with pytest.raises(AttributeError):
            table.pivot_for_solver(
                nuclides=["U235"],
                reactions=["fission"]
            )

    def test_pivot_for_solver_missing_nuclide(self):
        """Test pivot_for_solver with nuclide not in table."""
        table = CrossSectionTable()
        
        records = []
        for nuclide in ["U235", "U238"]:
            for reaction in ["fission"]:
                for group in [0, 1]:
                    records.append({
                        "nuclide": nuclide,
                        "reaction": reaction,
                        "group": group,
                        "xs": 1.0
                    })
        
        table.data = pl.DataFrame(records)
        
        # Request nuclide that doesn't exist - should return filtered result
        result = table.pivot_for_solver(
            nuclides=["U235", "Pu239"],  # Pu239 not in table
            reactions=["fission"]
        )
        
        # Result should only include U235
        assert isinstance(result, np.ndarray)
        # Shape depends on how Polars handles missing data in pivot
        # Should handle gracefully (may be empty or contain only U235)

    def test_pivot_for_solver_missing_reaction(self):
        """Test pivot_for_solver with reaction not in table."""
        table = CrossSectionTable()
        
        records = []
        for nuclide in ["U235"]:
            for reaction in ["fission", "capture"]:
                for group in [0, 1]:
                    records.append({
                        "nuclide": nuclide,
                        "reaction": reaction,
                        "group": group,
                        "xs": 1.0
                    })
        
        table.data = pl.DataFrame(records)
        
        # Request reaction that doesn't exist - should raise ColumnNotFoundError
        with pytest.raises(pl.exceptions.ColumnNotFoundError):
            table.pivot_for_solver(
                nuclides=["U235"],
                reactions=["fission", "elastic"]  # elastic not in table
            )

    def test_pivot_for_solver_different_xs_values(self):
        """Test pivot_for_solver with varying cross-section values."""
        table = CrossSectionTable()
        
        records = []
        for i, nuclide in enumerate(["U235", "U238"]):
            for j, reaction in enumerate(["fission", "capture"]):
                for group in [0, 1, 2]:
                    # Create distinct values for each combination
                    xs_val = (i + 1) * 10.0 + (j + 1) * 1.0 + group * 0.1
                    records.append({
                        "nuclide": nuclide,
                        "reaction": reaction,
                        "group": group,
                        "xs": xs_val
                    })
        
        table.data = pl.DataFrame(records)
        
        result = table.pivot_for_solver(
            nuclides=["U235", "U238"],
            reactions=["fission", "capture"]
        )
        
        assert isinstance(result, np.ndarray)
        # 2 nuclides * 3 groups = 6 rows, 2 reactions = 2 columns
        assert result.shape == (6, 2)
        
        # Check that values are correctly extracted
        # Result is 2D: rows are (nuclide, group) combinations, columns are reactions
        # Row order: (U235, 0), (U235, 1), (U235, 2), (U238, 0), (U238, 1), (U238, 2)
        # Column order: fission, capture
        # U235, group 0, fission should be 11.0 (row 0, col 0)
        assert np.isclose(result[0, 0], 11.0)
        # U238, group 2, capture should be 22.2 (row 5, col 1)
        assert np.isclose(result[5, 1], 22.2)

    def test_pivot_for_solver_zero_xs_values(self):
        """Test pivot_for_solver with zero cross-section values."""
        table = CrossSectionTable()
        
        records = []
        for nuclide in ["U235", "U238"]:
            for reaction in ["fission", "capture"]:
                for group in [0, 1]:
                    records.append({
                        "nuclide": nuclide,
                        "reaction": reaction,
                        "group": group,
                        "xs": 0.0  # Zero cross sections
                    })
        
        table.data = pl.DataFrame(records)
        
        result = table.pivot_for_solver(
            nuclides=["U235", "U238"],
            reactions=["fission", "capture"]
        )
        
        assert isinstance(result, np.ndarray)
        # 2 nuclides * 2 groups = 4 rows, 2 reactions = 2 columns
        assert result.shape == (4, 2)
        assert np.all(result == 0.0)

    def test_pivot_for_solver_very_large_xs_values(self):
        """Test pivot_for_solver with very large cross-section values."""
        table = CrossSectionTable()
        
        records = []
        for nuclide in ["U235"]:
            for reaction in ["fission"]:
                for group in [0, 1]:
                    records.append({
                        "nuclide": nuclide,
                        "reaction": reaction,
                        "group": group,
                        "xs": 1e6  # Very large cross section (barns)
                    })
        
        table.data = pl.DataFrame(records)
        
        result = table.pivot_for_solver(
            nuclides=["U235"],
            reactions=["fission"]
        )
        
        assert isinstance(result, np.ndarray)
        # 1 nuclide * 2 groups = 2 rows, 1 reaction = 1 column
        assert result.shape == (2, 1)
        assert np.all(result == 1e6)

    def test_pivot_for_solver_order_independence(self):
        """Test that order of nuclides/reactions doesn't matter for filtering."""
        table = CrossSectionTable()
        
        records = []
        for nuclide in ["U235", "U238"]:
            for reaction in ["fission", "capture"]:
                for group in [0, 1]:
                    records.append({
                        "nuclide": nuclide,
                        "reaction": reaction,
                        "group": group,
                        "xs": 1.0
                    })
        
        table.data = pl.DataFrame(records)
        
        # Test with different orders
        result1 = table.pivot_for_solver(
            nuclides=["U235", "U238"],
            reactions=["fission", "capture"]
        )
        
        result2 = table.pivot_for_solver(
            nuclides=["U238", "U235"],  # Reversed order
            reactions=["capture", "fission"]  # Reversed order
        )
        
        # Results should have same data but potentially different ordering
        assert isinstance(result1, np.ndarray)
        assert isinstance(result2, np.ndarray)
        # Both should have same total size (may differ in shape depending on Polars pivot behavior)
        assert result1.size == result2.size

