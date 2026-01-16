#!/usr/bin/env python
"""
Parameter Sweep Workflow Testing Script

This script tests the parameter sweep and sensitivity analysis workflow.

Usage:
    python test_04_parameter_sweep.py
"""

import sys
import json
from pathlib import Path

try:
    import smrforge as smr
    from smrforge.workflows.parameter_sweep import ParameterSweep, SweepConfig
except ImportError:
    print("ERROR: SMRForge not installed. Run: pip install -e .")
    sys.exit(1)


def test_create_reactor():
    """Create reactor for parameter sweep."""
    print("\n1. Creating reactor for parameter sweep...")
    try:
        reactor = smr.create_reactor('valar-10')
        print(f"✅ Created reactor: {type(reactor)}")
        return reactor
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_single_parameter_sweep(reactor):
    """Test single parameter sweep."""
    print("\n2. Testing single parameter sweep...")
    if reactor is None:
        print("⏭️  Skipped (no reactor)")
        return False
    
    try:
        # Create sweep configuration
        sweep_config = {
            'enrichment': SweepConfig(
                values=[0.15, 0.19, 0.23],
                param_type='reactor'
            )
        }
        
        # Create parameter sweep
        sweep = ParameterSweep(reactor, sweep_config)
        
        print("Running parameter sweep...")
        results = sweep.run(analysis='keff', parallel=False)
        
        print(f"✅ Parameter sweep completed!")
        print(f"   Results: {len(results) if results else 0} configurations")
        
        # Save results
        results_file = Path('sweep_results.json')
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"✅ Saved results to {results_file}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_parameter_sweep(reactor):
    """Test multi-parameter sweep."""
    print("\n3. Testing multi-parameter sweep...")
    if reactor is None:
        print("⏭️  Skipped (no reactor)")
        return False
    
    try:
        # Create sweep configuration with multiple parameters
        sweep_config = {
            'enrichment': SweepConfig(
                values=[0.17, 0.19, 0.21],
                param_type='reactor'
            ),
            'power': SweepConfig(
                values=[200, 250, 300],
                param_type='reactor'
            )
        }
        
        sweep = ParameterSweep(reactor, sweep_config)
        
        print("Running multi-parameter sweep...")
        results = sweep.run(analysis='keff', parallel=False)
        
        print(f"✅ Multi-parameter sweep completed!")
        print(f"   Total configurations: {len(results) if results else 0}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_range_sweep(reactor):
    """Test range-based parameter sweep."""
    print("\n4. Testing range-based parameter sweep...")
    if reactor is None:
        print("⏭️  Skipped (no reactor)")
        return False
    
    try:
        # Use range format: start:stop:step
        sweep_config = {
            'enrichment': SweepConfig(
                values='0.15:0.25:0.02',  # Range format
                param_type='reactor'
            )
        }
        
        sweep = ParameterSweep(reactor, sweep_config)
        results = sweep.run(analysis='keff', parallel=False)
        
        print(f"✅ Range sweep completed!")
        print(f"   Configurations: {len(results) if results else 0}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parallel_sweep(reactor):
    """Test parallel parameter sweep."""
    print("\n5. Testing parallel parameter sweep...")
    if reactor is None:
        print("⏭️  Skipped (no reactor)")
        return False
    
    try:
        sweep_config = {
            'enrichment': SweepConfig(
                values=[0.15, 0.17, 0.19, 0.21, 0.23],
                param_type='reactor'
            )
        }
        
        sweep = ParameterSweep(reactor, sweep_config)
        
        print("Running parallel parameter sweep...")
        results = sweep.run(analysis='keff', parallel=True, max_workers=2)
        
        print(f"✅ Parallel sweep completed!")
        print(f"   Configurations: {len(results) if results else 0}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_save_results():
    """Test saving sweep results."""
    print("\n6. Testing save results...")
    
    results_file = Path('sweep_results.json')
    if not results_file.exists():
        print("⏭️  Skipped (no results file)")
        return False
    
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        # Try to save as CSV if results are in DataFrame format
        try:
            import pandas as pd
            
            if isinstance(results, list):
                df = pd.DataFrame(results)
                csv_file = Path('sweep_results.csv')
                df.to_csv(csv_file, index=False)
                print(f"✅ Saved results to CSV: {csv_file}")
                return True
            else:
                print("⏭️  Results not in list format for CSV conversion")
                return False
        except ImportError:
            print("⏭️  Skipped (pandas not available)")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Parameter Sweep Workflow Testing")
    print("="*60)
    
    reactor = test_create_reactor()
    
    results = {}
    results['single_parameter'] = test_single_parameter_sweep(reactor)
    results['multi_parameter'] = test_multi_parameter_sweep(reactor)
    results['range_sweep'] = test_range_sweep(reactor)
    results['parallel_sweep'] = test_parallel_sweep(reactor)
    results['save_results'] = test_save_results()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅" if result else ("⏭️" if result is None else "❌")
        print(f"{status} {test}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
