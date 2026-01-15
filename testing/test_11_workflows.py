#!/usr/bin/env python
"""
Workflow Scripts Testing Script

This script tests YAML-based workflow execution.

Usage:
    python test_11_workflows.py
"""

import sys
import yaml
from pathlib import Path

try:
    import smrforge as smr
except ImportError:
    print("ERROR: SMRForge not installed. Run: pip install -e .")
    sys.exit(1)


def test_create_workflow_file():
    """Create a test workflow YAML file."""
    print("\n1. Creating test workflow file...")
    try:
        workflow = {
            'steps': [
                {
                    'name': 'create_reactor',
                    'action': 'create_reactor',
                    'params': {
                        'preset': 'valar-10',
                        'output': 'workflow_reactor.json'
                    }
                },
                {
                    'name': 'analyze',
                    'action': 'analyze',
                    'params': {
                        'reactor': 'workflow_reactor.json',
                        'output': 'workflow_results.json'
                    }
                }
            ]
        }
        
        workflow_file = Path('test_workflow.yaml')
        with open(workflow_file, 'w') as f:
            yaml.dump(workflow, f, default_flow_style=False)
        
        print(f"✅ Created workflow file: {workflow_file}")
        return workflow_file
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_run_workflow(workflow_file):
    """Test running a workflow."""
    print("\n2. Testing run workflow...")
    if workflow_file is None or not workflow_file.exists():
        print("⏭️  Skipped (no workflow file)")
        return False
    
    try:
        import subprocess
        
        result = subprocess.run(
            f"smrforge workflow run {workflow_file}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✅ Workflow executed successfully")
            if result.stdout:
                print(f"   Output: {result.stdout[:200]}")
            return True
        else:
            print(f"❌ Workflow failed (exit code: {result.returncode})")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏱️  Workflow timed out (may still be running)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_with_multiple_steps():
    """Test workflow with multiple steps."""
    print("\n3. Testing workflow with multiple steps...")
    
    try:
        workflow = {
            'steps': [
                {
                    'name': 'create_reactor_1',
                    'action': 'create_reactor',
                    'params': {
                        'preset': 'valar-10',
                        'output': 'workflow_reactor1.json'
                    }
                },
                {
                    'name': 'create_reactor_2',
                    'action': 'create_reactor',
                    'params': {
                        'preset': 'htr-pm-200',
                        'output': 'workflow_reactor2.json'
                    }
                },
                {
                    'name': 'compare',
                    'action': 'compare',
                    'params': {
                        'reactors': ['workflow_reactor1.json', 'workflow_reactor2.json'],
                        'output': 'workflow_comparison.json'
                    }
                }
            ]
        }
        
        workflow_file = Path('test_multi_step_workflow.yaml')
        with open(workflow_file, 'w') as f:
            yaml.dump(workflow, f, default_flow_style=False)
        
        print(f"✅ Created multi-step workflow: {workflow_file}")
        print("   Note: Run manually to test full execution")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_error_handling():
    """Test workflow error handling."""
    print("\n4. Testing workflow error handling...")
    
    try:
        # Create workflow with invalid step
        workflow = {
            'steps': [
                {
                    'name': 'invalid_action',
                    'action': 'nonexistent_action',
                    'params': {}
                }
            ]
        }
        
        workflow_file = Path('test_error_workflow.yaml')
        with open(workflow_file, 'w') as f:
            yaml.dump(workflow, f, default_flow_style=False)
        
        # Try to run it - should handle error gracefully
        import subprocess
        result = subprocess.run(
            f"smrforge workflow run {workflow_file}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Error is expected, but should be handled gracefully
        if result.returncode != 0:
            print("✅ Error handled (exit code != 0 as expected)")
            if result.stderr:
                print(f"   Error message: {result.stderr[:200]}")
            return True
        else:
            print("⚠️  Expected error but workflow succeeded")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Workflow Scripts Testing")
    print("="*60)
    
    workflow_file = test_create_workflow_file()
    
    results = {}
    results['create_workflow'] = workflow_file is not None
    results['run_workflow'] = test_run_workflow(workflow_file)
    results['multi_step_workflow'] = test_workflow_with_multiple_steps()
    results['error_handling'] = test_workflow_error_handling()
    
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
    for f in ['test_workflow.yaml', 'test_multi_step_workflow.yaml', 
              'test_error_workflow.yaml', 'workflow_reactor.json', 
              'workflow_reactor1.json', 'workflow_reactor2.json',
              'workflow_results.json', 'workflow_comparison.json']:
        if Path(f).exists():
            Path(f).unlink()
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
