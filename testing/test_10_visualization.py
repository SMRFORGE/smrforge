#!/usr/bin/env python
"""
Visualization Features Testing Script

This script tests visualization features (geometry, flux, burnup plots).

Usage:
    python test_10_visualization.py
"""

import sys
from pathlib import Path

try:
    import smrforge as smr
    from smrforge.visualization import plot_core_layout
except ImportError:
    print("ERROR: SMRForge not installed. Run: pip install -e .")
    sys.exit(1)


def test_create_reactor():
    """Create reactor for visualization testing."""
    print("\n1. Creating reactor for visualization...")
    try:
        reactor = smr.create_reactor(preset='valar-10')
        print(f"✅ Created reactor: {type(reactor)}")
        return reactor
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_geometry_visualization_2d(reactor):
    """Test 2D geometry visualization."""
    print("\n2. Testing 2D geometry visualization...")
    if reactor is None:
        print("⏭️  Skipped (no reactor)")
        return False
    
    try:
        output_file = Path('geometry_2d.png')
        
        plot_core_layout(reactor, output_file=output_file)
        
        if output_file.exists():
            print(f"✅ Created 2D geometry plot: {output_file}")
            return True
        else:
            print("⚠️  Plot function completed but file not created")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_geometry_visualization_3d(reactor):
    """Test 3D geometry visualization."""
    print("\n3. Testing 3D geometry visualization...")
    if reactor is None:
        print("⏭️  Skipped (no reactor)")
        return False
    
    try:
        from smrforge.visualization import plot_mesh3d_plotly
        
        output_file = Path('geometry_3d.html')
        
        plot_mesh3d_plotly(reactor, output_file=output_file)
        
        if output_file.exists():
            print(f"✅ Created 3D geometry plot: {output_file}")
            return True
        else:
            print("⚠️  3D plot may have been displayed but not saved")
            return False
    except ImportError:
        print("⏭️  Skipped (plotly not available)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_burnup_visualization():
    """Test burnup visualization."""
    print("\n4. Testing burnup visualization...")
    
    # Check if we have burnup results
    burnup_file = Path('burnup_results.json')
    if not burnup_file.exists():
        print("⏭️  Skipped (no burnup results file)")
        print("   Run test_03_burnup.py first to generate results")
        return False
    
    try:
        import json
        import matplotlib.pyplot as plt
        
        with open(burnup_file, 'r') as f:
            results = json.load(f)
        
        # Try to plot k-eff evolution
        if 'k_eff_history' in results or 'keff' in results:
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
            
            output_file = Path('burnup_keff_plot.png')
            plt.savefig(output_file)
            plt.close()
            
            print(f"✅ Created burnup plot: {output_file}")
            return True
        else:
            print("⏭️  No k-eff data in results")
            return False
            
    except ImportError:
        print("⏭️  Skipped (matplotlib not available)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_flux_visualization():
    """Test flux distribution visualization."""
    print("\n5. Testing flux visualization...")
    
    try:
        from smrforge.visualization import plot_flux_on_geometry
        
        # This requires analysis results with flux data
        print("⏭️  Requires analysis results with flux data")
        print("   Run reactor analysis first to generate flux data")
        return False
    except ImportError:
        print("⏭️  Skipped (visualization module not available)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Visualization Features Testing")
    print("="*60)
    
    reactor = test_create_reactor()
    
    results = {}
    results['geometry_2d'] = test_geometry_visualization_2d(reactor)
    results['geometry_3d'] = test_geometry_visualization_3d(reactor)
    results['burnup_viz'] = test_burnup_visualization()
    results['flux_viz'] = test_flux_visualization()
    
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
    for f in ['geometry_2d.png', 'geometry_3d.html', 'burnup_keff_plot.png']:
        if Path(f).exists():
            Path(f).unlink()
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
