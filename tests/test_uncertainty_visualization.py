"""
Tests for uncertainty visualization tools.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for tests

import numpy as np
import pytest

from smrforge.uncertainty.uq import UQResults, VisualizationTools


@pytest.fixture
def sample_uq_results():
    """Create sample UQResults for testing."""
    n_samples = 100
    n_params = 3
    n_outputs = 2

    # Generate sample data
    np.random.seed(42)
    param_samples = np.random.randn(n_samples, n_params)
    output_samples = np.random.randn(n_samples, n_outputs) * 10 + 100

    mean = np.mean(output_samples, axis=0)
    std = np.std(output_samples, axis=0)
    percentiles = {
        5: np.percentile(output_samples, 5, axis=0),
        25: np.percentile(output_samples, 25, axis=0),
        50: np.percentile(output_samples, 50, axis=0),
        75: np.percentile(output_samples, 75, axis=0),
        95: np.percentile(output_samples, 95, axis=0),
    }

    return UQResults(
        parameter_names=["param1", "param2", "param3"],
        parameter_samples=param_samples,
        output_samples=output_samples,
        output_names=["output1", "output2"],
        mean=mean,
        std=std,
        percentiles=percentiles,
    )


class TestVisualizationTools:
    """Test VisualizationTools class."""

    def test_plot_distributions(self, sample_uq_results):
        """Test plot_distributions method."""
        fig = VisualizationTools.plot_distributions(sample_uq_results, output_idx=0)

        assert fig is not None
        # Clean up
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_distributions_invalid_results(self):
        """Test that invalid results raises ValueError."""
        with pytest.raises(ValueError, match="results must be UQResults"):
            VisualizationTools.plot_distributions(None)

    def test_plot_distributions_invalid_output_idx(self, sample_uq_results):
        """Test that invalid output_idx raises ValueError."""
        with pytest.raises(ValueError, match="output_idx must be in"):
            VisualizationTools.plot_distributions(sample_uq_results, output_idx=10)

        with pytest.raises(ValueError, match="output_idx must be in"):
            VisualizationTools.plot_distributions(sample_uq_results, output_idx=-1)

    def test_plot_distributions_empty_samples(self):
        """Test that empty samples raises ValueError."""
        results = UQResults(
            parameter_names=["param1"],
            parameter_samples=np.array([]),
            output_samples=np.array([]),
            output_names=["output1"],
            mean=None,
            std=None,
            percentiles=None,
        )

        with pytest.raises(ValueError, match="results.output_samples is empty"):
            VisualizationTools.plot_distributions(results)

    def test_plot_distributions_missing_statistics(self):
        """Test that missing statistics raises ValueError."""
        results = UQResults(
            parameter_names=["param1"],
            parameter_samples=np.random.randn(10, 1),
            output_samples=np.random.randn(10, 1),
            output_names=["output1"],
            mean=None,  # Missing
            std=None,
            percentiles=None,
        )

        with pytest.raises(ValueError, match="results must have computed statistics"):
            VisualizationTools.plot_distributions(results)

    def test_plot_scatter_matrix(self, sample_uq_results):
        """Test plot_scatter_matrix method."""
        fig = VisualizationTools.plot_scatter_matrix(sample_uq_results, max_params=2)
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig.fig)

    def test_plot_scatter_matrix_invalid_results(self):
        """Test that invalid results raises ValueError."""
        with pytest.raises(ValueError, match="results must be UQResults"):
            VisualizationTools.plot_scatter_matrix(None)

    def test_plot_scatter_matrix_invalid_output_idx(self, sample_uq_results):
        """Test that invalid output_idx raises ValueError."""
        with pytest.raises(ValueError, match="output_idx must be in"):
            VisualizationTools.plot_scatter_matrix(sample_uq_results, output_idx=10)

    def test_plot_scatter_matrix_invalid_max_params(self, sample_uq_results):
        """Test that invalid max_params raises ValueError."""
        with pytest.raises(ValueError, match="max_params must be > 0"):
            VisualizationTools.plot_scatter_matrix(sample_uq_results, max_params=0)

    def test_plot_sobol_indices(self):
        """Test plot_sobol_indices method."""
        # Create mock Sobol results
        sobol_results = {
            "output1": {
                "S1": np.array([0.3, 0.5, 0.2]),
                "ST": np.array([0.4, 0.6, 0.3]),
            }
        }

        parameter_names = ["param1", "param2", "param3"]

        fig = VisualizationTools.plot_sobol_indices(
            sobol_results, "output1", parameter_names
        )

        assert fig is not None
        # Clean up
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_sobol_indices_invalid_results(self):
        """Test that invalid results raises ValueError."""
        with pytest.raises(ValueError, match="sobol_results must be dict"):
            VisualizationTools.plot_sobol_indices(None, "output1", ["param1"])

    def test_plot_sobol_indices_missing_output(self):
        """Test that missing output_name raises ValueError."""
        sobol_results = {
            "output1": {"S1": np.array([0.3]), "ST": np.array([0.4])}
        }

        with pytest.raises(ValueError, match="output_name.*not in sobol_results"):
            VisualizationTools.plot_sobol_indices(
                sobol_results, "nonexistent", ["param1"]
            )

    def test_plot_sobol_indices_invalid_parameter_names(self):
        """Test that invalid parameter_names raises ValueError."""
        sobol_results = {
            "output1": {"S1": np.array([0.3]), "ST": np.array([0.4])}
        }

        with pytest.raises(ValueError, match="parameter_names must be non-empty list"):
            VisualizationTools.plot_sobol_indices(sobol_results, "output1", [])

    def test_plot_sobol_indices_missing_keys(self):
        """Test that missing S1/ST keys raises ValueError."""
        sobol_results = {"output1": {}}  # Missing S1 and ST

        with pytest.raises(ValueError, match="must contain 'S1' and 'ST' keys"):
            VisualizationTools.plot_sobol_indices(
                sobol_results, "output1", ["param1"]
            )

    def test_plot_sobol_indices_length_mismatch(self):
        """Test that length mismatch raises ValueError."""
        sobol_results = {
            "output1": {
                "S1": np.array([0.3, 0.5]),  # 2 elements
                "ST": np.array([0.4, 0.6]),
            }
        }

        parameter_names = ["param1"]  # Only 1 element

        with pytest.raises(ValueError, match="Length mismatch"):
            VisualizationTools.plot_sobol_indices(
                sobol_results, "output1", parameter_names
            )

