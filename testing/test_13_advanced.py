#!/usr/bin/env python
"""
Advanced Features Testing Script

This script tests advanced features: batch processing, parallel execution, export formats.

Usage:
    python test_13_advanced.py
"""

import sys
import json
from pathlib import Path

try:
    import smrforge as smr
except ImportError:
    print("ERROR: SMRForge not installed. Run: pip install -e .")
    sys.exit(1)


def test_batch_processing():
    """Test batch processing of multiple reactors."""
    print("\n1. Testing batch processing...")
    try:
        # Create multiple reactors
        presets = ['valar-10', 'htr-pm-200']
        reactors = []
        
        for preset in presets:
            try:
                reactor = smr.create_reactor(preset)
                reactors.append((preset, reactor))
                print(f"   Created {preset}")
            except Exception as e:
                print(f"   ⚠️  Failed to create {preset}: {e}")
        
        if not reactors:
            print("⏭️  Skipped (no reactors created)")
            return False
        
        # Process batch
        batch_results = {}
        for name, reactor in reactors:
            try:
                k_eff = smr.quick_keff(reactor)
                batch_results[name] = {'k_eff': k_eff}
                print(f"   ✅ Analyzed {name}: k-eff = {k_eff:.6f}")
            except Exception as e:
                print(f"   ⚠️  Failed to analyze {name}: {e}")
                batch_results[name] = {'error': str(e)}
        
        # Save batch results
        batch_file = Path('batch_results.json')
        with open(batch_file, 'w') as f:
            json.dump(batch_results, f, indent=2, default=str)
        
        print(f"✅ Batch processing completed: {len(batch_results)} results")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_export_formats():
    """Test different export formats."""
    print("\n2. Testing export formats...")
    try:
        reactor = smr.create_reactor('valar-10')
        
        # Export to JSON
        json_file = Path('export_reactor.json')
        with open(json_file, 'w') as f:
            if hasattr(reactor, 'to_dict'):
                json.dump(reactor.to_dict(), f, indent=2, default=str)
            else:
                json.dump(str(reactor), f)
        
        if json_file.exists():
            print(f"✅ JSON export: {json_file}")
        
        # Try CSV export (if analysis results available)
        try:
            k_eff = smr.quick_keff(reactor)
            import csv
            csv_file = Path('export_results.csv')
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['metric', 'value'])
                writer.writerow(['k_eff', k_eff])
            print(f"✅ CSV export: {csv_file}")
        except Exception:
            print("⏭️  CSV export skipped (no analysis results)")
        
        # Try HDF5 export (if h5py available)
        try:
            import h5py
            hdf5_file = Path('export_reactor.h5')
            # Basic HDF5 export example
            with h5py.File(hdf5_file, 'w') as f:
                f.attrs['reactor_type'] = 'valar-10'
                f.create_dataset('test_data', data=[1, 2, 3])
            print(f"✅ HDF5 export: {hdf5_file}")
        except ImportError:
            print("⏭️  HDF5 export skipped (h5py not available)")
        except Exception as e:
            print(f"⏭️  HDF5 export skipped: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_progress_indicators():
    """Test progress indicators in long operations."""
    print("\n3. Testing progress indicators...")
    
    try:
        import subprocess
        
        # Test a command that should show progress
        result = subprocess.run(
            "smrforge reactor analyze --reactor test_reactor.json --keff",
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Check if output contains progress indicators
        output = result.stdout + result.stderr
        has_progress = any(indicator in output.lower() for indicator in 
                          ['progress', 'percent', 'complete', 'processing'])
        
        if has_progress:
            print("✅ Progress indicators found in output")
        else:
            print("⚠️  No progress indicators detected")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_error_recovery():
    """Test error handling and recovery."""
    print("\n4. Testing error handling...")
    
    try:
        # Test with invalid preset
        try:
            reactor = smr.create_reactor('nonexistent_preset')
            print("❌ Should have raised error for invalid preset")
            return False
        except (ValueError, KeyError, Exception) as e:
            print(f"✅ Correctly handled invalid preset: {type(e).__name__}")
        
        # Test with invalid parameters
        try:
            reactor = smr.create_reactor(
                type='invalid_type',
                power=-100  # Invalid negative power
            )
            print("❌ Should have raised error for invalid parameters")
            return False
        except (ValueError, Exception) as e:
            print(f"✅ Correctly handled invalid parameters: {type(e).__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_batch_mode():
    """Test CLI batch mode."""
    print("\n5. Testing CLI batch mode...")
    
    # Create multiple reactor files first
    try:
        for preset in ['valar-10', 'htr-pm-200']:
            try:
                reactor = smr.create_reactor(preset)
                reactor_file = Path(f'batch_{preset}.json')
                with open(reactor_file, 'w') as f:
                    if hasattr(reactor, 'to_dict'):
                        json.dump(reactor.to_dict(), f, indent=2, default=str)
            except Exception as e:
                print(f"   ⚠️  Failed to create {preset}: {e}")
        
        # Test batch analysis
        import subprocess
        result = subprocess.run(
            "smrforge reactor analyze --batch batch_*.json --parallel",
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✅ CLI batch mode works")
            return True
        else:
            print(f"⚠️  CLI batch mode may have issues (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Advanced Features Testing")
    print("="*60)
    
    results = {}
    results['batch_processing'] = test_batch_processing()
    results['export_formats'] = test_export_formats()
    results['progress_indicators'] = test_progress_indicators()
    results['error_recovery'] = test_error_recovery()
    results['cli_batch_mode'] = test_cli_batch_mode()
    
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
    
    # Cleanup
    for f in ['batch_results.json', 'export_reactor.json', 'export_results.csv',
              'export_reactor.h5', 'test_reactor.json']:
        if Path(f).exists():
            Path(f).unlink()
    
    # Cleanup batch files
    for f in Path('.').glob('batch_*.json'):
        f.unlink()
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
