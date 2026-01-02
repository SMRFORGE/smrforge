"""
Example: Using Thermal Scattering Law (TSL) data for accurate thermal reactor calculations.

This example demonstrates how to use TSL data to improve scattering
cross-section calculations for moderator materials like H2O and graphite.
"""

import numpy as np
from pathlib import Path

from smrforge.core.reactor_core import (
    Nuclide,
    NuclearDataCache,
    get_thermal_scattering_data,
)
from smrforge.core.thermal_scattering_parser import (
    ThermalScatteringParser,
    get_tsl_material_name,
    ScatteringLawData,
)


def main():
    """Demonstrate thermal scattering law usage."""
    
    print("=" * 60)
    print("SMRForge Thermal Scattering Law (TSL) Example")
    print("=" * 60)
    
    # Map common material names to TSL names
    print("\n1. Material name mapping:")
    materials = ["H2O", "graphite", "D2O", "BeO"]
    for material in materials:
        tsl_name = get_tsl_material_name(material)
        if tsl_name:
            print(f"   {material:12} -> {tsl_name}")
        else:
            print(f"   {material:12} -> (no TSL mapping)")
    
    # Create cache (optional: specify ENDF directory)
    print("\n2. Setting up nuclear data cache...")
    # If you have ENDF files, specify the directory:
    # cache = NuclearDataCache(local_endf_dir=Path("C:/path/to/ENDF-B-VIII.1"))
    cache = NuclearDataCache()
    
    # Get TSL data for H2O
    print("\n3. Loading TSL data for H2O...")
    tsl_name = get_tsl_material_name("H2O")
    if tsl_name:
        tsl_data = get_thermal_scattering_data(tsl_name, cache=cache)
        
        if tsl_data:
            print(f"   ✓ TSL data loaded successfully")
            print(f"   Material: {tsl_data.material_name}")
            print(f"   Temperature: {tsl_data.temperature} K")
            print(f"   Bound atom mass: {tsl_data.bound_atom_mass:.3f} amu")
            print(f"   Coherent scattering: {tsl_data.coherent_scattering}")
            print(f"   α range: [{tsl_data.alpha_values[0]:.2e}, {tsl_data.alpha_values[-1]:.2e}]")
            print(f"   β range: [{tsl_data.beta_values[0]:.2f}, {tsl_data.beta_values[-1]:.2f}]")
            print(f"   S(α,β) shape: {tsl_data.s_alpha_beta.shape}")
        else:
            print(f"   ⚠ TSL data not found (ENDF files may not be available)")
            print(f"   Creating placeholder data for demonstration...")
            # Create placeholder for demonstration
            parser = ThermalScatteringParser()
            tsl_data = parser._create_placeholder_data(tsl_name, Path("placeholder"))
    else:
        print("   ⚠ Could not map H2O to TSL material name")
        tsl_data = None
    
    # Demonstrate S(α,β) interpolation
    if tsl_data:
        print("\n4. S(α,β) interpolation examples:")
        test_cases = [
            (0.1, 0.0),   # Small α, zero β
            (1.0, 0.0),   # Medium α, zero β
            (10.0, 0.0),  # Large α, zero β
            (1.0, 5.0),   # Medium α, positive β
            (1.0, -5.0),  # Medium α, negative β
        ]
        
        print(f"   {'α':>8} {'β':>8} {'S(α,β)':>12}")
        print("   " + "-" * 30)
        for alpha, beta in test_cases:
            s_value = tsl_data.get_s(alpha, beta)
            print(f"   {alpha:8.2f} {beta:8.2f} {s_value:12.6e}")
    
    # Demonstrate cross-section calculation
    if tsl_data:
        print("\n5. Thermal scattering cross-section calculation:")
        parser = ThermalScatteringParser()
        
        # Thermal neutron energies
        energies_in = np.array([0.025, 0.1, 1.0])  # eV
        energies_out = np.array([0.025, 0.1, 1.0])  # eV
        
        print(f"   {'E_in (eV)':>12} {'E_out (eV)':>12} {'σ_s (barns)':>12}")
        print("   " + "-" * 40)
        for e_in in energies_in:
            for e_out in energies_out:
                xs = parser.compute_thermal_scattering_xs(
                    tsl_data, e_in, e_out, temperature=293.6
                )
                print(f"   {e_in:12.3f} {e_out:12.3f} {xs:12.2f}")
    
    # Show integration with scattering matrix
    print("\n6. Integration with scattering matrix:")
    print("   TSL data can be used to compute accurate scattering matrices")
    print("   for thermal energy groups in multi-group calculations.")
    print("   ")
    print("   Example workflow:")
    print("   1. Load TSL data for moderator material")
    print("   2. Compute S(α,β) for each energy group pair")
    print("   3. Convert to scattering cross-section matrix")
    print("   4. Use in MultiGroupDiffusion solver")
    
    print("\n" + "=" * 60)
    print("TSL example complete!")
    print("=" * 60)
    print("\nNote: For production use, ensure ENDF TSL files are available")
    print("      in thermal_scatt-version.VIII.1/ directory.")


if __name__ == "__main__":
    main()

