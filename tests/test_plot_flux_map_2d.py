"""Tests for plot_flux_map_2d (Community tier tally visualization)."""

import numpy as np
import pytest


class TestPlotFluxMap2D:
    """Tests for plot_flux_map_2d."""

    def test_plot_flux_map_2d_plotly(self):
        """plot_flux_map_2d with plotly backend returns Figure."""
        from smrforge.visualization.tally_data import plot_flux_map_2d

        flux = np.random.rand(10, 15)
        fig = plot_flux_map_2d(flux, backend="plotly")
        assert fig is not None
        assert hasattr(fig, "data")

    def test_plot_flux_map_2d_matplotlib(self):
        """plot_flux_map_2d with matplotlib backend returns (fig, ax)."""
        from smrforge.visualization.tally_data import plot_flux_map_2d

        flux = np.random.rand(8, 12)
        result = plot_flux_map_2d(flux, backend="matplotlib")
        assert isinstance(result, tuple)
        assert len(result) == 2
        fig, ax = result
        assert fig is not None
        assert ax is not None

    def test_plot_flux_map_2d_with_coords(self):
        """plot_flux_map_2d accepts r_coords and z_coords."""
        from smrforge.visualization.tally_data import plot_flux_map_2d

        flux = np.random.rand(5, 10)
        r = np.linspace(0, 50, 5)
        z = np.linspace(0, 200, 10)
        fig = plot_flux_map_2d(flux, r_coords=r, z_coords=z, backend="plotly")
        assert fig is not None

    def test_plot_flux_map_2d_raises_for_1d(self):
        """plot_flux_map_2d raises for 1D input."""
        from smrforge.visualization.tally_data import plot_flux_map_2d

        flux = np.array([1, 2, 3])
        with pytest.raises(ValueError, match="2D"):
            plot_flux_map_2d(flux, backend="plotly")
