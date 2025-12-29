"""
Geometry Import/Export Examples

This script demonstrates how to import and export reactor geometries
using the SMRForge geometry importers module.
"""

import json
from pathlib import Path

from smrforge.geometry.core_geometry import GeometryExporter, PrismaticCore, PebbleBedCore
from smrforge.geometry.importers import GeometryImporter


def example_export_prismatic_core():
    """Example: Export a prismatic core to JSON."""
    print("=" * 60)
    print("Example 1: Export Prismatic Core")
    print("=" * 60)

    # Create a prismatic core
    core = PrismaticCore(name="Example-Export")
    core.build_hexagonal_lattice(
        n_rings=2,
        pitch=40.0,
        block_height=79.3,
        n_axial=3,
        flat_to_flat=36.0,
    )
    core.core_height = 237.9  # 3 blocks * 79.3 cm
    core.core_diameter = 200.0  # Approximate

    print(f"Created core: {core.name}")
    print(f"  Blocks: {len(core.blocks)}")
    print(f"  Core height: {core.core_height:.1f} cm")
    print(f"  Core diameter: {core.core_diameter:.1f} cm")

    # Export to JSON
    output_file = Path("output/exported_prismatic_core.json")
    output_file.parent.mkdir(exist_ok=True)

    GeometryExporter.to_json(core, output_file)
    print(f"\nExported to: {output_file}")
    print(f"  File size: {output_file.stat().st_size} bytes")


def example_import_prismatic_core():
    """Example: Import a prismatic core from JSON."""
    print("\n" + "=" * 60)
    print("Example 2: Import Prismatic Core")
    print("=" * 60)

    # Import from the exported file
    input_file = Path("output/exported_prismatic_core.json")

    if input_file.exists():
        core = GeometryImporter.from_json(input_file)

        print(f"Imported core: {core.name}")
        print(f"  Type: {type(core).__name__}")
        print(f"  Blocks: {len(core.blocks)}")
        print(f"  Core height: {core.core_height:.1f} cm")
        print(f"  Core diameter: {core.core_diameter:.1f} cm")

        # Validate imported geometry
        validation = GeometryImporter.validate_imported_geometry(core)
        print(f"\nValidation:")
        print(f"  Valid: {validation['valid']}")
        if validation["errors"]:
            print(f"  Errors: {validation['errors']}")
        if validation["warnings"]:
            print(f"  Warnings: {len(validation['warnings'])}")
    else:
        print(f"File not found: {input_file}")
        print("  Run Example 1 first to create the export file")


def example_export_pebble_bed():
    """Example: Export a pebble bed core to JSON."""
    print("\n" + "=" * 60)
    print("Example 3: Export Pebble Bed Core")
    print("=" * 60)

    # Create a pebble bed core
    core = PebbleBedCore(name="Example-Pebble-Export")
    core.build_structured_packing(
        core_height=500.0,
        core_diameter=200.0,
        pebble_radius=3.0,
    )

    print(f"Created core: {core.name}")
    print(f"  Pebbles: {len(core.pebbles)}")
    print(f"  Core height: {core.core_height:.1f} cm")
    print(f"  Core diameter: {core.core_diameter:.1f} cm")
    print(f"  Packing fraction: {core.packing_fraction:.3f}")

    # Export to JSON
    output_file = Path("output/exported_pebble_bed.json")
    output_file.parent.mkdir(exist_ok=True)

    GeometryExporter.to_json(core, output_file)
    print(f"\nExported to: {output_file}")


def example_roundtrip_import_export():
    """Example: Roundtrip import/export test."""
    print("\n" + "=" * 60)
    print("Example 4: Roundtrip Import/Export")
    print("=" * 60)

    # Create original core
    original = PrismaticCore(name="Roundtrip-Test")
    original.build_hexagonal_lattice(n_rings=2, pitch=40.0, block_height=79.3, n_axial=2)
    original.core_height = 158.6
    original.core_diameter = 200.0

    print(f"Original core:")
    print(f"  Name: {original.name}")
    print(f"  Blocks: {len(original.blocks)}")

    # Export
    export_file = Path("output/roundtrip_test.json")
    export_file.parent.mkdir(exist_ok=True)
    GeometryExporter.to_json(original, export_file)

    # Import
    imported = GeometryImporter.from_json(export_file)

    print(f"\nImported core:")
    print(f"  Name: {imported.name}")
    print(f"  Blocks: {len(imported.blocks)}")
    print(f"  Core height: {imported.core_height:.1f} cm")

    # Compare
    if len(imported.blocks) == len(original.blocks):
        print("\n✓ Roundtrip successful: Block counts match")
    else:
        print(f"\n✗ Roundtrip issue: Block counts differ ({len(original.blocks)} vs {len(imported.blocks)})")


def example_create_json_manually():
    """Example: Create JSON file manually and import it."""
    print("\n" + "=" * 60)
    print("Example 5: Manual JSON Creation")
    print("=" * 60)

    # Create JSON structure manually
    json_data = {
        "name": "Manual-Core",
        "type": "PrismaticCore",
        "core_height": 793.0,
        "core_diameter": 400.0,
        "blocks": [
            {
                "id": 0,
                "position": [0.0, 0.0, 0.0],
                "type": "fuel",
                "flat_to_flat": 36.0,
                "height": 79.3,
                "n_fuel_channels": 210,
            },
            {
                "id": 1,
                "position": [40.0, 0.0, 0.0],
                "type": "fuel",
                "flat_to_flat": 36.0,
                "height": 79.3,
                "n_fuel_channels": 210,
            },
        ],
    }

    # Save to file
    output_file = Path("output/manual_core.json")
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(json_data, f, indent=2)

    print(f"Created manual JSON file: {output_file}")

    # Import it
    core = GeometryImporter.from_json(output_file)

    print(f"\nImported core:")
    print(f"  Name: {core.name}")
    print(f"  Blocks: {len(core.blocks)}")
    print(f"  Core height: {core.core_height:.1f} cm")


def example_import_openmc_xml():
    """Example: Import geometry from OpenMC XML file."""
    print("\n" + "=" * 60)
    print("Example 6: Import from OpenMC XML")
    print("=" * 60)

    # Create a sample OpenMC XML file
    openmc_file = Path("output/sample_openmc_geometry.xml")
    openmc_file.parent.mkdir(exist_ok=True)

    openmc_content = """<?xml version="1.0"?>
<geometry>
    <surface id="1" type="z-cylinder" coeffs="150.0 0.0 0.0"/>
    <surface id="2" type="z-plane" coeffs="-396.5"/>
    <surface id="3" type="z-plane" coeffs="396.5"/>
</geometry>
"""
    openmc_file.write_text(openmc_content)
    print(f"Created sample OpenMC XML file: {openmc_file}")

    try:
        # Import from OpenMC XML
        core = GeometryImporter.from_openmc_xml(openmc_file)

        print(f"\nImported core:")
        print(f"  Name: {core.name}")
        print(f"  Core diameter: {core.core_diameter:.1f} cm")
        print(f"  Core height: {core.core_height:.1f} cm")
        print(f"  Blocks: {len(core.blocks)}")

        # Validate
        validation = GeometryImporter.validate_imported_geometry(core)
        print(f"\nValidation:")
        print(f"  Valid: {validation['valid']}")
        if validation["warnings"]:
            print(f"  Warnings: {len(validation['warnings'])}")

    except NotImplementedError as e:
        print(f"\nNote: {e}")
        print("  This geometry may be too complex for the current implementation.")


def example_import_serpent():
    """Example: Import geometry from Serpent input file."""
    print("\n" + "=" * 60)
    print("Example 7: Import from Serpent Input")
    print("=" * 60)

    # Create a sample Serpent input file
    serpent_file = Path("output/sample_serpent_geometry.inp")
    serpent_file.parent.mkdir(exist_ok=True)

    serpent_content = """% Simple HTGR geometry
surf 1 cz 150.0
surf 2 pz -396.5
surf 3 pz 396.5
"""
    serpent_file.write_text(serpent_content)
    print(f"Created sample Serpent input file: {serpent_file}")

    try:
        # Import from Serpent
        core = GeometryImporter.from_serpent(serpent_file)

        print(f"\nImported core:")
        print(f"  Name: {core.name}")
        print(f"  Core diameter: {core.core_diameter:.1f} cm")
        print(f"  Core height: {core.core_height:.1f} cm")
        print(f"  Blocks: {len(core.blocks)}")

        # Validate
        validation = GeometryImporter.validate_imported_geometry(core)
        print(f"\nValidation:")
        print(f"  Valid: {validation['valid']}")
        if validation["warnings"]:
            print(f"  Warnings: {len(validation['warnings'])}")

    except NotImplementedError as e:
        print(f"\nNote: {e}")
        print("  This geometry may be too complex for the current implementation.")


def example_serpent_hexprism():
    """Example: Import hexagonal prism geometry from Serpent."""
    print("\n" + "=" * 60)
    print("Example 8: Serpent Hexagonal Prism")
    print("=" * 60)

    # Create a Serpent file with hexprism
    serpent_file = Path("output/sample_hexprism_geometry.inp")
    serpent_file.parent.mkdir(exist_ok=True)

    serpent_content = """% Hexagonal prism geometry
surf 1 hexprism 0.0 0.0 0.0 0.0 0.0 1.0 793.0 75.0
"""
    serpent_file.write_text(serpent_content)
    print(f"Created sample hexprism Serpent file: {serpent_file}")

    try:
        # Import from Serpent
        core = GeometryImporter.from_serpent(serpent_file)

        print(f"\nImported core:")
        print(f"  Name: {core.name}")
        print(f"  Core height: {core.core_height:.1f} cm")
        print(f"  Core diameter: {core.core_diameter:.1f} cm (approximate from apothem)")

    except NotImplementedError as e:
        print(f"\nNote: {e}")


if __name__ == "__main__":
    import os

    # Create output directory
    os.makedirs("output", exist_ok=True)

    # JSON examples
    example_export_prismatic_core()
    example_import_prismatic_core()
    example_export_pebble_bed()
    example_roundtrip_import_export()
    example_create_json_manually()

    # OpenMC and Serpent examples
    example_import_openmc_xml()
    example_import_serpent()
    example_serpent_hexprism()

    print("\n" + "=" * 60)
    print("Geometry import/export examples completed!")
    print("Check the output/ directory for generated files.")
    print("=" * 60)
    print("\nSupported formats:")
    print("  - JSON (full support)")
    print("  - OpenMC XML (simplified geometries)")
    print("  - Serpent input (simplified geometries)")

