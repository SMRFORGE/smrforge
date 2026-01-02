"""
Example: Discovering and listing thermal scattering law (TSL) files.

This example demonstrates how to discover and list available TSL files
in your ENDF directory.
"""

from pathlib import Path

from smrforge.core.reactor_core import NuclearDataCache
from smrforge.core.thermal_scattering_parser import get_tsl_material_name


def main():
    """Demonstrate TSL file discovery."""
    
    print("=" * 60)
    print("SMRForge TSL File Discovery Example")
    print("=" * 60)
    
    # Create cache (optional: specify ENDF directory)
    print("\n1. Setting up nuclear data cache...")
    # If you have ENDF files, specify the directory:
    # cache = NuclearDataCache(local_endf_dir=Path("C:/path/to/ENDF-B-VIII.1"))
    cache = NuclearDataCache()
    
    if cache.local_endf_dir:
        print(f"   ENDF directory: {cache.local_endf_dir}")
    else:
        print("   No ENDF directory specified (using default search)")
    
    # List available TSL materials
    print("\n2. Discovering TSL files...")
    materials = cache.list_available_tsl_materials()
    
    if materials:
        print(f"   ✓ Found {len(materials)} TSL materials:")
        for material in sorted(materials):
            tsl_file = cache.get_tsl_file(material)
            if tsl_file:
                rel_path = tsl_file.relative_to(cache.local_endf_dir) if cache.local_endf_dir else tsl_file
                print(f"      - {material:20} -> {rel_path}")
            else:
                print(f"      - {material:20} -> (file not found)")
    else:
        print("   ⚠ No TSL files found")
        print("   ")
        print("   Expected location:")
        if cache.local_endf_dir:
            expected_dir = cache.local_endf_dir / "thermal_scatt-version.VIII.1"
            print(f"      {expected_dir}")
        else:
            print("      {ENDF_DIR}/thermal_scatt-version.VIII.1/")
        print("   ")
        print("   Expected filename patterns:")
        print("      - tsl-*.endf")
        print("      - thermal-*.endf")
        print("      - ts-*.endf")
    
    # Test material name mapping
    print("\n3. Material name mapping:")
    common_materials = ["H2O", "graphite", "D2O", "BeO", "UO2", "ZrH"]
    for material in common_materials:
        tsl_name = get_tsl_material_name(material)
        if tsl_name:
            # Check if this material is available
            tsl_file = cache.get_tsl_file(tsl_name)
            status = "✓" if tsl_file else "✗"
            print(f"   {status} {material:12} -> {tsl_name:20} {'(found)' if tsl_file else '(not found)'}")
        else:
            print(f"   ✗ {material:12} -> (no mapping)")
    
    # Demonstrate file lookup
    print("\n4. Direct file lookup:")
    test_materials = ["H_in_H2O", "C_in_graphite", "D_in_D2O"]
    for material in test_materials:
        tsl_file = cache.get_tsl_file(material)
        if tsl_file:
            print(f"   ✓ {material:20} -> {tsl_file.name}")
        else:
            print(f"   ✗ {material:20} -> (not found)")
    
    print("\n" + "=" * 60)
    print("TSL file discovery complete!")
    print("=" * 60)
    print("\nNote: TSL files are automatically discovered and indexed")
    print("      when you create a NuclearDataCache instance.")


if __name__ == "__main__":
    main()

