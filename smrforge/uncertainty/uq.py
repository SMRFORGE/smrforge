# uncertainty/uq.py
"""
Comprehensive uncertainty quantification and sensitivity analysis.
Supports: Monte Carlo, Latin Hypercube, Sobol indices, FAST, polynomial chaos.
"""

import numpy as np
from numba import njit, prange
from scipy.stats import norm, uniform, lognorm, truncnorm
from scipy.stats import qmc  # Quasi-Monte Carlo
from typing import Dict, List, Tuple, Optional, Callable, Union
from dataclasses import dataclass, field
import polars as pl
from SALib.sample import saltelli, latin, sobol as sobol_sample
from SALib.analyze import sobol, fast, morris
import matplotlib.pyplot as plt
from rich.console import Console
from rich.progress import Progress, track
from rich.table import Table
import seaborn as sns


@dataclass
class UncertainParameter:
    """Definition of an uncertain parameter."""
    name: str
    distribution: str  # 'normal', 'uniform', 'lognormal', 'triangular'
    nominal: float
    uncertainty: Union[float, Tuple[float, float]]  # std or (min, max)
    units: str = ""
    description: str = ""
    
    def sample(self, n: int, random_state: Optional[int] = None) -> np.ndarray:
        """Generate samples from distribution."""
        rng = np.random.default_rng(random_state)
        
        if self.distribution == 'normal':
            std = self.uncertainty
            return rng.normal(self.nominal, std, n)
        
        elif self.distribution == 'uniform':
            low, high = self.uncertainty
            return rng.uniform(low, high, n)
        
        elif self.distribution == 'lognormal':
            # Log-normal with specified relative std
            rel_std = self.uncertainty
            sigma = np.sqrt(np.log(1 + rel_std**2))
            mu = np.log(self.nominal) - 0.5 * sigma**2
            return rng.lognormal(mu, sigma, n)
        
        elif self.distribution == 'triangular':
            low, high = self.uncertainty
            mode = self.nominal
            return rng.triangular(low, mode, high, n)
        
        else:
            raise ValueError(f"Unknown distribution: {self.distribution}")
    
    def to_salib_format(self) -> Dict:
        """Convert to SALib problem format."""
        if self.distribution == 'uniform':
            low, high = self.uncertainty
            return {'name': self.name, 'bounds': [low, high]}
        elif self.distribution == 'normal':
            std = self.uncertainty
            # Use 3-sigma bounds
            return {'name': self.name, 'bounds': [self.nominal - 3*std, self.nominal + 3*std]}
        else:
            # Fallback to nominal ± 20%
            return {'name': self.name, 'bounds': [self.nominal*0.8, self.nominal*1.2]}


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
    """
    
    def __init__(self, parameters: List[UncertainParameter]):
        self.parameters = parameters
        self.n_params = len(parameters)
        self.console = Console()
    
    def sample_monte_carlo(self, n_samples: int, 
                          random_state: Optional[int] = None) -> np.ndarray:
        """
        Simple Monte Carlo sampling.
        
        Args:
            n_samples: Number of samples
            random_state: Random seed
        
        Returns:
            Samples array (n_samples, n_params)
        """
        samples = np.zeros((n_samples, self.n_params))
        
        for i, param in enumerate(self.parameters):
            samples[:, i] = param.sample(n_samples, random_state)
        
        return samples
    
    def sample_latin_hypercube(self, n_samples: int,
                               random_state: Optional[int] = None) -> np.ndarray:
        """
        Latin Hypercube Sampling for better space-filling.
        More efficient than pure MC for same number of samples.
        """
        sampler = qmc.LatinHypercube(d=self.n_params, seed=random_state)
        
        # Generate LHS in [0,1]^d
        unit_samples = sampler.random(n=n_samples)
        
        # Transform to parameter distributions
        samples = np.zeros((n_samples, self.n_params))
        
        for i, param in enumerate(self.parameters):
            # Use quantile transformation
            if param.distribution == 'normal':
                std = param.uncertainty
                samples[:, i] = norm.ppf(unit_samples[:, i], 
                                        loc=param.nominal, scale=std)
            elif param.distribution == 'uniform':
                low, high = param.uncertainty
                samples[:, i] = uniform.ppf(unit_samples[:, i], 
                                           loc=low, scale=high-low)
            elif param.distribution == 'lognormal':
                rel_std = param.uncertainty
                sigma = np.sqrt(np.log(1 + rel_std**2))
                mu = np.log(param.nominal) - 0.5 * sigma**2
                samples[:, i] = lognorm.ppf(unit_samples[:, i], 
                                           s=sigma, scale=np.exp(mu))
            else:
                # Fallback to normal
                samples[:, i] = norm.ppf(unit_samples[:, i], 
                                        loc=param.nominal, scale=0.1*param.nominal)
        
        return samples
    
    def sample_sobol_sequence(self, n_samples: int,
                             random_state: Optional[int] = None) -> np.ndarray:
        """
        Sobol sequence sampling (quasi-Monte Carlo).
        Better convergence than random sampling.
        """
        sampler = qmc.Sobol(d=self.n_params, scramble=True, seed=random_state)
        
        # Get next power of 2
        n_sobol = 2 ** int(np.ceil(np.log2(n_samples)))
        unit_samples = sampler.random(n=n_sobol)[:n_samples]
        
        # Transform to distributions (same as LHS)
        samples = np.zeros((n_samples, self.n_params))
        
        for i, param in enumerate(self.parameters):
            if param.distribution == 'normal':
                std = param.uncertainty
                samples[:, i] = norm.ppf(unit_samples[:, i], 
                                        loc=param.nominal, scale=std)
            elif param.distribution == 'uniform':
                low, high = param.uncertainty
                samples[:, i] = uniform.ppf(unit_samples[:, i], 
                                           loc=low, scale=high-low)
            else:
                samples[:, i] = norm.ppf(unit_samples[:, i], 
                                        loc=param.nominal, scale=0.1*param.nominal)
        
        return samples


class UncertaintyPropagation:
    """
    Propagate uncertainties through reactor model.
    """
    
    def __init__(self, parameters: List[UncertainParameter],
                 model: Callable,
                 output_names: List[str]):
        self.parameters = parameters
        self.model = model
        self.output_names = output_names
        self.sampler = MonteCarloSampler(parameters)
        self.console = Console()
    
    def propagate(self, n_samples: int = 1000, 
                 method: str = 'lhs',
                 random_state: Optional[int] = None,
                 parallel: bool = True) -> UQResults:
        """
        Propagate uncertainties through model.
        
        Args:
            n_samples: Number of Monte Carlo samples
            method: 'mc', 'lhs', or 'sobol'
            random_state: Random seed
            parallel: Use parallel evaluation (if supported)
        
        Returns:
            UQResults object
        """
        self.console.print(f"[bold cyan]Uncertainty Propagation[/bold cyan]")
        self.console.print(f"Parameters: {len(self.parameters)}")
        self.console.print(f"Samples: {n_samples}")
        self.console.print(f"Method: {method.upper()}")
        
        # Generate samples
        if method == 'mc':
            samples = self.sampler.sample_monte_carlo(n_samples, random_state)
        elif method == 'lhs':
            samples = self.sampler.sample_latin_hypercube(n_samples, random_state)
        elif method == 'sobol':
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
                params = {p.name: samples[i, j] 
                         for j, p in enumerate(self.parameters)}
                
                # Run model
                result = self.model(params)
                
                # Extract outputs
                if isinstance(result, dict):
                    outputs[i, :] = [result[name] for name in self.output_names]
                else:
                    outputs[i, :] = result
                
                progress.update(task, advance=1)
        
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
            percentiles=percentiles
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
                f"[{p5:.4g}, {p95:.4g}]"
            )
        
        self.console.print(table)


class SensitivityAnalysis:
    """
    Global sensitivity analysis using Sobol indices and Morris method.
    """
    
    def __init__(self, parameters: List[UncertainParameter],
                 model: Callable,
                 output_names: List[str]):
        self.parameters = parameters
        self.model = model
        self.output_names = output_names
        self.console = Console()
    
    def sobol_analysis(self, n_samples: int = 1024,
                      calc_second_order: bool = True) -> Dict:
        """
        Sobol sensitivity analysis.
        Computes first-order and total-order indices.
        
        Args:
            n_samples: Base sample size (actual evaluations = n*(2*d+2))
            calc_second_order: Compute second-order interactions
        
        Returns:
            Dict of Sobol indices
        """
        self.console.print(f"[bold cyan]Sobol Sensitivity Analysis[/bold cyan]")
        
        # Define problem for SALib
        problem = {
            'num_vars': len(self.parameters),
            'names': [p.name for p in self.parameters],
            'bounds': [[p.uncertainty[0], p.uncertainty[1]] 
                      if isinstance(p.uncertainty, tuple)
                      else [p.nominal - 3*p.uncertainty, p.nominal + 3*p.uncertainty]
                      for p in self.parameters]
        }
        
        # Generate Saltelli samples
        param_samples = saltelli.sample(problem, n_samples, 
                                       calc_second_order=calc_second_order)
        
        n_evals = param_samples.shape[0]
        self.console.print(f"Total model evaluations: {n_evals}")
        
        # Evaluate model
        n_outputs = len(self.output_names)
        Y = np.zeros((n_evals, n_outputs))
        
        for i in track(range(n_evals), description="Evaluating..."):
            params = {name: param_samples[i, j] 
                     for j, name in enumerate(problem['names'])}
            result = self.model(params)
            
            if isinstance(result, dict):
                Y[i, :] = [result[name] for name in self.output_names]
            else:
                Y[i, :] = result
        
        # Analyze each output
        sobol_results = {}
        
        for i, output_name in enumerate(self.output_names):
            Si = sobol.analyze(problem, Y[:, i], 
                             calc_second_order=calc_second_order)
            sobol_results[output_name] = Si
        
        # Print results
        self._print_sobol_results(sobol_results)
        
        return sobol_results
    
    def _print_sobol_results(self, results: Dict):
        """Print Sobol indices."""
        for output_name, Si in results.items():
            self.console.print(f"\n[bold]Output: {output_name}[/bold]")
            
            table = Table()
            table.add_column("Parameter", style="cyan")
            table.add_column("S1 (First Order)", justify="right")
            table.add_column("ST (Total Order)", justify="right")
            table.add_column("Importance", style="yellow")
            
            # Sort by total order index
            indices = np.argsort(Si['ST'])[::-1]
            
            for idx in indices:
                param_name = self.parameters[idx].name
                s1 = Si['S1'][idx]
                st = Si['ST'][idx]
                
                # Importance classification
                if st > 0.5:
                    importance = "High"
                elif st > 0.1:
                    importance = "Medium"
                else:
                    importance = "Low"
                
                table.add_row(
                    param_name,
                    f"{s1:.3f}",
                    f"{st:.3f}",
                    importance
                )
            
            self.console.print(table)
    
    def morris_screening(self, n_trajectories: int = 10,
                        n_levels: int = 4) -> Dict:
        """
        Morris one-at-a-time screening method.
        Fast method to identify important parameters.
        
        Args:
            n_trajectories: Number of trajectories
            n_levels: Number of grid levels
        
        Returns:
            Dict of Morris indices (mu_star, sigma)
        """
        self.console.print(f"[bold cyan]Morris Screening[/bold cyan]")
        
        # Define problem
        problem = {
            'num_vars': len(self.parameters),
            'names': [p.name for p in self.parameters],
            'bounds': [[p.uncertainty[0], p.uncertainty[1]] 
                      if isinstance(p.uncertainty, tuple)
                      else [p.nominal - 3*p.uncertainty, p.nominal + 3*p.uncertainty]
                      for p in self.parameters]
        }
        
        # Generate Morris samples
        param_samples = morris.sample(problem, n_trajectories, 
                                     num_levels=n_levels)
        
        n_evals = param_samples.shape[0]
        self.console.print(f"Total evaluations: {n_evals}")
        
        # Evaluate
        n_outputs = len(self.output_names)
        Y = np.zeros((n_evals, n_outputs))
        
        for i in track(range(n_evals), description="Evaluating..."):
            params = {name: param_samples[i, j] 
                     for j, name in enumerate(problem['names'])}
            result = self.model(params)
            
            if isinstance(result, dict):
                Y[i, :] = [result[name] for name in self.output_names]
            else:
                Y[i, :] = result
        
        # Analyze
        morris_results = {}
        
        for i, output_name in enumerate(self.output_names):
            Si = morris.analyze(problem, param_samples, Y[:, i])
            morris_results[output_name] = Si
        
        self._print_morris_results(morris_results)
        
        return morris_results
    
    def _print_morris_results(self, results: Dict):
        """Print Morris indices."""
        for output_name, Si in results.items():
            self.console.print(f"\n[bold]Output: {output_name}[/bold]")
            
            table = Table()
            table.add_column("Parameter", style="cyan")
            table.add_column("μ* (Importance)", justify="right")
            table.add_column("σ (Interactions)", justify="right")
            table.add_column("Classification", style="yellow")
            
            mu_star = Si['mu_star']
            sigma = Si['sigma']
            
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
                    classification
                )
            
            self.console.print(table)


class VisualizationTools:
    """
    Visualization tools for UQ results.
    """
    
    @staticmethod
    def plot_distributions(results: UQResults, output_idx: int = 0,
                          figsize: Tuple[int, int] = (12, 8)):
        """Plot output distribution with statistics."""
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        
        output_name = results.output_names[output_idx]
        data = results.output_samples[:, output_idx]
        
        # Histogram
        axes[0, 0].hist(data, bins=50, density=True, alpha=0.7, color='steelblue')
        axes[0, 0].axvline(results.mean[output_idx], color='red', 
                          linestyle='--', label='Mean')
        axes[0, 0].axvline(results.percentiles[5][output_idx], color='orange',
                          linestyle='--', label='5/95 percentile')
        axes[0, 0].axvline(results.percentiles[95][output_idx], color='orange',
                          linestyle='--')
        axes[0, 0].set_xlabel(output_name)
        axes[0, 0].set_ylabel('Density')
        axes[0, 0].legend()
        axes[0, 0].set_title('Distribution')
        
        # Cumulative distribution
        sorted_data = np.sort(data)
        cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
        axes[0, 1].plot(sorted_data, cdf, linewidth=2)
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].set_xlabel(output_name)
        axes[0, 1].set_ylabel('CDF')
        axes[0, 1].set_title('Cumulative Distribution')
        
        # Box plot
        axes[1, 0].boxplot(data, vert=True)
        axes[1, 0].set_ylabel(output_name)
        axes[1, 0].set_title('Box Plot')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Q-Q plot
        from scipy import stats
        stats.probplot(data, dist="norm", plot=axes[1, 1])
        axes[1, 1].set_title('Q-Q Plot (Normal)')
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def plot_scatter_matrix(results: UQResults, max_params: int = 6,
                           output_idx: int = 0):
        """Scatter matrix showing parameter correlations with output."""
        n_params = min(len(results.parameter_names), max_params)
        
        # Create dataframe
        data_dict = {}
        for i in range(n_params):
            data_dict[results.parameter_names[i]] = results.parameter_samples[:, i]
        data_dict[results.output_names[output_idx]] = results.output_samples[:, output_idx]
        
        df = pl.DataFrame(data_dict).to_pandas()
        
        # Scatter matrix
        fig = sns.pairplot(df, diag_kind='kde', corner=True,
                          plot_kws={'alpha': 0.6, 's': 20})
        fig.fig.suptitle(f'Parameter-Output Correlations: {results.output_names[output_idx]}',
                        y=1.02)
        
        return fig
    
    @staticmethod
    def plot_sobol_indices(sobol_results: Dict, output_name: str,
                          parameter_names: List[str]):
        """Plot Sobol sensitivity indices."""
        Si = sobol_results[output_name]
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # First order
        axes[0].barh(parameter_names, Si['S1'], color='steelblue')
        axes[0].set_xlabel('First Order Index (S1)')
        axes[0].set_title('Direct Effect')
        axes[0].grid(True, alpha=0.3, axis='x')
        
        # Total order
        axes[1].barh(parameter_names, Si['ST'], color='coral')
        axes[1].set_xlabel('Total Order Index (ST)')
        axes[1].set_title('Total Effect (incl. interactions)')
        axes[1].grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        return fig


# Example HTGR-specific UQ problem
def create_htgr_uq_problem() -> List[UncertainParameter]:
    """Create standard HTGR uncertainty parameters."""
    return [
        UncertainParameter(
            name='enrichment',
            distribution='normal',
            nominal=0.195,
            uncertainty=0.005,  # ±0.5%
            units='fraction',
            description='U-235 enrichment'
        ),
        UncertainParameter(
            name='fuel_density',
            distribution='normal',
            nominal=10.96,  # g/cm³ for UCO
            uncertainty=0.22,  # 2%
            units='g/cm³',
            description='Fuel kernel density'
        ),
        UncertainParameter(
            name='graphite_conductivity',
            distribution='normal',
            nominal=100.0,  # W/m-K at 300K
            uncertainty=10.0,  # 10%
            units='W/m-K',
            description='Graphite thermal conductivity'
        ),
        UncertainParameter(
            name='flow_rate',
            distribution='normal',
            nominal=8.0,
            uncertainty=0.4,  # 5%
            units='kg/s',
            description='Helium mass flow rate'
        ),
        UncertainParameter(
            name='power_peaking',
            distribution='uniform',
            nominal=1.5,
            uncertainty=(1.3, 1.7),
            units='dimensionless',
            description='Radial power peaking factor'
        ),
        UncertainParameter(
            name='doppler_coefficient',
            distribution='normal',
            nominal=-3.5e-5,
            uncertainty=0.5e-5,  # 14%
            units='dk/k/K',
            description='Doppler temperature coefficient'
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
        enr = params_dict['enrichment']
        rho_fuel = params_dict['fuel_density']
        k_g = params_dict['graphite_conductivity']
        mdot = params_dict['flow_rate']
        peaking = params_dict['power_peaking']
        alpha_D = params_dict['doppler_coefficient']
        
        # Simplified k_eff model
        k_base = 1.05
        k_eff = k_base + 2.0 * (enr - 0.195) + 0.001 * (rho_fuel - 10.96)
        
        # Peak fuel temperature (simplified)
        T_peak = 1200 + 100 * peaking + 50 * (8.0 - mdot) - 0.5 * (k_g - 100)
        
        return {
            'k_eff': k_eff,
            'T_peak_fuel': T_peak
        }
    
    # Uncertainty propagation
    uq = UncertaintyPropagation(
        parameters=params,
        model=simple_htgr_model,
        output_names=['k_eff', 'T_peak_fuel']
    )
    
    results = uq.propagate(n_samples=500, method='lhs', random_state=42)
    
    # Sensitivity analysis
    console.print("\n[bold]Running Sensitivity Analysis...[/bold]\n")
    sa = SensitivityAnalysis(params, simple_htgr_model, ['k_eff', 'T_peak_fuel'])
    
    sobol_results = sa.sobol_analysis(n_samples=256, calc_second_order=False)
    
    console.print("\n[bold green]UQ analysis complete![/bold green]")
