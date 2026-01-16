#!/usr/bin/env python
"""
Reactor Creation and Analysis Testing Script

This script tests reactor creation, listing, analysis, and comparison features.

Usage:
    python test_02_reactor_creation.py
"""

import sys
import json
from pathlib import Path

try:
    import smrforge as smr
except ImportError:
    print("ERROR: SMRForge not installed. Run: pip install -e .")
    sys.exit(1)


def test_list_presets():
    """Test listing available presets."""
    print("\n1. Testing preset listing...")
    try:
        presets = smr.list_presets()
        print(f"✅ Found {len(presets)} presets: {presets}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_preset():
    """Test getting a specific preset."""
    print("\n2. Testing get preset...")
    try:
        preset = smr.get_preset('valar-10')
        print(f"✅ Got preset: {type(preset)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_create_from_preset():
    """Test creating reactor from preset."""
    print("\n3. Testing create reactor from preset...")
    try:
        reactor = smr.create_reactor('valar-10')
        print(f"✅ Created reactor: {type(reactor)}")
        
        # Save to file
        reactor_file = Path('test_reactor_preset.json')
        with open(reactor_file, 'w') as f:
            if hasattr(reactor, 'to_dict'):
                json.dump(reactor.to_dict(), f, indent=2, default=str)
            else:
                json.dump(str(reactor), f)
        print(f"✅ Saved to {reactor_file}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_custom():
    """Test creating reactor with custom parameters."""
    print("\n4. Testing create reactor with custom parameters...")
    try:
        reactor = smr.create_reactor(
            type='prismatic',
            power=300,
            enrichment=0.20,
            fuel_form='TRISO',
            coolant='helium'
        )
        print(f"✅ Created custom reactor: {type(reactor)}")
        
        # Save to file
        custom_file = Path('test_reactor_custom.json')
        with open(custom_file, 'w') as f:
            if hasattr(reactor, 'to_dict'):
                json.dump(reactor.to_dict(), f, indent=2, default=str)
            else:
                json.dump(str(reactor), f)
        print(f"✅ Saved to {custom_file}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quick_keff():
    """Test quick k-eff calculation."""
    print("\n5. Testing quick k-eff calculation...")
    try:
        reactor = smr.create_reactor('valar-10')
        keff = smr.quick_keff(reactor)
        print(f"✅ k-eff: {keff}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_analyze_preset():
    """Test analyzing a preset."""
    print("\n6. Testing analyze preset...")
    try:
        results = smr.analyze_preset('valar-10', analysis='keff')
        print(f"✅ Analysis results: {type(results)}")
        print(f"   Keys: {list(results.keys()) if isinstance(results, dict) else 'N/A'}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compare_designs():
    """Test comparing multiple designs."""
    print("\n7. Testing compare designs...")
    try:
        comparison = smr.compare_designs(
            designs=['valar-10', 'htr-pm-200'],
            metrics=['k_eff', 'power']
        )
        print(f"✅ Comparison results: {type(comparison)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Reactor Creation and Analysis Testing")
    print("="*60)
    
    results = {}
    results['list_presets'] = test_list_presets()
    results['get_preset'] = test_get_preset()
    results['create_from_preset'] = test_create_from_preset()
    results['create_custom'] = test_create_custom()
    results['quick_keff'] = test_quick_keff()
    results['analyze_preset'] = test_analyze_preset()
    results['compare_designs'] = test_compare_designs()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Cleanup
    for f in ['test_reactor_preset.json', 'test_reactor_custom.json']:
        if Path(f).exists():
            Path(f).unlink()
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
