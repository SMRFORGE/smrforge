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
    from smrforge.io.converters import SerpentConverter, OpenMCConverter
except ImportError as e:
    print(f"ERROR: SMRForge not installed. Run: pip install -e .")
    print(f"Import error: {e}")
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
        # Load reactor from file
        with open(reactor_file, 'r') as f:
            reactor_data = json.load(f)
        
        # Create reactor from data
        reactor = smr.create_reactor('valar-10')  # Use preset for testing
        
        # Try OpenMC converter
        try:
            # OpenMCConverter.export_reactor expects output_dir (directory), not file
            output_dir = Path('openmc_output')
            output_dir.mkdir(exist_ok=True)
            OpenMCConverter.export_reactor(reactor, output_dir)
            
            # Check for output files
            geometry_file = output_dir / 'geometry.xml'
            materials_file = output_dir / 'materials.xml'
            
            if geometry_file.exists() or materials_file.exists():
                print(f"✅ Converted to OpenMC format")
                print(f"   Output directory: {output_dir}")
                if geometry_file.exists():
                    print(f"   Created: {geometry_file.name}")
                if materials_file.exists():
                    print(f"   Created: {materials_file.name}")
                return True
            else:
                print("⚠️  Conversion completed but output files not found")
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
        # Load reactor from file
        reactor = smr.create_reactor('valar-10')  # Use preset for testing
        
        # Try Serpent converter
        try:
            output_file = Path('serpent_model.sss2')
            SerpentConverter.export_reactor(reactor, output_file)
            
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
    print("\n4. Testing convert from OpenMC format (import)...")
    
    # Check if we have an OpenMC model from previous conversion
    openmc_dir = Path('openmc_output')
    geometry_file = openmc_dir / 'geometry.xml' if openmc_dir.exists() else None
    
    if geometry_file is None or not geometry_file.exists():
        print("⏭️  Skipped (no OpenMC model available)")
        print("   Run convert_to_openmc first to generate model")
        return False
    
    try:
        output_file = Path('converted_from_openmc.json')
        
        # Try OpenMCConverter.import_reactor
        try:
            materials_file = openmc_dir / 'materials.xml' if (openmc_dir / 'materials.xml').exists() else None
            reactor_dict = OpenMCConverter.import_reactor(geometry_file, materials_file)
            
            if reactor_dict is not None:
                # Save reactor dict
                with open(output_file, 'w') as f:
                    json.dump(reactor_dict, f, indent=2, default=str)
                
                print(f"✅ Converted from OpenMC format: {output_file}")
                return True
            else:
                print("⚠️  Conversion returned None")
                return False
        except NotImplementedError as e:
            print(f"⏭️  Skipped (not yet implemented: {e})")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_serpent_run_parse():
    """Test Serpent run+parse (Community): parse_res_file with sample _res.m."""
    print("\n4a. Testing Serpent parse_res_file (Community)...")
    try:
        from pathlib import Path
        from smrforge.io import parse_serpent_res

        res_dir = Path("output/manual_testing") if Path("output").exists() else Path(".")
        res_dir.mkdir(parents=True, exist_ok=True)
        res_file = res_dir / "sample_model_res.m"
        res_file.write_text("IMP_KEFF (idx, [1: 2]) = [ 1.04349E+00 0.00189 ];\n")

        parsed = parse_serpent_res(res_file)
        if "k_eff" in parsed and parsed.get("k_eff_source") == "IMP_KEFF":
            print(f"✅ Serpent parse_res_file: k_eff={parsed['k_eff']:.5f}")
            if res_file.exists():
                res_file.unlink()
            return True
        print("⚠️ Parsed but k_eff/k_eff_source missing")
        return False
    except ImportError as e:
        print(f"⏭️ Skipped (parse_serpent_res not available: {e})")
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
        print("   Run convert_to_serpent first to generate model")
        return False
    
    try:
        output_file = Path('converted_from_serpent.json')
        
        # Try SerpentConverter.import_reactor
        try:
            reactor_dict = SerpentConverter.import_reactor(serpent_file)
            
            if reactor_dict is not None:
                # Save reactor dict
                with open(output_file, 'w') as f:
                    json.dump(reactor_dict, f, indent=2, default=str)
                
                print(f"✅ Converted from Serpent format: {output_file}")
                return True
            else:
                print("⚠️  Conversion returned None")
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
    results['serpent_run_parse'] = test_serpent_run_parse()
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
