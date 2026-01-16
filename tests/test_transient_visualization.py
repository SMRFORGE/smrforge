"""
Tests for transient visualization functions.
"""

import numpy as np
import pytest

# Test matplotlib availability
try:
    import matplotlib.pyplot as plt
    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False

# Test plotly availability
try:
    import plotly.graph_objects as go
    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False


class TestPlotTransient:
    """Test plot_transient function."""

    def test_plot_transient_plotly(self):
        """Test plotting transient with Plotly."""
        pytest.skip("Requires plotly installation and interactive display")

        if not _PLOTLY_AVAILABLE:
            pytest.skip("Plotly not available")

        from smrforge.visualization.transients import plot_transient

        # Create mock transient result
        time = np.linspace(0, 100, 1000)
        result = {
            "time": time,
            "power": 1e6 * np.exp(-time / 10.0),
            "T_fuel": 1200.0 + 100 * np.exp(-time / 50.0),
            "T_moderator": 800.0 + 50 * np.exp(-time / 50.0),
            "reactivity": 0.001 * np.exp(-time / 5.0),
        }

        # Test plotting (without display)
        fig = plot_transient(result, backend="plotly", show_plot=False)
        assert fig is not None

    @pytest.mark.skipif(not _MATPLOTLIB_AVAILABLE, reason="Matplotlib not available")
    def test_plot_transient_matplotlib(self):
        """Test plotting transient with Matplotlib."""
        from smrforge.visualization.transients import plot_transient

        # Create mock transient result
        time = np.linspace(0, 100, 1000)
        result = {
            "time": time,
            "power": 1e6 * np.exp(-time / 10.0),
            "T_fuel": 1200.0 + 100 * np.exp(-time / 50.0),
            "T_moderator": 800.0 + 50 * np.exp(-time / 50.0),
            "reactivity": 0.001 * np.exp(-time / 5.0),
        }

        # Test plotting (without display)
        fig = plot_transient(result, backend="matplotlib", show_plot=False)
        assert fig is not None
        plt.close(fig)

    def test_plot_transient_missing_data(self):
        """Test that missing required data raises error."""
        from smrforge.visualization.transients import plot_transient

        # Missing time
        with pytest.raises(ValueError):
            plot_transient({"power": [1e6]}, show_plot=False)

        # Missing power
        with pytest.raises(ValueError):
            plot_transient({"time": [0, 100]}, show_plot=False)

    def test_plot_transient_invalid_backend(self):
        """Test that invalid backend raises error."""
        from smrforge.visualization.transients import plot_transient

        result = {
            "time": [0, 100],
            "power": [1e6, 1e6],
        }

        with pytest.raises(ValueError):
            plot_transient(result, backend="invalid", show_plot=False)


class TestPlotLumpedThermal:
    """Test plot_lumped_thermal function."""

    def test_plot_lumped_thermal_plotly(self):
        """Test plotting lumped thermal with Plotly."""
        if not _PLOTLY_AVAILABLE:
            pytest.skip("Plotly not available")

        from smrforge.visualization.transients import plot_lumped_thermal

        # Create mock lumped thermal result
        time = np.linspace(0, 3600, 100)
        result = {
            "time": time,
            "T_fuel": 1200.0 + 100 * np.exp(-time / 1800.0),
            "T_moderator": 800.0 + 50 * np.exp(-time / 1800.0),
            "Q_fuel": 1e6 * np.exp(-time / 3600.0),
            "Q_moderator": np.zeros_like(time),
        }

        # Test plotting (without display)
        fig = plot_lumped_thermal(result, backend="plotly", show_plot=False)
        assert fig is not None

    @pytest.mark.skipif(not _MATPLOTLIB_AVAILABLE, reason="Matplotlib not available")
    def test_plot_lumped_thermal_matplotlib(self):
        """Test plotting lumped thermal with Matplotlib."""
        from smrforge.visualization.transients import plot_lumped_thermal

        # Create mock lumped thermal result
        time = np.linspace(0, 3600, 100)
        result = {
            "time": time,
            "T_fuel": 1200.0 + 100 * np.exp(-time / 1800.0),
            "T_moderator": 800.0 + 50 * np.exp(-time / 1800.0),
            "Q_fuel": 1e6 * np.exp(-time / 3600.0),
            "Q_moderator": np.zeros_like(time),
        }

        # Test plotting (without display)
        fig = plot_lumped_thermal(result, backend="matplotlib", show_plot=False)
        assert fig is not None
        plt.close(fig)

    def test_plot_lumped_thermal_missing_data(self):
        """Test that missing required data raises error."""
        from smrforge.visualization.transients import plot_lumped_thermal

        # Missing time
        with pytest.raises(ValueError):
            plot_lumped_thermal({"T_fuel": [1200.0]}, show_plot=False)

        # Missing temperature data
        with pytest.raises(ValueError):
            plot_lumped_thermal({"time": [0, 3600]}, show_plot=False)

    def test_plot_lumped_thermal_multiple_lumps(self):
        """Test plotting with multiple thermal lumps."""
        if not _MATPLOTLIB_AVAILABLE:
            pytest.skip("Matplotlib not available")

        from smrforge.visualization.transients import plot_lumped_thermal

        # Create mock result with multiple lumps
        time = np.linspace(0, 3600, 100)
        result = {
            "time": time,
            "T_fuel": 1200.0 * np.ones_like(time),
            "T_moderator": 800.0 * np.ones_like(time),
            "T_coolant": 600.0 * np.ones_like(time),
            "Q_fuel": 1e6 * np.ones_like(time),
        }

        # Test plotting (without display)
        fig = plot_lumped_thermal(result, backend="matplotlib", show_plot=False)
        assert fig is not None
        plt.close(fig)


class TestConvenienceIntegration:
    """Test visualization integration with convenience functions."""

    def test_quick_transient_with_plot(self):
        """Test quick_transient with plotting enabled."""
        pytest.skip("Requires full transient solver - integration test")

        # This would test the integration, but requires actual solver
        # which may be slow. Test manually or in integration tests.

    def test_import_visualization_functions(self):
        """Test that visualization functions can be imported."""
        from smrforge.visualization.transients import plot_transient, plot_lumped_thermal

        assert callable(plot_transient)
        assert callable(plot_lumped_thermal)
