"""
Example: LWR SMR Core Geometry and Nuclear Data Usage

Demonstrates how to use the new LWR SMR geometry classes and
SMR-focused nuclear data features for SMR development and prototyping.
"""

import numpy as np
from pathlib import Path

try:
    from smrforge.geometry import PWRSMRCore, FuelAssembly, FuelRod
    from smrforge.core.reactor_core import (
        NuclearDataCache,
        Nuclide,
        Library,
        get_cross_section_with_self_shielding,
        get_fission_yields,
        get_delayed_neutron_data,
    )

    print("[OK] All SMR modules imported successfully")
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    raise


def example_nuscale_core():
    """Example: Create a NuScale-style 17x17 PWR SMR core."""
    print("\n" + "=" * 60)
    print("Example 1: NuScale-Style PWR SMR Core")
    print("=" * 60)

    # Create PWR SMR core
    core = PWRSMRCore(name="NuScale-77MWe")

    # Build square lattice core
    # NuScale uses 17x17 fuel assemblies
    core.build_square_lattice_core(
        n_assemblies_x=4,  # Small core for example
        n_assemblies_y=4,
        assembly_pitch=21.5,  # cm (typical PWR)
        assembly_height=365.76,  # cm (12 feet)
        lattice_size=17,  # 17x17 NuScale
        rod_pitch=1.26,  # cm
    )

    print(f"Core: {core.name}")
    print(f"Assemblies: {len(core.assemblies)}")
    print(f"Total fuel rods: {sum(len(a.fuel_rods) for a in core.assemblies)}")
    print(f"Core height: {core.core_height:.1f} cm")
    print(f"Core diameter: {core.core_diameter:.1f} cm")

    # Access individual assemblies
    assembly = core.assemblies[0]
    print(f"\nFirst assembly:")
    print(f"  Lattice size: {assembly.lattice_size}x{assembly.lattice_size}")
    print(f"  Fuel rods: {len(assembly.fuel_rods)}")
    print(f"  Guide tubes: {len(assembly.guide_tubes)}")

    # Generate mesh for neutronics
    core.generate_mesh(n_radial=20, n_axial=30)
    print(f"\nMesh generated:")
    print(f"  Radial mesh points: {len(core.radial_mesh)}")
    print(f"  Axial mesh points: {len(core.axial_mesh)}")

    # Export to DataFrame
    df = core.to_dataframe()
    print(f"\nDataFrame export:")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {df.columns}")


def example_self_shielding():
    """Example: Get self-shielded cross-sections for SMR fuel pins."""
    print("\n" + "=" * 60)
    print("Example 2: Resonance Self-Shielding for SMR Fuel Pins")
    print("=" * 60)

    cache = NuclearDataCache()

    try:
        u238 = Nuclide(Z=92, A=238)

        # Get infinite dilution cross-section (no self-shielding)
        print("\nGetting cross-sections...")
        energy_inf, xs_inf = cache.get_cross_section(
            u238, "capture", temperature=900.0
        )

        # Get self-shielded cross-section (for fuel pin in water)
        # sigma_0 = 1000 barns is typical background in PWR
        energy_shielded, xs_shielded = get_cross_section_with_self_shielding(
            cache,
            u238,
            "capture",
            temperature=900.0,
            sigma_0=1000.0,  # Background XS [barns]
            use_self_shielding=True,
        )

        print(f"Energy range: {energy_inf.min():.2e} - {energy_inf.max():.2e} eV")
        print(f"Infinite dilution XS (mean): {xs_inf.mean():.4f} b")
        print(f"Self-shielded XS (mean): {xs_shielded.mean():.4f} b")

        reduction = (1 - xs_shielded.mean() / xs_inf.mean()) * 100
        print(f"Self-shielding reduction: {reduction:.2f}%")

        # Compare at thermal energy (1 eV)
        thermal_energy = 1.0  # eV
        xs_inf_thermal = np.interp(thermal_energy, energy_inf, xs_inf)
        xs_shielded_thermal = np.interp(thermal_energy, energy_shielded, xs_shielded)

        print(f"\nAt thermal energy (1 eV):")
        print(f"  Infinite dilution: {xs_inf_thermal:.4f} b")
        print(f"  Self-shielded: {xs_shielded_thermal:.4f} b")

    except (FileNotFoundError, ImportError) as e:
        print(f"[WARNING] ENDF files not available: {e}")
        print("   This example requires ENDF files to be set up.")
        print("   Run: python -m smrforge.core.endf_setup")


def example_fission_yields():
    """Example: Get fission yields for SMR burnup calculations."""
    print("\n" + "=" * 60)
    print("Example 3: Fission Yields for SMR Burnup Analysis")
    print("=" * 60)

    cache = NuclearDataCache()

    try:
        u235 = Nuclide(Z=92, A=235)

        # Get independent fission yields
        print("\nGetting independent fission yields...")
        yields = get_fission_yields(cache, u235, yield_type="independent")

        if yields:
            print(f"Found {len(yields)} fission products")

            # Find important fission products
            important_fps = [
                (Nuclide(Z=55, A=137), "Cs-137"),
                (Nuclide(Z=38, A=90), "Sr-90"),
                (Nuclide(Z=54, A=131), "Xe-131"),
                (Nuclide(Z=56, A=140), "Ba-140"),
            ]

            print("\nImportant fission products:")
            for fp, name in important_fps:
                yield_val = yields.get(fp, 0.0)
                if yield_val > 0:
                    print(f"  {name}: {yield_val:.6f}")

            # Get cumulative yields
            print("\nGetting cumulative yields...")
            cum_yields = get_fission_yields(cache, u235, yield_type="cumulative")
            if cum_yields:
                print(f"Found {len(cum_yields)} cumulative yields")
        else:
            print("[WARNING] Fission yield data not found")
            print("   This requires ENDF fission yield files (nfy-version.VIII.1/)")

    except (FileNotFoundError, ImportError) as e:
        print(f"[WARNING] ENDF files not available: {e}")


def example_delayed_neutrons():
    """Example: Get delayed neutron data for SMR transient analysis."""
    print("\n" + "=" * 60)
    print("Example 4: Delayed Neutron Data for SMR Safety Analysis")
    print("=" * 60)

    cache = NuclearDataCache()

    try:
        u235 = Nuclide(Z=92, A=235)

        print("\nGetting delayed neutron data...")
        dn_data = get_delayed_neutron_data(cache, u235)

        if dn_data:
            print(f"Total delayed neutron fraction (beta): {dn_data['beta']:.6f}")
            print(f"Number of delayed neutron groups: {len(dn_data['beta_i'])}")

            print("\nDelayed neutron group data:")
            for i, (beta_i, lambda_i) in enumerate(
                zip(dn_data["beta_i"], dn_data["lambda_i"])
            ):
                half_life = np.log(2) / lambda_i  # seconds
                print(
                    f"  Group {i+1}: beta={beta_i:.6f}, "
                    f"lambda={lambda_i:.3f} 1/s, "
                    f"T_1/2={half_life:.2f} s"
                )

            # Verify beta sum
            beta_sum = sum(dn_data["beta_i"])
            print(f"\nBeta sum: {beta_sum:.6f} (should equal total beta)")
        else:
            print("[WARNING] Delayed neutron data not found")
            print("   This requires ENDF files with MF=1, MT=455 data")

    except (FileNotFoundError, ImportError) as e:
        print(f"[WARNING] ENDF files not available: {e}")


def example_integration():
    """Example: Integration of geometry and nuclear data for SMR analysis."""
    print("\n" + "=" * 60)
    print("Example 5: Integrated SMR Analysis Workflow")
    print("=" * 60)

    # Create SMR core
    core = PWRSMRCore(name="Example-SMR")
    core.build_square_lattice_core(
        n_assemblies_x=3,
        n_assemblies_y=3,
        lattice_size=17,
    )

    # Get nuclear data with self-shielding
    cache = NuclearDataCache()

    try:
        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)

        print("\nGetting cross-sections for fuel composition...")
        print("(This would be used in neutronics solver)")

        # Get self-shielded cross-sections
        for nuclide, name in [(u235, "U-235"), (u238, "U-238")]:
            try:
                energy, xs = get_cross_section_with_self_shielding(
                    cache,
                    nuclide,
                    "fission",
                    temperature=900.0,
                    sigma_0=1000.0,
                )
                print(f"  {name} fission XS: {xs.mean():.4f} b (mean)")
            except (FileNotFoundError, ImportError):
                print(f"  {name}: ENDF file not available")

        print("\n[OK] SMR core geometry and nuclear data ready for analysis")

    except (FileNotFoundError, ImportError) as e:
        print(f"[WARNING] ENDF files not available: {e}")


if __name__ == "__main__":
    print("SMRForge LWR SMR Examples")
    print("=" * 60)

    # Run examples
    example_nuscale_core()
    example_self_shielding()
    example_fission_yields()
    example_delayed_neutrons()
    example_integration()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
