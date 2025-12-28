"""Tests for generate_multigroup edge cases and error handling."""

import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestGenerateMultigroupEdgeCases:
    """Test generate_multigroup edge cases and error handling."""

    def test_generate_multigroup_empty_nuclides(self, temp_dir, pre_populated_cache):
        """Test generate_multigroup with empty nuclides list."""
        from smrforge.core.reactor_core import CrossSectionTable

        table = CrossSectionTable()
        table._cache = pre_populated_cache

        group_structure = np.array([1e7, 1e6, 1e5])

        df = table.generate_multigroup(
            nuclides=[],
            reactions=["total"],
            group_structure=group_structure,
            temperature=900.0
        )

        # Should return empty DataFrame with correct structure
        assert df is not None
        assert len(df) == 0
        assert 'nuclide' in df.columns
        assert 'reaction' in df.columns
        assert 'group' in df.columns
        assert 'xs' in df.columns

    def test_generate_multigroup_empty_reactions(self, temp_dir, pre_populated_cache):
        """Test generate_multigroup with empty reactions list."""
        from smrforge.core.reactor_core import CrossSectionTable, Nuclide

        table = CrossSectionTable()
        table._cache = pre_populated_cache

        u235 = Nuclide(Z=92, A=235, m=0)
        group_structure = np.array([1e7, 1e6, 1e5])

        df = table.generate_multigroup(
            nuclides=[u235],
            reactions=[],
            group_structure=group_structure,
            temperature=900.0
        )

        # Should return empty DataFrame with correct structure
        assert df is not None
        assert len(df) == 0

    def test_generate_multigroup_single_group(self, temp_dir, pre_populated_cache):
        """Test generate_multigroup with single group structure."""
        from smrforge.core.reactor_core import CrossSectionTable, Nuclide

        table = CrossSectionTable()
        table._cache = pre_populated_cache

        u235 = Nuclide(Z=92, A=235, m=0)
        group_structure = np.array([1e7, 1e5])  # Single group

        with patch.object(pre_populated_cache, 'get_cross_section') as mock_get:
            energy = np.logspace(5, 7, 100)
            xs = np.ones_like(energy) * 10.0
            mock_get.return_value = (energy, xs)

            with patch.object(CrossSectionTable, '_collapse_to_multigroup',
                            return_value=np.array([10.0])) as mock_collapse:
                df = table.generate_multigroup(
                    nuclides=[u235],
                    reactions=["total"],
                    group_structure=group_structure,
                    temperature=900.0
                )

                # Should have 1 row (1 nuclide × 1 reaction × 1 group)
                assert len(df) == 1
                assert df['group'].unique().to_list() == [0]
                mock_collapse.assert_called_once()

    def test_generate_multigroup_none_cross_section(self, temp_dir, pre_populated_cache):
        """Test generate_multigroup when get_cross_section returns None."""
        from smrforge.core.reactor_core import CrossSectionTable, Nuclide

        table = CrossSectionTable()
        table._cache = pre_populated_cache

        u235 = Nuclide(Z=92, A=235, m=0)
        group_structure = np.array([1e7, 1e6, 1e5])

        with patch.object(pre_populated_cache, 'get_cross_section', return_value=(None, None)):
            # Should raise an error or handle gracefully
            with pytest.raises((ValueError, TypeError, AttributeError)):
                table.generate_multigroup(
                    nuclides=[u235],
                    reactions=["total"],
                    group_structure=group_structure,
                    temperature=900.0
                )

    def test_generate_multigroup_empty_cross_section(self, temp_dir, pre_populated_cache):
        """Test generate_multigroup with empty cross-section arrays."""
        from smrforge.core.reactor_core import CrossSectionTable, Nuclide

        table = CrossSectionTable()
        table._cache = pre_populated_cache

        u235 = Nuclide(Z=92, A=235, m=0)
        group_structure = np.array([1e7, 1e6, 1e5])

        with patch.object(pre_populated_cache, 'get_cross_section') as mock_get:
            mock_get.return_value = (np.array([]), np.array([]))

            # Should raise ValueError for empty arrays
            with pytest.raises(ValueError, match="Empty cross-section data"):
                table.generate_multigroup(
                    nuclides=[u235],
                    reactions=["total"],
                    group_structure=group_structure,
                    temperature=900.0
                )

    def test_generate_multigroup_mismatched_energy_xs(self, temp_dir, pre_populated_cache):
        """Test generate_multigroup with mismatched energy and xs arrays."""
        from smrforge.core.reactor_core import CrossSectionTable, Nuclide

        table = CrossSectionTable()
        table._cache = pre_populated_cache

        u235 = Nuclide(Z=92, A=235, m=0)
        group_structure = np.array([1e7, 1e6, 1e5])

        with patch.object(pre_populated_cache, 'get_cross_section') as mock_get:
            # Mismatched lengths
            mock_get.return_value = (np.array([1e5, 1e6, 1e7]), np.array([10.0, 20.0]))

            # Should be handled by _collapse_to_multigroup or raise error
            with patch.object(CrossSectionTable, '_collapse_to_multigroup') as mock_collapse:
                # Either handles it or raises error
                try:
                    table.generate_multigroup(
                        nuclides=[u235],
                        reactions=["total"],
                        group_structure=group_structure,
                        temperature=900.0
                    )
                except (ValueError, IndexError):
                    pass  # Expected behavior

    def test_generate_multigroup_very_large_group_structure(self, temp_dir, pre_populated_cache):
        """Test generate_multigroup with very large group structure."""
        from smrforge.core.reactor_core import CrossSectionTable, Nuclide

        table = CrossSectionTable()
        table._cache = pre_populated_cache

        u235 = Nuclide(Z=92, A=235, m=0)
        # Create 100-group structure
        group_structure = np.logspace(7, -5, 101)  # 100 groups

        with patch.object(pre_populated_cache, 'get_cross_section') as mock_get:
            energy = np.logspace(-5, 7, 1000)
            xs = np.ones_like(energy) * 10.0
            mock_get.return_value = (energy, xs)

            with patch.object(CrossSectionTable, '_collapse_to_multigroup',
                            return_value=np.ones(100) * 10.0):
                df = table.generate_multigroup(
                    nuclides=[u235],
                    reactions=["total"],
                    group_structure=group_structure,
                    temperature=900.0
                )

                # Should have 100 rows (1 nuclide × 1 reaction × 100 groups)
                assert len(df) == 100
                assert df['group'].max() == 99
                assert df['group'].min() == 0

    def test_generate_multigroup_weighting_flux_mismatch(self, temp_dir, pre_populated_cache):
        """Test generate_multigroup with weighting flux that doesn't match energy."""
        from smrforge.core.reactor_core import CrossSectionTable, Nuclide

        table = CrossSectionTable()
        table._cache = pre_populated_cache

        u235 = Nuclide(Z=92, A=235, m=0)
        group_structure = np.array([1e7, 1e6, 1e5])

        with patch.object(pre_populated_cache, 'get_cross_section') as mock_get:
            energy = np.logspace(4, 7, 100)
            xs = np.ones_like(energy) * 10.0
            mock_get.return_value = (energy, xs)

            # Weighting flux with different length
            weighting_flux = np.ones(50)  # Mismatched length

            # Should be handled by _collapse_to_multigroup
            with patch.object(CrossSectionTable, '_collapse_to_multigroup',
                            return_value=np.array([10.0, 10.0])) as mock_collapse:
                df = table.generate_multigroup(
                    nuclides=[u235],
                    reactions=["total"],
                    group_structure=group_structure,
                    temperature=900.0,
                    weighting_flux=weighting_flux
                )

                # Verify weighting_flux was passed (handling is in collapse method)
                call_args = mock_collapse.call_args
                assert call_args[0][3] is not None  # weighting_flux was passed

    def test_generate_multigroup_negative_temperature(self, temp_dir, pre_populated_cache):
        """Test generate_multigroup with negative temperature (should handle gracefully)."""
        from smrforge.core.reactor_core import CrossSectionTable, Nuclide

        table = CrossSectionTable()
        table._cache = pre_populated_cache

        u235 = Nuclide(Z=92, A=235, m=0)
        group_structure = np.array([1e7, 1e6, 1e5])

        with patch.object(pre_populated_cache, 'get_cross_section') as mock_get:
            energy = np.logspace(4, 7, 100)
            xs = np.ones_like(energy) * 10.0
            mock_get.return_value = (energy, xs)

            with patch.object(CrossSectionTable, '_collapse_to_multigroup',
                            return_value=np.array([10.0, 10.0])):
                # Should either work (temperature passed through) or raise error
                try:
                    df = table.generate_multigroup(
                        nuclides=[u235],
                        reactions=["total"],
                        group_structure=group_structure,
                        temperature=-100.0  # Invalid temperature
                    )
                    # If it works, verify structure
                    assert df is not None
                except (ValueError, AssertionError):
                    pass  # Expected if temperature validation exists

    def test_generate_multigroup_zero_temperature(self, temp_dir, pre_populated_cache):
        """Test generate_multigroup with zero temperature."""
        from smrforge.core.reactor_core import CrossSectionTable, Nuclide

        table = CrossSectionTable()
        table._cache = pre_populated_cache

        u235 = Nuclide(Z=92, A=235, m=0)
        group_structure = np.array([1e7, 1e6, 1e5])

        with patch.object(pre_populated_cache, 'get_cross_section') as mock_get:
            energy = np.logspace(4, 7, 100)
            xs = np.ones_like(energy) * 10.0
            mock_get.return_value = (energy, xs)

            with patch.object(CrossSectionTable, '_collapse_to_multigroup',
                            return_value=np.array([10.0, 10.0])):
                # Should handle zero temperature
                df = table.generate_multigroup(
                    nuclides=[u235],
                    reactions=["total"],
                    group_structure=group_structure,
                    temperature=0.0
                )
                assert df is not None

    def test_generate_multigroup_dataframe_persistence(self, temp_dir, pre_populated_cache):
        """Test that generate_multigroup updates table.data correctly."""
        from smrforge.core.reactor_core import CrossSectionTable, Nuclide

        table = CrossSectionTable()
        table._cache = pre_populated_cache

        u235 = Nuclide(Z=92, A=235, m=0)
        group_structure = np.array([1e7, 1e6, 1e5])

        with patch.object(pre_populated_cache, 'get_cross_section') as mock_get:
            energy = np.logspace(4, 7, 100)
            xs = np.ones_like(energy) * 10.0
            mock_get.return_value = (energy, xs)

            with patch.object(CrossSectionTable, '_collapse_to_multigroup',
                            return_value=np.array([10.0, 10.0])):
                df1 = table.generate_multigroup(
                    nuclides=[u235],
                    reactions=["total"],
                    group_structure=group_structure,
                    temperature=900.0
                )

                # Verify table.data is set
                assert table.data is not None
                assert table.data is df1

                # Generate again with different data
                with patch.object(CrossSectionTable, '_collapse_to_multigroup',
                                return_value=np.array([20.0, 20.0])):
                    df2 = table.generate_multigroup(
                        nuclides=[u235],
                        reactions=["total"],
                        group_structure=group_structure,
                        temperature=900.0
                    )

                    # table.data should be updated
                    assert table.data is df2
                    assert table.data is not df1

