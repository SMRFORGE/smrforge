"""
Comprehensive tests for uncertainty quantification module.
"""

import numpy as np
import pytest


@pytest.fixture
def simple_param():
    """Create a simple uncertain parameter for testing."""
    from smrforge.uncertainty.uq import UncertainParameter

    return UncertainParameter(
        name="test_param",
        distribution="normal",
        nominal=1.0,
        uncertainty=0.1,  # std
        units="dimensionless",
        description="Test parameter",
    )


@pytest.fixture
def simple_params():
    """Create a list of simple uncertain parameters."""
    from smrforge.uncertainty.uq import UncertainParameter

    return [
        UncertainParameter(
            name="param1",
            distribution="normal",
            nominal=1.0,
            uncertainty=0.1,
        ),
        UncertainParameter(
            name="param2",
            distribution="uniform",
            nominal=2.0,
            uncertainty=(1.5, 2.5),
        ),
    ]


@pytest.fixture
def simple_model():
    """Create a simple test model."""
    def model(params):
        """Simple linear model for testing."""
        p1 = params.get("param1", 1.0)
        p2 = params.get("param2", 2.0)
        return {
            "output1": p1 + p2,
            "output2": p1 * p2,
        }
    return model


class TestUncertainParameter:
    """Test UncertainParameter class."""

    def test_normal_distribution_creation(self):
        """Test creating parameter with normal distribution."""
        from smrforge.uncertainty.uq import UncertainParameter

        param = UncertainParameter(
            name="test",
            distribution="normal",
            nominal=1.0,
            uncertainty=0.1,
        )

        assert param.name == "test"
        assert param.distribution == "normal"
        assert param.nominal == 1.0
        assert param.uncertainty == 0.1

    def test_uniform_distribution_creation(self):
        """Test creating parameter with uniform distribution."""
        from smrforge.uncertainty.uq import UncertainParameter

        param = UncertainParameter(
            name="test",
            distribution="uniform",
            nominal=1.0,
            uncertainty=(0.5, 1.5),
        )

        assert param.distribution == "uniform"
        assert param.uncertainty == (0.5, 1.5)

    def test_lognormal_distribution_creation(self):
        """Test creating parameter with lognormal distribution."""
        from smrforge.uncertainty.uq import UncertainParameter

        param = UncertainParameter(
            name="test",
            distribution="lognormal",
            nominal=1.0,
            uncertainty=0.1,  # relative std
        )

        assert param.distribution == "lognormal"

    def test_triangular_distribution_creation(self):
        """Test creating parameter with triangular distribution."""
        from smrforge.uncertainty.uq import UncertainParameter

        param = UncertainParameter(
            name="test",
            distribution="triangular",
            nominal=1.0,
            uncertainty=(0.5, 1.5),
        )

        assert param.distribution == "triangular"

    def test_invalid_distribution(self):
        """Test that invalid distribution raises ValueError."""
        from smrforge.uncertainty.uq import UncertainParameter

        with pytest.raises(ValueError, match="distribution must be one of"):
            UncertainParameter(
                name="test",
                distribution="invalid",
                nominal=1.0,
                uncertainty=0.1,
            )

    def test_empty_name(self):
        """Test that empty name raises ValueError."""
        from smrforge.uncertainty.uq import UncertainParameter

        with pytest.raises(ValueError, match="name must be non-empty string"):
            UncertainParameter(
                name="",
                distribution="normal",
                nominal=1.0,
                uncertainty=0.1,
            )

    def test_invalid_uncertainty_for_normal(self):
        """Test that invalid uncertainty for normal raises ValueError."""
        from smrforge.uncertainty.uq import UncertainParameter

        # Tuple instead of float
        with pytest.raises(ValueError, match="uncertainty must be float"):
            UncertainParameter(
                name="test",
                distribution="normal",
                nominal=1.0,
                uncertainty=(0.5, 1.5),
            )

        # Negative std
        with pytest.raises(ValueError, match="uncertainty.*must be > 0"):
            UncertainParameter(
                name="test",
                distribution="normal",
                nominal=1.0,
                uncertainty=-0.1,
            )

    def test_invalid_uncertainty_for_uniform(self):
        """Test that invalid uncertainty for uniform raises ValueError."""
        from smrforge.uncertainty.uq import UncertainParameter

        # Float instead of tuple
        with pytest.raises(ValueError, match="uncertainty must be tuple"):
            UncertainParameter(
                name="test",
                distribution="uniform",
                nominal=1.0,
                uncertainty=0.1,
            )

        # min >= max
        with pytest.raises(ValueError, match="uncertainty\[0\] must be < uncertainty\[1\]"):
            UncertainParameter(
                name="test",
                distribution="uniform",
                nominal=1.0,
                uncertainty=(1.5, 0.5),
            )

    def test_invalid_nominal_for_triangular(self):
        """Test that nominal outside bounds for triangular raises ValueError."""
        from smrforge.uncertainty.uq import UncertainParameter

        with pytest.raises(ValueError, match="nominal must be between uncertainty bounds"):
            UncertainParameter(
                name="test",
                distribution="triangular",
                nominal=2.0,  # Outside bounds
                uncertainty=(0.5, 1.5),
            )

    def test_sample_normal(self, simple_param):
        """Test sampling from normal distribution."""
        samples = simple_param.sample(100, random_state=42)

        assert len(samples) == 100
        assert np.all(np.isfinite(samples))
        # Mean should be close to nominal
        assert np.isclose(np.mean(samples), simple_param.nominal, rtol=0.2)

    def test_sample_uniform(self):
        """Test sampling from uniform distribution."""
        from smrforge.uncertainty.uq import UncertainParameter

        param = UncertainParameter(
            name="test",
            distribution="uniform",
            nominal=1.0,
            uncertainty=(0.5, 1.5),
        )

        samples = param.sample(100, random_state=42)

        assert len(samples) == 100
        assert np.all(samples >= 0.5)
        assert np.all(samples <= 1.5)

    def test_sample_invalid_n(self, simple_param):
        """Test that invalid n raises ValueError."""
        with pytest.raises(ValueError, match="n must be > 0"):
            simple_param.sample(0)

        with pytest.raises(ValueError, match="n must be > 0"):
            simple_param.sample(-10)

    def test_to_salib_format(self, simple_param):
        """Test conversion to SALib format."""
        result = simple_param.to_salib_format()

        assert "name" in result
        assert "bounds" in result
        assert result["name"] == "test_param"
        assert len(result["bounds"]) == 2


class TestMonteCarloSampler:
    """Test MonteCarloSampler class."""

    def test_sampler_creation(self, simple_params):
        """Test creating MonteCarloSampler."""
        from smrforge.uncertainty.uq import MonteCarloSampler

        sampler = MonteCarloSampler(simple_params)

        assert len(sampler.parameters) == 2
        assert sampler.n_params == 2

    def test_invalid_parameters_type(self):
        """Test that invalid parameters type raises ValueError."""
        from smrforge.uncertainty.uq import MonteCarloSampler

        with pytest.raises(ValueError, match="parameters must be list"):
            MonteCarloSampler(parameters="invalid")

    def test_empty_parameters(self):
        """Test that empty parameters list raises ValueError."""
        from smrforge.uncertainty.uq import MonteCarloSampler

        with pytest.raises(ValueError, match="parameters list cannot be empty"):
            MonteCarloSampler(parameters=[])

    def test_invalid_parameter_type(self, simple_params):
        """Test that invalid parameter type raises ValueError."""
        from smrforge.uncertainty.uq import MonteCarloSampler

        invalid = simple_params + ["invalid"]
        with pytest.raises(ValueError, match="must be UncertainParameter"):
            MonteCarloSampler(parameters=invalid)

    def test_sample_monte_carlo(self, simple_params):
        """Test Monte Carlo sampling."""
        from smrforge.uncertainty.uq import MonteCarloSampler

        sampler = MonteCarloSampler(simple_params)
        samples = sampler.sample_monte_carlo(50, random_state=42)

        assert samples.shape == (50, 2)
        assert np.all(np.isfinite(samples))

    def test_sample_monte_carlo_invalid_n(self, simple_params):
        """Test that invalid n_samples raises ValueError."""
        from smrforge.uncertainty.uq import MonteCarloSampler

        sampler = MonteCarloSampler(simple_params)
        with pytest.raises(ValueError, match="n_samples must be > 0"):
            sampler.sample_monte_carlo(0)

    def test_sample_latin_hypercube(self, simple_params):
        """Test Latin Hypercube sampling."""
        from smrforge.uncertainty.uq import MonteCarloSampler

        sampler = MonteCarloSampler(simple_params)
        samples = sampler.sample_latin_hypercube(50, random_state=42)

        assert samples.shape == (50, 2)
        assert np.all(np.isfinite(samples))

    def test_sample_sobol_sequence(self, simple_params):
        """Test Sobol sequence sampling."""
        from smrforge.uncertainty.uq import MonteCarloSampler

        sampler = MonteCarloSampler(simple_params)
        samples = sampler.sample_sobol_sequence(50, random_state=42)

        assert samples.shape == (50, 2)
        assert np.all(np.isfinite(samples))


class TestUncertaintyPropagation:
    """Test UncertaintyPropagation class."""

    def test_propagation_creation(self, simple_params, simple_model):
        """Test creating UncertaintyPropagation."""
        from smrforge.uncertainty.uq import UncertaintyPropagation

        uq = UncertaintyPropagation(
            parameters=simple_params,
            model=simple_model,
            output_names=["output1", "output2"],
        )

        assert len(uq.parameters) == 2
        assert len(uq.output_names) == 2

    def test_invalid_parameters_empty(self, simple_model):
        """Test that empty parameters raises ValueError."""
        from smrforge.uncertainty.uq import UncertaintyPropagation

        with pytest.raises(ValueError, match="parameters must be non-empty list"):
            UncertaintyPropagation(
                parameters=[],
                model=simple_model,
                output_names=["output1"],
            )

    def test_invalid_model(self, simple_params):
        """Test that non-callable model raises ValueError."""
        from smrforge.uncertainty.uq import UncertaintyPropagation

        with pytest.raises(ValueError, match="model must be callable"):
            UncertaintyPropagation(
                parameters=simple_params,
                model="invalid",
                output_names=["output1"],
            )

    def test_invalid_output_names_empty(self, simple_params, simple_model):
        """Test that empty output_names raises ValueError."""
        from smrforge.uncertainty.uq import UncertaintyPropagation

        with pytest.raises(ValueError, match="output_names must be non-empty list"):
            UncertaintyPropagation(
                parameters=simple_params,
                model=simple_model,
                output_names=[],
            )

    def test_invalid_output_name_type(self, simple_params, simple_model):
        """Test that invalid output name type raises ValueError."""
        from smrforge.uncertainty.uq import UncertaintyPropagation

        with pytest.raises(ValueError, match="must be non-empty string"):
            UncertaintyPropagation(
                parameters=simple_params,
                model=simple_model,
                output_names=[123],  # Not string
            )

    def test_propagate_mc(self, simple_params, simple_model):
        """Test uncertainty propagation with Monte Carlo."""
        from smrforge.uncertainty.uq import UncertaintyPropagation

        uq = UncertaintyPropagation(
            parameters=simple_params,
            model=simple_model,
            output_names=["output1", "output2"],
        )

        results = uq.propagate(n_samples=50, method="mc", random_state=42)

        assert results.mean is not None
        assert results.std is not None
        assert len(results.mean) == 2
        assert len(results.std) == 2
        assert results.output_samples.shape == (50, 2)

    def test_propagate_lhs(self, simple_params, simple_model):
        """Test uncertainty propagation with Latin Hypercube."""
        from smrforge.uncertainty.uq import UncertaintyPropagation

        uq = UncertaintyPropagation(
            parameters=simple_params,
            model=simple_model,
            output_names=["output1", "output2"],
        )

        results = uq.propagate(n_samples=50, method="lhs", random_state=42)

        assert results.mean is not None
        assert results.std is not None

    def test_propagate_invalid_method(self, simple_params, simple_model):
        """Test that invalid method raises ValueError."""
        from smrforge.uncertainty.uq import UncertaintyPropagation

        uq = UncertaintyPropagation(
            parameters=simple_params,
            model=simple_model,
            output_names=["output1"],
        )

        with pytest.raises(ValueError, match="method must be one of"):
            uq.propagate(n_samples=50, method="invalid")

    def test_propagate_invalid_n_samples(self, simple_params, simple_model):
        """Test that invalid n_samples raises ValueError."""
        from smrforge.uncertainty.uq import UncertaintyPropagation

        uq = UncertaintyPropagation(
            parameters=simple_params,
            model=simple_model,
            output_names=["output1"],
        )

        with pytest.raises(ValueError, match="n_samples must be > 0"):
            uq.propagate(n_samples=0)

    def test_propagate_model_returns_dict(self, simple_params, simple_model):
        """Test propagation with model returning dict."""
        from smrforge.uncertainty.uq import UncertaintyPropagation

        uq = UncertaintyPropagation(
            parameters=simple_params,
            model=simple_model,
            output_names=["output1", "output2"],
        )

        results = uq.propagate(n_samples=10, method="mc", random_state=42)

        assert results.output_samples.shape == (10, 2)

    def test_propagate_model_returns_array(self, simple_params):
        """Test propagation with model returning array."""
        from smrforge.uncertainty.uq import UncertaintyPropagation

        def array_model(params):
            return np.array([params["param1"] + params["param2"], params["param1"] * params["param2"]])

        uq = UncertaintyPropagation(
            parameters=simple_params,
            model=array_model,
            output_names=["output1", "output2"],
        )

        results = uq.propagate(n_samples=10, method="mc", random_state=42)

        assert results.output_samples.shape == (10, 2)

    def test_propagate_model_missing_output(self, simple_params, simple_model):
        """Test that missing output in model result raises RuntimeError."""
        from smrforge.uncertainty.uq import UncertaintyPropagation

        def bad_model(params):
            return {"output1": 1.0}  # Missing output2

        uq = UncertaintyPropagation(
            parameters=simple_params,
            model=bad_model,
            output_names=["output1", "output2"],
        )

        with pytest.raises(RuntimeError, match="Model result missing outputs"):
            uq.propagate(n_samples=10, method="mc", random_state=42)

    def test_propagate_model_raises_exception(self, simple_params):
        """Test that model exception is caught and re-raised."""
        from smrforge.uncertainty.uq import UncertaintyPropagation

        def failing_model(params):
            raise ValueError("Model failed")

        uq = UncertaintyPropagation(
            parameters=simple_params,
            model=failing_model,
            output_names=["output1"],
        )

        with pytest.raises(RuntimeError, match="Model evaluation failed"):
            uq.propagate(n_samples=10, method="mc", random_state=42)


class TestSensitivityAnalysis:
    """Test SensitivityAnalysis class."""

    def test_sensitivity_analysis_creation(self, simple_params, simple_model):
        """Test creating SensitivityAnalysis."""
        from smrforge.uncertainty.uq import SensitivityAnalysis

        sa = SensitivityAnalysis(
            parameters=simple_params,
            model=simple_model,
            output_names=["output1", "output2"],
        )

        assert len(sa.parameters) == 2
        assert len(sa.output_names) == 2

    def test_invalid_parameters_empty(self, simple_model):
        """Test that empty parameters raises ValueError."""
        from smrforge.uncertainty.uq import SensitivityAnalysis

        with pytest.raises(ValueError, match="parameters must be non-empty list"):
            SensitivityAnalysis(
                parameters=[],
                model=simple_model,
                output_names=["output1"],
            )

    def test_invalid_model(self, simple_params):
        """Test that non-callable model raises ValueError."""
        from smrforge.uncertainty.uq import SensitivityAnalysis

        with pytest.raises(ValueError, match="model must be callable"):
            SensitivityAnalysis(
                parameters=simple_params,
                model="invalid",
                output_names=["output1"],
            )

    def test_invalid_output_names_empty(self, simple_params, simple_model):
        """Test that empty output_names raises ValueError."""
        from smrforge.uncertainty.uq import SensitivityAnalysis

        with pytest.raises(ValueError, match="output_names must be non-empty list"):
            SensitivityAnalysis(
                parameters=simple_params,
                model=simple_model,
                output_names=[],
            )

    def test_morris_screening_invalid_n_trajectories(self, simple_params, simple_model):
        """Test that invalid n_trajectories raises ValueError."""
        from smrforge.uncertainty.uq import SensitivityAnalysis

        sa = SensitivityAnalysis(
            parameters=simple_params,
            model=simple_model,
            output_names=["output1"],
        )

        with pytest.raises(ValueError, match="n_trajectories must be > 0"):
            sa.morris_screening(n_trajectories=0)

    def test_morris_screening_invalid_n_levels(self, simple_params, simple_model):
        """Test that invalid n_levels raises ValueError."""
        from smrforge.uncertainty.uq import SensitivityAnalysis

        sa = SensitivityAnalysis(
            parameters=simple_params,
            model=simple_model,
            output_names=["output1"],
        )

        with pytest.raises(ValueError, match="n_levels must be >= 2"):
            sa.morris_screening(n_levels=1)

    def test_sobol_analysis_invalid_n_samples(self, simple_params, simple_model):
        """Test that invalid n_samples raises ValueError."""
        from smrforge.uncertainty.uq import SensitivityAnalysis

        sa = SensitivityAnalysis(
            parameters=simple_params,
            model=simple_model,
            output_names=["output1"],
        )

        with pytest.raises(ValueError, match="n_samples must be > 0"):
            sa.sobol_analysis(n_samples=0)

