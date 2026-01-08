"""
Comprehensive tests for uncertainty quantification module.

Tests cover:
- UncertainParameter validation and sampling
- MonteCarloSampler (MC, LHS, Sobol)
- UncertaintyPropagation
- SensitivityAnalysis (Sobol, Morris)
- VisualizationTools
"""

import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock

from smrforge.uncertainty.uq import (
    UncertainParameter,
    UQResults,
    MonteCarloSampler,
    UncertaintyPropagation,
    SensitivityAnalysis,
    VisualizationTools,
)


class TestUncertainParameter:
    """Test UncertainParameter class."""
    
    def test_parameter_creation_normal(self):
        """Test creating normal distribution parameter."""
        param = UncertainParameter(
            name="temperature",
            distribution="normal",
            nominal=500.0,
            uncertainty=50.0,  # std
            units="K",
            description="Core temperature",
        )
        assert param.name == "temperature"
        assert param.distribution == "normal"
        assert param.nominal == 500.0
        assert param.uncertainty == 50.0
        assert param.units == "K"
    
    def test_parameter_creation_uniform(self):
        """Test creating uniform distribution parameter."""
        param = UncertainParameter(
            name="pressure",
            distribution="uniform",
            nominal=15.0,
            uncertainty=(10.0, 20.0),  # (min, max)
        )
        assert param.distribution == "uniform"
        assert param.uncertainty == (10.0, 20.0)
    
    def test_parameter_creation_lognormal(self):
        """Test creating lognormal distribution parameter."""
        param = UncertainParameter(
            name="power",
            distribution="lognormal",
            nominal=100.0,
            uncertainty=0.1,  # relative std
        )
        assert param.distribution == "lognormal"
    
    def test_parameter_creation_triangular(self):
        """Test creating triangular distribution parameter."""
        param = UncertainParameter(
            name="efficiency",
            distribution="triangular",
            nominal=0.33,
            uncertainty=(0.30, 0.35),
        )
        assert param.distribution == "triangular"
    
    def test_parameter_validation_invalid_distribution(self):
        """Test validation with invalid distribution."""
        with pytest.raises(ValueError, match="distribution must be one of"):
            UncertainParameter(
                name="test",
                distribution="invalid",
                nominal=1.0,
                uncertainty=0.1,
            )
    
    def test_parameter_validation_empty_name(self):
        """Test validation with empty name."""
        with pytest.raises(ValueError, match="name must be non-empty string"):
            UncertainParameter(
                name="",
                distribution="normal",
                nominal=1.0,
                uncertainty=0.1,
            )
    
    def test_parameter_validation_normal_invalid_uncertainty(self):
        """Test validation with invalid uncertainty for normal."""
        with pytest.raises(ValueError, match="uncertainty must be float"):
            UncertainParameter(
                name="test",
                distribution="normal",
                nominal=1.0,
                uncertainty=(0.1, 0.2),  # Should be float
            )
        
        with pytest.raises(ValueError, match="uncertainty.*must be > 0"):
            UncertainParameter(
                name="test",
                distribution="normal",
                nominal=1.0,
                uncertainty=-0.1,  # Should be positive
            )
    
    def test_parameter_validation_uniform_invalid_uncertainty(self):
        """Test validation with invalid uncertainty for uniform."""
        with pytest.raises(ValueError, match="uncertainty must be tuple"):
            UncertainParameter(
                name="test",
                distribution="uniform",
                nominal=1.0,
                uncertainty=0.1,  # Should be tuple
            )
        
        with pytest.raises(ValueError, match="uncertainty\[0\] must be < uncertainty\[1\]"):
            UncertainParameter(
                name="test",
                distribution="uniform",
                nominal=1.0,
                uncertainty=(0.2, 0.1),  # min >= max
            )
    
    def test_parameter_validation_triangular_nominal_outside_bounds(self):
        """Test validation with nominal outside triangular bounds."""
        with pytest.raises(ValueError, match="nominal must be between uncertainty bounds"):
            UncertainParameter(
                name="test",
                distribution="triangular",
                nominal=0.5,
                uncertainty=(0.1, 0.2),  # nominal outside bounds
            )
    
    def test_parameter_sample_normal(self):
        """Test sampling from normal distribution."""
        param = UncertainParameter(
            name="test",
            distribution="normal",
            nominal=100.0,
            uncertainty=10.0,
        )
        samples = param.sample(n=1000, random_state=42)
        assert len(samples) == 1000
        assert np.isclose(np.mean(samples), 100.0, rtol=0.1)
        assert np.isclose(np.std(samples), 10.0, rtol=0.1)
    
    def test_parameter_sample_uniform(self):
        """Test sampling from uniform distribution."""
        param = UncertainParameter(
            name="test",
            distribution="uniform",
            nominal=15.0,
            uncertainty=(10.0, 20.0),
        )
        samples = param.sample(n=1000, random_state=42)
        assert len(samples) == 1000
        assert np.all(samples >= 10.0)
        assert np.all(samples <= 20.0)
    
    def test_parameter_sample_lognormal(self):
        """Test sampling from lognormal distribution."""
        param = UncertainParameter(
            name="test",
            distribution="lognormal",
            nominal=100.0,
            uncertainty=0.1,  # relative std
        )
        samples = param.sample(n=1000, random_state=42)
        assert len(samples) == 1000
        assert np.all(samples > 0)
    
    def test_parameter_sample_triangular(self):
        """Test sampling from triangular distribution."""
        param = UncertainParameter(
            name="test",
            distribution="triangular",
            nominal=15.0,
            uncertainty=(10.0, 20.0),
        )
        samples = param.sample(n=1000, random_state=42)
        assert len(samples) == 1000
        assert np.all(samples >= 10.0)
        assert np.all(samples <= 20.0)
    
    def test_parameter_sample_invalid_n(self):
        """Test sampling with invalid n."""
        param = UncertainParameter(
            name="test",
            distribution="normal",
            nominal=1.0,
            uncertainty=0.1,
        )
        with pytest.raises(ValueError, match="n must be > 0"):
            param.sample(n=0)
        
        with pytest.raises(ValueError, match="n must be > 0"):
            param.sample(n=-1)
    
    def test_parameter_sample_unknown_distribution(self):
        """Test sampling with unknown distribution (should not happen after validation)."""
        param = UncertainParameter(
            name="test",
            distribution="normal",
            nominal=1.0,
            uncertainty=0.1,
        )
        # Manually set invalid distribution (bypassing validation)
        param.distribution = "unknown"
        with pytest.raises(ValueError, match="Unknown distribution"):
            param.sample(n=10)
    
    def test_parameter_to_salib_format_uniform(self):
        """Test converting to SALib format for uniform distribution."""
        param = UncertainParameter(
            name="test",
            distribution="uniform",
            nominal=15.0,
            uncertainty=(10.0, 20.0),
        )
        salib_format = param.to_salib_format()
        assert salib_format["name"] == "test"
        assert salib_format["bounds"] == [10.0, 20.0]
    
    def test_parameter_to_salib_format_normal(self):
        """Test converting to SALib format for normal distribution."""
        param = UncertainParameter(
            name="test",
            distribution="normal",
            nominal=100.0,
            uncertainty=10.0,
        )
        salib_format = param.to_salib_format()
        assert salib_format["name"] == "test"
        assert salib_format["bounds"] == [70.0, 130.0]  # nominal ± 3*std
    
    def test_parameter_to_salib_format_other(self):
        """Test converting to SALib format for other distributions."""
        param = UncertainParameter(
            name="test",
            distribution="lognormal",
            nominal=100.0,
            uncertainty=0.1,
        )
        salib_format = param.to_salib_format()
        assert salib_format["name"] == "test"
        # Should use nominal ± 20%
        assert salib_format["bounds"][0] == pytest.approx(80.0)
        assert salib_format["bounds"][1] == pytest.approx(120.0)


class TestMonteCarloSampler:
    """Test MonteCarloSampler class."""
    
    def test_sampler_creation(self):
        """Test creating sampler."""
        params = [
            UncertainParameter("p1", "normal", 100.0, 10.0),
            UncertainParameter("p2", "uniform", 50.0, (40.0, 60.0)),
        ]
        sampler = MonteCarloSampler(params)
        assert len(sampler.parameters) == 2
        assert sampler.n_params == 2
    
    def test_sampler_creation_invalid_parameters_type(self):
        """Test creating sampler with invalid parameters type."""
        with pytest.raises(ValueError, match="parameters must be list"):
            MonteCarloSampler("not a list")
    
    def test_sampler_creation_empty_parameters(self):
        """Test creating sampler with empty parameters."""
        with pytest.raises(ValueError, match="parameters list cannot be empty"):
            MonteCarloSampler([])
    
    def test_sampler_creation_invalid_parameter_type(self):
        """Test creating sampler with invalid parameter type."""
        with pytest.raises(ValueError, match="must be UncertainParameter"):
            MonteCarloSampler(["not a parameter"])
    
    def test_sampler_monte_carlo(self):
        """Test Monte Carlo sampling."""
        params = [
            UncertainParameter("p1", "normal", 100.0, 10.0),
            UncertainParameter("p2", "uniform", 50.0, (40.0, 60.0)),
        ]
        sampler = MonteCarloSampler(params)
        samples = sampler.sample_monte_carlo(n_samples=100, random_state=42)
        assert samples.shape == (100, 2)
        assert np.all(samples[:, 0] > 0)  # Normal should be mostly positive
        assert np.all(samples[:, 1] >= 40.0)
        assert np.all(samples[:, 1] <= 60.0)
    
    def test_sampler_monte_carlo_invalid_n_samples(self):
        """Test Monte Carlo sampling with invalid n_samples."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        sampler = MonteCarloSampler(params)
        with pytest.raises(ValueError, match="n_samples must be > 0"):
            sampler.sample_monte_carlo(n_samples=0)
    
    def test_sampler_latin_hypercube(self):
        """Test Latin Hypercube sampling."""
        params = [
            UncertainParameter("p1", "normal", 100.0, 10.0),
            UncertainParameter("p2", "uniform", 50.0, (40.0, 60.0)),
        ]
        sampler = MonteCarloSampler(params)
        samples = sampler.sample_latin_hypercube(n_samples=100, random_state=42)
        assert samples.shape == (100, 2)
    
    def test_sampler_latin_hypercube_invalid_n_samples(self):
        """Test Latin Hypercube sampling with invalid n_samples."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        sampler = MonteCarloSampler(params)
        with pytest.raises(ValueError, match="n_samples must be > 0"):
            sampler.sample_latin_hypercube(n_samples=0)
    
    def test_sampler_sobol_sequence(self):
        """Test Sobol sequence sampling."""
        params = [
            UncertainParameter("p1", "normal", 100.0, 10.0),
            UncertainParameter("p2", "uniform", 50.0, (40.0, 60.0)),
        ]
        sampler = MonteCarloSampler(params)
        samples = sampler.sample_sobol_sequence(n_samples=100, random_state=42)
        assert samples.shape == (100, 2)
    
    def test_sampler_sobol_sequence_invalid_n_samples(self):
        """Test Sobol sequence sampling with invalid n_samples."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        sampler = MonteCarloSampler(params)
        with pytest.raises(ValueError, match="n_samples must be > 0"):
            sampler.sample_sobol_sequence(n_samples=0)


class TestUncertaintyPropagation:
    """Test UncertaintyPropagation class."""
    
    def test_propagation_creation(self):
        """Test creating propagation object."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        
        def model(params_dict):
            return {"output": params_dict["p1"] * 2}
        
        propagation = UncertaintyPropagation(
            parameters=params,
            model=model,
            output_names=["output"],
        )
        assert len(propagation.parameters) == 1
        assert len(propagation.output_names) == 1
    
    def test_propagation_creation_invalid_parameters(self):
        """Test creating propagation with invalid parameters."""
        def model(params_dict):
            return {"output": 1.0}
        
        with pytest.raises(ValueError, match="parameters must be non-empty list"):
            UncertaintyPropagation(
                parameters=[],
                model=model,
                output_names=["output"],
            )
    
    def test_propagation_creation_invalid_model(self):
        """Test creating propagation with invalid model."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        
        with pytest.raises(ValueError, match="model must be callable"):
            UncertaintyPropagation(
                parameters=params,
                model="not callable",
                output_names=["output"],
            )
    
    def test_propagation_creation_invalid_output_names(self):
        """Test creating propagation with invalid output_names."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        def model(params_dict):
            return {"output": 1.0}
        
        with pytest.raises(ValueError, match="output_names must be non-empty list"):
            UncertaintyPropagation(
                parameters=params,
                model=model,
                output_names=[],
            )
        
        with pytest.raises(ValueError, match="must be non-empty string"):
            UncertaintyPropagation(
                parameters=params,
                model=model,
                output_names=[""],
            )
    
    def test_propagation_propagate_mc(self):
        """Test uncertainty propagation with Monte Carlo."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        
        def model(params_dict):
            return {"output": params_dict["p1"] * 2}
        
        propagation = UncertaintyPropagation(
            parameters=params,
            model=model,
            output_names=["output"],
        )
        
        results = propagation.propagate(n_samples=100, method="mc", random_state=42)
        assert isinstance(results, UQResults)
        assert results.parameter_samples.shape == (100, 1)
        assert results.output_samples.shape == (100, 1)
        assert results.mean is not None
        assert results.std is not None
        assert results.percentiles is not None
    
    def test_propagation_propagate_lhs(self):
        """Test uncertainty propagation with Latin Hypercube."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        
        def model(params_dict):
            return {"output": params_dict["p1"] * 2}
        
        propagation = UncertaintyPropagation(
            parameters=params,
            model=model,
            output_names=["output"],
        )
        
        results = propagation.propagate(n_samples=100, method="lhs", random_state=42)
        assert isinstance(results, UQResults)
        assert results.parameter_samples.shape == (100, 1)
        assert results.output_samples.shape == (100, 1)
    
    def test_propagation_propagate_sobol(self):
        """Test uncertainty propagation with Sobol sequence."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        
        def model(params_dict):
            return {"output": params_dict["p1"] * 2}
        
        propagation = UncertaintyPropagation(
            parameters=params,
            model=model,
            output_names=["output"],
        )
        
        results = propagation.propagate(n_samples=100, method="sobol", random_state=42)
        assert isinstance(results, UQResults)
        assert results.parameter_samples.shape == (100, 1)
        assert results.output_samples.shape == (100, 1)
    
    def test_propagation_propagate_invalid_n_samples(self):
        """Test propagation with invalid n_samples."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        def model(params_dict):
            return {"output": 1.0}
        
        propagation = UncertaintyPropagation(
            parameters=params,
            model=model,
            output_names=["output"],
        )
        
        with pytest.raises(ValueError, match="n_samples must be > 0"):
            propagation.propagate(n_samples=0)
    
    def test_propagation_propagate_invalid_method(self):
        """Test propagation with invalid method."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        def model(params_dict):
            return {"output": 1.0}
        
        propagation = UncertaintyPropagation(
            parameters=params,
            model=model,
            output_names=["output"],
        )
        
        with pytest.raises(ValueError, match="method must be one of"):
            propagation.propagate(n_samples=10, method="invalid")
    
    def test_propagation_propagate_model_returns_array(self):
        """Test propagation when model returns array instead of dict."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        
        def model(params_dict):
            return np.array([params_dict["p1"] * 2])
        
        propagation = UncertaintyPropagation(
            parameters=params,
            model=model,
            output_names=["output"],
        )
        
        results = propagation.propagate(n_samples=10, method="mc", random_state=42)
        assert results.output_samples.shape == (10, 1)
    
    def test_propagation_propagate_model_raises_exception(self):
        """Test propagation when model raises exception."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        
        def model(params_dict):
            raise ValueError("Model error")
        
        propagation = UncertaintyPropagation(
            parameters=params,
            model=model,
            output_names=["output"],
        )
        
        with pytest.raises(RuntimeError, match="Model evaluation failed"):
            propagation.propagate(n_samples=10, method="mc", random_state=42)
    
    def test_propagation_propagate_missing_output(self):
        """Test propagation when model result is missing output."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        
        def model(params_dict):
            return {}  # Missing output
        
        propagation = UncertaintyPropagation(
            parameters=params,
            model=model,
            output_names=["output"],
        )
        
        with pytest.raises(RuntimeError, match="missing outputs"):
            propagation.propagate(n_samples=10, method="mc", random_state=42)
    
    def test_propagation_propagate_wrong_shape(self):
        """Test propagation when model result has wrong shape."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        
        def model(params_dict):
            return np.array([1.0, 2.0])  # Wrong shape - should be (1,)
        
        propagation = UncertaintyPropagation(
            parameters=params,
            model=model,
            output_names=["output"],
        )
        
        with pytest.raises(RuntimeError, match="Model result shape"):
            propagation.propagate(n_samples=10, method="mc", random_state=42)


class TestSensitivityAnalysis:
    """Test SensitivityAnalysis class."""
    
    def test_sensitivity_creation(self):
        """Test creating sensitivity analysis object."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        
        def model(params_dict):
            return {"output": params_dict["p1"] * 2}
        
        analysis = SensitivityAnalysis(
            parameters=params,
            model=model,
            output_names=["output"],
        )
        assert len(analysis.parameters) == 1
        assert len(analysis.output_names) == 1
    
    def test_sensitivity_creation_invalid_parameters(self):
        """Test creating sensitivity analysis with invalid parameters."""
        def model(params_dict):
            return {"output": 1.0}
        
        with pytest.raises(ValueError, match="parameters must be non-empty list"):
            SensitivityAnalysis(
                parameters=[],
                model=model,
                output_names=["output"],
            )
    
    def test_sensitivity_creation_invalid_model(self):
        """Test creating sensitivity analysis with invalid model."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        
        with pytest.raises(ValueError, match="model must be callable"):
            SensitivityAnalysis(
                parameters=params,
                model="not callable",
                output_names=["output"],
            )
    
    def test_sensitivity_sobol_analysis_no_salib(self):
        """Test Sobol analysis when SALib is not available."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        def model(params_dict):
            return {"output": 1.0}
        
        analysis = SensitivityAnalysis(
            parameters=params,
            model=model,
            output_names=["output"],
        )
        
        with patch("smrforge.uncertainty.uq._SALIB_AVAILABLE", False):
            with pytest.raises(ImportError, match="SALib is required"):
                analysis.sobol_analysis(n_samples=10)
    
    def test_sensitivity_sobol_analysis_invalid_n_samples(self):
        """Test Sobol analysis with invalid n_samples."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        def model(params_dict):
            return {"output": 1.0}
        
        analysis = SensitivityAnalysis(
            parameters=params,
            model=model,
            output_names=["output"],
        )
        
        with pytest.raises(ValueError, match="n_samples must be > 0"):
            analysis.sobol_analysis(n_samples=0)
    
    def test_sensitivity_morris_screening_no_salib(self):
        """Test Morris screening when SALib is not available."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        def model(params_dict):
            return {"output": 1.0}
        
        analysis = SensitivityAnalysis(
            parameters=params,
            model=model,
            output_names=["output"],
        )
        
        with patch("smrforge.uncertainty.uq._SALIB_AVAILABLE", False):
            with pytest.raises(ImportError, match="SALib is required"):
                analysis.morris_screening(n_trajectories=10)
    
    def test_sensitivity_morris_screening_invalid_n_trajectories(self):
        """Test Morris screening with invalid n_trajectories."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        def model(params_dict):
            return {"output": 1.0}
        
        analysis = SensitivityAnalysis(
            parameters=params,
            model=model,
            output_names=["output"],
        )
        
        with pytest.raises(ValueError, match="n_trajectories must be > 0"):
            analysis.morris_screening(n_trajectories=0)
    
    def test_sensitivity_morris_screening_invalid_n_levels(self):
        """Test Morris screening with invalid n_levels."""
        params = [UncertainParameter("p1", "normal", 100.0, 10.0)]
        def model(params_dict):
            return {"output": 1.0}
        
        analysis = SensitivityAnalysis(
            parameters=params,
            model=model,
            output_names=["output"],
        )
        
        with pytest.raises(ValueError, match="n_levels must be >= 2"):
            analysis.morris_screening(n_trajectories=10, n_levels=1)


class TestUQResults:
    """Test UQResults dataclass."""
    
    def test_results_creation(self):
        """Test creating UQResults."""
        results = UQResults(
            parameter_names=["p1", "p2"],
            parameter_samples=np.random.rand(10, 2),
            output_samples=np.random.rand(10, 1),
            output_names=["output"],
            mean=np.array([1.0]),
            std=np.array([0.1]),
            percentiles={5: np.array([0.9]), 95: np.array([1.1])},
        )
        assert len(results.parameter_names) == 2
        assert results.parameter_samples.shape == (10, 2)
        assert results.output_samples.shape == (10, 1)
        assert results.mean is not None
        assert results.std is not None


class TestVisualizationTools:
    """Test VisualizationTools class."""
    
    def test_plot_distributions_invalid_results_type(self):
        """Test plot_distributions with invalid results type."""
        with pytest.raises(ValueError, match="results must be UQResults"):
            VisualizationTools.plot_distributions("not UQResults")
    
    def test_plot_distributions_invalid_output_idx(self):
        """Test plot_distributions with invalid output_idx."""
        results = UQResults(
            parameter_names=["p1"],
            parameter_samples=np.random.rand(10, 1),
            output_samples=np.random.rand(10, 1),
            output_names=["output"],
            mean=np.array([1.0]),
            percentiles={5: np.array([0.9]), 95: np.array([1.1])},
        )
        
        with pytest.raises(ValueError, match="output_idx must be in"):
            VisualizationTools.plot_distributions(results, output_idx=10)
    
    def test_plot_distributions_empty_samples(self):
        """Test plot_distributions with empty samples."""
        results = UQResults(
            parameter_names=["p1"],
            parameter_samples=np.array([]).reshape(0, 1),
            output_samples=np.array([]).reshape(0, 1),
            output_names=["output"],
        )
        
        with pytest.raises(ValueError, match="output_samples is empty"):
            VisualizationTools.plot_distributions(results)
    
    def test_plot_distributions_missing_statistics(self):
        """Test plot_distributions without computed statistics."""
        results = UQResults(
            parameter_names=["p1"],
            parameter_samples=np.random.rand(10, 1),
            output_samples=np.random.rand(10, 1),
            output_names=["output"],
        )
        
        with pytest.raises(ValueError, match="must have computed statistics"):
            VisualizationTools.plot_distributions(results)
    
    def test_plot_scatter_matrix_invalid_results_type(self):
        """Test plot_scatter_matrix with invalid results type."""
        with pytest.raises(ValueError, match="results must be UQResults"):
            VisualizationTools.plot_scatter_matrix("not UQResults")
    
    def test_plot_scatter_matrix_invalid_output_idx(self):
        """Test plot_scatter_matrix with invalid output_idx."""
        results = UQResults(
            parameter_names=["p1"],
            parameter_samples=np.random.rand(10, 1),
            output_samples=np.random.rand(10, 1),
            output_names=["output"],
        )
        
        with pytest.raises(ValueError, match="output_idx must be in"):
            VisualizationTools.plot_scatter_matrix(results, output_idx=10)
    
    def test_plot_scatter_matrix_invalid_max_params(self):
        """Test plot_scatter_matrix with invalid max_params."""
        results = UQResults(
            parameter_names=["p1"],
            parameter_samples=np.random.rand(10, 1),
            output_samples=np.random.rand(10, 1),
            output_names=["output"],
        )
        
        with pytest.raises(ValueError, match="max_params must be > 0"):
            VisualizationTools.plot_scatter_matrix(results, max_params=0)
    
    def test_plot_scatter_matrix_empty_parameter_samples(self):
        """Test plot_scatter_matrix with empty parameter samples."""
        results = UQResults(
            parameter_names=["p1"],
            parameter_samples=np.array([]).reshape(0, 1),
            output_samples=np.random.rand(10, 1),
            output_names=["output"],
        )
        
        with pytest.raises(ValueError, match="parameter_samples is empty"):
            VisualizationTools.plot_scatter_matrix(results)
    
    def test_plot_scatter_matrix_no_seaborn(self):
        """Test plot_scatter_matrix when seaborn is not available."""
        results = UQResults(
            parameter_names=["p1"],
            parameter_samples=np.random.rand(10, 1),
            output_samples=np.random.rand(10, 1),
            output_names=["output"],
        )
        
        with patch("smrforge.uncertainty.uq.sns", None):
            with pytest.raises(ImportError, match="seaborn is required"):
                VisualizationTools.plot_scatter_matrix(results)
    
    def test_plot_sobol_indices_invalid_results_type(self):
        """Test plot_sobol_indices with invalid results type."""
        with pytest.raises(ValueError, match="sobol_results must be dict"):
            VisualizationTools.plot_sobol_indices("not dict", "output", ["p1"])
    
    def test_plot_sobol_indices_missing_output(self):
        """Test plot_sobol_indices with missing output."""
        sobol_results = {"output1": {"S1": [0.1], "ST": [0.2]}}
        
        with pytest.raises(ValueError, match="not in sobol_results"):
            VisualizationTools.plot_sobol_indices(sobol_results, "output2", ["p1"])
    
    def test_plot_sobol_indices_invalid_parameter_names(self):
        """Test plot_sobol_indices with invalid parameter_names."""
        sobol_results = {"output": {"S1": [0.1, 0.2], "ST": [0.3, 0.4]}}
        
        with pytest.raises(ValueError, match="parameter_names must be non-empty list"):
            VisualizationTools.plot_sobol_indices(sobol_results, "output", [])
    
    def test_plot_sobol_indices_missing_keys(self):
        """Test plot_sobol_indices with missing S1 or ST keys."""
        sobol_results = {"output": {"S1": [0.1]}}  # Missing ST
        
        with pytest.raises(ValueError, match="must contain 'S1' and 'ST' keys"):
            VisualizationTools.plot_sobol_indices(sobol_results, "output", ["p1"])
    
    def test_plot_sobol_indices_length_mismatch(self):
        """Test plot_sobol_indices with length mismatch."""
        sobol_results = {"output": {"S1": [0.1, 0.2], "ST": [0.3, 0.4]}}
        
        with pytest.raises(ValueError, match="Length mismatch"):
            VisualizationTools.plot_sobol_indices(sobol_results, "output", ["p1"])
