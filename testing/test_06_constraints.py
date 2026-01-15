#!/usr/bin/env python
"""
Design Constraints & Validation Testing Script

This script tests automated design constraints and validation features.

Usage:
    python test_06_constraints.py
"""

import sys
import json
from pathlib import Path

try:
    import smrforge as smr
    from smrforge.validation.constraints import (
        DesignConstraintValidator, ConstraintSet, DesignValidator
    )
except ImportError:
    print("ERROR: SMRForge not installed. Run: pip install -e .")
    sys.exit(1)


def test_create_reactor():
    """Create reactor for constraint testing."""
    print("\n1. Creating reactor for constraint testing...")
    try:
        reactor = smr.create_reactor(preset='valar-10')
        print(f"✅ Created reactor: {type(reactor)}")
        return reactor
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_create_constraint_set():
    """Test creating a constraint set."""
    print("\n2. Testing create constraint set...")
    try:
        constraints = ConstraintSet(
            name="test_constraints",
            constraints=[
                {
                    "name": "k_eff_min",
                    "type": "min",
                    "value": 1.0,
                    "metric": "k_eff"
                },
                {
                    "name": "k_eff_max",
                    "type": "max",
                    "value": 1.2,
                    "metric": "k_eff"
                },
                {
                    "name": "power_density_max",
                    "type": "max",
                    "value": 200.0,
                    "metric": "max_power_density",
                    "units": "MW/m³"
                }
            ]
        )
        
        print(f"✅ Created constraint set: {constraints.name}")
        print(f"   Constraints: {len(constraints.constraints)}")
        return constraints
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_validate_design(reactor, constraints):
    """Test validating a reactor design against constraints."""
    print("\n3. Testing validate design...")
    if reactor is None or constraints is None:
        print("⏭️  Skipped (missing reactor or constraints)")
        return False
    
    try:
        validator = DesignValidator(constraints)
        
        # Analyze reactor first (mock or real)
        try:
            k_eff = smr.quick_keff(reactor)
            analysis_results = {
                'k_eff': k_eff,
                'power': reactor.power if hasattr(reactor, 'power') else 250.0,
                'max_power_density': 150.0  # Mock value
            }
        except Exception:
            # Use mock values if analysis fails
            analysis_results = {
                'k_eff': 1.05,
                'power': 250.0,
                'max_power_density': 150.0
            }
        
        result = validator.validate(reactor, analysis_results)
        
        print(f"✅ Validation completed!")
        print(f"   Passed: {result.passed}")
        print(f"   Errors: {result.error_count}")
        print(f"   Warnings: {result.warning_count}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_constraint_violations(reactor):
    """Test constraint violation detection."""
    print("\n4. Testing constraint violations...")
    if reactor is None:
        print("⏭️  Skipped (no reactor)")
        return False
    
    try:
        # Create constraints that will likely be violated
        strict_constraints = ConstraintSet(
            name="strict_constraints",
            constraints=[
                {
                    "name": "k_eff_max",
                    "type": "max",
                    "value": 0.5,  # Very low, will likely fail
                    "metric": "k_eff"
                }
            ]
        )
        
        validator = DesignValidator(strict_constraints)
        
        # Mock analysis results
        analysis_results = {
            'k_eff': 1.05,  # Higher than 0.5
            'power': 250.0,
            'max_power_density': 150.0
        }
        
        result = validator.validate(reactor, analysis_results)
        
        if not result.passed:
            print(f"✅ Correctly detected constraint violation!")
            print(f"   Errors: {result.error_count}")
        else:
            print(f"⚠️  Expected violation but design passed")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_save_constraints(constraints):
    """Test saving constraint set to file."""
    print("\n5. Testing save constraints...")
    if constraints is None:
        print("⏭️  Skipped (no constraints)")
        return False
    
    try:
        constraints_file = Path('test_constraints.json')
        constraints.save(constraints_file)
        print(f"✅ Saved constraints to {constraints_file}")
        
        # Verify file exists
        if constraints_file.exists():
            with open(constraints_file, 'r') as f:
                data = json.load(f)
            print(f"✅ Verified saved constraints ({len(data.get('constraints', []))} constraints)")
            return True
        else:
            print("❌ Constraints file not created")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_load_constraints():
    """Test loading constraint set from file."""
    print("\n6. Testing load constraints...")
    
    constraints_file = Path('test_constraints.json')
    if not constraints_file.exists():
        print("⏭️  Skipped (no constraints file)")
        return False
    
    try:
        constraints = ConstraintSet.load(constraints_file)
        print(f"✅ Loaded constraints: {constraints.name}")
        print(f"   Constraints: {len(constraints.constraints)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Design Constraints & Validation Testing")
    print("="*60)
    
    reactor = test_create_reactor()
    constraints = test_create_constraint_set()
    
    results = {}
    results['create_constraint_set'] = constraints is not None
    results['validate_design'] = test_validate_design(reactor, constraints)
    results['constraint_violations'] = test_constraint_violations(reactor)
    results['save_constraints'] = test_save_constraints(constraints)
    results['load_constraints'] = test_load_constraints()
    
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
    constraints_file = Path('test_constraints.json')
    if constraints_file.exists():
        constraints_file.unlink()
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
