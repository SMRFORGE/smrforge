"""
Example: Basic burnup calculation using BurnupSolver.

This example demonstrates how to use the burnup solver to track
nuclide concentrations over time in a reactor core.
"""

import numpy as np
from pathlib import Path

from smrforge.burnup import BurnupSolver, BurnupOptions
from smrforge.core.reactor_core import Nuclide, NuclearDataCache
from smrforge.geometry import PrismaticCore
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.validation.models import CrossSectionData, SolverOptions


def main():
    """Run a simple burnup calculation."""
    
    print("=" * 60)
    print("SMRForge Burnup Calculation Example")
    print("=" * 60)
    
    # Create geometry
    print("\n1. Creating geometry...")
    geometry = PrismaticCore(name="BurnupTestCore")
    geometry.core_height = 200.0  # cm
    geometry.core_diameter = 100.0  # cm
    geometry.build_mesh(n_radial=10, n_axial=5)
    print(f"   Mesh: {geometry.n_axial} axial × {geometry.n_radial} radial cells")
    
    # Create initial cross-sections (2-group, simplified)
    print("\n2. Creating initial cross-sections...")
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
    
    # Create neutronics solver
    print("\n3. Creating neutronics solver...")
    solver_options = SolverOptions(
        max_iterations=100,
        tolerance=1e-6,
        eigen_method="power",
        verbose=False,
    )
    neutronics = MultiGroupDiffusion(geometry, xs_data, solver_options)
    
    # Solve initial neutronics
    print("   Solving initial neutronics...")
    k_eff, flux = neutronics.solve_steady_state()
    print(f"   Initial k-eff: {k_eff:.6f}")
    
    # Create burnup options
    print("\n4. Setting up burnup calculation...")
    burnup_options = BurnupOptions(
        time_steps=[0, 30, 60, 90, 180, 365],  # days
        power_density=1e6,  # W/cm³ (1 MW/cm³)
        initial_enrichment=0.195,  # 19.5% U-235
        track_fission_products=True,
        track_actinides=True,
    )
    print(f"   Time steps: {burnup_options.time_steps} days")
    print(f"   Initial enrichment: {burnup_options.initial_enrichment*100:.1f}% U-235")
    
    # Create burnup solver
    # Note: If you have ENDF files, you can pass a cache:
    # cache = NuclearDataCache(local_endf_dir=Path("C:/path/to/ENDF-B-VIII.1"))
    # burnup = BurnupSolver(neutronics, burnup_options, cache=cache)
    burnup = BurnupSolver(neutronics, burnup_options)
    
    print(f"   Tracking {len(burnup.nuclides)} nuclides")
    
    # Run burnup calculation
    print("\n5. Running burnup calculation...")
    print("   (This may take a few minutes...)")
    inventory = burnup.solve()
    
    # Display results
    print("\n" + "=" * 60)
    print("Burnup Results")
    print("=" * 60)
    
    # Show key nuclides
    key_nuclides = [
        (Nuclide(Z=92, A=235), "U-235"),
        (Nuclide(Z=92, A=238), "U-238"),
        (Nuclide(Z=94, A=239), "Pu-239"),
        (Nuclide(Z=54, A=135), "Xe-135"),
        (Nuclide(Z=55, A=137), "Cs-137"),
    ]
    
    print("\nNuclide Concentrations (atoms/cm³):")
    print("-" * 60)
    print(f"{'Nuclide':<10} {'Initial':>15} {'Final':>15} {'Change':>15}")
    print("-" * 60)
    
    for nuc, name in key_nuclides:
        initial = inventory.get_concentration(nuc, time_index=0)
        final = inventory.get_concentration(nuc, time_index=-1)
        change = final - initial
        print(f"{name:<10} {initial:>15.2e} {final:>15.2e} {change:>15.2e}")
    
    # Show burnup
    print("\nBurnup:")
    print("-" * 60)
    final_burnup = inventory.burnup[-1]
    print(f"Final burnup: {final_burnup:.2f} MWd/kgU")
    
    # Show decay heat
    print("\nDecay Heat:")
    print("-" * 60)
    decay_heat = burnup.compute_decay_heat()
    print(f"Decay heat: {decay_heat:.2e} W")
    
    print("\n" + "=" * 60)
    print("Burnup calculation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

