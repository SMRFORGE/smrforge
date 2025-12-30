# examples/complete_workflow.py
"""
Complete SMRForge workflow demonstration.
Shows integration of all modules: geometry, neutronics, thermal, analysis.
"""

import numpy as np
from pathlib import Path
import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
import matplotlib.pyplot as plt

# Import SMRForge modules
from smrforge.presets.htgr import ValarAtomicsReactor, DesignLibrary
from smrforge.geometry import PrismaticCore
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.validation.models import SolverOptions
from smrforge.thermal import ChannelThermalHydraulics, ChannelGeometry
from smrforge.core import NuclearDataCache, CrossSectionTable, Nuclide, ResonanceSelfShielding
from smrforge.core.materials_database import MaterialDatabase
# Note: PerformanceProfiler, BenchmarkSuite, BenchmarkLibrary, BenchmarkRunner are not yet implemented
# Stub classes for now
class PerformanceProfiler:
    """Stub for PerformanceProfiler (not yet implemented)."""
    def __init__(self):
        pass
    def profile(self, name):
        """Context manager stub."""
        return self
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def print_report(self, top_n=10):
        """Stub method."""
        pass
    def export_results(self, path):
        """Stub method."""
        pass

class BenchmarkLibrary:
    """Stub for BenchmarkLibrary (not yet implemented)."""
    pass

class BenchmarkRunner:
    """Stub for BenchmarkRunner (not yet implemented)."""
    def __init__(self, library):
        self.library = library
    def run_suite(self, category, solver):
        """Stub method."""
        return {}


class HTGRAnalysisPipeline:
    """
    Complete HTGR analysis pipeline integrating all SMRForge capabilities.
    """
    
    def __init__(self, design_name: str = "valar-10"):
        self.console = Console()
        self.profiler = PerformanceProfiler()
        self.design_name = design_name
        
        # Will be populated
        self.reactor = None
        self.core = None
        self.xs_data = None
        self.neutronics_solver = None
        self.results = {}
    
    def run_complete_analysis(self):
        """Execute full analysis workflow."""
        
        self.console.print(Panel.fit(
            "[bold cyan]SMRForge Complete Analysis Pipeline[/bold cyan]\n"
            f"Design: {self.design_name}",
            border_style="cyan"
        ))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            # Step 1: Load design
            task1 = progress.add_task("Loading reference design...", total=1)
            with self.profiler.profile("load_design"):
                self._load_design()
            progress.update(task1, advance=1)
            
            # Step 2: Build geometry
            task2 = progress.add_task("Building core geometry...", total=1)
            with self.profiler.profile("build_geometry"):
                self._build_geometry()
            progress.update(task2, advance=1)
            
            # Step 3: Prepare nuclear data
            task3 = progress.add_task("Generating cross sections...", total=1)
            with self.profiler.profile("prepare_nuclear_data"):
                self._prepare_nuclear_data()
            progress.update(task3, advance=1)
            
            # Step 4: Solve neutronics
            task4 = progress.add_task("Solving neutronics (k-eff)...", total=1)
            with self.profiler.profile("solve_neutronics"):
                self._solve_neutronics()
            progress.update(task4, advance=1)
            
            # Step 5: Thermal-hydraulics
            task5 = progress.add_task("Computing thermal-hydraulics...", total=1)
            with self.profiler.profile("solve_thermal"):
                self._solve_thermal()
            progress.update(task5, advance=1)
            
            # Step 6: Safety analysis
            task6 = progress.add_task("Performing safety analysis...", total=1)
            with self.profiler.profile("safety_analysis"):
                self._safety_analysis()
            progress.update(task6, advance=1)
            
            # Step 7: Optimization
            task7 = progress.add_task("Running design optimization...", total=1)
            with self.profiler.profile("optimization"):
                self._design_optimization()
            progress.update(task7, advance=1)
        
        # Print results
        self._print_results()
        
        # Performance report
        self.profiler.print_report(top_n=10)
    
    def _load_design(self):
        """Load reference design from library."""
        library = DesignLibrary()
        spec = library.get_design(self.design_name)
        
        # Instantiate reactor
        self.reactor = ValarAtomicsReactor()
        self.results['specification'] = spec
    
    def _build_geometry(self):
        """Build core geometry."""
        self.core = self.reactor.build_core()
        
        self.results['geometry'] = {
            'n_blocks': len(self.core.blocks),
            'fuel_volume_cm3': self.core.total_fuel_volume(),
            'core_height_cm': self.core.core_height,
            'core_diameter_cm': self.core.core_diameter,
        }
    
    def _prepare_nuclear_data(self):
        """Prepare cross section data with self-shielding."""
        # Initialize nuclear data cache
        # Check for local ENDF directory (useful for Docker or offline use)
        import os
        from pathlib import Path
        
        # Try to find local ENDF directory
        local_endf_dir = None
        
        # Check environment variable first
        if os.getenv('SMRFORGE_ENDF_DIR'):
            local_endf_dir = Path(os.getenv('SMRFORGE_ENDF_DIR'))
        # Check standard locations
        elif (Path('/app/endf-data').exists()):
            # Docker container with mounted ENDF data
            local_endf_dir = Path('/app/endf-data')
        elif (Path.home() / 'ENDF-Data').exists():
            # Standard local directory
            local_endf_dir = Path.home() / 'ENDF-Data'
        elif (Path('C:/Users/cmwha/Downloads/ENDF-B-VIII.1').exists()):
            # User's specific directory (if exists)
            local_endf_dir = Path('C:/Users/cmwha/Downloads/ENDF-B-VIII.1')
        
        # Initialize cache with local directory if found
        if local_endf_dir and local_endf_dir.exists():
            print(f"Using local ENDF directory: {local_endf_dir}")
            cache = NuclearDataCache(local_endf_dir=local_endf_dir)
        else:
            print("No local ENDF directory found, will attempt automatic downloads")
            cache = NuclearDataCache()
        
        # Define fuel composition
        fuel_nuclides = [
            Nuclide(92, 235),  # U-235
            Nuclide(92, 238),  # U-238
            Nuclide(8, 16),    # O-16
            Nuclide(6, 12),    # C-12 (graphite)
        ]
        
        # Generate multi-group cross sections
        xs_table = CrossSectionTable(cache=cache)
        
        # 8-group structure optimized for HTGR
        from smrforge.core.constants import GROUP_STRUCTURES
        group_structure = GROUP_STRUCTURES['HTGR-8']
        
        # Generate at operating temperature
        T_fuel = 1200.0  # K
        
        xs_df = xs_table.generate_multigroup(
            nuclides=fuel_nuclides,
            reactions=['total', 'fission', 'capture', 'elastic'],
            group_structure=group_structure,
            temperature=T_fuel
        )
        
        print(f"Generated cross-section table with {len(xs_df)} entries")
        print(f"Available nuclides: {xs_df['nuclide'].unique().to_list()}")
        print(f"Available reactions: {xs_df['reaction'].unique().to_list()}")
        
        # Apply resonance self-shielding
        # Note: ResonanceSelfShielding may require additional setup
        try:
            shielding = ResonanceSelfShielding()
        except Exception as e:
            print(f"Warning: Resonance self-shielding initialization failed: {e}")
            print("Continuing without self-shielding...")
            shielding = None
        
        triso_geometry = {
            'kernel_radius': 212.5e-4,  # cm
            'buffer_thickness': 100e-4,
            'packing_fraction': 0.35
        }
        
        fuel_composition = {
            'U235': 0.0005,  # atoms/b-cm
            'U238': 0.0020,
            'O16': 0.0050,
        }
        
        if shielding is not None:
            shielded_xs = shielding.htgr_fuel_shielding(
                fuel_composition, triso_geometry, T_fuel
            )
        else:
            # Use unshielded cross-sections if self-shielding is not available
            shielded_xs = xs_df
            print("Using unshielded cross-sections (self-shielding not available)")
        
        # Get processed XS data (simplified - would combine with xs_table)
        self.xs_data = self.reactor.get_cross_sections()
        
        self.results['nuclear_data'] = {
            'n_groups': 8,
            'n_nuclides': len(fuel_nuclides),
            'temperature_K': T_fuel,
        }
    
    def _solve_neutronics(self):
        """Solve multi-group neutron diffusion."""
        options = SolverOptions(
            max_iterations=100,
            tolerance=1e-6,
            eigen_method="power",
            verbose=False
        )
        
        self.neutronics_solver = MultiGroupDiffusion(
            self.core, self.xs_data, options
        )
        
        # Solve for k-eff and flux
        k_eff, flux = self.neutronics_solver.solve_steady_state()
        
        # Compute power distribution
        power = self.neutronics_solver.compute_power_distribution(
            self.reactor.spec.power_thermal
        )
        
        # Compute reactivity coefficients
        coefficients = self.neutronics_solver.compute_reactivity_coefficients()
        
        self.results['neutronics'] = {
            'k_eff': k_eff,
            'peak_flux': np.max(flux),
            'peak_power_density_W_cm3': np.max(power),
            'avg_power_density_W_cm3': np.mean(power),
            'doppler_coefficient': coefficients['doppler'],
            'moderator_coefficient': coefficients['moderator'],
            'total_coefficient': coefficients['total'],
        }
    
    def _solve_thermal(self):
        """Solve thermal-hydraulics for representative channel."""
        # Select hottest channel
        power_dist = self.neutronics_solver.compute_power_distribution(
            self.reactor.spec.power_thermal
        )
        
        # Channel geometry
        geom = ChannelGeometry(
            length=self.reactor.spec.core_height,
            diameter=1.588,  # cm
            flow_area=1.98,  # cm²
            heated_perimeter=4.98
        )
        
        # Inlet conditions
        inlet = {
            'temperature': self.reactor.spec.inlet_temperature,
            'pressure': self.reactor.spec.primary_pressure,
            'mass_flow_rate': 0.05  # kg/s per channel
        }
        
        channel = ChannelThermalHydraulics(geom, inlet)
        
        # Set power profile (simplified: use axial average)
        z_centers = self.neutronics_solver.z_centers
        power_profile = np.mean(power_dist, axis=1)  # Radial average
        
        # Convert to linear power density [W/cm]
        channel_area = geom.flow_area
        q_linear = power_profile * channel_area
        
        channel.set_power_profile(q_linear)
        
        # Solve
        th_result = channel.solve_steady_state()
        
        self.results['thermal'] = {
            'outlet_temperature_K': th_result['T_coolant'][-1],
            'outlet_temperature_C': th_result['T_coolant'][-1] - 273,
            'max_wall_temperature_K': np.max(th_result['T_wall']),
            'pressure_drop_Pa': inlet['pressure'] - th_result['P_coolant'][-1],
            'delta_T_coolant_K': th_result['T_coolant'][-1] - th_result['T_coolant'][0],
        }
        
        # Check against design limits
        max_fuel_temp = self.reactor.spec.max_fuel_temperature
        actual_max = np.max(th_result['T_wall'])
        
        self.results['thermal']['margin_to_limit_K'] = max_fuel_temp - actual_max
        self.results['thermal']['design_margin_pct'] = 100 * (1 - actual_max / max_fuel_temp)
    
    def _safety_analysis(self):
        """Perform key safety calculations."""
        # 1. Shutdown margin
        k_eff = self.results['neutronics']['k_eff']
        
        # Estimate all-rods-in k_eff (simplified)
        rod_worth = 0.15  # Typical HTGR
        k_shutdown = k_eff - rod_worth
        shutdown_margin = (1.0 - k_shutdown) / k_shutdown
        
        # 2. Temperature coefficient check
        alpha_total = self.results['neutronics']['total_coefficient']
        
        # 3. LOFC transient peak temperature estimate
        # Simplified: assume decay heat removal through passive means
        decay_heat_fraction = 0.06  # 6% at shutdown
        decay_power = self.reactor.spec.power_thermal * decay_heat_fraction
        
        # Estimate temperature rise (very simplified)
        heat_capacity = 1.74 * 800 * self.core.total_fuel_volume()  # ρ*cp*V
        time_to_peak = 2 * 3600  # 2 hours
        delta_T_lofc = decay_power * time_to_peak / heat_capacity
        
        peak_temp_lofc = 1200 + delta_T_lofc  # Starting from 1200K
        
        self.results['safety'] = {
            'shutdown_margin': shutdown_margin,
            'shutdown_margin_target': self.reactor.spec.shutdown_margin,
            'shutdown_margin_ok': shutdown_margin > self.reactor.spec.shutdown_margin,
            'temp_coefficient_pcm_K': alpha_total * 1e5,  # Convert to pcm/K
            'temp_coefficient_negative': alpha_total < 0,
            'lofc_peak_temp_K': peak_temp_lofc,
            'lofc_peak_temp_C': peak_temp_lofc - 273,
            'lofc_margin_K': self.reactor.spec.max_fuel_temperature - peak_temp_lofc,
        }
    
    def _design_optimization(self):
        """Optimize key design parameters."""
        # Simplified optimization: evaluate sensitivity
        
        # Vary enrichment
        enrichments = np.linspace(0.15, 0.20, 5)
        k_eff_vs_enrichment = []
        
        for enr in enrichments:
            # Would re-run neutronics with new enrichment
            # Simplified: linear approximation
            k_base = self.results['neutronics']['k_eff']
            dk_denr = 0.5  # Rough estimate
            k_new = k_base + dk_denr * (enr - 0.195)
            k_eff_vs_enrichment.append(k_new)
        
        # Find optimal enrichment (k_eff closest to 1.05)
        target_k = 1.05
        errors = [abs(k - target_k) for k in k_eff_vs_enrichment]
        optimal_idx = np.argmin(errors)
        
        self.results['optimization'] = {
            'optimal_enrichment': enrichments[optimal_idx],
            'optimal_k_eff': k_eff_vs_enrichment[optimal_idx],
            'enrichment_range': (enrichments[0], enrichments[-1]),
        }
    
    def _print_results(self):
        """Print formatted results summary."""
        self.console.print("\n" + "="*70)
        self.console.print("[bold cyan]ANALYSIS RESULTS SUMMARY[/bold cyan]")
        self.console.print("="*70 + "\n")
        
        # Neutronics table
        table1 = Table(title="Neutronics Results", show_header=False)
        table1.add_column("Parameter", style="cyan")
        table1.add_column("Value", style="yellow", justify="right")
        table1.add_column("Units", style="green")
        
        neut = self.results['neutronics']
        table1.add_row("k-effective", f"{neut['k_eff']:.6f}", "")
        table1.add_row("Peak power density", f"{neut['peak_power_density_W_cm3']:.2f}", "W/cm³")
        table1.add_row("Avg power density", f"{neut['avg_power_density_W_cm3']:.2f}", "W/cm³")
        table1.add_row("Doppler coefficient", f"{neut['doppler_coefficient']*1e5:.2f}", "pcm/K")
        table1.add_row("Total temperature coef", f"{neut['total_coefficient']*1e5:.2f}", "pcm/K")
        
        self.console.print(table1)
        self.console.print()
        
        # Thermal table
        table2 = Table(title="Thermal-Hydraulics Results", show_header=False)
        table2.add_column("Parameter", style="cyan")
        table2.add_column("Value", style="yellow", justify="right")
        table2.add_column("Units", style="green")
        
        therm = self.results['thermal']
        table2.add_row("Outlet temperature", f"{therm['outlet_temperature_C']:.1f}", "°C")
        table2.add_row("Coolant ΔT", f"{therm['delta_T_coolant_K']:.1f}", "K")
        table2.add_row("Max wall temperature", f"{therm['max_wall_temperature_K']-273:.1f}", "°C")
        table2.add_row("Pressure drop", f"{therm['pressure_drop_Pa']/1000:.1f}", "kPa")
        table2.add_row("Design margin", f"{therm['design_margin_pct']:.1f}", "%")
        
        self.console.print(table2)
        self.console.print()
        
        # Safety table
        table3 = Table(title="Safety Analysis", show_header=False)
        table3.add_column("Parameter", style="cyan")
        table3.add_column("Value", style="yellow", justify="right")
        table3.add_column("Status", style="green")
        
        safety = self.results['safety']
        
        sdm_status = "✓ PASS" if safety['shutdown_margin_ok'] else "✗ FAIL"
        tc_status = "✓ PASS" if safety['temp_coefficient_negative'] else "✗ FAIL"
        lofc_status = "✓ PASS" if safety['lofc_margin_K'] > 0 else "✗ FAIL"
        
        table3.add_row("Shutdown margin", f"{safety['shutdown_margin']:.4f}", sdm_status)
        table3.add_row("Temp coefficient", f"{safety['temp_coefficient_pcm_K']:.2f} pcm/K", tc_status)
        table3.add_row("LOFC peak temp", f"{safety['lofc_peak_temp_C']:.0f}°C", lofc_status)
        table3.add_row("LOFC margin", f"{safety['lofc_margin_K']:.0f} K", "")
        
        self.console.print(table3)
        self.console.print("\n" + "="*70 + "\n")
    
    def export_results(self, output_dir: Path):
        """Export all results to files."""
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # JSON summary
        import json
        with open(output_dir / 'results_summary.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Geometry data
        self.core.to_dataframe().write_csv(output_dir / 'core_geometry.csv')
        
        # Performance profile
        self.profiler.export_results(output_dir / 'performance_profile.json')
        
        self.console.print(f"[green]Results exported to: {output_dir}[/green]")


if __name__ == "__main__":
    # Run complete analysis
    pipeline = HTGRAnalysisPipeline(design_name='valar-10')
    pipeline.run_complete_analysis()
    
    # Export results
    output_dir = Path('./results/valar-10')
    pipeline.export_results(output_dir)
    
    # Optional: Run benchmark validation
    console = Console()
    console.print("\n[bold]Running Benchmark Validation...[/bold]\n")
    
    bench_library = BenchmarkLibrary()
    runner = BenchmarkRunner(bench_library)
    
    # Run criticality benchmarks
    validation_results = runner.run_suite(category='criticality', solver=None)
    
    console.print("\n[bold green]Complete workflow finished successfully![/bold green]")
