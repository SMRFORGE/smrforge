"""
Example: Decay Heat Calculation

This example demonstrates how to calculate time-dependent decay heat
using decay data with gamma and beta spectra.
"""

import numpy as np

from smrforge.core.reactor_core import Nuclide
from smrforge.decay_heat import DecayHeatCalculator


def main():
    """Run decay heat calculation example."""
    print("=" * 60)
    print("Decay Heat Calculation Example")
    print("=" * 60)
    
    # Initialize calculator
    calculator = DecayHeatCalculator()
    
    # Define nuclides and initial concentrations
    # Typical post-shutdown inventory
    u235 = Nuclide(Z=92, A=235)
    u238 = Nuclide(Z=92, A=238)
    cs137 = Nuclide(Z=55, A=137)
    sr90 = Nuclide(Z=38, A=90)
    i131 = Nuclide(Z=53, A=131)
    
    # Initial concentrations [atoms/cm³]
    # These would come from burnup calculations in a real scenario
    concentrations = {
        u235: 1e20,  # Fissile material
        u238: 5e20,  # Fertile material
        cs137: 1e19,  # Fission product
        sr90: 5e18,   # Fission product
        i131: 1e18,   # Fission product
    }
    
    # Time points after shutdown [s]
    # 0, 1 hour, 1 day, 1 week, 1 month, 1 year
    times = np.array([
        0,
        3600,        # 1 hour
        86400,       # 1 day
        604800,      # 1 week
        2592000,     # 1 month
        31536000,    # 1 year
    ])
    
    print(f"\nCalculating decay heat for {len(concentrations)} nuclides")
    print(f"Time range: {times[0]/3600:.1f} hours to {times[-1]/86400:.1f} days")
    
    # Calculate decay heat
    result = calculator.calculate_decay_heat(concentrations, times)
    
    # Display results
    print("\n" + "=" * 60)
    print("Decay Heat Results")
    print("=" * 60)
    print(f"{'Time':<12} {'Total [W]':<15} {'Gamma [W]':<15} {'Beta [W]':<15}")
    print("-" * 60)
    
    for i, t in enumerate(times):
        total = result.total_decay_heat[i]
        gamma = result.gamma_decay_heat[i]
        beta = result.beta_decay_heat[i]
        
        time_str = f"{t/3600:.1f} h" if t < 86400 else f"{t/86400:.1f} d"
        print(f"{time_str:<12} {total:.4e}    {gamma:.4e}    {beta:.4e}")
    
    # Show nuclide contributions at 1 day
    print("\n" + "=" * 60)
    print("Nuclide Contributions at 1 Day")
    print("=" * 60)
    
    time_1day = 86400  # 1 day
    heat_1day = result.get_decay_heat_at_time(time_1day)
    
    print(f"Total decay heat: {heat_1day:.4e} W")
    print("\nTop contributors:")
    
    # Sort nuclides by contribution
    contributions = []
    for nuclide, heat_array in result.nuclide_contributions.items():
        idx = np.searchsorted(result.times, time_1day)
        if idx >= len(result.times):
            idx = len(result.times) - 1
        contributions.append((nuclide, heat_array[idx]))
    
    contributions.sort(key=lambda x: x[1], reverse=True)
    
    for nuclide, heat in contributions[:5]:
        fraction = heat / heat_1day * 100 if heat_1day > 0 else 0
        print(f"  {nuclide.name}: {heat:.4e} W ({fraction:.1f}%)")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

