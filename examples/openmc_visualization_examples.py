"""
OpenMC-Inspired Visualization Examples

This file demonstrates all the OpenMC-inspired visualization features
implemented in SMRForge, including:
- Unified Plot API
- Mesh tally visualization
- Geometry verification visualization
- Voxel plots with HDF5 export
- Material composition visualization
- Tally data visualization
"""

import numpy as np
from pathlib import Path

# Core imports
from smrforge.geometry import PrismaticCore
from smrforge.geometry.lwr_smr import PWRSMRCore

# Visualization imports
try:
    from smrforge.visualization.plot_api import Plot, create_plot
    _PLOT_API_AVAILABLE = True
except ImportError:
    _PLOT_API_AVAILABLE = False
    print("Warning: Plot API not available")

try:
    from smrforge.visualization.mesh_tally import MeshTally, plot_mesh_tally, plot_multi_group_mesh_tally
    _MESH_TALLY_AVAILABLE = True
except ImportError:
    _MESH_TALLY_AVAILABLE = False
    print("Warning: Mesh tally visualization not available")

try:
    from smrforge.visualization.geometry_verification import (
        plot_overlap_detection,
        plot_geometry_consistency,
        plot_material_assignment,
    )
    _GEOMETRY_VERIFICATION_AVAILABLE = True
except ImportError:
    _GEOMETRY_VERIFICATION_AVAILABLE = False
    print("Warning: Geometry verification visualization not available")

try:
    from smrforge.visualization.voxel_plots import (
        plot_voxel,
        export_voxel_to_hdf5,
        convert_voxel_hdf5_to_vtk,
    )
    from smrforge.visualization.voxel_plots import _create_voxel_grid
    _VOXEL_PLOTS_AVAILABLE = True
except ImportError:
    _VOXEL_PLOTS_AVAILABLE = False
    print("Warning: Voxel plots not available")

try:
    from smrforge.visualization.material_composition import (
        plot_nuclide_concentration,
        plot_material_property,
        plot_burnup_composition,
    )
    _MATERIAL_COMPOSITION_AVAILABLE = True
except ImportError:
    _MATERIAL_COMPOSITION_AVAILABLE = False
    print("Warning: Material composition visualization not available")

try:
    from smrforge.visualization.tally_data import (
        plot_energy_spectrum,
        plot_spatial_distribution,
        plot_time_dependent_tally,
        plot_uncertainty,
    )
    _TALLY_DATA_AVAILABLE = True
except ImportError:
    _TALLY_DATA_AVAILABLE = False
    print("Warning: Tally data visualization not available")

# Core data imports
try:
    from smrforge.core.reactor_core import Nuclide, NuclideInventoryTracker
    _CORE_DATA_AVAILABLE = True
except ImportError:
    _CORE_DATA_AVAILABLE = False
    print("Warning: Core data classes not available")


def example_unified_plot_api():
    """Example: Using the Unified Plot API."""
    print("=" * 70)
    print("Example 1: Unified Plot API")
    print("=" * 70)
    
    if not _PLOT_API_AVAILABLE:
        print("Plot API not available. Skipping example.")
        return
    
    # Create a reactor core
    core = PrismaticCore(name="Plot-API-Example")
    core.core_height = 400.0
    core.core_diameter = 300.0
    core.build_hexagonal_lattice(n_rings=3, pitch=40.0)
    core.build_mesh(n_radial=20, n_axial=10)
    
    print("\n1. Creating slice plot:")
    plot = Plot(
        plot_type="slice",
        origin=(0, 0, 200),
        width=(300, 300, 400),
        basis="xy",
        color_by="material",
        backend="plotly",
    )
    try:
        fig = plot.plot(core)
        print("   ✓ Slice plot created")
        print("   (In Jupyter, fig.show() will display the plot)")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n2. Creating voxel plot:")
    voxel_plot = create_plot(
        plot_type="voxel",
        origin=(0, 0, 0),
        width=(300, 300, 400),
        color_by="material",
        backend="plotly",
    )
    try:
        fig = voxel_plot.plot(core)
        print("   ✓ Voxel plot created")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n3. Creating ray-traced plot:")
    ray_plot = create_plot(
        plot_type="ray_trace",
        origin=(0, 0, 200),
        width=(300, 300, 400),
        basis="xyz",
        color_by="material",
        backend="plotly",
    )
    try:
        fig = ray_plot.plot(core)
        print("   ✓ Ray-traced plot created")
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_mesh_tally_visualization():
    """Example: Mesh tally visualization."""
    print("\n" + "=" * 70)
    print("Example 2: Mesh Tally Visualization")
    print("=" * 70)
    
    if not _MESH_TALLY_AVAILABLE:
        print("Mesh tally visualization not available. Skipping example.")
        return
    
    # Create geometry
    core = PrismaticCore(name="Mesh-Tally-Example")
    core.core_height = 400.0
    core.core_diameter = 300.0
    core.build_mesh(n_radial=20, n_axial=10)
    
    # Create mock flux data [nz, nr, ng]
    nz, nr, ng = 10, 20, 2
    flux = np.random.rand(nz, nr, ng) * 1e14  # Mock flux data
    # Mock absolute 1-sigma uncertainty (e.g., 5% of value)
    uncertainty = 0.05 * flux
    
    # Create mesh coordinates
    r_coords = np.linspace(0, core.core_diameter/2, nr + 1)
    z_coords = np.linspace(0, core.core_height, nz + 1)
    energy_groups = np.logspace(7, -5, ng + 1)
    
    print("\n1. Creating mesh tally:")
    tally = MeshTally(
        name="flux",
        tally_type="flux",
        data=flux,
        mesh_coords=(r_coords, z_coords),
        energy_groups=energy_groups,
        uncertainty=uncertainty,
        geometry_type="cylindrical",
    )
    print(f"   ✓ Created mesh tally: {tally.name}")
    print(f"   ✓ Data shape: {tally.data.shape}")
    print(f"   ✓ Geometry type: {tally.geometry_type}")
    
    print("\n2. Plotting total flux:")
    try:
        fig = plot_mesh_tally(
            tally,
            core,
            field="flux",
            energy_group=None,  # Total
            backend="plotly",
            show_uncertainty=True,
            uncertainty_mode="percent",
        )
        print("   ✓ Total flux plot created")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n3. Plotting specific energy group:")
    try:
        fig = plot_mesh_tally(
            tally,
            core,
            field="flux",
            energy_group=0,  # First group
            backend="plotly",
        )
        print("   ✓ Energy group plot created")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n4. Plotting all energy groups:")
    try:
        fig = plot_multi_group_mesh_tally(
            tally,
            core,
            backend="plotly",
        )
        print("   ✓ Multi-group plot created")
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_geometry_verification():
    """Example: Geometry verification visualization."""
    print("\n" + "=" * 70)
    print("Example 3: Geometry Verification Visualization")
    print("=" * 70)
    
    if not _GEOMETRY_VERIFICATION_AVAILABLE:
        print("Geometry verification visualization not available. Skipping example.")
        return
    
    # Create geometry
    core = PrismaticCore(name="Verification-Example")
    core.core_height = 400.0
    core.core_diameter = 300.0
    core.build_hexagonal_lattice(n_rings=3, pitch=40.0)
    
    print("\n1. Material assignment verification:")
    material_map = {
        "block_1": "fuel",
        "block_2": "moderator",
        "block_3": "reflector",
    }
    try:
        fig = plot_material_assignment(
            core,
            material_map,
            backend="plotly",
        )
        print("   ✓ Material assignment plot created")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n2. Geometry consistency check:")
    consistency_checks = {
        "material_assignment": True,
        "boundary_connectivity": True,
        "cell_volumes": True,
    }
    issues = []  # No issues in this example
    
    try:
        fig = plot_geometry_consistency(
            core,
            consistency_checks,
            issues,
            backend="plotly",
        )
        print("   ✓ Consistency check plot created")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n3. Overlap detection (simulated):")
    # Simulate overlaps (in real usage, would come from validation module)
    overlaps = []  # No overlaps in this example
    
    try:
        fig = plot_overlap_detection(
            core,
            overlaps,
            backend="plotly",
        )
        print("   ✓ Overlap detection plot created")
        if len(overlaps) > 0:
            print(f"   ⚠ Warning: {len(overlaps)} overlaps detected!")
        else:
            print("   ✓ No overlaps detected")
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_voxel_plots():
    """Example: Voxel plots with HDF5 export."""
    print("\n" + "=" * 70)
    print("Example 4: Voxel Plots with HDF5 Export")
    print("=" * 70)
    
    if not _VOXEL_PLOTS_AVAILABLE:
        print("Voxel plots not available. Skipping example.")
        return
    
    # Create geometry
    core = PrismaticCore(name="Voxel-Example")
    core.core_height = 400.0
    core.core_diameter = 300.0
    core.build_hexagonal_lattice(n_rings=3, pitch=40.0)
    
    print("\n1. Creating voxel plot:")
    try:
        fig = plot_voxel(
            core,
            origin=(0, 0, 0),
            width=(300, 300, 400),
            color_by="material",
            backend="plotly",
        )
        print("   ✓ Voxel plot created")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n2. Exporting to HDF5:")
    try:
        voxel_grid = _create_voxel_grid(
            core,
            origin=(0, 0, 0),
            width=(300, 300, 400),
            resolution=(50, 50, 100),
        )
        
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        export_voxel_to_hdf5(
            voxel_grid,
            output_dir / "reactor_voxels.h5",
            metadata={"reactor_name": "Voxel-Example", "date": "2026-01-01"},
        )
        print("   ✓ Exported to HDF5: output/reactor_voxels.h5")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n3. Converting HDF5 to VTK:")
    try:
        hdf5_file = output_dir / "reactor_voxels.h5"
        vtk_file = output_dir / "reactor_voxels.vtk"
        
        if hdf5_file.exists():
            convert_voxel_hdf5_to_vtk(
                hdf5_file,
                vtk_file,
            )
            print(f"   ✓ Converted to VTK: {vtk_file}")
            print("   (Open reactor_voxels.vtk in ParaView or VisIt)")
        else:
            print("   ⚠ HDF5 file not found, skipping conversion")
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_material_composition():
    """Example: Material composition visualization."""
    print("\n" + "=" * 70)
    print("Example 5: Material Composition Visualization")
    print("=" * 70)
    
    if not _MATERIAL_COMPOSITION_AVAILABLE or not _CORE_DATA_AVAILABLE:
        print("Material composition visualization not available. Skipping example.")
        return
    
    # Create geometry
    core = PrismaticCore(name="Material-Example")
    core.core_height = 400.0
    core.core_diameter = 300.0
    core.build_hexagonal_lattice(n_rings=3, pitch=40.0)
    
    # Create inventory
    inventory = NuclideInventoryTracker()
    u235 = Nuclide(Z=92, A=235)
    u238 = Nuclide(Z=92, A=238)
    cs137 = Nuclide(Z=55, A=137)
    
    inventory.add_nuclide(u235, atom_density=0.0005)
    inventory.add_nuclide(u238, atom_density=0.02)
    inventory.add_nuclide(cs137, atom_density=0.0001)
    inventory.burnup = 10.0  # MWd/kgU
    
    print("\n1. Plotting nuclide concentration:")
    try:
        fig = plot_nuclide_concentration(
            inventory,
            u235,
            core,
            backend="plotly",
        )
        print(f"   ✓ U-235 concentration plot created")
        print(f"   ✓ Concentration: {inventory.get_atom_density(u235):.6f} atoms/barn-cm")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n2. Plotting material property:")
    density_map = {
        "fuel": 10.5,      # g/cm³
        "moderator": 1.0,  # g/cm³
        "reflector": 1.8,  # g/cm³
    }
    try:
        fig = plot_material_property(
            core,
            density_map,
            property_name="density",
            backend="plotly",
        )
        print("   ✓ Material property plot created")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n3. Plotting burnup composition:")
    try:
        fig = plot_burnup_composition(
            inventory,
            core,
            nuclides=[u235, u238, cs137],
            backend="plotly",
        )
        print(f"   ✓ Burnup composition plot created")
        print(f"   ✓ Burnup: {inventory.burnup:.1f} MWd/kgU")
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_tally_data():
    """Example: Tally data visualization."""
    print("\n" + "=" * 70)
    print("Example 6: Tally Data Visualization")
    print("=" * 70)
    
    if not _TALLY_DATA_AVAILABLE:
        print("Tally data visualization not available. Skipping example.")
        return
    
    # Create mock data
    energy_groups = np.logspace(7, -5, 27)  # 26 groups
    flux = np.random.rand(26) * 1e14  # Mock flux spectrum
    
    print("\n1. Plotting energy spectrum:")
    try:
        fig = plot_energy_spectrum(
            flux,
            energy_groups,
            backend="plotly",
        )
        print("   ✓ Energy spectrum plot created")
        print(f"   ✓ Peak flux: {np.max(flux):.2e} n/cm²/s")
        print(f"   ✓ Peak energy: {energy_groups[np.argmax(flux)]:.2e} eV")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n2. Plotting spatial distribution:")
    # Create mock spatial data
    n_positions = 100
    positions = np.random.rand(n_positions, 3) * 200  # Random positions
    flux_spatial = np.random.rand(n_positions) * 1e14
    
    try:
        fig = plot_spatial_distribution(
            flux_spatial,
            positions,
            field_name="Flux",
            backend="plotly",
        )
        print("   ✓ Spatial distribution plot created")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n3. Plotting time-dependent data:")
    times = np.linspace(0, 100, 100)  # 100 seconds
    flux_time = np.random.rand(100) * 1e14
    
    try:
        fig = plot_time_dependent_tally(
            flux_time,
            times,
            field_name="Flux",
            backend="plotly",
        )
        print("   ✓ Time-dependent plot created")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n4. Plotting uncertainty:")
    mean_flux = np.random.rand(50) * 1e14
    uncertainty_flux = mean_flux * 0.1  # 10% uncertainty
    
    try:
        fig = plot_uncertainty(
            mean_flux,
            uncertainty_flux,
            backend="plotly",
        )
        print("   ✓ Uncertainty plot created")
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_complete_workflow():
    """Example: Complete integrated workflow."""
    print("\n" + "=" * 70)
    print("Example 7: Complete Integrated Workflow")
    print("=" * 70)
    
    print("\nThis example demonstrates a complete workflow:")
    print("  1. Create geometry")
    print("  2. Run neutronics (simulated)")
    print("  3. Create visualizations")
    print("  4. Export results")
    
    # Step 1: Create geometry
    print("\n1. Creating geometry...")
    core = PrismaticCore(name="Complete-Workflow")
    core.core_height = 400.0
    core.core_diameter = 300.0
    core.build_hexagonal_lattice(n_rings=3, pitch=40.0)
    core.build_mesh(n_radial=20, n_axial=10)
    print(f"   ✓ Created {len(core.blocks)} blocks")
    
    # Step 2: Simulate neutronics (mock data)
    print("\n2. Simulating neutronics (mock data)...")
    nz, nr, ng = 10, 20, 2
    flux = np.random.rand(nz, nr, ng) * 1e14
    k_eff = 1.05  # Mock k-effective
    print(f"   ✓ k-effective: {k_eff:.6f}")
    print(f"   ✓ Flux shape: {flux.shape}")
    
    # Step 3: Create visualizations
    print("\n3. Creating visualizations...")
    
    if _PLOT_API_AVAILABLE:
        print("   - Creating slice plot...")
        try:
            plot = Plot(
                plot_type="slice",
                origin=(0, 0, 200),
                width=(300, 300, 400),
                basis="xy",
                color_by="material",
                backend="plotly",
            )
            fig = plot.plot(core)
            print("     ✓ Slice plot created")
        except Exception as e:
            print(f"     ✗ Error: {e}")
    
    if _MESH_TALLY_AVAILABLE:
        print("   - Creating mesh tally...")
        try:
            r_coords = np.linspace(0, core.core_diameter/2, nr + 1)
            z_coords = np.linspace(0, core.core_height, nz + 1)
            energy_groups = np.logspace(7, -5, ng + 1)
            
            tally = MeshTally(
                name="flux",
                tally_type="flux",
                data=flux,
                mesh_coords=(r_coords, z_coords),
                energy_groups=energy_groups,
                geometry_type="cylindrical",
            )
            fig = plot_mesh_tally(tally, core, backend="plotly")
            print("     ✓ Mesh tally plot created")
        except Exception as e:
            print(f"     ✗ Error: {e}")
    
    # Step 4: Export results
    print("\n4. Exporting results...")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    print(f"   ✓ Output directory: {output_dir}")
    
    print("\n✓ Complete workflow finished!")


def main():
    """Run all OpenMC visualization examples."""
    print("\n" + "=" * 70)
    print("OpenMC-Inspired Visualization Examples")
    print("=" * 70)
    print("\nThis script demonstrates all OpenMC-inspired visualization features.")
    print("Some examples require ENDF files or additional setup.\n")
    
    # Run examples
    example_unified_plot_api()
    example_mesh_tally_visualization()
    example_geometry_verification()
    example_voxel_plots()
    example_material_composition()
    example_tally_data()
    example_complete_workflow()
    
    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)
    print("\nFor more information, see:")
    print("  - docs/status/openmc-visualization-gaps-analysis.md")
    print("  - docs/status/openmc-visualization-implementation-summary.md")
    print("  - examples/advanced_features_examples.py")


if __name__ == "__main__":
    main()
