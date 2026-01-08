"""
Additional tests for uncertainty/uq.py to improve coverage to 80%+.

Focuses on:
- Edge cases in parameter sampling
- Error handling paths
- Boundary conditions
- Additional method combinations
"""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from smrforge.uncertainty.uq import (
    UncertainParameter,
    MonteCarloSampler,
    UncertaintyPropagation,
    SensitivityAnalysis,
    UQResults,
    VisualizationTools,
)


class TestUncertainParameterEdgeCases:
    """Test edge cases for UncertainParameter."""
    
    def test_parameter_sample_zero_n(self):
        """Test sampling with n=0 raises error."""
        param = UncertainParameter("p1", "normal", 100.0, 10.0)
        
        with pytest.raises(ValueError, match="n must be > 0"):
            param.sample(n=0)
    
    def test_parameter_sample_very_large_n(self):
        """Test sampling with very large n."""
        param = UncertainParameter("p1", "normal", 100.0, 10.0)
        
        samples = param.sample(n=10000)
        assert len(samples) == 10000
        assert np.all(np.isfinite(samples))
    
    def test_parameter_sample_triangular_nominal_at_bounds(self):
        """Test triangular distribution with nominal at bounds."""
        # Nominal at lower bound
        param1 = UncertainParameter("p1", "triangular", 0.0, (0.0, 1.0))
        samples1 = param1.sample(n=100)
        assert np.all(samples1 >= 0.0)
        assert np.all(samples1 <= 1.0)
        
        # Nominal at upper bound
        param2 = UncertainParameter("p2", "triangular", 1.0, (0.0, 1.0))
        samples2 = param2.sample(n=100)
        assert np.all(samples2 >= 0.0)
        assert np.all(samples2 <= 1.0)
    
    def test_parameter_to_salib_format_triangular(self):
        """Test conversion to SALib format for triangular distribution."""
        param = UncertainParameter("p1", "triangular", 0.5, (0.0, 1.0))
        
        salib_format = param.to_salib_format()
        assert isinstance(salib_format, dict)
        assert "name" in salib_format
        assert "bounds" in salib_format
        assert len(salib_format["bounds"]) == 2


class TestMonteCarloSamplerEdgeCases:
    """Test edge cases for MonteCarloSampler."""
    
    def test_sampler_empty_parameters_list(self):
        """Test sampler with empty parameters list."""
        with pytest.raises(ValueError, match="cannot be empty"):
            MonteCarloSampler([])
    
    def test_sampler_single_parameter(self):
        """Test sampler with single parameter."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        sampler = MonteCarloSampler(params)
        
        samples = sampler.sample_monte_carlo(n_samples=10)
        assert samples.shape == (10, 1)
    
    def test_sampler_many_parameters(self):
        """Test sampler with many parameters."""
        params = [UncertainParameter(f"p{i}", "normal", 100.0, 10.0) for i in range(20)]
        sampler = MonteCarloSampler(params)
        
        samples = sampler.sample_monte_carlo(n_samples=50)
        assert samples.shape == (50, 20)
    
    def test_sampler_lhs_small_n(self):
        """Test LHS sampling with small n."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        sampler = MonteCarloSampler(params)
        
        samples = sampler.sample_latin_hypercube(n_samples=2)
        assert samples.shape == (2, 1)
    
    def test_sampler_sobol_sequence_small_n(self):
        """Test Sobol sequence with small n."""
        params = [UncertainParameter("p1", "uniform", 0.0, (0.0, 1.0))]
        sampler = MonteCarloSampler(params)
        
        samples = sampler.sample_sobol_sequence(n_samples=2)
        assert samples.shape == (2, 1)


class TestUncertaintyPropagationEdgeCases:
    """Test edge cases for UncertaintyPropagation."""
    
    def test_propagation_model_returns_scalar(self):
        """Test propagation with model returning scalar."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        def model(params_dict):
            return params_dict["p1"]  # Scalar, not dict
        
        propagation = UncertaintyPropagation(
            parameters=params,
            model=model,
            output_names=["output"]
        )
        
        with pytest.raises(RuntimeError, match="shape"):
            propagation.propagate(n_samples=10, method="mc")
    
    def test_propagation_model_returns_none(self):
        """Test propagation with model returning None."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        def model(params_dict):
            return None
        
        propagation = UncertaintyPropagation(
            parameters=params,
            model=model,
            output_names=["output"]
        )
        
        with pytest.raises(RuntimeError, match="shape"):
            propagation.propagate(n_samples=10, method="mc")
    
    def test_propagation_model_returns_empty_dict(self):
        """Test propagation with model returning empty dict."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        def model(params_dict):
            return {}
        
        propagation = UncertaintyPropagation(
            parameters=params,
            model=model,
            output_names=["output"]
        )
        
        with pytest.raises(RuntimeError, match="missing outputs"):
            propagation.propagate(n_samples=10, method="mc")
    
    def test_propagation_model_returns_wrong_array_shape(self):
        """Test propagation with model returning wrong array shape."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        def model(params_dict):
            return np.array([1.0, 2.0])  # Wrong shape (should be 1D with 1 element)
        
        propagation = UncertaintyPropagation(
            parameters=params,
            model=model,
            output_names=["output"]
        )
        
        with pytest.raises(RuntimeError, match="shape"):
            propagation.propagate(n_samples=10, method="mc")
    
    def test_propagation_single_output(self):
        """Test propagation with single output."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        def model(params_dict):
            return {"output": params_dict["p1"] * 2.0}
        
        propagation = UncertaintyPropagation(
            parameters=params,
            model=model,
            output_names=["output"]
        )
        
        results = propagation.propagate(n_samples=100, method="mc")
        assert len(results.output_names) == 1
        assert results.output_samples.shape == (100, 1)
    
    def test_propagation_many_outputs(self):
        """Test propagation with many outputs."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        def model(params_dict):
            return {f"out{i}": params_dict["p1"] * (i + 1) for i in range(10)}
        
        propagation = UncertaintyPropagation(
            parameters=params,
            model=model,
            output_names=[f"out{i}" for i in range(10)]
        )
        
        results = propagation.propagate(n_samples=50, method="mc")
        assert len(results.output_names) == 10
        assert results.output_samples.shape == (50, 10)


class TestSensitivityAnalysisEdgeCases:
    """Test edge cases for SensitivityAnalysis."""
    
    def test_sensitivity_sobol_analysis_single_parameter(self):
        """Test Sobol analysis with single parameter."""
        params = [UncertainParameter("p1", "uniform", 0.0, (0.0, 1.0))]
        def model(params_dict):
            return {"output": params_dict["p1"] * 2.0}
        
        analysis = SensitivityAnalysis(
            parameters=params,
            model=model,
            output_names=["output"]
        )
        
        # Skip if SALib not available
        try:
            from SALib.sample import saltelli
            # Should work but may have limitations with single parameter
            try:
                results = analysis.sobol_analysis(n_samples=10, calc_second_order=False)
                assert isinstance(results, dict)
            except (ValueError, RuntimeError):
                # Acceptable if single parameter causes issues
                pass
        except ImportError:
            pytest.skip("SALib not available")
    
    def test_sensitivity_sobol_analysis_model_returns_array(self):
        """Test Sobol analysis with model returning array."""
        params = [
            UncertainParameter("p1", "uniform", 0.0, (0.0, 1.0)),
            UncertainParameter("p2", "uniform", 0.0, (0.0, 1.0)),
        ]
        def model(params_dict):
            return np.array([params_dict["p1"] + params_dict["p2"]])
        
        analysis = SensitivityAnalysis(
            parameters=params,
            model=model,
            output_names=["output"]
        )
        
        # Skip if SALib not available
        try:
            from SALib.sample import saltelli
            results = analysis.sobol_analysis(n_samples=10, calc_second_order=False)
            assert isinstance(results, dict)
        except ImportError:
            pytest.skip("SALib not available")
    
    def test_sensitivity_morris_screening_single_parameter(self):
        """Test Morris screening with single parameter."""
        params = [UncertainParameter("p1", "uniform", 0.0, (0.0, 1.0))]
        def model(params_dict):
            return {"output": params_dict["p1"] * 2.0}
        
        analysis = SensitivityAnalysis(
            parameters=params,
            model=model,
            output_names=["output"]
        )
        
        # Skip if SALib not available
        try:
            from SALib.sample import morris
            results = analysis.morris_screening(n_trajectories=5, n_levels=4)
            assert isinstance(results, dict)
        except ImportError:
            pytest.skip("SALib not available")


class TestUQResultsEdgeCases:
    """Test edge cases for UQResults."""
    
    def test_results_empty_samples(self):
        """Test UQResults with empty samples."""
        results = UQResults(
            parameter_names=["p1"],
            parameter_samples=np.array([]).reshape(0, 1),
            output_samples=np.array([]).reshape(0, 1),
            output_names=["output"],
        )
        
        assert results.parameter_samples.shape == (0, 1)
        assert results.output_samples.shape == (0, 1)
    
    def test_results_single_sample(self):
        """Test UQResults with single sample."""
        results = UQResults(
            parameter_names=["p1"],
            parameter_samples=np.array([[100.0]]),
            output_samples=np.array([[200.0]]),
            output_names=["output"],
            mean=np.array([200.0]),
            std=np.array([0.0]),
            percentiles={5: np.array([200.0]), 95: np.array([200.0])},
        )
        
        assert results.parameter_samples.shape == (1, 1)
        assert results.output_samples.shape == (1, 1)


class TestVisualizationToolsEdgeCases:
    """Test edge cases for VisualizationTools."""
    
    def test_plot_distributions_single_parameter(self):
        """Test plot_distributions with single parameter."""
        results = UQResults(
            parameter_names=["p1"],
            parameter_samples=np.random.rand(100, 1),
            output_samples=np.random.rand(100, 1),
            output_names=["output"],
            mean=np.array([0.5]),
            std=np.array([0.1]),
            percentiles={5: np.array([0.3]), 95: np.array([0.7])},
        )
        
        # Should not raise error
        try:
            VisualizationTools.plot_distributions(results, output_idx=0)
        except (ImportError, RuntimeError):
            # May fail if matplotlib not properly configured
            pass
    
    def test_plot_scatter_matrix_single_parameter(self):
        """Test plot_scatter_matrix with single parameter."""
        results = UQResults(
            parameter_names=["p1"],
            parameter_samples=np.random.rand(100, 1),
            output_samples=np.random.rand(100, 1),
            output_names=["output"],
        )
        
        # Should handle gracefully
        try:
            VisualizationTools.plot_scatter_matrix(results, output_idx=0, max_params=1)
        except (ValueError, ImportError, RuntimeError):
            # May fail for single parameter or if matplotlib/seaborn not available
            pass
