# smrforge/uncertainty/uq.py
"""
Comprehensive uncertainty quantification and sensitivity analysis.
Supports: Monte Carlo, Latin Hypercube, Sobol indices, FAST, polynomial chaos.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
try:
    import seaborn as sns
except ImportError:
    sns = None  # Optional dependency
try:
    import plotly.graph_objects as go
except ImportError:
    go = None  # Optional dependency
from numba import njit, prange
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

# Optional dependencies for sensitivity analysis
try:
    from SALib.analyze import fast, morris, sobol
    from SALib.sample import latin, saltelli
    from SALib.sample import sobol as sobol_sample
    _SALIB_AVAILABLE = True
except ImportError:
    _SALIB_AVAILABLE = False
    # Define dummy functions for type hints
    fast = None
    morris = None
    sobol = None
    latin = None
    saltelli = None
    sobol_sample = None

from scipy.stats import qmc  # Quasi-Monte Carlo
from scipy.stats import lognorm, norm, truncnorm, uniform

from ..utils.logging import get_logger

# Get logger for this module
logger = get_logger("smrforge.uncertainty.uq")


@dataclass
class UncertainParameter:
    """
    Definition of an uncertain parameter.

    Args:
        name: Parameter name
        distribution: Distribution type ('normal', 'uniform', 'lognormal', 'triangular')
        nominal: Nominal value
        uncertainty: Uncertainty specification - float (std) for normal/lognormal,
            tuple (min, max) for uniform/triangular
        units: Parameter units (optional)
        description: Parameter description (optional)

    Raises:
        ValueError: If inputs are invalid
    """

    name: str
    distribution: str  # 'normal', 'uniform', 'lognormal', 'triangular'
    nominal: float
    uncertainty: Union[float, Tuple[float, float]]  # std or (min, max)
    units: str = ""
    description: str = ""

    def __post_init__(self):
        """Validate parameter definition."""
        valid_distributions = ["normal", "uniform", "lognormal", "triangular"]
        if self.distribution not in valid_distributions:
            raise ValueError(
                f"distribution must be one of {valid_distributions}, "
                f"got {self.distribution}"
            )

        if not isinstance(self.name, str) or len(self.name) == 0:
            raise ValueError(f"name must be non-empty string, got {self.name}")

        # Validate uncertainty format based on distribution
        if self.distribution in ["normal", "lognormal"]:
            if not isinstance(self.uncertainty, (int, float)):
                raise ValueError(
                    f"For {self.distribution} distribution, uncertainty must be float (std), "
                    f"got {type(self.uncertainty)}"
                )
            if self.uncertainty <= 0:
                raise ValueError(
                    f"For {self.distribution} distribution, uncertainty (std) must be > 0, "
                    f"got {self.uncertainty}"
                )
        elif self.distribution in ["uniform", "triangular"]:
            if not isinstance(self.uncertainty, tuple) or len(self.uncertainty) != 2:
                raise ValueError(
                    f"For {self.distribution} distribution, uncertainty must be tuple (min, max), "
                    f"got {self.uncertainty}"
                )
            if self.uncertainty[0] >= self.uncertainty[1]:
                raise ValueError(
                    f"For {self.distribution} distribution, uncertainty[0] must be < uncertainty[1], "
                    f"got {self.uncertainty}"
                )
            if self.distribution == "triangular":
                if not (self.uncertainty[0] <= self.nominal <= self.uncertainty[1]):
                    raise ValueError(
                        f"For triangular distribution, nominal must be between uncertainty bounds, "
                        f"got nominal={self.nominal}, bounds={self.uncertainty}"
                    )

    def sample(self, n: int, random_state: Optional[int] = None) -> np.ndarray:
        """
        Generate samples from distribution.

        Args:
            n: Number of samples
            random_state: Random seed

        Returns:
            Array of n samples

        Raises:
            ValueError: If n is invalid
        """
        if n <= 0:
            raise ValueError(f"n must be > 0, got {n}")

        rng = np.random.default_rng(random_state)

        if self.distribution == "normal":
            std = self.uncertainty
            return rng.normal(self.nominal, std, n)

        elif self.distribution == "uniform":
            low, high = self.uncertainty
            return rng.uniform(low, high, n)

        elif self.distribution == "lognormal":
            # Log-normal with specified relative std
            rel_std = self.uncertainty
            sigma = np.sqrt(np.log(1 + rel_std**2))
            mu = np.log(self.nominal) - 0.5 * sigma**2
            return rng.lognormal(mu, sigma, n)

        elif self.distribution == "triangular":
            low, high = self.uncertainty
            mode = self.nominal
            return rng.triangular(low, mode, high, n)

        else:
            raise ValueError(f"Unknown distribution: {self.distribution}")

    def to_salib_format(self) -> Dict:
        """Convert to SALib problem format."""
        if self.distribution == "uniform":
            low, high = self.uncertainty
            return {"name": self.name, "bounds": [low, high]}
        elif self.distribution == "normal":
            std = self.uncertainty
            # Use 3-sigma bounds
            return {
                "name": self.name,
                "bounds": [self.nominal - 3 * std, self.nominal + 3 * std],
            }
        else:
            # Fallback to nominal ± 20%
            return {
                "name": self.name,
                "bounds": [self.nominal * 0.8, self.nominal * 1.2],
            }


@dataclass
class UQResults:
    """Results from uncertainty quantification analysis."""

    parameter_names: List[str]
    parameter_samples: np.ndarray  # (n_samples, n_params)
    output_samples: np.ndarray  # (n_samples, n_outputs)
    output_names: List[str]

    # Statistics
    mean: Optional[np.ndarray] = None
    std: Optional[np.ndarray] = None
    percentiles: Optional[Dict[float, np.ndarray]] = None

    # Sensitivity indices
    sobol_indices: Optional[Dict] = None
    morris_indices: Optional[Dict] = None


class MonteCarloSampler:
    """
    Monte Carlo and Latin Hypercube sampling for UQ.

    Args:
        parameters: List of UncertainParameter objects

    Raises:
        ValueError: If parameters list is invalid
    """

    def __init__(self, parameters: List[UncertainParameter]):
        if not isinstance(parameters, list):
            raise ValueError(f"parameters must be list, got {type(parameters)}")

        if len(parameters) == 0:
            raise ValueError("parameters list cannot be empty")

        for i, param in enumerate(parameters):
            if not isinstance(param, UncertainParameter):
                raise ValueError(
                    f"parameters[{i}] must be UncertainParameter, got {type(param)}"
                )

        self.parameters = parameters
        self.n_params = len(parameters)
        self.console = Console()

        logger.debug(f"MonteCarloSampler initialized with {self.n_params} parameters")

    def sample_monte_carlo(
        self, n_samples: int, random_state: Optional[int] = None
    ) -> np.ndarray:
        """
        Simple Monte Carlo sampling.

        Args:
            n_samples: Number of samples
            random_state: Random seed

        Returns:
            Samples array (n_samples, n_params)

        Raises:
            ValueError: If n_samples is invalid
        """
        if n_samples <= 0:
            raise ValueError(f"n_samples must be > 0, got {n_samples}")

        logger.debug(f"Generating {n_samples} Monte Carlo samples")

        samples = np.zeros((n_samples, self.n_params))

        for i, param in enumerate(self.parameters):
            samples[:, i] = param.sample(n_samples, random_state)

        return samples

    def sample_latin_hypercube(
        self, n_samples: int, random_state: Optional[int] = None
    ) -> np.ndarray:
        """
        Latin Hypercube Sampling for better space-filling.
        More efficient than pure MC for same number of samples.

        Args:
            n_samples: Number of samples
            random_state: Random seed

        Returns:
            Samples array (n_samples, n_params)

        Raises:
            ValueError: If n_samples is invalid
        """
        if n_samples <= 0:
            raise ValueError(f"n_samples must be > 0, got {n_samples}")

        logger.debug(f"Generating {n_samples} Latin Hypercube samples")

        sampler = qmc.LatinHypercube(d=self.n_params, seed=random_state)

        # Generate LHS in [0,1]^d
        unit_samples = sampler.random(n=n_samples)

        # Transform to parameter distributions
        samples = np.zeros((n_samples, self.n_params))

        for i, param in enumerate(self.parameters):
            # Use quantile transformation
            if param.distribution == "normal":
                std = param.uncertainty
                samples[:, i] = norm.ppf(
                    unit_samples[:, i], loc=param.nominal, scale=std
                )
            elif param.distribution == "uniform":
                low, high = param.uncertainty
                samples[:, i] = uniform.ppf(
                    unit_samples[:, i], loc=low, scale=high - low
                )
            elif param.distribution == "lognormal":
                rel_std = param.uncertainty
                sigma = np.sqrt(np.log(1 + rel_std**2))
                mu = np.log(param.nominal) - 0.5 * sigma**2
                samples[:, i] = lognorm.ppf(
                    unit_samples[:, i], s=sigma, scale=np.exp(mu)
                )
            else:
                # Fallback to normal
                samples[:, i] = norm.ppf(
                    unit_samples[:, i], loc=param.nominal, scale=0.1 * param.nominal
                )

        return samples

    def sample_sobol_sequence(
        self, n_samples: int, random_state: Optional[int] = None
    ) -> np.ndarray:
        """
        Sobol sequence sampling (quasi-Monte Carlo).
        Better convergence than random sampling.

        Args:
            n_samples: Number of samples (will be rounded up to next power of 2)
            random_state: Random seed

        Returns:
            Samples array (n_samples, n_params)

        Raises:
            ValueError: If n_samples is invalid
        """
        if n_samples <= 0:
            raise ValueError(f"n_samples must be > 0, got {n_samples}")

        logger.debug(f"Generating {n_samples} Sobol sequence samples")

        sampler = qmc.Sobol(d=self.n_params, scramble=True, seed=random_state)

        # Get next power of 2
        n_sobol = 2 ** int(np.ceil(np.log2(n_samples)))
        unit_samples = sampler.random(n=n_sobol)[:n_samples]

        # Transform to distributions (same as LHS)
        samples = np.zeros((n_samples, self.n_params))

        for i, param in enumerate(self.parameters):
            if param.distribution == "normal":
                std = param.uncertainty
                samples[:, i] = norm.ppf(
                    unit_samples[:, i], loc=param.nominal, scale=std
                )
            elif param.distribution == "uniform":
                low, high = param.uncertainty
                samples[:, i] = uniform.ppf(
                    unit_samples[:, i], loc=low, scale=high - low
                )
            else:
                samples[:, i] = norm.ppf(
                    unit_samples[:, i], loc=param.nominal, scale=0.1 * param.nominal
                )

        return samples


class UncertaintyPropagation:
    """
    Propagate uncertainties through reactor model.

    Args:
        parameters: List of UncertainParameter objects
        model: Callable function that takes a parameter dict and returns results
        output_names: List of output variable names

    Raises:
        ValueError: If inputs are invalid
    """

    def __init__(
        self,
        parameters: List[UncertainParameter],
        model: Callable,
        output_names: List[str],
    ):
        # Validate inputs
        if not isinstance(parameters, list) or len(parameters) == 0:
            raise ValueError("parameters must be non-empty list")

        if not callable(model):
            raise ValueError(f"model must be callable, got {type(model)}")

        if not isinstance(output_names, list) or len(output_names) == 0:
            raise ValueError("output_names must be non-empty list")

        for i, name in enumerate(output_names):
            if not isinstance(name, str) or len(name) == 0:
                raise ValueError(f"output_names[{i}] must be non-empty string, got {name}")

        self.parameters = parameters
        self.model = model
        self.output_names = output_names
        self.sampler = MonteCarloSampler(parameters)
        self.console = Console()

        logger.info(
            f"UncertaintyPropagation initialized: {len(parameters)} parameters, "
            f"{len(output_names)} outputs"
        )

    def propagate(
        self,
        n_samples: int = 1000,
        method: str = "lhs",
        random_state: Optional[int] = None,
        parallel: bool = True,
    ) -> UQResults:
        """
        Propagate uncertainties through model.

        Args:
            n_samples: Number of Monte Carlo samples
            method: 'mc', 'lhs', or 'sobol'
            random_state: Random seed
            parallel: Use parallel evaluation (if supported)

        Returns:
            UQResults object

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If model evaluation fails
        """
        # Validate inputs
        if n_samples <= 0:
            raise ValueError(f"n_samples must be > 0, got {n_samples}")

        valid_methods = ["mc", "lhs", "sobol"]
        if method not in valid_methods:
            raise ValueError(f"method must be one of {valid_methods}, got {method}")

        logger.info(
            f"Starting uncertainty propagation: {n_samples} samples, method={method}"
        )

        self.console.print(f"[bold cyan]Uncertainty Propagation[/bold cyan]")
        self.console.print(f"Parameters: {len(self.parameters)}")
        self.console.print(f"Samples: {n_samples}")
        self.console.print(f"Method: {method.upper()}")

        # Generate samples
        if method == "mc":
            samples = self.sampler.sample_monte_carlo(n_samples, random_state)
        elif method == "lhs":
            samples = self.sampler.sample_latin_hypercube(n_samples, random_state)
        elif method == "sobol":
            samples = self.sampler.sample_sobol_sequence(n_samples, random_state)
        else:
            raise ValueError(f"Unknown method: {method}")

        # Evaluate model for each sample
        n_outputs = len(self.output_names)
        outputs = np.zeros((n_samples, n_outputs))

        with Progress() as progress:
            task = progress.add_task("Evaluating model...", total=n_samples)

            for i in range(n_samples):
                # Create parameter dict
                params = {p.name: samples[i, j] for j, p in enumerate(self.parameters)}

                # Run model
                try:
                    result = self.model(params)
                except Exception as e:
                    raise RuntimeError(
                        f"Model evaluation failed at sample {i}: {e}"
                    ) from e

                # Extract outputs
                if isinstance(result, dict):
                    # Check all output names are present
                    missing = [name for name in self.output_names if name not in result]
                    if missing:
                        raise RuntimeError(
                            f"Model result missing outputs: {missing}"
                        )
                    outputs[i, :] = [result[name] for name in self.output_names]
                else:
                    # Assume result is array-like
                    result_array = np.array(result)
                    if result_array.shape != (n_outputs,):
                        raise RuntimeError(
                            f"Model result shape {result_array.shape} != expected ({n_outputs},)"
                        )
                    outputs[i, :] = result_array

                progress.update(task, advance=1)

        logger.info(f"Completed {n_samples} model evaluations")

        # Compute statistics
        mean = np.mean(outputs, axis=0)
        std = np.std(outputs, axis=0)

        percentiles = {
            5: np.percentile(outputs, 5, axis=0),
            25: np.percentile(outputs, 25, axis=0),
            50: np.percentile(outputs, 50, axis=0),
            75: np.percentile(outputs, 75, axis=0),
            95: np.percentile(outputs, 95, axis=0),
        }

        results = UQResults(
            parameter_names=[p.name for p in self.parameters],
            parameter_samples=samples,
            output_samples=outputs,
            output_names=self.output_names,
            mean=mean,
            std=std,
            percentiles=percentiles,
        )

        self._print_statistics(results)

        return results

    def _print_statistics(self, results: UQResults):
        """Print statistics table."""
        table = Table(title="Output Statistics")
        table.add_column("Output", style="cyan")
        table.add_column("Mean", justify="right")
        table.add_column("Std Dev", justify="right")
        table.add_column("5%", justify="right")
        table.add_column("95%", justify="right")
        table.add_column("Range", justify="right")

        for i, name in enumerate(results.output_names):
            mean = results.mean[i]
            std = results.std[i]
            p5 = results.percentiles[5][i]
            p95 = results.percentiles[95][i]

            table.add_row(
                name,
                f"{mean:.4g}",
                f"{std:.4g}",
                f"{p5:.4g}",
                f"{p95:.4g}",
                f"[{p5:.4g}, {p95:.4g}]",
            )

        self.console.print(table)


class SensitivityAnalysis:
    """
    Global sensitivity analysis using Sobol indices and Morris method.

    Args:
        parameters: List of UncertainParameter objects
        model: Callable function that takes a parameter dict and returns results
        output_names: List of output variable names

    Raises:
        ValueError: If inputs are invalid
    """

    def __init__(
        self,
        parameters: List[UncertainParameter],
        model: Callable,
        output_names: List[str],
    ):
        # Validate inputs
        if not isinstance(parameters, list) or len(parameters) == 0:
            raise ValueError("parameters must be non-empty list")

        if not callable(model):
            raise ValueError(f"model must be callable, got {type(model)}")

        if not isinstance(output_names, list) or len(output_names) == 0:
            raise ValueError("output_names must be non-empty list")

        self.parameters = parameters
        self.model = model
        self.output_names = output_names
        self.console = Console()

        logger.info(
            f"SensitivityAnalysis initialized: {len(parameters)} parameters, "
            f"{len(output_names)} outputs"
        )

    def sobol_analysis(
        self, n_samples: int = 1024, calc_second_order: bool = True
    ) -> Dict:
        """
        Sobol sensitivity analysis.
        Computes first-order and total-order indices.

        Args:
            n_samples: Base sample size (actual evaluations = n*(2*d+2))
            calc_second_order: Compute second-order interactions

        Returns:
            Dict of Sobol indices

        Raises:
            ValueError: If n_samples is invalid
            ImportError: If SALib is not installed
            RuntimeError: If model evaluation fails
        """
        if n_samples <= 0:
            raise ValueError(f"n_samples must be > 0, got {n_samples}")

        if not _SALIB_AVAILABLE:
            raise ImportError(
                "SALib is required for Sobol analysis. "
                "Install with: pip install salib"
            )

        logger.info(
            f"Starting Sobol analysis: n_samples={n_samples}, "
            f"calc_second_order={calc_second_order}"
        )

        self.console.print(f"[bold cyan]Sobol Sensitivity Analysis[/bold cyan]")

        # Define problem for SALib
        problem = {
            "num_vars": len(self.parameters),
            "names": [p.name for p in self.parameters],
            "bounds": [
                (
                    [p.uncertainty[0], p.uncertainty[1]]
                    if isinstance(p.uncertainty, tuple)
                    else [p.nominal - 3 * p.uncertainty, p.nominal + 3 * p.uncertainty]
                )
                for p in self.parameters
            ],
        }

        # Generate Saltelli samples
        param_samples = saltelli.sample(
            problem, n_samples, calc_second_order=calc_second_order
        )

        n_evals = param_samples.shape[0]
        self.console.print(f"Total model evaluations: {n_evals}")

        # Evaluate model
        n_outputs = len(self.output_names)
        Y = np.zeros((n_evals, n_outputs))

        with Progress() as progress:
            task = progress.add_task("Evaluating...", total=n_evals)

            for i in range(n_evals):
                params = {
                    name: param_samples[i, j] for j, name in enumerate(problem["names"])
                }
                try:
                    result = self.model(params)
                except Exception as e:
                    raise RuntimeError(
                        f"Model evaluation failed at evaluation {i}: {e}"
                    ) from e

                if isinstance(result, dict):
                    missing = [name for name in self.output_names if name not in result]
                    if missing:
                        raise RuntimeError(
                            f"Model result missing outputs: {missing}"
                        )
                    Y[i, :] = [result[name] for name in self.output_names]
                else:
                    result_array = np.array(result)
                    if result_array.shape != (len(self.output_names),):
                        raise RuntimeError(
                            f"Model result shape {result_array.shape} != expected "
                            f"({len(self.output_names)},)"
                        )
                    Y[i, :] = result_array

                progress.update(task, advance=1)

        logger.info(f"Completed {n_evals} model evaluations for Sobol analysis")

        # Analyze each output
        sobol_results = {}

        for i, output_name in enumerate(self.output_names):
            Si = sobol.analyze(problem, Y[:, i], calc_second_order=calc_second_order)
            sobol_results[output_name] = Si

        # Print results
        self._print_sobol_results(sobol_results)

        return sobol_results

    def _print_sobol_results(self, results: Dict):
        """
        Print Sobol indices in a formatted table.

        Args:
            results: Dict of Sobol analysis results

        Raises:
            ValueError: If results structure is invalid
        """
        if not isinstance(results, dict):
            raise ValueError(f"results must be dict, got {type(results)}")

        for output_name, Si in results.items():
            if not isinstance(Si, dict) or "S1" not in Si or "ST" not in Si:
                logger.warning(
                    f"Skipping {output_name}: invalid Sobol results structure"
                )
                continue
            self.console.print(f"\n[bold]Output: {output_name}[/bold]")

            table = Table()
            table.add_column("Parameter", style="cyan")
            table.add_column("S1 (First Order)", justify="right")
            table.add_column("ST (Total Order)", justify="right")
            table.add_column("Importance", style="yellow")

            # Sort by total order index
            indices = np.argsort(Si["ST"])[::-1]

            for idx in indices:
                param_name = self.parameters[idx].name
                s1 = Si["S1"][idx]
                st = Si["ST"][idx]

                # Importance classification
                if st > 0.5:
                    importance = "High"
                elif st > 0.1:
                    importance = "Medium"
                else:
                    importance = "Low"

                table.add_row(param_name, f"{s1:.3f}", f"{st:.3f}", importance)

            self.console.print(table)

    def morris_screening(self, n_trajectories: int = 10, n_levels: int = 4) -> Dict:
        """
        Morris one-at-a-time screening method.
        Fast method to identify important parameters.

        Args:
            n_trajectories: Number of trajectories
            n_levels: Number of grid levels

        Returns:
            Dict of Morris indices (mu_star, sigma)

        Raises:
            ValueError: If inputs are invalid
            ImportError: If SALib is not installed
            RuntimeError: If model evaluation fails
        """
        if n_trajectories <= 0:
            raise ValueError(f"n_trajectories must be > 0, got {n_trajectories}")
        if n_levels < 2:
            raise ValueError(f"n_levels must be >= 2, got {n_levels}")

        if not _SALIB_AVAILABLE:
            raise ImportError(
                "SALib is required for Morris screening. "
                "Install with: pip install salib"
            )

        logger.info(
            f"Starting Morris screening: n_trajectories={n_trajectories}, "
            f"n_levels={n_levels}"
        )

        self.console.print(f"[bold cyan]Morris Screening[/bold cyan]")

        # Define problem
        problem = {
            "num_vars": len(self.parameters),
            "names": [p.name for p in self.parameters],
            "bounds": [
                (
                    [p.uncertainty[0], p.uncertainty[1]]
                    if isinstance(p.uncertainty, tuple)
                    else [p.nominal - 3 * p.uncertainty, p.nominal + 3 * p.uncertainty]
                )
                for p in self.parameters
            ],
        }

        # Generate Morris samples
        param_samples = morris.sample(problem, n_trajectories, num_levels=n_levels)

        n_evals = param_samples.shape[0]
        self.console.print(f"Total evaluations: {n_evals}")

        # Evaluate
        n_outputs = len(self.output_names)
        Y = np.zeros((n_evals, n_outputs))

        with Progress() as progress:
            task = progress.add_task("Evaluating...", total=n_evals)

            for i in range(n_evals):
                params = {
                    name: param_samples[i, j] for j, name in enumerate(problem["names"])
                }
                try:
                    result = self.model(params)
                except Exception as e:
                    raise RuntimeError(
                        f"Model evaluation failed at evaluation {i}: {e}"
                    ) from e

                if isinstance(result, dict):
                    missing = [name for name in self.output_names if name not in result]
                    if missing:
                        raise RuntimeError(
                            f"Model result missing outputs: {missing}"
                        )
                    Y[i, :] = [result[name] for name in self.output_names]
                else:
                    result_array = np.array(result)
                    if result_array.shape != (len(self.output_names),):
                        raise RuntimeError(
                            f"Model result shape {result_array.shape} != expected "
                            f"({len(self.output_names)},)"
                        )
                    Y[i, :] = result_array

                progress.update(task, advance=1)

        logger.info(f"Completed {n_evals} model evaluations for Morris screening")

        # Analyze
        morris_results = {}

        for i, output_name in enumerate(self.output_names):
            Si = morris.analyze(problem, param_samples, Y[:, i])
            morris_results[output_name] = Si

        self._print_morris_results(morris_results)

        return morris_results

    def _print_morris_results(self, results: Dict):
        """
        Print Morris indices in a formatted table.

        Args:
            results: Dict of Morris analysis results

        Raises:
            ValueError: If results structure is invalid
        """
        if not isinstance(results, dict):
            raise ValueError(f"results must be dict, got {type(results)}")

        for output_name, Si in results.items():
            if not isinstance(Si, dict) or "mu_star" not in Si or "sigma" not in Si:
                logger.warning(
                    f"Skipping {output_name}: invalid Morris results structure"
                )
                continue
            self.console.print(f"\n[bold]Output: {output_name}[/bold]")

            table = Table()
            table.add_column("Parameter", style="cyan")
            table.add_column("μ* (Importance)", justify="right")
            table.add_column("σ (Interactions)", justify="right")
            table.add_column("Classification", style="yellow")

            mu_star = Si["mu_star"]
            sigma = Si["sigma"]

            # Sort by mu_star
            indices = np.argsort(mu_star)[::-1]

            for idx in indices:
                param_name = self.parameters[idx].name

                # Classification
                if mu_star[idx] > 0.5 * np.max(mu_star):
                    classification = "Important"
                elif mu_star[idx] > 0.1 * np.max(mu_star):
                    classification = "Moderate"
                else:
                    classification = "Negligible"

                table.add_row(
                    param_name,
                    f"{mu_star[idx]:.3f}",
                    f"{sigma[idx]:.3f}",
                    classification,
                )

            self.console.print(table)


class VisualizationTools:
    """
    Visualization tools for UQ results.
    """

    @staticmethod
    def plot_distributions(
        results: UQResults, output_idx: int = 0, figsize: Tuple[int, int] = (12, 8)
    ):
        """
        Plot output distribution with statistics.

        Args:
            results: UQResults object with output samples
            output_idx: Index of output to plot
            figsize: Figure size tuple

        Returns:
            matplotlib Figure object

        Raises:
            ValueError: If inputs are invalid
        """
        if not isinstance(results, UQResults):
            raise ValueError(f"results must be UQResults, got {type(results)}")

        if output_idx < 0 or output_idx >= len(results.output_names):
            raise ValueError(
                f"output_idx must be in [0, {len(results.output_names)}), got {output_idx}"
            )

        if results.output_samples is None or results.output_samples.size == 0:
            raise ValueError("results.output_samples is empty")

        if results.mean is None or results.percentiles is None:
            raise ValueError("results must have computed statistics (mean, percentiles)")

        fig, axes = plt.subplots(2, 2, figsize=figsize)

        output_name = results.output_names[output_idx]
        data = results.output_samples[:, output_idx]

        # Histogram
        axes[0, 0].hist(data, bins=50, density=True, alpha=0.7, color="steelblue")
        axes[0, 0].axvline(
            results.mean[output_idx], color="red", linestyle="--", label="Mean"
        )
        axes[0, 0].axvline(
            results.percentiles[5][output_idx],
            color="orange",
            linestyle="--",
            label="5/95 percentile",
        )
        axes[0, 0].axvline(
            results.percentiles[95][output_idx], color="orange", linestyle="--"
        )
        axes[0, 0].set_xlabel(output_name)
        axes[0, 0].set_ylabel("Density")
        axes[0, 0].legend()
        axes[0, 0].set_title("Distribution")

        # Cumulative distribution
        sorted_data = np.sort(data)
        cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
        axes[0, 1].plot(sorted_data, cdf, linewidth=2)
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].set_xlabel(output_name)
        axes[0, 1].set_ylabel("CDF")
        axes[0, 1].set_title("Cumulative Distribution")

        # Box plot
        axes[1, 0].boxplot(data, vert=True)
        axes[1, 0].set_ylabel(output_name)
        axes[1, 0].set_title("Box Plot")
        axes[1, 0].grid(True, alpha=0.3)

        # Q-Q plot
        from scipy import stats

        stats.probplot(data, dist="norm", plot=axes[1, 1])
        axes[1, 1].set_title("Q-Q Plot (Normal)")

        plt.tight_layout()
        return fig

    @staticmethod
    def plot_scatter_matrix(
        results: UQResults, max_params: int = 6, output_idx: int = 0
    ):
        """
        Scatter matrix showing parameter correlations with output.

        Args:
            results: UQResults object with parameter and output samples
            max_params: Maximum number of parameters to include
            output_idx: Index of output to plot

        Returns:
            seaborn PairGrid object

        Raises:
            ValueError: If inputs are invalid
            ImportError: If seaborn is not installed
        """
        if not isinstance(results, UQResults):
            raise ValueError(f"results must be UQResults, got {type(results)}")

        if output_idx < 0 or output_idx >= len(results.output_names):
            raise ValueError(
                f"output_idx must be in [0, {len(results.output_names)}), got {output_idx}"
            )

        if max_params <= 0:
            raise ValueError(f"max_params must be > 0, got {max_params}")

        if results.parameter_samples is None or results.parameter_samples.size == 0:
            raise ValueError("results.parameter_samples is empty")

        if sns is None:
            raise ImportError(
                "seaborn is required for scatter matrix plots. "
                "Install with: pip install seaborn"
            )

        n_params = min(len(results.parameter_names), max_params)

        # Create dataframe
        data_dict = {}
        for i in range(n_params):
            data_dict[results.parameter_names[i]] = results.parameter_samples[:, i]
        data_dict[results.output_names[output_idx]] = results.output_samples[
            :, output_idx
        ]

        df = pl.DataFrame(data_dict).to_pandas()

        # Scatter matrix (sns is checked above)
        fig = sns.pairplot(
            df, diag_kind="kde", corner=True, plot_kws={"alpha": 0.6, "s": 20}
        )
        fig.fig.suptitle(
            f"Parameter-Output Correlations: {results.output_names[output_idx]}", y=1.02
        )

        return fig

    @staticmethod
    def plot_sobol_indices(
        sobol_results: Dict, output_name: str, parameter_names: List[str]
    ):
        """
        Plot Sobol sensitivity indices.

        Args:
            sobol_results: Dict of Sobol analysis results (from SensitivityAnalysis.sobol_analysis)
            output_name: Name of output to plot
            parameter_names: List of parameter names

        Returns:
            matplotlib Figure object

        Raises:
            ValueError: If inputs are invalid
        """
        if not isinstance(sobol_results, dict):
            raise ValueError(f"sobol_results must be dict, got {type(sobol_results)}")

        if output_name not in sobol_results:
            raise ValueError(
                f"output_name '{output_name}' not in sobol_results. "
                f"Available: {list(sobol_results.keys())}"
            )

        if not isinstance(parameter_names, list) or len(parameter_names) == 0:
            raise ValueError("parameter_names must be non-empty list")

        Si = sobol_results[output_name]

        if not isinstance(Si, dict) or "S1" not in Si or "ST" not in Si:
            raise ValueError(
                f"Sobol results for '{output_name}' must contain 'S1' and 'ST' keys"
            )

        if len(Si["S1"]) != len(parameter_names) or len(Si["ST"]) != len(parameter_names):
            raise ValueError(
                f"Length mismatch: parameter_names has {len(parameter_names)} elements, "
                f"but Sobol indices have {len(Si['S1'])} elements"
            )

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # First order
        axes[0].barh(parameter_names, Si["S1"], color="steelblue")
        axes[0].set_xlabel("First Order Index (S1)")
        axes[0].set_title("Direct Effect")
        axes[0].grid(True, alpha=0.3, axis="x")

        # Total order
        axes[1].barh(parameter_names, Si["ST"], color="coral")
        axes[1].set_xlabel("Total Order Index (ST)")
        axes[1].set_title("Total Effect (incl. interactions)")
        axes[1].grid(True, alpha=0.3, axis="x")

        plt.tight_layout()
        return fig

    @staticmethod
    def plot_distribution_plotly(
        results: "UQResults",
        output_idx: int = 0,
        bins: int = 50,
    ):
        """
        Plotly-based distribution plot for dashboards.

        This is a lightweight wrapper around `smrforge.uncertainty.visualization`.
        """
        if go is None:
            raise ImportError("plotly is required for plot_distribution_plotly. Install with: pip install plotly")
        from smrforge.uncertainty.visualization import plot_uq_distribution

        return plot_uq_distribution(results, output_idx=output_idx, bins=bins, backend="plotly")

    @staticmethod
    def plot_correlation_matrix(
        results: "UQResults",
        include_outputs: bool = True,
        backend: str = "plotly",
    ):
        """Correlation matrix for UQ (plotly or matplotlib)."""
        from smrforge.uncertainty.visualization import plot_uq_correlation_matrix

        return plot_uq_correlation_matrix(results, include_outputs=include_outputs, backend=backend)

    @staticmethod
    def plot_sobol_indices_plotly(
        sobol_results: Dict,
        output_name: str,
        parameter_names: List[str],
    ):
        """Plotly Sobol indices for dashboards."""
        if go is None:
            raise ImportError("plotly is required for plot_sobol_indices_plotly. Install with: pip install plotly")
        from smrforge.uncertainty.visualization import plot_uq_sobol_indices

        return plot_uq_sobol_indices(
            sobol_results,
            output_name=output_name,
            parameter_names=parameter_names,
            backend="plotly",
        )

    @staticmethod
    def plot_morris_indices(
        morris_results: Dict,
        output_name: str,
        parameter_names: List[str],
        backend: str = "plotly",
    ):
        """Morris indices (plotly or matplotlib)."""
        from smrforge.uncertainty.visualization import plot_uq_morris_indices

        return plot_uq_morris_indices(
            morris_results,
            output_name=output_name,
            parameter_names=parameter_names,
            backend=backend,
        )


# Example HTGR-specific UQ problem
def create_htgr_uq_problem() -> List[UncertainParameter]:
    """Create standard HTGR uncertainty parameters."""
    return [
        UncertainParameter(
            name="enrichment",
            distribution="normal",
            nominal=0.195,
            uncertainty=0.005,  # ±0.5%
            units="fraction",
            description="U-235 enrichment",
        ),
        UncertainParameter(
            name="fuel_density",
            distribution="normal",
            nominal=10.96,  # g/cm³ for UCO
            uncertainty=0.22,  # 2%
            units="g/cm³",
            description="Fuel kernel density",
        ),
        UncertainParameter(
            name="graphite_conductivity",
            distribution="normal",
            nominal=100.0,  # W/m-K at 300K
            uncertainty=10.0,  # 10%
            units="W/m-K",
            description="Graphite thermal conductivity",
        ),
        UncertainParameter(
            name="flow_rate",
            distribution="normal",
            nominal=8.0,
            uncertainty=0.4,  # 5%
            units="kg/s",
            description="Helium mass flow rate",
        ),
        UncertainParameter(
            name="power_peaking",
            distribution="uniform",
            nominal=1.5,
            uncertainty=(1.3, 1.7),
            units="dimensionless",
            description="Radial power peaking factor",
        ),
        UncertainParameter(
            name="doppler_coefficient",
            distribution="normal",
            nominal=-3.5e-5,
            uncertainty=0.5e-5,  # 14%
            units="dk/k/K",
            description="Doppler temperature coefficient",
        ),
    ]


if __name__ == "__main__":
    console = Console()
    console.print("[bold cyan]Uncertainty Quantification Demo[/bold cyan]\n")

    # Define uncertain parameters
    params = create_htgr_uq_problem()

    # Simple model: k_eff as function of parameters
    def simple_htgr_model(params_dict):
        """Simplified HTGR model for demonstration."""
        enr = params_dict["enrichment"]
        rho_fuel = params_dict["fuel_density"]
        k_g = params_dict["graphite_conductivity"]
        mdot = params_dict["flow_rate"]
        peaking = params_dict["power_peaking"]
        alpha_D = params_dict["doppler_coefficient"]

        # Simplified k_eff model
        k_base = 1.05
        k_eff = k_base + 2.0 * (enr - 0.195) + 0.001 * (rho_fuel - 10.96)

        # Peak fuel temperature (simplified)
        T_peak = 1200 + 100 * peaking + 50 * (8.0 - mdot) - 0.5 * (k_g - 100)

        return {"k_eff": k_eff, "T_peak_fuel": T_peak}

    # Uncertainty propagation
    uq = UncertaintyPropagation(
        parameters=params,
        model=simple_htgr_model,
        output_names=["k_eff", "T_peak_fuel"],
    )

    results = uq.propagate(n_samples=500, method="lhs", random_state=42)

    # Sensitivity analysis
    console.print("\n[bold]Running Sensitivity Analysis...[/bold]\n")
    sa = SensitivityAnalysis(params, simple_htgr_model, ["k_eff", "T_peak_fuel"])

    sobol_results = sa.sobol_analysis(n_samples=256, calc_second_order=False)

    console.print("\n[bold green]UQ analysis complete![/bold green]")
