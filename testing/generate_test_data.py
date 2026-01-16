#!/usr/bin/env python
"""
Test Data Generator for Manual Testing

This script generates test data files needed for testing features that
require data files (burnup results, flux data, etc.).

Usage:
    python generate_test_data.py
"""

import sys
import json
import numpy as np
from pathlib import Path

try:
    import smrforge as smr
except ImportError:
    print("ERROR: SMRForge not installed. Run: pip install -e .")
    sys.exit(1)


def generate_burnup_results():
    """Generate mock burnup results file for visualization testing."""
    print("\n1. Generating burnup results file...")
    
    # Create mock burnup results
    # Time steps in days
    time_steps = [0, 30, 60, 90, 180, 365, 730, 1095]  # 0 to 3 years
    
    # Mock k-eff evolution (typical: starts high, decreases with burnup)
    k_eff_history = [
        1.05,   # Initial
        1.04,   # 30 days
        1.03,   # 60 days
        1.02,   # 90 days
        1.00,   # 180 days
        0.98,   # 365 days (1 year)
        0.96,   # 730 days (2 years)
        0.94,   # 1095 days (3 years)
    ]
    
    # Mock nuclide concentrations (simplified)
    nuclides = ['U235', 'U238', 'Pu239', 'Pu240', 'Xe135']
    concentrations = {}
    for nuclide in nuclides:
        # Mock depletion curves (U235 decreases, Pu239 increases)
        if nuclide == 'U235':
            concentrations[nuclide] = [1e21 * (1 - 0.1 * i / len(time_steps)) 
                                       for i in range(len(time_steps))]
        elif nuclide == 'Pu239':
            concentrations[nuclide] = [1e19 * (1 + 0.5 * i / len(time_steps)) 
                                       for i in range(len(time_steps))]
        else:
            concentrations[nuclide] = [1e20] * len(time_steps)
    
    # Create burnup results dictionary
    burnup_results = {
        'times': time_steps,  # days
        'k_eff_history': k_eff_history,
        'keff': k_eff_history,  # Alternative key name
        'burnup_mwd_per_kg': [t * 10.0 for t in time_steps],  # Mock burnup values
        'nuclides': nuclides,
        'concentrations': concentrations,
        'metadata': {
            'power_density': 1e6,  # W/cm³
            'initial_enrichment': 0.195,
            'description': 'Mock burnup results for testing visualization'
        }
    }
    
    # Save to file
    output_file = Path('burnup_results.json')
    with open(output_file, 'w') as f:
        json.dump(burnup_results, f, indent=2, default=str)
    
    print(f"✅ Generated burnup results file: {output_file}")
    print(f"   Time steps: {len(time_steps)} ({time_steps[0]} to {time_steps[-1]} days)")
    print(f"   k-eff range: {min(k_eff_history):.3f} to {max(k_eff_history):.3f}")
    
    return output_file


def generate_flux_data():
    """Generate analysis results with flux data for visualization testing."""
    print("\n2. Generating flux data from reactor analysis...")
    
    try:
        # Create a reactor and run analysis to get real flux data
        reactor = smr.create_reactor('valar-10')
        print(f"✅ Created reactor: {reactor.spec.name}")
        
        # Try to solve for flux (may fail due to solver/convergence - that's OK)
        try:
            results = reactor.solve()
            print(f"✅ Analysis completed")
            
            # Save results with flux data
            flux_results = {
                'k_eff': float(results.get('k_eff', 1.0)),
                'flux': results.get('flux'),
                'flux_stats': {
                    'max': float(np.max(results.get('flux', [0]))) if isinstance(results.get('flux'), np.ndarray) else 0.0,
                    'min': float(np.min(results.get('flux', [0]))) if isinstance(results.get('flux'), np.ndarray) else 0.0,
                    'mean': float(np.mean(results.get('flux', [0]))) if isinstance(results.get('flux'), np.ndarray) else 0.0,
                },
                'power_distribution': results.get('power_distribution'),
                'metadata': {
                    'reactor_name': results.get('name', 'valar-10'),
                    'power_thermal_mw': results.get('power_thermal_mw', 10.0),
                    'description': 'Reactor analysis results with flux data'
                }
            }
            
            # Convert numpy arrays to lists for JSON serialization
            if isinstance(flux_results.get('flux'), np.ndarray):
                flux_array = flux_results['flux']
                # Store sample of flux data (not the full array which could be large)
                flux_results['flux_sample'] = flux_array.flatten()[:1000].tolist()
                flux_results['flux_shape'] = list(flux_array.shape)
            
            if isinstance(flux_results.get('power_distribution'), np.ndarray):
                power_array = flux_results['power_distribution']
                flux_results['power_sample'] = power_array.flatten()[:1000].tolist()
                flux_results['power_shape'] = list(power_array.shape)
            
            output_file = Path('flux_results.json')
            with open(output_file, 'w') as f:
                json.dump(flux_results, f, indent=2, default=str)
            
            print(f"✅ Generated flux results file: {output_file}")
            print(f"   k-eff: {flux_results['k_eff']:.6f}")
            if flux_results.get('flux_stats'):
                print(f"   Flux max: {flux_results['flux_stats']['max']:.2e} n/cm²/s")
            
            return output_file, reactor
            
        except (ValueError, RuntimeError) as e:
            # Solver may fail due to validation/convergence - create mock data
            print(f"⚠️  Solver failed (expected with approximate XS): {str(e)[:100]}")
            print("   Creating mock flux data instead...")
            
            # Create mock flux distribution
            n_points = 1000
            positions = np.linspace(0, 200, n_points)  # cm
            flux_values = 1e14 * np.exp(-positions / 50.0) * (1 + 0.1 * np.sin(positions / 10.0))
            
            flux_results = {
                'k_eff': 1.05,
                'flux_sample': flux_values.tolist(),
                'flux_shape': [n_points],
                'positions': positions.tolist(),
                'flux_stats': {
                    'max': float(np.max(flux_values)),
                    'min': float(np.min(flux_values)),
                    'mean': float(np.mean(flux_values)),
                },
                'power_distribution': (flux_values * 1e-10).tolist(),  # Mock power
                'metadata': {
                    'reactor_name': 'valar-10',
                    'power_thermal_mw': 10.0,
                    'description': 'Mock flux data for testing visualization (solver failed)'
                }
            }
            
            output_file = Path('flux_results.json')
            with open(output_file, 'w') as f:
                json.dump(flux_results, f, indent=2)
            
            print(f"✅ Generated mock flux results file: {output_file}")
            print(f"   Flux max: {flux_results['flux_stats']['max']:.2e} n/cm²/s")
            
            return output_file, reactor
            
    except Exception as e:
        print(f"❌ Error generating flux data: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def create_checkpoint_file():
    """Create a mock checkpoint file for burnup resume testing."""
    print("\n3. Creating mock checkpoint file...")
    
    try:
        import h5py
        
        checkpoint_dir = Path('./checkpoints')
        checkpoint_dir.mkdir(exist_ok=True)
        
        checkpoint_file = checkpoint_dir / 'checkpoint_5.0.h5'
        
        # Create HDF5 checkpoint file
        with h5py.File(checkpoint_file, 'w') as f:
            # Save checkpoint metadata
            f.attrs['time_days'] = 5.0
            f.attrs['time_step_index'] = 1
            f.attrs['checkpoint_version'] = '1.0'
            
            # Mock nuclide data
            nuclides = ['U235', 'U238', 'Pu239']
            for nuclide in nuclides:
                grp = f.create_group(f'nuclide_{nuclide}')
                grp.attrs['Z'] = 92 if 'U' in nuclide else 94
                grp.attrs['A'] = int(nuclide[-3:])
                grp.create_dataset('concentration', data=[1e21, 1e21])  # Two time steps
            
            # Mock burnup data
            burnup_grp = f.create_group('burnup')
            burnup_grp.create_dataset('values', data=[0.0, 5.0])  # MWd/kgU
            burnup_grp.create_dataset('times', data=[0.0, 5.0])  # days
        
        print(f"✅ Created checkpoint file: {checkpoint_file}")
        print(f"   Time: 5.0 days")
        print(f"   Nuclides: {len(nuclides)}")
        
        return checkpoint_file
        
    except ImportError:
        print("⏭️  Skipped (h5py not available for checkpoint creation)")
        return None
    except Exception as e:
        print(f"⚠️  Error creating checkpoint: {e}")
        return None


def setup_validation_benchmark_data():
    """Setup mock benchmark data for validation testing."""
    print("\n4. Setting up validation benchmark data...")
    
    # Note: ValidationBenchmarker is in tests module
    # For now, just document what would be needed
    benchmark_data = {
        'description': 'Mock benchmark data for validation testing',
        'benchmarks': {
            'test_benchmark': {
                'k_eff': 1.050,
                'uncertainty': 0.001,
                'source': 'Mock benchmark',
                'description': 'Test benchmark for validation testing'
            }
        }
    }
    
    # Save benchmark data file
    benchmark_file = Path('test_benchmark_data.json')
    with open(benchmark_file, 'w') as f:
        json.dump(benchmark_data, f, indent=2)
    
    print(f"✅ Created benchmark data file: {benchmark_file}")
    print("   Note: ValidationBenchmarker requires integration with tests module")
    print("   This file can be used when benchmarker is properly initialized")
    
    return benchmark_file


def generate_parameter_sweep_results():
    """Generate mock parameter sweep results for testing."""
    print("\n5. Generating parameter sweep results...")
    
    try:
        from smrforge.workflows.parameter_sweep import SweepConfig, SweepResult
        
        # Create a mock SweepConfig
        config = SweepConfig(
            parameters={
                'enrichment': [0.10, 0.15, 0.20, 0.25],  # 4 values
                'power_mw': [50, 75, 100]  # 3 values
            },
            analysis_types=['keff'],
            reactor_template={'name': 'valar-10'},
            output_dir=Path('sweep_results'),
            parallel=False,
            save_intermediate=True
        )
        
        # Generate mock results for all combinations (4 * 3 = 12 cases)
        results = []
        enrichments = config.get_parameter_values('enrichment')
        powers = config.get_parameter_values('power_mw')
        
        for enrichment in enrichments:
            for power in powers:
                # Mock k-eff calculation (realistic: higher enrichment -> higher k-eff)
                # Add some noise for realism
                base_keff = 1.0 + (enrichment - 0.15) * 2.0 + (power - 75) * 0.001
                noise = np.random.normal(0, 0.01)  # Small random variation
                k_eff = base_keff + noise
                
                results.append({
                    'enrichment': float(enrichment),
                    'power_mw': float(power),
                    'k_eff': float(k_eff),
                    'success': True,
                    'case_id': len(results) + 1
                })
        
        # Calculate summary statistics
        k_eff_values = [r['k_eff'] for r in results]
        summary_stats = {
            'total_cases': len(results),
            'successful_cases': len(results),
            'failed_cases': 0,
            'k_eff': {
                'mean': float(np.mean(k_eff_values)),
                'std': float(np.std(k_eff_values)),
                'min': float(np.min(k_eff_values)),
                'max': float(np.max(k_eff_values))
            },
            'enrichment': {
                'mean': float(np.mean([r['enrichment'] for r in results])),
                'range': [float(min([r['enrichment'] for r in results])), 
                         float(max([r['enrichment'] for r in results]))]
            },
            'power_mw': {
                'mean': float(np.mean([r['power_mw'] for r in results])),
                'range': [float(min([r['power_mw'] for r in results])), 
                         float(max([r['power_mw'] for r in results]))]
            }
        }
        
        # Create SweepResult object
        sweep_result = SweepResult(
            config=config,
            results=results,
            failed_cases=[],
            summary_stats=summary_stats
        )
        
        # Save to JSON file
        output_file = Path('sweep_results.json')
        sweep_result.save(output_file)
        
        print(f"✅ Generated parameter sweep results: {output_file}")
        print(f"   Total cases: {len(results)}")
        print(f"   Parameters: enrichment ({len(enrichments)} values), power_mw ({len(powers)} values)")
        print(f"   k-eff range: {summary_stats['k_eff']['min']:.4f} to {summary_stats['k_eff']['max']:.4f}")
        print(f"   Mean k-eff: {summary_stats['k_eff']['mean']:.4f}")
        
        return output_file
        
    except ImportError as e:
        print(f"⏭️  Skipped (could not import ParameterSweep: {e})")
        return None
    except Exception as e:
        print(f"⚠️  Error generating sweep results: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Generate all test data files."""
    print("="*60)
    print("Test Data Generator")
    print("="*60)
    print("\nGenerating test data files for manual testing...")
    
    results = {}
    
    # Generate burnup results
    burnup_file = generate_burnup_results()
    results['burnup_results'] = burnup_file is not None
    
    # Generate flux data
    flux_file, reactor = generate_flux_data()
    results['flux_data'] = flux_file is not None
    
    # Create checkpoint file
    checkpoint_file = create_checkpoint_file()
    results['checkpoint_file'] = checkpoint_file is not None
    
    # Setup benchmark data
    benchmark_file = setup_validation_benchmark_data()
    results['benchmark_data'] = benchmark_file is not None
    
    # Generate parameter sweep results
    sweep_file = generate_parameter_sweep_results()
    results['sweep_results'] = sweep_file is not None
    
    # Summary
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)
    
    for test, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {test}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\nTotal: {passed}/{total} data files generated")
    
    if passed == total:
        print("\n✅ All test data files generated successfully!")
        print("\nYou can now run:")
        print("  - test_03_burnup.py (burnup visualization)")
        print("  - test_04_parameter_sweep.py (parameter sweep save results)")
        print("  - test_10_visualization.py (burnup and flux visualization)")
        print("  - test_09_validation.py (with benchmark data)")
    else:
        print("\n⚠️  Some data files could not be generated")
        print("   Tests that require these files will be skipped")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
