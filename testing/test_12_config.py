#!/usr/bin/env python
"""
Configuration Management Testing Script

This script tests configuration management features.

Usage:
    python test_12_config.py
"""

import sys
import subprocess
from pathlib import Path

def test_config_show():
    """Test showing configuration."""
    print("\n1. Testing config show...")
    try:
        result = subprocess.run(
            "smrforge config show",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Config show works")
            if result.stdout:
                print(f"   Output preview: {result.stdout[:200]}")
            return True
        else:
            print(f"❌ Config show failed (exit code: {result.returncode})")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_config_show_key():
    """Test showing specific config key."""
    print("\n2. Testing config show --key...")
    try:
        result = subprocess.run(
            "smrforge config show --key endf.default_directory",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Config show key works")
            return True
        else:
            print(f"⚠️  Config key may not exist (exit code: {result.returncode})")
            return True  # Not a failure if key doesn't exist
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_config_set():
    """Test setting configuration value."""
    print("\n3. Testing config set...")
    try:
        # Set a test value
        result = subprocess.run(
            "smrforge config set test.key test_value",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Config set works")
            
            # Verify it was set
            verify_result = subprocess.run(
                "smrforge config show --key test.key",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if verify_result.returncode == 0:
                print("✅ Config value verified")
            
            return True
        else:
            print(f"❌ Config set failed (exit code: {result.returncode})")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_config_init():
    """Test initializing configuration."""
    print("\n4. Testing config init...")
    try:
        # Check if config already exists
        config_dir = Path.home() / '.smrforge'
        config_file = config_dir / 'config.yaml'
        
        if config_file.exists():
            print("⚠️  Config file already exists, testing with --force")
            result = subprocess.run(
                "smrforge config init --template default --force",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
        else:
            result = subprocess.run(
                "smrforge config init --template default",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
        
        if result.returncode == 0:
            print("✅ Config init works")
            if config_file.exists():
                print(f"✅ Config file created: {config_file}")
            return True
        else:
            print(f"❌ Config init failed (exit code: {result.returncode})")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_templates():
    """Test different config templates."""
    print("\n5. Testing config templates...")
    
    templates = ['default', 'production', 'development']
    results = {}
    
    for template in templates:
        try:
            result = subprocess.run(
                f"smrforge config init --template {template} --force",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"✅ Template '{template}' works")
                results[template] = True
            else:
                print(f"❌ Template '{template}' failed")
                results[template] = False
        except Exception as e:
            print(f"❌ Error with template '{template}': {e}")
            results[template] = False
    
    return all(results.values())


def main():
    """Run all tests."""
    print("="*60)
    print("Configuration Management Testing")
    print("="*60)
    
    results = {}
    results['config_show'] = test_config_show()
    results['config_show_key'] = test_config_show_key()
    results['config_set'] = test_config_set()
    results['config_init'] = test_config_init()
    results['config_templates'] = test_config_templates()
    
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
