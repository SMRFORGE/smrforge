"""
Advanced SMRForge Features - Comprehensive Examples

This file demonstrates advanced features and new capabilities in SMRForge, including:
- Advanced visualization (ray-traced geometry, interactive viewers, dashboards)
- Decay chain utilities and Bateman equation solving
- Prompt/delayed chi for transient analysis
- LWR SMR geometry and analysis
- Resonance self-shielding
- Fission yield and delayed neutron data
- Thermal scattering laws (TSL)
- Nuclide inventory tracking
- Integral reactor designs
"""

import numpy as np
from pathlib import Path

# Core imports
from smrforge.core.reactor_core import (
    NuclearDataCache,
    Nuclide,
    get_cross_section_with_self_shielding,
    get_fission_yields,
    get_delayed_neutron_data,
    get_prompt_delayed_chi,
    get_thermal_scattering_data,
    NuclideInventoryTracker,
)

# Decay chain utilities
try:
    from smrforge.core.decay_chain_utils import (
        DecayChain,
        build_fission_product_chain,
        solve_bateman_equations,
        get_prompt_delayed_chi_for_transient,
        collapse_with_adjoint_for_sensitivity,
    )
    _DECAY_CHAIN_AVAILABLE = True
except ImportError:
    _DECAY_CHAIN_AVAILABLE = False
    print("Warning: Decay chain utilities not available")

# Geometry imports
from smrforge.geometry import PrismaticCore, PebbleBedCore
from smrforge.geometry.lwr_smr import (
    PWRSMRCore,
    BWRSMRCore,
    InVesselSteamGenerator,
    IntegratedPrimarySystem,
    SteamGeneratorTube,
    Point3D,
)
from smrforge.geometry.smr_compact_core import CompactSMRCore

# Advanced visualization
try:
    from smrforge.visualization.advanced import (
        plot_ray_traced_geometry,
        plot_slice,
        plot_isosurface,
        plot_vector_field,
        plot_material_boundaries,
        create_dashboard,
        create_interactive_viewer,
        export_visualization,
    )
    _ADVANCED_VIZ_AVAILABLE = True
except ImportError:
    _ADVANCED_VIZ_AVAILABLE = False
    print("Warning: Advanced visualization not available")

# Thermal scattering
try:
    from smrforge.core.thermal_scattering_parser import get_tsl_material_name
    _TSL_AVAILABLE = True
except ImportError:
    _TSL_AVAILABLE = False

# Neutronics
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.validation.models import CrossSectionData, SolverOptions


def example_advanced_visualization():
    """Example: Advanced 3D visualization capabilities."""
    print("=" * 70)
    print("Example 1: Advanced Visualization")
    print("=" * 70)
    
    if not _ADVANCED_VIZ_AVAILABLE:
        print("Advanced visualization not available. Install plotly and pyvista.")
        return
    
    # Create a prismatic core
    core = PrismaticCore(name="Viz-Example")
    core.core_height = 400.0
    core.core_diameter = 300.0
    core.build_hexagonal_lattice(n_rings=3, pitch=40.0)
    core.build_mesh(n_radial=30, n_axial=20)
    
    print("\n1. Ray-traced geometry visualization:")
    print("   Creating 3D ray-traced view of reactor geometry...")
    try:
        fig = plot_ray_traced_geometry(
            core,
            origin=(0, 0, 200),
            width=(300, 300, 400),
            basis='xy',
            color_by='material',
            backend='plotly',
        )
        print("   ✓ Ray-traced plot created")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n2. Cross-section slice plotting:")
    print("   Creating slice through core at z=200 cm...")
    try:
        # Create dummy flux data for visualization
        flux = np.random.rand(30, 20, 2)  # [radial, axial, groups]
        fig = plot_slice(
            core,
            flux,
            position=200.0,
            axis='z',
            backend='plotly',
        )
        print("   ✓ Slice plot created")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n3. Interactive 3D viewer:")
    print("   Creating interactive exploration interface...")
    try:
        viewer = create_interactive_viewer(
            core,
            backend='plotly',
        )
        print("   ✓ Interactive viewer created")
        print("   (In Jupyter, viewer will be displayed automatically)")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n4. Multi-view dashboard:")
    print("   Creating dashboard with multiple views...")
    try:
        flux = np.random.rand(30, 20, 2)
        power = np.random.rand(30, 20)
        dashboard = create_dashboard(
            core,
            flux=flux,
            power=power,
            views=['xy', 'xz', 'yz', '3d'],
            backend='plotly',
        )
        print("   ✓ Dashboard created")
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_lwr_smr_geometry():
    """Example: LWR SMR geometry creation and analysis."""
    print("\n" + "=" * 70)
    print("Example 2: LWR SMR Geometry")
    print("=" * 70)
    
    print("\n1. Creating PWR SMR core (NuScale-style):")
    core = PWRSMRCore(name="NuScale-Example")
    
    # Build 4x4 assembly core (16 assemblies total)
    core.build_square_lattice_core(
        n_assemblies_x=4,
        n_assemblies_y=4,
        assembly_pitch=21.5,  # cm
        assembly_height=365.76,  # cm
        lattice_size=17,  # 17x17 fuel rods per assembly
        rod_pitch=1.26,  # cm
    )
    
    print(f"   ✓ Created {core.n_assemblies} fuel assemblies")
    print(f"   ✓ Total fuel rods: {sum(len(a.fuel_rods) for a in core.assemblies)}")
    print(f"   ✓ Core height: {core.core_height:.1f} cm")
    print(f"   ✓ Core diameter: {core.core_diameter:.1f} cm")
    
    print("\n2. Creating compact SMR core:")
    compact_core = CompactSMRCore(name="Compact-SMR")
    compact_core.build_compact_core(
        n_assemblies=37,  # NuScale has 37 assemblies
        assembly_pitch=21.5,
        assembly_height=365.76,
        lattice_size=17,
        rod_pitch=1.26,
        reflector_thickness=10.0,  # Compact reflector
        core_shape='square',
    )
    print(f"   ✓ Created compact core with {compact_core.n_assemblies} assemblies")
    print(f"   ✓ Reflector thickness: {compact_core.reflector_thickness:.1f} cm")
    
    print("\n3. Creating integral reactor design:")
    # Create in-vessel steam generator
    sg = InVesselSteamGenerator(
        id=1,
        position=Point3D(0, 0, 500),  # Above core
        n_tubes=1000,
        tube_bundle_diameter=200.0,
        height=600.0,
    )
    sg.build_tube_bundle(
        tube_outer_diameter=1.9,
        tube_inner_diameter=1.7,
        tube_length=600.0,
        tube_pitch=2.5,
    )
    
    # Create integrated primary system
    integrated_system = IntegratedPrimarySystem(
        name="Integral-PWR-SMR",
        vessel_diameter=400.0,
        vessel_height=1200.0,
        core=core,
    )
    integrated_system.add_steam_generator(sg)
    
    print(f"   ✓ Created integrated system")
    print(f"   ✓ Vessel volume: {integrated_system.vessel_volume()/1e6:.2f} m³")
    print(f"   ✓ Steam generators: {len(integrated_system.steam_generators)}")
    print(f"   ✓ Total heat transfer area: {integrated_system.total_steam_generator_heat_transfer()/1e6:.2f} MW")


def example_resonance_self_shielding():
    """Example: Resonance self-shielding for accurate cross-sections."""
    print("\n" + "=" * 70)
    print("Example 3: Resonance Self-Shielding")
    print("=" * 70)
    
    cache = NuclearDataCache()
    u238 = Nuclide(Z=92, A=238)
    
    print("\n1. Getting cross-section with self-shielding:")
    print("   U-238 capture cross-section in fuel pin (sigma_0 = 1000 barns)...")
    
    try:
        energy, xs_shielded = get_cross_section_with_self_shielding(
            cache,
            u238,
            "capture",
            temperature=900.0,  # K
            sigma_0=1000.0,  # Background cross-section [barns]
            use_self_shielding=True,
        )
        print(f"   ✓ Retrieved shielded cross-section")
        print(f"   ✓ Energy range: {energy.min():.2e} - {energy.max():.2e} eV")
        print(f"   ✓ Cross-section range: {xs_shielded.min():.2f} - {xs_shielded.max():.2f} barns")
        print(f"   ✓ Thermal (1 eV) value: {np.interp(1.0, energy, xs_shielded):.2f} barns")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print("   (ENDF files may not be set up. Run: python -m smrforge.core.endf_setup)")


def example_fission_data():
    """Example: Fission yield and delayed neutron data."""
    print("\n" + "=" * 70)
    print("Example 4: Fission Data (Yields & Delayed Neutrons)")
    print("=" * 70)
    
    cache = NuclearDataCache()
    u235 = Nuclide(Z=92, A=235)
    
    print("\n1. Getting fission yields (MF=5):")
    try:
        yields = get_fission_yields(
            cache,
            u235,
            yield_type="independent",
        )
        if yields:
            print(f"   ✓ Retrieved {len(yields)} fission products")
            # Show a few examples
            cs137 = Nuclide(Z=55, A=137)
            sr90 = Nuclide(Z=38, A=90)
            print(f"   ✓ Cs-137 yield: {yields.get(cs137, 0.0):.4f}")
            print(f"   ✓ Sr-90 yield: {yields.get(sr90, 0.0):.4f}")
        else:
            print("   ⚠ Fission yield data not found (ENDF files may not be set up)")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n2. Getting delayed neutron data:")
    try:
        delayed_data = get_delayed_neutron_data(cache, u235)
        if delayed_data:
            print(f"   ✓ Retrieved delayed neutron data")
            print(f"   ✓ Total beta: {delayed_data.get('beta', 0.0):.4f}")
            if 'beta_i' in delayed_data:
                print(f"   ✓ Delayed groups: {len(delayed_data['beta_i'])}")
                print(f"   ✓ Beta values: {[f'{b:.4f}' for b in delayed_data['beta_i']]}")
        else:
            print("   ⚠ Delayed neutron data not found")
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_prompt_delayed_chi():
    """Example: Prompt and delayed chi for transient analysis."""
    print("\n" + "=" * 70)
    print("Example 5: Prompt/Delayed Chi for Transients")
    print("=" * 70)
    
    cache = NuclearDataCache()
    u235 = Nuclide(Z=92, A=235)
    
    # Create energy group structure (26 groups from 10 MeV to 1e-5 eV)
    group_structure = np.logspace(7, -5, 27)  # 26 groups
    
    print("\n1. Getting prompt and delayed chi:")
    try:
        chi_prompt, chi_delayed = get_prompt_delayed_chi(
            cache,
            u235,
            group_structure,
        )
        print(f"   ✓ Retrieved chi spectra")
        print(f"   ✓ Number of groups: {len(chi_prompt)}")
        print(f"   ✓ Prompt chi sum: {chi_prompt.sum():.4f} (should be ~1.0)")
        print(f"   ✓ Delayed chi sum: {chi_delayed.sum():.4f} (should be ~1.0)")
        print(f"   ✓ Peak prompt energy: {group_structure[np.argmax(chi_prompt)]:.2e} eV")
        print(f"   ✓ Peak delayed energy: {group_structure[np.argmax(chi_delayed)]:.2e} eV")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print("   (ENDF files may not be set up)")


def example_decay_chains():
    """Example: Decay chain utilities and Bateman equations."""
    print("\n" + "=" * 70)
    print("Example 6: Decay Chain Utilities")
    print("=" * 70)
    
    if not _DECAY_CHAIN_AVAILABLE:
        print("Decay chain utilities not available.")
        return
    
    cache = NuclearDataCache()
    u235 = Nuclide(Z=92, A=235)
    
    print("\n1. Building fission product decay chain:")
    try:
        # Build chain for Cs-137 (important fission product)
        cs137 = Nuclide(Z=55, A=137)
        chain = build_fission_product_chain(
            cache,
            u235,
            target_nuclide=cs137,
            max_depth=5,
        )
        print(f"   ✓ Built decay chain with {len(chain.nuclides)} nuclides")
        print(f"   ✓ Chain nuclides: {[n.name for n in chain.nuclides[:5]]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n2. Solving Bateman equations:")
    try:
        # Simple decay chain: U-235 -> (decay) -> ...
        u235 = Nuclide(Z=92, A=235)
        initial_concentrations = np.array([1.0, 0.0, 0.0])  # U-235, daughter1, daughter2
        nuclides = [u235]  # Simplified for example
        
        # Time evolution (1 year)
        time = 365.0 * 24 * 3600  # seconds
        
        final_concentrations = solve_bateman_equations(
            nuclides,
            initial_concentrations,
            time,
            cache=cache,
        )
        print(f"   ✓ Solved Bateman equations")
        print(f"   ✓ Initial U-235: {initial_concentrations[0]:.4f}")
        print(f"   ✓ Final U-235: {final_concentrations[0]:.4f}")
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_thermal_scattering():
    """Example: Thermal scattering laws (TSL) for moderator materials."""
    print("\n" + "=" * 70)
    print("Example 7: Thermal Scattering Laws (TSL)")
    print("=" * 70)
    
    if not _TSL_AVAILABLE:
        print("TSL utilities not available.")
        return
    
    cache = NuclearDataCache()
    
    print("\n1. Getting TSL data for H2O:")
    try:
        tsl_name = get_tsl_material_name("H2O")
        print(f"   ✓ TSL material name: {tsl_name}")
        
        tsl_data = get_thermal_scattering_data(tsl_name, cache=cache)
        if tsl_data:
            print(f"   ✓ Retrieved TSL data")
            print(f"   ✓ Material: {tsl_data.material_name}")
            print(f"   ✓ Temperature: {tsl_data.temperature:.1f} K")
            print(f"   ✓ Alpha values: {len(tsl_data.alpha_values)} points")
            print(f"   ✓ Beta values: {len(tsl_data.beta_values)} points")
            print(f"   ✓ S(α,β) array shape: {tsl_data.s_alpha_beta.shape}")
        else:
            print("   ⚠ TSL data not found (ENDF files may not be set up)")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n2. Getting TSL data for graphite:")
    try:
        tsl_name = get_tsl_material_name("graphite")
        tsl_data = get_thermal_scattering_data(tsl_name, cache=cache)
        if tsl_data:
            print(f"   ✓ Retrieved graphite TSL data")
            print(f"   ✓ Material: {tsl_data.material_name}")
        else:
            print("   ⚠ Graphite TSL data not found")
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_nuclide_inventory_tracking():
    """Example: Nuclide inventory tracking for burnup."""
    print("\n" + "=" * 70)
    print("Example 8: Nuclide Inventory Tracking")
    print("=" * 70)
    
    print("\n1. Creating inventory tracker:")
    tracker = NuclideInventoryTracker()
    
    # Add initial nuclides
    u235 = Nuclide(Z=92, A=235)
    u238 = Nuclide(Z=92, A=238)
    
    tracker.add_nuclide(u235, atom_density=0.0005)  # atoms/barn-cm
    tracker.add_nuclide(u238, atom_density=0.02)
    
    print(f"   ✓ Created inventory tracker")
    print(f"   ✓ Tracking {len(tracker.nuclides)} nuclides")
    print(f"   ✓ U-235 density: {tracker.get_atom_density(u235):.6f} atoms/barn-cm")
    print(f"   ✓ U-238 density: {tracker.get_atom_density(u238):.6f} atoms/barn-cm")
    
    print("\n2. Updating inventory after burnup step:")
    # Simulate burnup: U-235 decreases, fission products increase
    tracker.update_nuclide(u235, atom_density=0.0004)
    tracker.burnup = 10.0  # MWd/kgU
    
    print(f"   ✓ Updated inventory")
    print(f"   ✓ New U-235 density: {tracker.get_atom_density(u235):.6f} atoms/barn-cm")
    print(f"   ✓ Burnup: {tracker.burnup:.1f} MWd/kgU")
    
    print("\n3. Adding fission products:")
    cs137 = Nuclide(Z=55, A=137)
    sr90 = Nuclide(Z=38, A=90)
    tracker.add_nuclide(cs137, atom_density=0.0001)
    tracker.add_nuclide(sr90, atom_density=0.00008)
    
    print(f"   ✓ Added fission products")
    print(f"   ✓ Total nuclides tracked: {len(tracker.nuclides)}")
    print(f"   ✓ Total atom density: {tracker.get_total_atom_density():.6f} atoms/barn-cm")


def example_integrated_smr_analysis():
    """Example: Complete integrated SMR analysis workflow."""
    print("\n" + "=" * 70)
    print("Example 9: Integrated SMR Analysis Workflow")
    print("=" * 70)
    
    print("\nThis example demonstrates a complete workflow:")
    print("  1. Create LWR SMR geometry")
    print("  2. Set up nuclear data with self-shielding")
    print("  3. Run neutronics calculation")
    print("  4. Track nuclide inventory")
    print("  5. Visualize results")
    
    # Step 1: Create geometry
    print("\n1. Creating PWR SMR core...")
    core = PWRSMRCore(name="Integrated-Analysis")
    core.build_square_lattice_core(
        n_assemblies_x=3,
        n_assemblies_y=3,
        assembly_pitch=21.5,
        assembly_height=365.76,
        lattice_size=17,
    )
    core.build_mesh(n_radial=20, n_axial=10)
    print(f"   ✓ Created {core.n_assemblies} assemblies")
    
    # Step 2: Nuclear data (simplified for example)
    print("\n2. Setting up nuclear data...")
    cache = NuclearDataCache()
    print("   ✓ Nuclear data cache initialized")
    
    # Step 3: Neutronics (simplified)
    print("\n3. Running neutronics calculation...")
    # Create simple 2-group cross-sections
    xs_data = CrossSectionData(
        n_groups=2,
        n_materials=1,
        sigma_t=np.array([[0.5, 0.8]]),
        sigma_a=np.array([[0.1, 0.2]]),
        sigma_f=np.array([[0.05, 0.15]]),
        nu_sigma_f=np.array([[0.125, 0.375]]),
        sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
        chi=np.array([[1.0, 0.0]]),
        D=np.array([[1.5, 0.4]]),
    )
    
    options = SolverOptions(max_iterations=100, tolerance=1e-6)
    solver = MultiGroupDiffusion(core, xs_data, options)
    
    try:
        k_eff, flux = solver.solve_steady_state()
        print(f"   ✓ k-effective: {k_eff:.6f}")
        print(f"   ✓ Flux shape: {flux.shape}")
    except Exception as e:
        print(f"   ✗ Error in neutronics: {e}")
    
    # Step 4: Inventory tracking
    print("\n4. Setting up nuclide inventory tracking...")
    tracker = NuclideInventoryTracker()
    u235 = Nuclide(Z=92, A=235)
    tracker.add_nuclide(u235, atom_density=0.0005)
    print(f"   ✓ Tracking {len(tracker.nuclides)} nuclides")
    
    # Step 5: Visualization
    if _ADVANCED_VIZ_AVAILABLE:
        print("\n5. Creating visualization...")
        try:
            # Create dummy power distribution
            power = np.random.rand(20, 10)
            dashboard = create_dashboard(
                core,
                flux=flux if 'flux' in locals() else None,
                power=power,
                views=['xy', 'xz'],
                backend='plotly',
            )
            print("   ✓ Dashboard created")
        except Exception as e:
            print(f"   ✗ Visualization error: {e}")
    
    print("\n✓ Integrated analysis workflow complete!")


def main():
    """Run all advanced feature examples."""
    print("\n" + "=" * 70)
    print("SMRForge Advanced Features - Comprehensive Examples")
    print("=" * 70)
    print("\nThis script demonstrates advanced features and new capabilities.")
    print("Some examples require ENDF files to be set up.")
    print("Run: python -m smrforge.core.endf_setup\n")
    
    # Run examples
    example_advanced_visualization()
    example_lwr_smr_geometry()
    example_resonance_self_shielding()
    example_fission_data()
    example_prompt_delayed_chi()
    example_decay_chains()
    example_thermal_scattering()
    example_nuclide_inventory_tracking()
    example_integrated_smr_analysis()
    
    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)
    print("\nFor more examples, see:")
    print("  - examples/comprehensive_examples.py (basic features)")
    print("  - examples/lwr_smr_example.py (LWR SMR specific)")
    print("  - examples/visualization_3d_example.py (3D visualization)")
    print("  - examples/burnup_example.py (burnup calculations)")


if __name__ == "__main__":
    main()
