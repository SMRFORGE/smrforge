"""
Example: Gamma Source Integration with Decay Heat and Transport

This example demonstrates:
1. Calculating decay heat with gamma production data
2. Generating time-dependent gamma source terms
3. Solving gamma transport with time-dependent sources
"""

import numpy as np

from smrforge.core.reactor_core import Nuclide, NuclearDataCache
from smrforge.decay_heat import DecayHeatCalculator
from smrforge.gamma_transport import GammaTransportSolver, GammaTransportOptions
from smrforge.geometry import PrismaticCore


def main():
    """Run gamma source integration example."""
    print("=" * 60)
    print("Gamma Source Integration Example")
    print("=" * 60)
    
    # Initialize cache with ENDF directory
    cache = NuclearDataCache()
    
    # Initialize decay heat calculator
    decay_calc = DecayHeatCalculator(cache=cache)
    
    # Define nuclides (typical post-shutdown inventory)
    u235 = Nuclide(Z=92, A=235)
    cs137 = Nuclide(Z=55, A=137)
    sr90 = Nuclide(Z=38, A=90)
    
    concentrations = {
        u235: 1e20,
        cs137: 1e19,
        sr90: 5e18,
    }
    
    # Time points after shutdown [s]
    times = np.array([0, 3600, 86400, 604800])  # 0, 1h, 1d, 1w
    
    print("\n1. Calculating decay heat...")
    decay_result = decay_calc.calculate_decay_heat(concentrations, times)
    
    print(f"   Decay heat at 1 day: {decay_result.get_decay_heat_at_time(86400):.4e} W")
    
    # Create gamma transport solver
    print("\n2. Setting up gamma transport solver...")
    geometry = PrismaticCore(name="Shielding")
    geometry.core_height = 200.0  # cm
    geometry.core_diameter = 100.0  # cm
    geometry.build_mesh(n_radial=10, n_axial=5)
    
    options = GammaTransportOptions(n_groups=20, verbose=False)
    transport = GammaTransportSolver(geometry, options, cache=cache)
    
    # Generate gamma source from decay heat
    print("\n3. Generating gamma source spectrum...")
    energy_groups = transport.energy_groups  # [MeV]
    gamma_source_4d = decay_calc.calculate_gamma_source(
        concentrations, times, energy_groups
    )  # [n_times, nz, nr, ng]
    
    print(f"   Source shape: {gamma_source_4d.shape}")
    print(f"   Max source: {np.max(gamma_source_4d):.4e} photons/cm³/s")
    
    # Solve gamma transport at different times
    print("\n4. Solving gamma transport at different times...")
    
    for i, t in enumerate(times):
        time_str = f"{t/3600:.1f} h" if t < 86400 else f"{t/86400:.1f} d"
        print(f"\n   Time: {time_str}")
        
        # Reshape source for this time step [nz, nr, ng]
        source_3d = gamma_source_4d[i, :, :, :]
        
        # Solve
        flux = transport.solve(source_3d, time=t)
        
        # Compute dose rate
        dose_rate = transport.compute_dose_rate(flux)
        
        print(f"   Max flux: {np.max(flux):.4e} photons/cm²/s")
        print(f"   Max dose rate: {np.max(dose_rate):.4e} Sv/h")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

