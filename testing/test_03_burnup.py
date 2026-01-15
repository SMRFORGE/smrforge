#!/usr/bin/env python
"""
Burnup Calculations Testing Script

This script tests burnup calculation features including checkpointing and visualization.

Usage:
    python test_03_burnup.py
"""

import sys
import json
from pathlib import Path

try:
    import smrforge as smr
    from smrforge.burnup import BurnupSolver, BurnupOptions
except ImportError:
    print("ERROR: SMRForge not installed. Run: pip install -e .")
    sys.exit(1)


def test_create_reactor():
    """Create reactor for burnup testing."""
    print("\n1. Creating reactor for burnup...")
    try:
        reactor = smr.create_reactor(preset='valar-10')
        print(f"✅ Created reactor: {type(reactor)}")
        return reactor
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_basic_burnup(reactor):
    """Test basic burnup calculation."""
    print("\n2. Testing basic burnup calculation...")
    if reactor is None:
        print("⏭️  Skipped (no reactor)")
        return False
    
    try:
        options = BurnupOptions(
            time_steps=10,
            time_units='days',
            power_density=100.0,
            adaptive_tracking=False
        )
        
        solver = BurnupSolver(reactor, options=options)
        print("Starting burnup calculation...")
        results = solver.solve()
        
        print(f"✅ Burnup calculation completed!")
        print(f"   Result type: {type(results)}")
        if isinstance(results, dict):
            print(f"   Result keys: {list(results.keys())}")
        
        # Save results
        results_file = Path('burnup_results.json')
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"✅ Saved results to {results_file}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_burnup_with_checkpointing(reactor):
    """Test burnup with checkpointing."""
    print("\n3. Testing burnup with checkpointing...")
    if reactor is None:
        print("⏭️  Skipped (no reactor)")
        return False
    
    try:
        checkpoint_dir = Path('./checkpoints')
        checkpoint_dir.mkdir(exist_ok=True)
        
        options = BurnupOptions(
            time_steps=15,
            time_units='days',
            power_density=100.0,
            checkpoint_interval=5,
            checkpoint_dir=checkpoint_dir
        )
        
        solver = BurnupSolver(reactor, options=options)
        print("Starting burnup calculation with checkpointing...")
        results = solver.solve()
        
        print(f"✅ Burnup with checkpointing completed!")
        
        # Check for checkpoint files
        checkpoint_files = list(checkpoint_dir.glob('*.h5'))
        print(f"✅ Created {len(checkpoint_files)} checkpoint files")
        for cf in checkpoint_files[:3]:  # Show first 3
            print(f"   - {cf.name}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_resume_from_checkpoint(reactor):
    """Test resuming from checkpoint."""
    print("\n4. Testing resume from checkpoint...")
    if reactor is None:
        print("⏭️  Skipped (no reactor)")
        return False
    
    checkpoint_dir = Path('./checkpoints')
    if not checkpoint_dir.exists():
        print("⏭️  Skipped (no checkpoint directory)")
        return False
    
    try:
        checkpoint_files = sorted(checkpoint_dir.glob('checkpoint_*.h5'))
        if not checkpoint_files:
            print("⏭️  Skipped (no checkpoint files found)")
            return False
        
        latest_checkpoint = checkpoint_files[-1]
        print(f"Resuming from: {latest_checkpoint}")
        
        options = BurnupOptions(
            time_steps=20,
            time_units='days',
            power_density=100.0,
            checkpoint_dir=checkpoint_dir
        )
        
        solver = BurnupSolver(reactor, options=options)
        solver.resume_from_checkpoint(latest_checkpoint)
        
        results = solver.solve()
        print(f"✅ Resumed from checkpoint and completed!")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_burnup_visualization():
    """Test burnup visualization."""
    print("\n5. Testing burnup visualization...")
    
    results_file = Path('burnup_results.json')
    if not results_file.exists():
        print("⏭️  Skipped (no results file)")
        return False
    
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        # Try to plot k-eff evolution if available
        if 'k_eff_history' in results or 'keff' in results:
            try:
                import matplotlib.pyplot as plt
                
                plt.figure(figsize=(10, 6))
                
                if 'k_eff_history' in results:
                    keff_data = results['k_eff_history']
                    times = results.get('times', range(len(keff_data)))
                    plt.plot(times, keff_data, 'b-o', label='k-eff')
                elif isinstance(results.get('keff'), list):
                    plt.plot(results['keff'], 'b-o', label='k-eff')
                
                plt.xlabel('Time Step')
                plt.ylabel('k-eff')
                plt.title('k-eff Evolution During Burnup')
                plt.grid(True)
                plt.legend()
                plt.savefig('burnup_keff_plot.png')
                plt.close()
                
                print(f"✅ Created visualization: burnup_keff_plot.png")
                return True
            except ImportError:
                print("⏭️  Skipped (matplotlib not available)")
                return False
        else:
            print("⏭️  Skipped (no k-eff data in results)")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Burnup Calculations Testing")
    print("="*60)
    
    reactor = test_create_reactor()
    
    results = {}
    results['basic_burnup'] = test_basic_burnup(reactor)
    results['burnup_checkpointing'] = test_burnup_with_checkpointing(reactor)
    results['resume_checkpoint'] = test_resume_from_checkpoint(reactor)
    results['visualization'] = test_burnup_visualization()
    
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
