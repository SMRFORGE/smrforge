"""Tests for generate_multigroup method in CrossSectionTable."""

import numpy as np
import pytest
from unittest.mock import Mock, patch


class TestGenerateMultigroup:
    """Test generate_multigroup method comprehensively."""

    def test_generate_multigroup_basic(self, temp_dir, pre_populated_cache):
        """Test basic generate_multigroup functionality."""
        from smrforge.core.reactor_core import CrossSectionTable, Nuclide

        table = CrossSectionTable()
        table._cache = pre_populated_cache  # Use pre-populated cache

        u235 = Nuclide(Z=92, A=235, m=0)
        
        # Create a simple 3-group structure (high to low energy)
        group_structure = np.array([1e7, 1e6, 1e5, 1e4])  # 3 groups

        # Mock get_cross_section to return test data
        with patch.object(pre_populated_cache, 'get_cross_section') as mock_get:
            # Return simple test data
            energy = np.logspace(4, 7, 100)  # 10 keV to 10 MeV
            xs = np.ones_like(energy) * 10.0  # Constant 10 barns
            mock_get.return_value = (energy, xs)

            # Mock _collapse_to_multigroup to return simple values
            with patch.object(CrossSectionTable, '_collapse_to_multigroup', 
                            return_value=np.array([10.0, 10.0, 10.0])) as mock_collapse:
                df = table.generate_multigroup(
                    nuclides=[u235],
                    reactions=["total"],
                    group_structure=group_structure,
                    temperature=900.0
                )

                # Verify structure
                assert df is not None
                assert hasattr(df, 'columns')
                
                # Check that get_cross_section was called
                mock_get.assert_called_once_with(u235, "total", 900.0)
                
                # Check that collapse was called with correct arguments
                mock_collapse.assert_called_once()
                call_args = mock_collapse.call_args
                assert np.array_equal(call_args[0][0], energy)  # energy
                assert np.array_equal(call_args[0][1], xs)  # xs
                assert np.array_equal(call_args[0][2], group_structure)  # group_structure
                assert call_args[0][3] is None  # weighting_flux (None by default)

    def test_generate_multigroup_multiple_nuclides_reactions(self, temp_dir, pre_populated_cache):
        """Test generate_multigroup with multiple nuclides and reactions."""
        from smrforge.core.reactor_core import CrossSectionTable, Nuclide

        table = CrossSectionTable()
        table._cache = pre_populated_cache

        u235 = Nuclide(Z=92, A=235, m=0)
        u238 = Nuclide(Z=92, A=238, m=0)

        group_structure = np.array([1e7, 1e6, 1e5])  # 2 groups
        reactions = ["fission", "capture"]

        with patch.object(pre_populated_cache, 'get_cross_section') as mock_get:
            energy = np.logspace(4, 7, 100)
            xs = np.ones_like(energy) * 5.0
            mock_get.return_value = (energy, xs)

            # Mock collapse to return 2 values (one per group)
            with patch.object(CrossSectionTable, '_collapse_to_multigroup',
                            return_value=np.array([5.0, 5.0])) as mock_collapse:
                df = table.generate_multigroup(
                    nuclides=[u235, u238],
                    reactions=reactions,
                    group_structure=group_structure,
                    temperature=900.0
                )

                # Should be called 4 times (2 nuclides × 2 reactions)
                assert mock_get.call_count == 4
                assert mock_collapse.call_count == 4

                # Verify DataFrame structure
                assert df is not None
                # Should have 2 nuclides × 2 reactions × 2 groups = 8 rows
                assert len(df) == 8

                # Check columns exist
                assert 'nuclide' in df.columns
                assert 'reaction' in df.columns
                assert 'group' in df.columns
                assert 'xs' in df.columns

                # Verify data stored in table
                assert table.data is not None
                assert table.data is df

    def test_generate_multigroup_with_weighting_flux(self, temp_dir, pre_populated_cache):
        """Test generate_multigroup with custom weighting flux."""
        from smrforge.core.reactor_core import CrossSectionTable, Nuclide

        table = CrossSectionTable()
        table._cache = pre_populated_cache

        u235 = Nuclide(Z=92, A=235, m=0)
        group_structure = np.array([1e7, 1e6, 1e5])
        energy = np.logspace(4, 7, 100)
        weighting_flux = np.ones_like(energy)  # Flat flux

        with patch.object(pre_populated_cache, 'get_cross_section') as mock_get:
            xs = np.ones_like(energy) * 10.0
            mock_get.return_value = (energy, xs)

            with patch.object(CrossSectionTable, '_collapse_to_multigroup',
                            return_value=np.array([10.0, 10.0])) as mock_collapse:
                df = table.generate_multigroup(
                    nuclides=[u235],
                    reactions=["total"],
                    group_structure=group_structure,
                    temperature=900.0,
                    weighting_flux=weighting_flux
                )

                # Verify weighting_flux was passed to collapse
                call_args = mock_collapse.call_args
                assert np.array_equal(call_args[0][3], weighting_flux)

    def test_generate_multigroup_dataframe_structure(self, temp_dir, pre_populated_cache):
        """Test that generate_multigroup returns properly structured DataFrame."""
        from smrforge.core.reactor_core import CrossSectionTable, Nuclide
        import polars as pl

        table = CrossSectionTable()
        table._cache = pre_populated_cache

        u235 = Nuclide(Z=92, A=235, m=0)
        group_structure = np.array([1e7, 1e6, 1e5, 1e4])  # 3 groups

        with patch.object(pre_populated_cache, 'get_cross_section') as mock_get:
            energy = np.logspace(4, 7, 100)
            xs = np.ones_like(energy) * 10.0
            mock_get.return_value = (energy, xs)

            with patch.object(CrossSectionTable, '_collapse_to_multigroup',
                            return_value=np.array([10.0, 10.0, 10.0])):
                df = table.generate_multigroup(
                    nuclides=[u235],
                    reactions=["total"],
                    group_structure=group_structure,
                    temperature=900.0
                )

                # Verify it's a Polars DataFrame
                assert isinstance(df, pl.DataFrame)

                # Verify columns
                expected_columns = ['nuclide', 'reaction', 'group', 'xs']
                assert all(col in df.columns for col in expected_columns)

                # Verify data types
                assert df['nuclide'].dtype == pl.Utf8
                assert df['reaction'].dtype == pl.Utf8
                assert df['group'].dtype in [pl.Int64, pl.Int32]  # integer group index
                assert df['xs'].dtype in [pl.Float64, pl.Float32]  # cross section

                # Verify group indices are 0-based
                groups = df['group'].unique().sort()
                expected_groups = list(range(3))  # 0, 1, 2 for 3 groups
                assert groups.to_list() == expected_groups

    def test_generate_multigroup_different_temperatures(self, temp_dir, pre_populated_cache):
        """Test generate_multigroup with different temperatures."""
        from smrforge.core.reactor_core import CrossSectionTable, Nuclide

        table = CrossSectionTable()
        table._cache = pre_populated_cache

        u235 = Nuclide(Z=92, A=235, m=0)
        group_structure = np.array([1e7, 1e6, 1e5])

        temperatures = [600.0, 900.0, 1200.0]

        with patch.object(pre_populated_cache, 'get_cross_section') as mock_get:
            energy = np.logspace(4, 7, 100)
            xs = np.ones_like(energy) * 10.0
            mock_get.return_value = (energy, xs)

            with patch.object(CrossSectionTable, '_collapse_to_multigroup',
                            return_value=np.array([10.0, 10.0])):
                for temp in temperatures:
                    df = table.generate_multigroup(
                        nuclides=[u235],
                        reactions=["total"],
                        group_structure=group_structure,
                        temperature=temp
                    )

                    # Verify temperature was passed to get_cross_section
                    calls = [call[0][2] for call in mock_get.call_args_list]  # Extract temperature arg
                    assert temp in calls

    def test_generate_multigroup_group_structure_validation(self, temp_dir, pre_populated_cache):
        """Test that group_structure is used correctly (n_groups = len - 1)."""
        from smrforge.core.reactor_core import CrossSectionTable, Nuclide

        table = CrossSectionTable()
        table._cache = pre_populated_cache

        u235 = Nuclide(Z=92, A=235, m=0)

        # Test with different group structures
        test_cases = [
            (np.array([1e7, 1e5]), 1),  # 2 boundaries = 1 group
            (np.array([1e7, 1e6, 1e5]), 2),  # 3 boundaries = 2 groups
            (np.array([1e7, 1e6, 1e5, 1e4, 1e3]), 4),  # 5 boundaries = 4 groups
        ]

        with patch.object(pre_populated_cache, 'get_cross_section') as mock_get:
            energy = np.logspace(3, 7, 100)
            xs = np.ones_like(energy) * 10.0
            mock_get.return_value = (energy, xs)

            for group_structure, expected_n_groups in test_cases:
                with patch.object(CrossSectionTable, '_collapse_to_multigroup',
                                return_value=np.ones(expected_n_groups) * 10.0) as mock_collapse:
                    df = table.generate_multigroup(
                        nuclides=[u235],
                        reactions=["total"],
                        group_structure=group_structure,
                        temperature=900.0
                    )

                    # Verify correct number of groups returned
                    unique_groups = df['group'].unique().sort()
                    assert len(unique_groups) == expected_n_groups
                    assert unique_groups.to_list() == list(range(expected_n_groups))

                    # Verify collapse was called with correct return size
                    assert len(mock_collapse.return_value) == expected_n_groups

