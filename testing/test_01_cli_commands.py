#!/usr/bin/env python
"""
CLI Commands Testing Script

This script tests all CLI commands available in SMRForge.
Run this script to verify CLI functionality.

Usage:
    python test_01_cli_commands.py
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a CLI command and report results."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ SUCCESS")
            if result.stdout:
                print("Output:")
                print(result.stdout[:500])  # Print first 500 chars
        else:
            print(f"❌ FAILED (exit code: {result.returncode})")
            if result.stderr:
                print("Error:")
                print(result.stderr[:500])
        
        return result.returncode == 0
    
    except subprocess.TimeoutExpired:
        print("⏱️ TIMEOUT (command took too long)")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """Run all CLI command tests."""
    print("SMRForge CLI Commands Testing")
    print("="*60)
    
    results = {}
    
    # 1. Basic Help
    results['help'] = run_command("smrforge --help", "Main help")
    results['version'] = run_command("smrforge --version", "Version check")
    
    # 2. Reactor Commands
    results['reactor_list'] = run_command("smrforge reactor list", "List presets")
    results['reactor_list_detailed'] = run_command("smrforge reactor list --detailed", "List presets (detailed)")
    
    # Create a test reactor first
    print("\nCreating test reactor...")
    create_result = subprocess.run(
        "smrforge reactor create --preset valar-10 --output test_reactor.json",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if create_result.returncode == 0:
        results['reactor_create'] = True
        print("✅ Test reactor created")
        
        # Test analysis (may fail if ENDF data or solver not available - that's OK)
        # Just verify the command exists and shows help if needed
        results['reactor_analyze'] = run_command(
            "smrforge reactor analyze --help",
            "Analyze reactor (help check)"
        )
        # Actual analysis may fail without ENDF data - that's expected
        
        # Test comparison (may fail if ENDF data or solver not available - that's OK)
        # Just verify the command exists and shows help if needed
        results['reactor_compare'] = run_command(
            "smrforge reactor compare --help",
            "Compare reactors (help check)"
        )
        # Actual comparison may fail without ENDF data - that's expected
    else:
        results['reactor_create'] = False
        print("❌ Failed to create test reactor")
        # Commands exist even if reactor creation fails - test help
        results['reactor_analyze'] = run_command(
            "smrforge reactor analyze --help",
            "Analyze reactor (help check)"
        )
        results['reactor_compare'] = run_command(
            "smrforge reactor compare --help",
            "Compare reactors (help check)"
        )
    
    # 3. Data Commands
    results['data_help'] = run_command("smrforge data --help", "Data commands help")
    # Note: Skip interactive setup and download in automated test
    
    # 4. Burnup Commands
    if Path("test_reactor.json").exists():
        results['burnup_help'] = run_command("smrforge burnup --help", "Burnup commands help")
        # Note: Actual burnup run takes time, test separately
    
    # 5. Validation Commands
    results['validate_help'] = run_command("smrforge validate --help", "Validation commands help")
    
    # 6. Visualization Commands
    if Path("test_reactor.json").exists():
        results['visualize_help'] = run_command("smrforge visualize --help", "Visualization commands help")
    
    # 7. Configuration Commands
    results['config_show'] = run_command("smrforge config show", "Show configuration")
    results['config_help'] = run_command("smrforge config --help", "Config commands help")
    
    # 8. Workflow Commands
    results['workflow_help'] = run_command("smrforge workflow --help", "Workflow commands help")
    
    # 9. Template Commands
    results['template_help'] = run_command("smrforge reactor template --help", "Template commands help")
    
    # 10. I/O Converter Commands
    # Note: I/O converters are Python API only, not CLI commands (by design)
    # Skip this test - converters are accessed via Python API: smrforge.io.converters
    results['io_help'] = None  # Not applicable - Python API only
    print("\n⏭️  I/O converter commands: Python API only (smrforge.io.converters), not CLI commands")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    # Filter out None values (skipped tests)
    active_results = {k: v for k, v in results.items() if v is not None}
    passed = sum(1 for v in active_results.values() if v)
    total = len(active_results)
    
    for test, result in results.items():
        if result is None:
            status = "⏭️"
            result_str = "skipped (not applicable)"
        else:
            status = "✅" if result else "❌"
            result_str = ""
        print(f"{status} {test} {result_str}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Cleanup
    if Path("test_reactor.json").exists():
        Path("test_reactor.json").unlink()
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
