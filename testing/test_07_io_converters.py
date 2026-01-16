#!/usr/bin/env python
"""
I/O Converters Testing Script

This script tests file format conversion capabilities (Serpent, OpenMC, etc.).

Usage:
    python test_07_io_converters.py
"""

import sys
import json
from pathlib import Path

try:
    import smrforge as smr
    from smrforge.io.converters import convert_file
except ImportError:
    print("ERROR: SMRForge not installed. Run: pip install -e .")
    sys.exit(1)


def test_create_reactor():
    """Create reactor for conversion testing."""
    print("\n1. Creating reactor for conversion...")
    try:
        reactor = smr.create_reactor('valar-10')
        
        # Save reactor to JSON for testing
        reactor_file = Path('test_reactor_for_conversion.json')
        with open(reactor_file, 'w') as f:
            if hasattr(reactor, 'to_dict'):
                json.dump(reactor.to_dict(), f, indent=2, default=str)
            else:
                json.dump(str(reactor), f)
        
        print(f"✅ Created and saved reactor: {reactor_file}")
        return reactor_file
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_convert_to_openmc(reactor_file):
    """Test converting to OpenMC format."""
    print("\n2. Testing convert to OpenMC format...")
    if reactor_file is None or not reactor_file.exists():
        print("⏭️  Skipped (no reactor file)")
        return False
    
    try:
        output_dir = Path('openmc_output')
        output_dir.mkdir(exist_ok=True)
        
        convert_file(
            input_file=reactor_file,
            output_file=str(output_dir / 'openmc_model'),
            from_format='smrforge',
            to_format='openmc'
        )
        
        # Check if output files were created
        if (output_dir / 'openmc_model').exists() or any(output_dir.iterdir()):
            print(f"✅ Converted to OpenMC format")
            print(f"   Output directory: {output_dir}")
            return True
        else:
            print("⚠️  Conversion completed but no output files found")
            return False
            
    except NotImplementedError as e:
        print(f"⏭️  Skipped (not yet implemented: {e})")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_convert_to_serpent(reactor_file):
    """Test converting to Serpent format."""
    print("\n3. Testing convert to Serpent format...")
    if reactor_file is None or not reactor_file.exists():
        print("⏭️  Skipped (no reactor file)")
        return False
    
    try:
        output_file = Path('serpent_model.sss2')
        
        convert_file(
            input_file=reactor_file,
            output_file=str(output_file),
            from_format='smrforge',
            to_format='serpent'
        )
        
        if output_file.exists():
            print(f"✅ Converted to Serpent format: {output_file}")
            return True
        else:
            print("⚠️  Conversion completed but output file not found")
            return False
            
    except NotImplementedError as e:
        print(f"⏭️  Skipped (not yet implemented: {e})")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_convert_from_openmc():
    """Test converting from OpenMC format."""
    print("\n4. Testing convert from OpenMC format...")
    
    # Check if we have an OpenMC model from previous conversion
    openmc_dir = Path('openmc_output')
    if not openmc_dir.exists():
        print("⏭️  Skipped (no OpenMC model available)")
        return False
    
    try:
        output_file = Path('converted_from_openmc.json')
        
        # Try to find OpenMC input files
        openmc_files = list(openmc_dir.glob('*.xml')) + list(openmc_dir.glob('geometry.xml'))
        
        if not openmc_files:
            print("⏭️  Skipped (no OpenMC XML files found)")
            return False
        
        convert_file(
            input_file=openmc_files[0],
            output_file=str(output_file),
            from_format='openmc',
            to_format='smrforge'
        )
        
        if output_file.exists():
            print(f"✅ Converted from OpenMC format: {output_file}")
            return True
        else:
            print("⚠️  Conversion completed but output file not found")
            return False
            
    except NotImplementedError as e:
        print(f"⏭️  Skipped (not yet implemented: {e})")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_convert_from_serpent():
    """Test converting from Serpent format."""
    print("\n5. Testing convert from Serpent format...")
    
    serpent_file = Path('serpent_model.sss2')
    if not serpent_file.exists():
        print("⏭️  Skipped (no Serpent model available)")
        return False
    
    try:
        output_file = Path('converted_from_serpent.json')
        
        convert_file(
            input_file=serpent_file,
            output_file=str(output_file),
            from_format='serpent',
            to_format='smrforge'
        )
        
        if output_file.exists():
            print(f"✅ Converted from Serpent format: {output_file}")
            return True
        else:
            print("⚠️  Conversion completed but output file not found")
            return False
            
    except NotImplementedError as e:
        print(f"⏭️  Skipped (not yet implemented: {e})")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("I/O Converters Testing")
    print("="*60)
    
    reactor_file = test_create_reactor()
    
    results = {}
    results['convert_to_openmc'] = test_convert_to_openmc(reactor_file)
    results['convert_to_serpent'] = test_convert_to_serpent(reactor_file)
    results['convert_from_openmc'] = test_convert_from_openmc()
    results['convert_from_serpent'] = test_convert_from_serpent()
    
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
    print("\nNote: Some converters may not be fully implemented yet.")
    print("This is expected - the framework is in place for future implementation.")
    
    # Cleanup
    for f in ['test_reactor_for_conversion.json', 'serpent_model.sss2', 
              'converted_from_openmc.json', 'converted_from_serpent.json']:
        if Path(f).exists():
            Path(f).unlink()
    
    import shutil
    if Path('openmc_output').exists():
        shutil.rmtree('openmc_output')
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
