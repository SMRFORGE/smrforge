"""
Basic Neutronics Example
========================

This example demonstrates the simplest neutronics calculation: computing k-effective
for a reactor core using the multi-group diffusion solver.

This is the "hello world" of reactor physics calculations.
"""

import numpy as np
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.validation.models import CrossSectionData, SolverOptions

# Import test utilities for simple geometry
from tests.test_utilities import SimpleGeometry


def create_simple_cross_sections():
    """
    Create simple 2-group cross-section data.
    
    Returns:
        CrossSectionData object with fuel and reflector cross-sections
    """
    return CrossSectionData(
        n_groups=2,
        n_materials=2,  # Fuel and reflector
        sigma_t=np.array([
            [0.30, 0.90],  # Fuel: fast, thermal total cross-section
            [0.28, 0.75],  # Reflector: fast, thermal total cross-section
        ]),
        sigma_a=np.array([
            [0.008, 0.12],  # Fuel: absorption
            [0.002, 0.025],  # Reflector: absorption
        ]),
        sigma_f=np.array([
            [0.006, 0.10],  # Fuel: fission (reflector has none)
            [0.0, 0.0],
        ]),
        nu_sigma_f=np.array([
            [0.015, 0.25],  # Fuel: nu * fission
            [0.0, 0.0],
        ]),
        sigma_s=np.array([
            [[0.29, 0.01], [0.0, 0.78]],  # Fuel scattering matrix
            [[0.28, 0.0], [0.0, 0.73]],  # Reflector scattering matrix
        ]),
        chi=np.array([
            [1.0, 0.0],  # Fission spectrum (all fast neutrons)
            [1.0, 0.0],
        ]),
        D=np.array([
            [1.0, 0.4],  # Diffusion coefficients
            [1.2, 0.5],
        ]),
    )


def main():
    """Run basic neutronics calculation."""
    
    print("=" * 60)
    print("Basic Neutronics Example")
    print("=" * 60)
    print()
    
    # Step 1: Create geometry
    print("1. Creating reactor geometry...")
    geometry = SimpleGeometry(
        core_diameter=200.0,  # cm
        core_height=400.0     # cm
    )
    print(f"   Core diameter: {geometry.core_diameter} cm")
    print(f"   Core height: {geometry.core_height} cm")
    print(f"   Radial mesh points: {len(geometry.radial_mesh)}")
    print(f"   Axial mesh points: {len(geometry.axial_mesh)}")
    print()
    
    # Step 2: Create cross-section data
    print("2. Creating cross-section data...")
    xs_data = create_simple_cross_sections()
    print(f"   Energy groups: {xs_data.n_groups}")
    print(f"   Materials: {xs_data.n_materials}")
    print()
    
    # Step 3: Create solver options
    print("3. Setting up solver...")
    options = SolverOptions(
        max_iterations=100,
        tolerance=1e-5,
        eigen_method="power",  # Power iteration method
        verbose=False
    )
    print(f"   Max iterations: {options.max_iterations}")
    print(f"   Tolerance: {options.tolerance}")
    print()
    
    # Step 4: Create solver
    print("4. Creating neutronics solver...")
    solver = MultiGroupDiffusion(geometry, xs_data, options)
    print(f"   Mesh size: {solver.nz} × {solver.nr} × {solver.ng}")
    print(f"   Total unknowns: {solver.nz * solver.nr * solver.ng}")
    print()
    
    # Step 5: Solve for k-effective
    print("5. Solving eigenvalue problem...")
    k_eff, flux = solver.solve_steady_state()
    print()
    
    # Step 6: Display results
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"k-effective: {k_eff:.6f}")
    
    if k_eff < 1.0:
        print("Reactor is SUBCRITICAL (k < 1.0)")
    elif k_eff > 1.0:
        print("Reactor is SUPERCRITICAL (k > 1.0)")
    else:
        print("Reactor is CRITICAL (k = 1.0)")
    
    print()
    print(f"Flux shape: {flux.shape}")
    print(f"Maximum flux: {np.max(flux):.4e}")
    print(f"Minimum flux: {np.min(flux):.4e}")
    print(f"Average flux: {np.mean(flux):.4e}")
    
    # Step 7: Compute power distribution
    print()
    print("6. Computing power distribution...")
    total_power = 10e6  # 10 MW
    power = solver.compute_power_distribution(total_power)
    print(f"   Total power: {total_power / 1e6:.1f} MW")
    print(f"   Peak power density: {np.max(power):.2e} W/cm³")
    print(f"   Average power density: {np.mean(power):.2e} W/cm³")
    print()
    
    print("=" * 60)
    print("Calculation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

