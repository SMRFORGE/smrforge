"""
Example: Gamma Transport Calculation

This example demonstrates gamma-ray transport calculations for
shielding analysis using the gamma transport solver.
"""

import numpy as np

from smrforge.gamma_transport import GammaTransportSolver, GammaTransportOptions
from smrforge.geometry import PrismaticCore


def main():
    """Run gamma transport example."""
    print("=" * 60)
    print("Gamma Transport Calculation Example")
    print("=" * 60)
    
    # Create geometry (shielding configuration)
    geometry = PrismaticCore(name="Shielding")
    geometry.core_height = 200.0  # cm
    geometry.core_diameter = 100.0  # cm
    geometry.build_mesh(n_radial=10, n_axial=5)
    
    print(f"\nGeometry: {geometry.n_axial}×{geometry.n_radial} mesh")
    print(f"Height: {geometry.core_height} cm")
    print(f"Diameter: {geometry.core_diameter} cm")
    
    # Initialize solver
    options = GammaTransportOptions(
        n_groups=20,  # 20 energy groups
        max_iterations=100,
        tolerance=1e-6,
        verbose=True,
    )
    
    solver = GammaTransportSolver(geometry, options)
    
    # Create gamma source (from decay heat, etc.)
    # Source is typically highest at center, decreases radially
    source = np.zeros((geometry.n_axial, geometry.n_radial, options.n_groups))
    
    # Place source in center region (simplified)
    center_z = geometry.n_axial // 2
    center_r = geometry.n_radial // 2
    
    # Source strength: 1e10 photons/cm³/s per group (typical)
    source[center_z, center_r, :] = 1e10
    
    # Exponential decay radially
    for ir in range(geometry.n_radial):
        r = geometry.r_centers[ir]
        r_center = geometry.r_centers[center_r]
        decay = np.exp(-(r - r_center) / 10.0)  # 10 cm decay length
        source[center_z, ir, :] = 1e10 * decay
    
    print(f"\nSource strength: {np.max(source):.2e} photons/cm³/s")
    print(f"Source location: z={center_z}, r={center_r}")
    
    # Solve gamma transport
    print("\nSolving gamma transport equation...")
    flux = solver.solve(source)
    
    print(f"\nFlux range: [{np.min(flux):.2e}, {np.max(flux):.2e}] photons/cm²/s")
    
    # Compute dose rate
    print("\nComputing dose rate...")
    dose_rate = solver.compute_dose_rate(flux)
    
    print(f"Dose rate range: [{np.min(dose_rate):.2e}, {np.max(dose_rate):.2e}] Sv/h")
    
    # Display results at key locations
    print("\n" + "=" * 60)
    print("Results at Key Locations")
    print("=" * 60)
    
    locations = [
        ("Center", center_z, center_r),
        ("Edge", center_z, geometry.n_radial - 1),
        ("Top", geometry.n_axial - 1, center_r),
        ("Bottom", 0, center_r),
    ]
    
    print(f"{'Location':<12} {'Flux [ph/cm²/s]':<20} {'Dose [Sv/h]':<15}")
    print("-" * 60)
    
    for name, iz, ir in locations:
        flux_val = np.sum(flux[iz, ir, :])  # Total flux over all groups
        dose_val = dose_rate[iz, ir]
        print(f"{name:<12} {flux_val:.4e}        {dose_val:.4e}")
    
    # Energy group analysis
    print("\n" + "=" * 60)
    print("Energy Group Analysis (at center)")
    print("=" * 60)
    
    print(f"{'Group':<8} {'Energy [MeV]':<15} {'Flux [ph/cm²/s]':<20}")
    print("-" * 60)
    
    for g in range(0, options.n_groups, 2):  # Show every other group
        E_center = (solver.energy_groups[g] + solver.energy_groups[g + 1]) / 2
        flux_g = flux[center_z, center_r, g]
        print(f"{g:<8} {E_center:.4f}        {flux_g:.4e}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

