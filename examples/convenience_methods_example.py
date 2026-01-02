"""
Example: Using Convenience Methods and Functions

Demonstrates the new convenience methods and functions that simplify
common SMRForge operations.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np

# Import convenience functions
from smrforge import (
    create_simple_core,
    create_simple_solver,
    create_simple_xs_data,
    get_nuclide,
    create_nuclide_list,
    quick_keff_calculation,
    quick_mesh_extraction,
    run_complete_analysis,
    get_material,
    list_materials,
)


def main():
    """Demonstrate convenience methods."""
    print("=" * 60)
    print("Convenience Methods Example")
    print("=" * 60)

    # 1. Quick core creation
    print("\n1. Quick Core Creation")
    print("-" * 60)
    core = create_simple_core(
        name="ConvenienceCore",
        n_rings=3,
        pitch=40.0,
        block_height=80.0,
        n_axial=2,
    )
    print(f"   Created core: {core.name}")
    print(f"   Blocks: {len(core.blocks)}")
    print(f"   Core height: {core.core_height:.1f} cm")
    print(f"   Core diameter: {core.core_diameter:.1f} cm")

    # 2. Quick solver setup
    print("\n2. Quick Solver Setup")
    print("-" * 60)
    solver = create_simple_solver(core=core, n_groups=2, verbose=False)
    print(f"   Solver created with {solver.ng} groups")
    print(f"   Mesh: {solver.nz} axial × {solver.nr} radial")

    # 3. Quick k-eff calculation
    print("\n3. Quick k-eff Calculation")
    print("-" * 60)
    k_eff, flux = quick_keff_calculation(core=core)
    print(f"   k-eff: {k_eff:.6f}")
    print(f"   Peak flux: {np.max(flux):.2e}")

    # 4. Nuclide convenience functions
    print("\n4. Nuclide Convenience Functions")
    print("-" * 60)
    u235 = get_nuclide("U235")
    pu239 = get_nuclide("Pu239")
    cs137 = get_nuclide("Cs137")
    print(f"   U235: ZAM = {u235.zam}, name = {u235.name}")
    print(f"   Pu239: ZAM = {pu239.zam}, name = {pu239.name}")
    print(f"   Cs137: ZAM = {cs137.zam}, name = {cs137.name}")

    nuclides = create_nuclide_list(["U235", "U238", "Pu239", "Cs137"])
    print(f"   Created {len(nuclides)} nuclides from list")

    # 5. Material convenience functions
    print("\n5. Material Convenience Functions")
    print("-" * 60)
    try:
        materials = list_materials()
        print(f"   Available materials: {len(materials)}")
        print(f"   First 5: {materials[:5]}")

        moderator_materials = list_materials(category="moderator")
        print(f"   Moderator materials: {moderator_materials}")

        graphite = get_material("graphite_IG-110")
        k = graphite.thermal_conductivity(1200.0)
        print(f"   Graphite IG-110 thermal conductivity at 1200K: {k:.2f} W/m-K")
    except Exception as e:
        print(f"   Note: Material database not fully available: {e}")

    # 6. Quick mesh extraction
    print("\n6. Quick Mesh Extraction")
    print("-" * 60)
    try:
        volume_mesh = quick_mesh_extraction(core, mesh_type="volume")
        print(f"   Volume mesh: {volume_mesh.n_vertices} vertices, {volume_mesh.n_cells} cells")

        surface_mesh = quick_mesh_extraction(core, mesh_type="surface")
        print(f"   Surface mesh: {surface_mesh.n_vertices} vertices, {surface_mesh.n_faces} faces")
    except Exception as e:
        print(f"   Note: Mesh extraction requires geometry module: {e}")

    # 7. Complete analysis workflow
    print("\n7. Complete Analysis Workflow")
    print("-" * 60)
    try:
        results = run_complete_analysis(
            core=core,
            power_mw=10.0,
            include_burnup=False,
        )
        print(f"   k-eff: {results['k_eff']:.6f}")
        print(f"   Peak flux: {results['peak_flux']:.2e}")
        print(f"   Peak power density: {results['peak_power_density']:.2e} W/cm³")
        print(f"   Average power density: {results['avg_power_density']:.2e} W/cm³")
    except Exception as e:
        print(f"   Note: Complete analysis requires all modules: {e}")

    # 8. Using convenience methods on classes
    print("\n8. Class Convenience Methods")
    print("-" * 60)
    try:
        # Quick setup method on PrismaticCore
        core2 = create_simple_core(name="QuickSetupCore")
        if hasattr(core2, "quick_setup"):
            print("   ✓ PrismaticCore.quick_setup() available")
        else:
            print("   Note: quick_setup method not available")

        # Quick solve method on MultiGroupDiffusion
        solver2 = create_simple_solver()
        if hasattr(solver2, "quick_solve"):
            k_eff2 = solver2.quick_solve()
            print(f"   ✓ MultiGroupDiffusion.quick_solve() available")
            print(f"   k-eff from quick_solve: {k_eff2:.6f}")
        else:
            print("   Note: quick_solve method not available")
    except Exception as e:
        print(f"   Note: Class methods may not be available: {e}")

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)
    print("\nSummary of convenience functions:")
    print("  - create_simple_core() - Quick core creation")
    print("  - create_simple_solver() - Quick solver setup")
    print("  - create_simple_xs_data() - Quick cross-section creation")
    print("  - get_nuclide() - Get nuclide from name")
    print("  - create_nuclide_list() - Create nuclide list")
    print("  - quick_keff_calculation() - Quick k-eff")
    print("  - quick_mesh_extraction() - Quick mesh extraction")
    print("  - get_material() - Get material from database")
    print("  - list_materials() - List available materials")
    print("  - run_complete_analysis() - Complete workflow")


if __name__ == "__main__":
    main()

