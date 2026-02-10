"""
OpenMC Export/Import Example (Community)

Demonstrates SMRForge's OpenMC integration:
- Export reactor to OpenMC XML format (geometry.xml, materials.xml, settings.xml)
- Import geometry and materials from OpenMC XML
- Run OpenMC as subprocess (requires OpenMC installed)
- Parse statepoint HDF5 for k-eff and tallies

Requires: smrforge, h5py (for statepoint parsing)
Optional: OpenMC binary (pip install openmc or conda install -c conda-forge openmc)
"""

from pathlib import Path

import smrforge as smr
from smrforge.io import OpenMCConverter


def example_export_to_openmc():
    """Export SMRForge reactor to OpenMC format."""
    print("=" * 60)
    print("Example 1: Export to OpenMC")
    print("=" * 60)

    # Create reactor and build core
    reactor = smr.create_reactor("valar-10")
    if hasattr(reactor, "build_core"):
        reactor.build_core()
    elif hasattr(reactor, "_get_core"):
        reactor._get_core()

    output_dir = Path("output/openmc_run")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export (geometry.xml, materials.xml, settings.xml)
    OpenMCConverter.export_reactor(
        reactor,
        output_dir,
        particles=1000,  # Neutrons per generation (quick test)
        batches=20,
    )

    print(f"Exported to: {output_dir}")
    print(f"  geometry.xml: {(output_dir / 'geometry.xml').exists()}")
    print(f"  materials.xml: {(output_dir / 'materials.xml').exists()}")
    print(f"  settings.xml: {(output_dir / 'settings.xml').exists()}")


def example_import_from_openmc():
    """Import geometry from OpenMC XML."""
    print("\n" + "=" * 60)
    print("Example 2: Import from OpenMC")
    print("=" * 60)

    # Create minimal OpenMC geometry for demo
    geom_file = Path("output/openmc_geometry_demo.xml")
    geom_file.parent.mkdir(parents=True, exist_ok=True)
    geom_file.write_text(
        '<?xml version="1.0"?><geometry>'
        '<surface id="1" type="z-plane" coeffs="0" boundary="vacuum"/>'
        '<surface id="2" type="z-plane" coeffs="200" boundary="vacuum"/>'
        '<surface id="3" type="z-cylinder" coeffs="0 0 50" boundary="vacuum"/>'
        '<cell id="1" material="1" region="-1 2 -3"/>'
        '<cell id="2" material="void" region="1 | -2 | 3"/>'
        "</geometry>"
    )

    result = OpenMCConverter.import_reactor(geom_file)
    print(f"Imported: core={result['core'].name}, format={result['format']}")


def example_run_openmc():
    """Run OpenMC and parse results (requires OpenMC installed)."""
    print("\n" + "=" * 60)
    print("Example 3: Run OpenMC (optional)")
    print("=" * 60)

    work_dir = Path("output/openmc_run")
    if not (work_dir / "geometry.xml").exists():
        print("  Run example_export_to_openmc() first.")
        return

    try:
        from smrforge.io.openmc_run import run_and_parse

        results = run_and_parse(work_dir, timeout=60)
        if results.get("returncode") == 0:
            print(f"  k_eff: {results.get('k_eff', 'N/A')} ± {results.get('k_eff_std', 'N/A')}")
        else:
            print(f"  OpenMC exit code: {results.get('returncode')}")
            print("  (Install OpenMC and set OPENMC_CROSS_SECTIONS to run)")
    except FileNotFoundError:
        print("  OpenMC not found. Install: pip install openmc")
    except Exception as e:
        print(f"  Error: {e}")


if __name__ == "__main__":
    example_export_to_openmc()
    example_import_from_openmc()
    example_run_openmc()
    print("\nDone.")
