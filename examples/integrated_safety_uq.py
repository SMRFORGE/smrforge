# examples/safety_with_uncertainty.py
"""
Integrated safety analysis with uncertainty quantification.
Demonstrates probabilistic safety assessment for HTGR transients.
"""

import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import matplotlib.pyplot as plt

# Import SMRForge modules
from smrforge.presets.htgr import ValarAtomicsReactor
from smrforge.safety.transients import (
    LOFCTransient, ATWSTransient, TransientConditions, TransientType
)
from smrforge.uncertainty.uq import (
    UncertainParameter, UncertaintyPropagation, SensitivityAnalysis,
    VisualizationTools
)


class ProbabilisticSafetyAnalysis:
    """
    Probabilistic safety analysis framework.
    Combines transient analysis with uncertainty quantification.
    """
    
    def __init__(self, reactor_spec, core_geometry):
        self.spec = reactor_spec
        self.geometry = core_geometry
        self.console = Console()
        
    def analyze_lofc_with_uncertainty(self, n_samples: int = 200) -> Dict:
        """
        LOFC analysis with propagated uncertainties.
        
        Uncertain parameters:
        - Initial power level
        - Decay heat curve parameters
        - Heat transfer coefficients
        - Material properties
        - Passive cooling effectiveness
        """
        self.console.print(Panel.fit(
            "[bold cyan]Probabilistic LOFC Analysis[/bold cyan]\n"
            f"Monte Carlo samples: {n_samples}",
            border_style="cyan"
        ))
        
        # Define uncertain parameters
        uncertain_params = [
            UncertainParameter(
                name='initial_power',
                distribution='normal',
                nominal=self.spec.power_thermal,
                uncertainty=0.02 * self.spec.power_thermal,  # 2% uncertainty
                units='W',
                description='Initial operating power'
            ),
            UncertainParameter(
                name='decay_heat_multiplier',
                distribution='normal',
                nominal=1.0,
                uncertainty=0.10,  # 10% uncertainty in decay heat
                units='dimensionless',
                description='Decay heat curve multiplier'
            ),
            UncertainParameter(
                name='passive_cooling_effectiveness',
                distribution='uniform',
                nominal=0.85,
                uncertainty=(0.70, 1.0),  # 70-100% effectiveness
                units='fraction',
                description='RCCS heat removal effectiveness'
            ),
            UncertainParameter(
                name='graphite_conductivity',
                distribution='normal',
                nominal=100.0,
                uncertainty=15.0,  # 15% uncertainty
                units='W/m-K',
                description='Graphite thermal conductivity'
            ),
            UncertainParameter(
                name='scram_delay',
                distribution='uniform',
                nominal=1.0,
                uncertainty=(0.5, 2.0),  # 0.5-2 seconds
                units='s',
                description='Time to scram insertion'
            ),
            UncertainParameter(
                name='initial_temperature',
                distribution='normal',
                nominal=1100.0,
                uncertainty=50.0,  # ±50K
                units='K',
                description='Initial average core temperature'
            ),
        ]
        
        # Define model wrapper
        def lofc_model(params_dict):
            """Run LOFC simulation with given parameters."""
            # Setup conditions
            conditions = TransientConditions(
                initial_power=params_dict['initial_power'],
                initial_temperature=params_dict['initial_temperature'],
                initial_flow_rate=8.0,
                initial_pressure=7.0e6,
                transient_type=TransientType.LOFC,
                trigger_time=0.0,
                scram_available=True,
                scram_delay=params_dict['scram_delay'],
                t_end=72*3600
            )
            
            # Run LOFC simulation (simplified for speed)
            lofc = LOFCTransient(self.spec, self.geometry)
            
            # Simplified result computation
            # In production, would run full transient
            result = self._simplified_lofc_calculation(
                params_dict, conditions
            )
            
            return result
        
        # Run UQ
        uq = UncertaintyPropagation(
            parameters=uncertain_params,
            model=lofc_model,
            output_names=['T_peak_fuel', 'time_to_peak', 'T_final']
        )
        
        results = uq.propagate(n_samples=n_samples, method='lhs', random_state=42)
        
        # Analyze results
        self._analyze_lofc_results(results)
        
        # Sensitivity analysis
        sa = SensitivityAnalysis(
            uncertain_params,
            lofc_model,
            ['T_peak_fuel', 'time_to_peak', 'T_final']
        )
        
        self.console.print("\n[bold]Running sensitivity analysis...[/bold]")
        sobol_results = sa.sobol_analysis(n_samples=128, calc_second_order=False)
        
        return {
            'uq_results': results,
            'sobol_results': sobol_results
        }
    
    def _simplified_lofc_calculation(self, params: Dict, 
                                    conditions: TransientConditions) -> Dict:
        """
        Simplified LOFC calculation for demonstration.
        Real implementation would use full point kinetics solver.
        """
        # Initial state
        P0 = params['initial_power']
        T0 = params['initial_temperature']
        
        # Decay heat parameters
        decay_mult = params['decay_heat_multiplier']
        
        # Passive cooling
        passive_eff = params['passive_cooling_effectiveness']
        k_graphite = params['graphite_conductivity']
        
        # Time points
        t = np.linspace(0, 72*3600, 1000)
        
        # Simplified decay heat
        P_decay = decay_mult * 0.066 * P0 * (t + 1)**(-0.2)
        
        # Heat capacity
        C_core = 1.74 * 800 * self.geometry.total_fuel_volume()  # J/K
        
        # Passive cooling rate (simplified)
        T = np.zeros_like(t)
        T[0] = T0
        
        for i in range(1, len(t)):
            dt = t[i] - t[i-1]
            
            # Energy balance
            Q_decay = P_decay[i]
            
            # Passive removal (radiation + convection)
            sigma = 5.67e-8
            epsilon = 0.8
            A_vessel = 50.0  # m²
            T_amb = 300.0
            
            Q_passive = passive_eff * epsilon * sigma * A_vessel * \
                       (T[i-1]**4 - T_amb**4) * (k_graphite / 100.0)
            
            # Update temperature
            dT = (Q_decay - Q_passive) * dt / C_core
            T[i] = T[i-1] + dT
        
        # Find peak
        idx_peak = np.argmax(T)
        T_peak = T[idx_peak]
        t_peak = t[idx_peak]
        T_final = T[-1]
        
        return {
            'T_peak_fuel': T_peak,
            'time_to_peak': t_peak,
            'T_final': T_final
        }
    
    def _analyze_lofc_results(self, results):
        """Analyze and print LOFC UQ results."""
        self.console.print("\n[bold cyan]LOFC Results with Uncertainty[/bold cyan]\n")
        
        # Peak temperature analysis
        T_peak_samples = results.output_samples[:, 0]
        T_limit = self.spec.max_fuel_temperature
        
        # Probability of exceeding limit
        n_exceed = np.sum(T_peak_samples > T_limit)
        prob_exceed = n_exceed / len(T_peak_samples)
        
        table = Table(title="Peak Fuel Temperature Statistics")
        table.add_column("Statistic", style="cyan")
        table.add_column("Value", justify="right", style="yellow")
        table.add_column("Units", style="green")
        
        table.add_row("Mean", f"{results.mean[0]:.1f}", "K")
        table.add_row("Std Dev", f"{results.std[0]:.1f}", "K")
        table.add_row("5th percentile", f"{results.percentiles[5][0]:.1f}", "K")
        table.add_row("50th percentile", f"{results.percentiles[50][0]:.1f}", "K")
        table.add_row("95th percentile", f"{results.percentiles[95][0]:.1f}", "K")
        table.add_row("Design limit", f"{T_limit:.1f}", "K")
        table.add_row("Exceedance probability", f"{prob_exceed*100:.2f}", "%")
        
        self.console.print(table)
        
        # Safety assessment
        if prob_exceed < 0.001:  # < 0.1%
            self.console.print("\n[bold green]✓ Very low probability of exceeding limit[/bold green]")
        elif prob_exceed < 0.05:  # < 5%
            self.console.print("\n[bold yellow]⚠ Low but non-negligible probability[/bold yellow]")
        else:
            self.console.print("\n[bold red]✗ Significant probability of exceeding limit[/bold red]")
        
        # Confidence interval for peak temperature
        ci_95_low = results.percentiles[2.5][0] if 2.5 in results.percentiles else results.percentiles[5][0]
        ci_95_high = results.percentiles[97.5][0] if 97.5 in results.percentiles else results.percentiles[95][0]
        
        self.console.print(f"\n95% Confidence Interval: [{ci_95_low:.1f}, {ci_95_high:.1f}] K")
    
    def analyze_multiple_scenarios(self, n_samples: int = 100) -> Dict:
        """
        Analyze multiple accident scenarios with uncertainty.
        Compare safety margins across scenarios.
        """
        self.console.print(Panel.fit(
            "[bold cyan]Multi-Scenario Probabilistic Analysis[/bold cyan]\n"
            "Scenarios: LOFC, ATWS, RIA",
            border_style="cyan"
        ))
        
        scenarios = ['LOFC', 'ATWS', 'RIA']
        results_all = {}
        
        for scenario in scenarios:
            self.console.print(f"\n[bold]Analyzing {scenario}...[/bold]")
            
            if scenario == 'LOFC':
                results_all[scenario] = self.analyze_lofc_with_uncertainty(n_samples)
            # Add other scenarios similarly
        
        # Compare scenarios
        self._compare_scenarios(results_all)
        
        return results_all
    
    def _compare_scenarios(self, results: Dict):
        """Compare safety margins across scenarios."""
        self.console.print("\n[bold cyan]Scenario Comparison[/bold cyan]\n")
        
        table = Table()
        table.add_column("Scenario", style="cyan")
        table.add_column("Mean T_peak (K)", justify="right")
        table.add_column("95% T_peak (K)", justify="right")
        table.add_column("Exceedance Prob", justify="right")
        table.add_column("Safety Margin (K)", justify="right", style="green")
        
        T_limit = self.spec.max_fuel_temperature
        
        for scenario_name, scenario_results in results.items():
            uq_res = scenario_results['uq_results']
            
            mean_T = uq_res.mean[0]
            p95_T = uq_res.percentiles[95][0]
            
            T_peak_samples = uq_res.output_samples[:, 0]
            prob_exceed = np.sum(T_peak_samples > T_limit) / len(T_peak_samples)
            
            margin = T_limit - p95_T
            
            table.add_row(
                scenario_name,
                f"{mean_T:.1f}",
                f"{p95_T:.1f}",
                f"{prob_exceed*100:.2f}%",
                f"{margin:.1f}"
            )
        
        self.console.print(table)
    
    def importance_ranking(self, sobol_results: Dict) -> None:
        """
        Rank parameters by importance across all outputs.
        """
        self.console.print("\n[bold cyan]Parameter Importance Ranking[/bold cyan]\n")
        
        # Average total Sobol indices across outputs
        param_importance = {}
        
        for output_name, Si in sobol_results.items():
            for i, param_name in enumerate(Si['names']):
                if param_name not in param_importance:
                    param_importance[param_name] = []
                param_importance[param_name].append(Si['ST'][i])
        
        # Compute average importance
        avg_importance = {name: np.mean(indices) 
                         for name, indices in param_importance.items()}
        
        # Sort
        sorted_params = sorted(avg_importance.items(), 
                              key=lambda x: x[1], reverse=True)
        
        table = Table(title="Overall Parameter Importance")
        table.add_column("Rank", justify="right", style="cyan")
        table.add_column("Parameter", style="yellow")
        table.add_column("Avg ST Index", justify="right")
        table.add_column("Classification", style="green")
        
        for rank, (param, importance) in enumerate(sorted_params, 1):
            if importance > 0.5:
                classification = "Critical"
            elif importance > 0.2:
                classification = "Important"
            elif importance > 0.05:
                classification = "Moderate"
            else:
                classification = "Minor"
            
            table.add_row(
                str(rank),
                param,
                f"{importance:.3f}",
                classification
            )
        
        self.console.print(table)
        
        # Recommendations
        critical_params = [p for p, i in sorted_params if i > 0.5]
        
        if critical_params:
            self.console.print("\n[bold yellow]⚠ Recommendations:[/bold yellow]")
            self.console.print("Focus uncertainty reduction efforts on:")
            for param in critical_params:
                self.console.print(f"  • {param}")


def generate_safety_report(analysis_results: Dict, output_dir: Path):
    """
    Generate comprehensive safety analysis report.
    """
    output_dir.mkdir(exist_ok=True, parents=True)
    
    console = Console()
    console.print(f"\n[bold]Generating safety report...[/bold]")
    
    # 1. Save numerical results
    import json
    
    summary = {
        'analysis_type': 'Probabilistic Safety Analysis',
        'date': str(np.datetime64('today')),
        'scenarios': list(analysis_results.keys()),
    }
    
    with open(output_dir / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    # 2. Generate plots
    for scenario, results in analysis_results.items():
        uq_res = results['uq_results']
        
        # Distribution plots
        fig = VisualizationTools.plot_distributions(uq_res, output_idx=0)
        fig.savefig(output_dir / f'{scenario}_temperature_distribution.png', dpi=150)
        plt.close(fig)
        
        # Sobol indices
        if 'sobol_results' in results:
            sobol_res = results['sobol_results']
            for output_name in sobol_res.keys():
                fig = VisualizationTools.plot_sobol_indices(
                    sobol_res, output_name, 
                    [p.name for p in uq_res.parameter_names]
                )
                fig.savefig(output_dir / f'{scenario}_{output_name}_sobol.png', dpi=150)
                plt.close(fig)
    
    console.print(f"[green]Report saved to: {output_dir}[/green]")


if __name__ == "__main__":
    console = Console()
    console.print("[bold cyan]Integrated Safety Analysis with UQ[/bold cyan]\n")
    
    # Setup reactor
    reactor = ValarAtomicsReactor()
    core = reactor.build_core()
    
    # Run probabilistic safety analysis
    psa = ProbabilisticSafetyAnalysis(reactor.spec, core)
    
    # Single scenario analysis
    console.print("[bold]1. LOFC with Uncertainty Propagation[/bold]\n")
    lofc_results = psa.analyze_lofc_with_uncertainty(n_samples=200)
    
    # Importance ranking
    psa.importance_ranking(lofc_results['sobol_results'])
    
    # Generate visualizations
    uq_res = lofc_results['uq_results']
    
    console.print("\n[bold]Generating visualizations...[/bold]")
    fig1 = VisualizationTools.plot_distributions(uq_res, output_idx=0)
    fig1.savefig('lofc_temperature_distribution.png', dpi=150)
    
    fig2 = VisualizationTools.plot_scatter_matrix(uq_res, output_idx=0)
    fig2.savefig('lofc_parameter_correlations.png', dpi=150)
    
    console.print("[green]Plots saved![/green]")
    
    # Generate report
    output_dir = Path('./safety_analysis_results')
    generate_safety_report({'LOFC': lofc_results}, output_dir)
    
    console.print("\n[bold green]Integrated safety analysis complete![/bold green]")
    console.print(f"\nKey findings:")
    console.print(f"  • Peak temperature mean: {uq_res.mean[0]:.1f} K")
    console.print(f"  • 95% confidence: {uq_res.percentiles[95][0]:.1f} K")
    console.print(f"  • Design limit: {reactor.spec.max_fuel_temperature:.1f} K")
    
    T_peak_samples = uq_res.output_samples[:, 0]
    prob_exceed = np.sum(T_peak_samples > reactor.spec.max_fuel_temperature) / len(T_peak_samples)
    console.print(f"  • Probability of exceeding limit: {prob_exceed*100:.3f}%")
