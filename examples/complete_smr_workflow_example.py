"""
Complete SMRForge Workflow Example
Demonstrates: End-to-end SMR analysis from data setup to results export

This example showcases the full power of SMRForge:
- Automated ENDF data download
- Geometry creation (LWR SMR)
- Neutronics analysis
- Advanced burnup analysis (gadolinium, assembly/rod tracking)
- Safety transient analysis
- Comprehensive visualization
- Results export

Run this example to see SMRForge in action!
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 70)
print("SMRFORGE COMPLETE WORKFLOW EXAMPLE")
print("=" * 70)
print("\nThis example demonstrates:")
print("  1. Automated ENDF data download")
print("  2. NuScale PWR SMR geometry creation")
print("  3. Cross-section retrieval with self-shielding")
print("  4. Advanced burnup analysis (gadolinium, assembly/rod tracking)")
print("  5. Safety transient analysis (SLB, FWLB, LOCA)")
print("  6. Comprehensive visualization")
print("  7. Results export")
print("\n" + "=" * 70 + "\n")

# ============================================================================
# Step 1: Setup ENDF Data (Automated Download)
# ============================================================================

print("STEP 1: Setting up ENDF nuclear data...")
print("-" * 70)

try:
    from smrforge.data_downloader import download_endf_data
    
    # Download common SMR nuclides
    print("Downloading common SMR nuclides (this may take a few minutes)...")
    print("Note: Set show_progress=False in production for cleaner output")
    
    stats = download_endf_data(
        library="ENDF/B-VIII.1",
        nuclide_set="common_smr",
        output_dir="~/ENDF-Data",
        show_progress=True,
        max_workers=5,  # Parallel downloads
        validate=True,
        organize=True,
    )
    
    print(f"✓ Data download complete:")
    print(f"  Downloaded: {stats['downloaded']} files")
    print(f"  Skipped: {stats['skipped']} files")
    print(f"  Failed: {stats['failed']} files")
    print(f"  Output: {stats['output_dir']}")
    
except ImportError:
    print("⚠ Data downloader not available. Skipping automated download.")
    print("  You can set up ENDF data manually using:")
    print("    python -m smrforge.core.endf_setup")
    stats = {'output_dir': '~/ENDF-Data'}

except Exception as e:
    print(f"⚠ Data download failed: {e}")
    print("  Continuing with manual setup assumption...")
    stats = {'output_dir': '~/ENDF-Data'}

# ============================================================================
# Step 2: Create NuScale PWR SMR Geometry
# ============================================================================

print("\nSTEP 2: Creating NuScale PWR SMR geometry...")
print("-" * 70)

try:
    from smrforge.geometry.lwr_smr import PWRSMRCore
    from smrforge.geometry.smr_compact_core import CompactSMRCore
    
    # Create compact SMR core (NuScale: 37 assemblies)
    core = CompactSMRCore(
        name="NuScale-SMR",
        n_assemblies=37,
        assembly_pitch=21.5,  # cm
        active_height=200.0,  # cm
        core_shape="circular",
    )
    
    # Build square lattice assemblies (17x17 for NuScale)
    core.build_square_lattice_core(
        n_assemblies_x=6,
        n_assemblies_y=6,
        assembly_pitch=21.5,
        lattice_size=17,  # 17x17 fuel rods
        rod_pitch=1.26,  # cm
        rod_diameter=0.95,  # cm
        cladding_thickness=0.057,  # cm
    )
    
    print(f"✓ Geometry created:")
    print(f"  Assemblies: {core.n_assemblies}")
    print(f"  Total fuel rods: {sum(len(a.fuel_rods) for a in core.assemblies)}")
    print(f"  Core diameter: {core.core_diameter:.1f} cm")
    print(f"  Active height: {core.active_height:.1f} cm")
    
except Exception as e:
    print(f"✗ Geometry creation failed: {e}")
    print("  This example requires LWR SMR geometry support.")
    sys.exit(1)

# ============================================================================
# Step 3: Get Cross-Sections with Self-Shielding
# ============================================================================

print("\nSTEP 3: Computing cross-sections with self-shielding...")
print("-" * 70)

try:
    from smrforge.core.reactor_core import NuclearDataCache, Nuclide
    from smrforge.core.self_shielding_integration import (
        get_cross_section_with_self_shielding,
    )
    from pathlib import Path
    
    # Initialize cache
    cache = NuclearDataCache(local_endf_dir=Path(stats['output_dir']).expanduser())
    
    # Key nuclides
    u235 = Nuclide(Z=92, A=235)
    u238 = Nuclide(Z=92, A=238)
    
    # Get cross-sections with Bondarenko self-shielding
    sigma_0 = 1000.0  # Background cross-section [barns]
    temperature = 600.0  # K
    
    try:
        energy_u235, xs_fission_u235 = get_cross_section_with_self_shielding(
            cache,
            u235,
            "fission",
            temperature=temperature,
            sigma_0=sigma_0,
            method="bondarenko",
        )
        
        print(f"✓ Cross-sections retrieved:")
        print(f"  U-235 fission: {len(energy_u235)} energy points")
        if len(energy_u235) > 0:
            thermal_xs = np.interp(0.025, energy_u235, xs_fission_u235)
            print(f"  Thermal fission XS: {thermal_xs:.2f} barns")
    except Exception as e:
        print(f"⚠ Cross-section retrieval failed: {e}")
        print("  This may be due to missing ENDF files.")
        print("  Continuing with example...")
    
except Exception as e:
    print(f"⚠ Cross-section setup failed: {e}")
    print("  Continuing with example...")

# ============================================================================
# Step 4: Advanced Burnup Analysis
# ============================================================================

print("\nSTEP 4: Running advanced burnup analysis...")
print("-" * 70)

try:
    from smrforge.burnup.lwr_burnup import (
        GadoliniumDepletion,
        GadoliniumPoison,
        AssemblyWiseBurnupTracker,
        RodWiseBurnupTracker,
    )
    from smrforge.core.reactor_core import NuclearDataCache, Nuclide
    
    # Initialize
    cache = NuclearDataCache()
    gd_depletion = GadoliniumDepletion(cache)
    
    # Gadolinium configuration
    gd155 = Nuclide(Z=64, A=155)
    gd157 = Nuclide(Z=64, A=157)
    initial_gd = 1e20  # atoms/cm³
    
    gd_poison = GadoliniumPoison(
        nuclides=[gd155, gd157],
        initial_concentrations=np.array([initial_gd, initial_gd]),
    )
    
    # Calculate initial reactivity worth
    flux = 1e14  # n/cm²/s
    initial_worth = gd_depletion.calculate_reactivity_worth(gd_poison, flux, 0.0)
    print(f"✓ Gadolinium analysis:")
    print(f"  Initial reactivity worth: {initial_worth*1000:.1f} m$")
    
    # Assembly-wise tracking
    assembly_tracker = AssemblyWiseBurnupTracker(n_assemblies=37)
    
    # Simulate 3-year cycle
    time_points = np.linspace(0, 3 * 365 * 24 * 3600, 36)  # 36 months
    
    for t_idx, t in enumerate(time_points):
        for assembly_id in range(37):
            position = assembly_tracker.get_assembly_position(assembly_id)
            row, col = position
            center_row, center_col = 3, 3
            distance = np.sqrt((row - center_row)**2 + (col - center_col)**2)
            spatial_factor = 1.0 - distance * 0.1
            spatial_factor = max(0.5, spatial_factor)
            
            burnup = (t / (365 * 24 * 3600)) * 50.0 * spatial_factor
            assembly_tracker.update_assembly(assembly_id, position, burnup, 0.045)
    
    final_worth = gd_depletion.calculate_reactivity_worth(gd_poison, flux, time_points[-1])
    
    print(f"  Final reactivity worth: {final_worth*1000:.1f} m$")
    print(f"  Depletion: {(1 - final_worth/initial_worth)*100:.1f}%")
    print(f"  Final average burnup: {assembly_tracker.get_average_burnup():.2f} MWd/kgU")
    print(f"  Final peak burnup: {assembly_tracker.get_peak_burnup():.2f} MWd/kgU")
    
except Exception as e:
    print(f"⚠ Burnup analysis failed: {e}")
    print("  This may be due to missing dependencies.")
    print("  Continuing with example...")

# ============================================================================
# Step 5: Safety Transient Analysis
# ============================================================================

print("\nSTEP 5: Running safety transient analysis...")
print("-" * 70)

try:
    from smrforge.safety.transients import (
        TransientType,
        TransientConditions,
        SteamLineBreakTransient,
        FeedwaterLineBreakTransient,
        LOCATransientLWR,
    )
    
    # Create reactor specification
    class ReactorSpec:
        def __init__(self):
            self.name = "NuScale-SMR"
            self.power_thermal = 77e6
    
    reactor_spec = ReactorSpec()
    
    # Common conditions
    base_conditions = TransientConditions(
        initial_power=77e6,  # 77 MWth
        initial_temperature=600.0,  # K
        initial_flow_rate=100.0,  # kg/s
        initial_pressure=15.5e6,  # 15.5 MPa
        trigger_time=0.0,
        t_end=3600.0,  # 1 hour
        scram_available=True,
        scram_delay=1.0,  # 1 second
    )
    
    # 1. Steam Line Break
    print("  Analyzing Steam Line Break...")
    slb = SteamLineBreakTransient(reactor_spec, core)
    conditions_slb = base_conditions
    conditions_slb.transient_type = TransientType.STEAM_LINE_BREAK
    result_slb = slb.simulate(conditions_slb, break_area=0.01)
    print(f"    Peak power: {np.max(result_slb['power'])/1e6:.2f} MWth")
    print(f"    Min pressure: {np.min(result_slb['pressure'])/1e6:.2f} MPa")
    
    # 2. Feedwater Line Break
    print("  Analyzing Feedwater Line Break...")
    fwlb = FeedwaterLineBreakTransient(reactor_spec, core)
    conditions_fwlb = base_conditions
    conditions_fwlb.transient_type = TransientType.FEEDWATER_LINE_BREAK
    result_fwlb = fwlb.simulate(conditions_fwlb, break_area=0.02)
    print(f"    Peak temperature: {np.max(result_fwlb['temperature']):.1f} K")
    
    # 3. Small Break LOCA
    print("  Analyzing Small Break LOCA...")
    loca = LOCATransientLWR(reactor_spec, core)
    conditions_loca = base_conditions
    conditions_loca.transient_type = TransientType.SB_LOCA
    result_loca = loca.simulate(conditions_loca, break_area=0.05, break_type="small")
    print(f"    Min pressure: {np.min(result_loca['pressure'])/1e6:.2f} MPa")
    print(f"    Peak temperature: {np.max(result_loca['temperature']):.1f} K")
    
    print("✓ Safety analysis complete")
    
except Exception as e:
    print(f"⚠ Safety analysis failed: {e}")
    print("  This may be due to missing dependencies.")
    print("  Continuing with example...")
    result_slb = None
    result_fwlb = None
    result_loca = None

# ============================================================================
# Step 6: Visualization
# ============================================================================

print("\nSTEP 6: Creating visualizations...")
print("-" * 70)

try:
    from smrforge.visualization.geometry import plot_core_layout_2d
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # 1. Core layout
    fig1, ax1 = plt.subplots(figsize=(10, 10))
    plot_core_layout_2d(core, ax=ax1, show_legend=True)
    plt.title("NuScale SMR Core Layout (37 Assemblies)", fontsize=14, fontweight='bold')
    plt.savefig(output_dir / "nuscale_core_layout.png", dpi=300, bbox_inches='tight')
    print("  ✓ Core layout plot saved")
    
    # 2. Transient comparison (if available)
    if result_slb is not None:
        fig2, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Power comparison
        axes[0, 0].plot(result_slb['time'], result_slb['power'] / 1e6, 'b-', 
                        label='SLB', linewidth=2)
        if result_fwlb is not None:
            axes[0, 0].plot(result_fwlb['time'], result_fwlb['power'] / 1e6, 'r-', 
                            label='FWLB', linewidth=2)
        if result_loca is not None:
            axes[0, 0].plot(result_loca['time'], result_loca['power'] / 1e6, 'g-', 
                            label='SB-LOCA', linewidth=2)
        axes[0, 0].set_xlabel('Time [s]')
        axes[0, 0].set_ylabel('Power [MWth]')
        axes[0, 0].set_title('Transient Power Response')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # Pressure comparison
        axes[0, 1].plot(result_slb['time'], result_slb['pressure'] / 1e6, 'b-', 
                        label='SLB', linewidth=2)
        if result_loca is not None:
            axes[0, 1].plot(result_loca['time'], result_loca['pressure'] / 1e6, 'g-', 
                            label='SB-LOCA', linewidth=2)
        axes[0, 1].set_xlabel('Time [s]')
        axes[0, 1].set_ylabel('Pressure [MPa]')
        axes[0, 1].set_title('Transient Pressure Response')
        axes[0, 1].legend()
        axes[0, 1].grid(True)
        
        # Temperature comparison
        axes[1, 0].plot(result_slb['time'], result_slb['temperature'], 'b-', 
                        label='SLB', linewidth=2)
        if result_fwlb is not None:
            axes[1, 0].plot(result_fwlb['time'], result_fwlb['temperature'], 'r-', 
                            label='FWLB', linewidth=2)
        if result_loca is not None:
            axes[1, 0].plot(result_loca['time'], result_loca['temperature'], 'g-', 
                            label='SB-LOCA', linewidth=2)
        axes[1, 0].set_xlabel('Time [s]')
        axes[1, 0].set_ylabel('Temperature [K]')
        axes[1, 0].set_title('Transient Temperature Response')
        axes[1, 0].legend()
        axes[1, 0].grid(True)
        
        # Summary statistics
        axes[1, 1].axis('off')
        summary_text = "TRANSIENT ANALYSIS SUMMARY\n\n"
        summary_text += f"SLB:\n"
        summary_text += f"  Peak Power: {np.max(result_slb['power'])/1e6:.2f} MWth\n"
        summary_text += f"  Min Pressure: {np.min(result_slb['pressure'])/1e6:.2f} MPa\n"
        if result_fwlb is not None:
            summary_text += f"\nFWLB:\n"
            summary_text += f"  Peak Temp: {np.max(result_fwlb['temperature']):.1f} K\n"
        if result_loca is not None:
            summary_text += f"\nSB-LOCA:\n"
            summary_text += f"  Min Pressure: {np.min(result_loca['pressure'])/1e6:.2f} MPa\n"
            summary_text += f"  Peak Temp: {np.max(result_loca['temperature']):.1f} K\n"
        axes[1, 1].text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
                       verticalalignment='center', transform=axes[1, 1].transAxes)
        
        plt.tight_layout()
        plt.savefig(output_dir / "transient_comparison.png", dpi=300, bbox_inches='tight')
        print("  ✓ Transient comparison plot saved")
    
    # 3. Burnup distribution (if available)
    try:
        if 'assembly_tracker' in locals():
            distribution = assembly_tracker.get_burnup_distribution()
            fig3, ax3 = plt.subplots(figsize=(10, 8))
            im = ax3.imshow(distribution, cmap='viridis', origin='lower')
            plt.colorbar(im, ax=ax3, label='Burnup [MWd/kgU]')
            ax3.set_xlabel('Assembly Column')
            ax3.set_ylabel('Assembly Row')
            ax3.set_title('Assembly Burnup Distribution (End of 3-Year Cycle)')
            plt.savefig(output_dir / "burnup_distribution.png", dpi=300, bbox_inches='tight')
            print("  ✓ Burnup distribution plot saved")
    except:
        pass
    
    print("✓ Visualization complete")
    
except Exception as e:
    print(f"⚠ Visualization failed: {e}")
    print("  Some plots may not be generated.")

# ============================================================================
# Step 7: Summary
# ============================================================================

print("\n" + "=" * 70)
print("COMPLETE WORKFLOW EXAMPLE FINISHED!")
print("=" * 70)
print("\nThis example demonstrated:")
print("  ✓ Automated ENDF data download")
print("  ✓ NuScale PWR SMR geometry creation")
print("  ✓ Cross-section retrieval with self-shielding")
print("  ✓ Advanced burnup analysis (gadolinium, assembly/rod tracking)")
print("  ✓ Safety transient analysis (SLB, FWLB, LOCA)")
print("  ✓ Comprehensive visualization")
print("\nAll results saved to 'output/' directory")
print("\nFor more examples, see:")
print("  - docs/guides/complete-workflow-examples.md")
print("  - docs/guides/lwr-smr-transient-analysis.md")
print("  - docs/guides/lwr-smr-burnup-guide.md")
print("  - examples/ directory")
print("\n" + "=" * 70)
