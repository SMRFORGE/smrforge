# LWR SMR Burnup Analysis Guide

**Last Updated:** January 2026

Comprehensive guide for performing advanced burnup analysis on Light Water Reactor (LWR) Small Modular Reactors (SMRs) using SMRForge.

---

## Overview

SMRForge provides advanced burnup analysis capabilities for LWR SMRs, including:

- ✅ **Gadolinium depletion** - Track burnable poison depletion during burnup
- ✅ **Assembly-wise tracking** - Monitor burnup distribution across fuel assemblies
- ✅ **Rod-wise tracking** - Detailed intra-assembly burnup distribution
- ✅ **Control rod shadowing** - Account for flux depression near control rods
- ✅ **Long-cycle optimization** - Support for 3-5 year fuel cycles
- ✅ **Nuclide inventory tracking** - Complete isotope evolution

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Gadolinium Depletion](#gadolinium-depletion)
3. [Assembly-Wise Burnup Tracking](#assembly-wise-burnup-tracking)
4. [Rod-Wise Burnup Tracking](#rod-wise-burnup-tracking)
5. [Complete Workflow](#complete-workflow)
6. [Advanced Techniques](#advanced-techniques)

---

## Quick Start

### Basic Gadolinium Depletion

```python
from smrforge.burnup.lwr_burnup import GadoliniumDepletion, GadoliniumPoison
from smrforge.core.reactor_core import Nuclide, NuclearDataCache
import numpy as np
import matplotlib.pyplot as plt

# Initialize cache and depletion calculator
cache = NuclearDataCache()
gd_depletion = GadoliniumDepletion(cache)

# Define gadolinium isotopes
gd155 = Nuclide(Z=64, A=155)
gd157 = Nuclide(Z=64, A=157)

# Initial concentrations (typical: 2-4 wt% Gd2O3 in UO2)
# For 3 wt% Gd2O3: ~1e20 atoms/cm³ of each isotope
initial_gd155 = 1e20  # atoms/cm³
initial_gd157 = 1e20  # atoms/cm³

# Create gadolinium poison configuration
gd_poison = GadoliniumPoison(
    nuclides=[gd155, gd157],
    initial_concentrations=np.array([initial_gd155, initial_gd157]),
)

# Time points (1 year cycle)
time_points = np.linspace(0, 365 * 24 * 3600, 100)  # seconds
flux = 1e14  # n/cm²/s (typical thermal flux)

# Calculate depletion over time
gd155_remaining = []
gd157_remaining = []

for t in time_points:
    gd155_conc = gd_depletion.deplete(gd155, initial_gd155, flux, t)
    gd157_conc = gd_depletion.deplete(gd157, initial_gd157, flux, t)
    gd155_remaining.append(gd155_conc / initial_gd155 * 100)
    gd157_remaining.append(gd157_conc / initial_gd157 * 100)

# Plot results
plt.figure(figsize=(10, 6))
plt.plot(time_points / (365 * 24 * 3600), gd155_remaining, 'b-', 
         label='Gd-155', linewidth=2)
plt.plot(time_points / (365 * 24 * 3600), gd157_remaining, 'r--', 
         label='Gd-157', linewidth=2)
plt.xlabel('Time [years]')
plt.ylabel('Remaining Concentration [%]')
plt.title('Gadolinium Depletion During Burnup')
plt.legend()
plt.grid(True)
plt.savefig('gadolinium_depletion.png', dpi=300)
plt.show()

print(f"Gd-155 remaining after 1 year: {gd155_remaining[-1]:.1f}%")
print(f"Gd-157 remaining after 1 year: {gd157_remaining[-1]:.1f}%")
```

---

## Gadolinium Depletion

### Understanding Gadolinium Poisons

Gadolinium (Gd) is used as a burnable poison in LWR fuel to:
- Control initial reactivity
- Flatten power distribution
- Extend fuel cycle length

Gd-155 and Gd-157 have extremely high thermal capture cross-sections (~60,000 and 254,000 barns respectively) and deplete rapidly.

### Complete Gadolinium Analysis

```python
from smrforge.burnup.lwr_burnup import GadoliniumDepletion, GadoliniumPoison
from smrforge.core.reactor_core import Nuclide, NuclearDataCache
import numpy as np
import matplotlib.pyplot as plt

# Initialize
cache = NuclearDataCache()
gd_depletion = GadoliniumDepletion(cache)

# Define isotopes
gd155 = Nuclide(Z=64, A=155)
gd157 = Nuclide(Z=64, A=157)

# Multiple initial concentrations (different Gd loadings)
gd_loadings = {
    "Low (2 wt%)": 6.7e19,   # atoms/cm³
    "Medium (3 wt%)": 1e20,   # atoms/cm³
    "High (4 wt%)": 1.33e20,  # atoms/cm³
}

# Time array (3-year cycle)
time_years = np.linspace(0, 3, 100)
time_seconds = time_years * 365 * 24 * 3600

# Flux (typical PWR SMR)
flux = 1e14  # n/cm²/s

# Calculate depletion for each loading
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

for loading_name, initial_conc in gd_loadings.items():
    # Gd-155 depletion
    gd155_remaining = []
    gd157_remaining = []
    reactivity_worth = []
    
    for t in time_seconds:
        gd155_conc = gd_depletion.deplete(gd155, initial_conc, flux, t)
        gd157_conc = gd_depletion.deplete(gd157, initial_conc, flux, t)
        gd155_remaining.append(gd155_conc / initial_conc * 100)
        gd157_remaining.append(gd157_conc / initial_conc * 100)
        
        # Calculate reactivity worth
        gd_poison = GadoliniumPoison(
            nuclides=[gd155, gd157],
            initial_concentrations=np.array([initial_conc, initial_conc]),
        )
        worth = gd_depletion.calculate_reactivity_worth(gd_poison, flux, t)
        reactivity_worth.append(worth * 1000)  # Convert to m$
    
    # Plot Gd-155
    axes[0, 0].plot(time_years, gd155_remaining, label=loading_name, linewidth=2)
    
    # Plot Gd-157
    axes[0, 1].plot(time_years, gd157_remaining, label=loading_name, linewidth=2)
    
    # Plot reactivity worth
    axes[1, 0].plot(time_years, reactivity_worth, label=loading_name, linewidth=2)

# Format plots
axes[0, 0].set_xlabel('Time [years]')
axes[0, 0].set_ylabel('Gd-155 Remaining [%]')
axes[0, 0].set_title('Gd-155 Depletion')
axes[0, 0].legend()
axes[0, 0].grid(True)

axes[0, 1].set_xlabel('Time [years]')
axes[0, 1].set_ylabel('Gd-157 Remaining [%]')
axes[0, 1].set_title('Gd-157 Depletion')
axes[0, 1].legend()
axes[0, 1].grid(True)

axes[1, 0].set_xlabel('Time [years]')
axes[1, 0].set_ylabel('Reactivity Worth [m$]')
axes[1, 0].set_title('Gadolinium Reactivity Worth')
axes[1, 0].legend()
axes[1, 0].grid(True)

# Cross-section comparison
sigma_gd155 = gd_depletion.get_capture_cross_section(gd155)
sigma_gd157 = gd_depletion.get_capture_cross_section(gd157)

axes[1, 1].bar(['Gd-155', 'Gd-157'], [sigma_gd155/1000, sigma_gd157/1000], 
               color=['b', 'r'], alpha=0.7)
axes[1, 1].set_ylabel('Capture Cross-Section [kb]')
axes[1, 1].set_title('Gadolinium Capture Cross-Sections')
axes[1, 1].grid(True, axis='y')

plt.tight_layout()
plt.savefig('gadolinium_complete_analysis.png', dpi=300)
plt.show()

# Print summary
print("=" * 60)
print("Gadolinium Depletion Summary (3-year cycle)")
print("=" * 60)
for loading_name, initial_conc in gd_loadings.items():
    gd155_final = gd_depletion.deplete(gd155, initial_conc, flux, time_seconds[-1])
    gd157_final = gd_depletion.deplete(gd157, initial_conc, flux, time_seconds[-1])
    print(f"\n{loading_name}:")
    print(f"  Gd-155 remaining: {gd155_final/initial_conc*100:.1f}%")
    print(f"  Gd-157 remaining: {gd157_final/initial_conc*100:.1f}%")
```

### Temperature-Dependent Depletion

Gadolinium depletion is temperature-dependent due to cross-section changes:

```python
# Calculate depletion at different temperatures
temperatures = [300, 600, 900, 1200]  # K
time = 365 * 24 * 3600  # 1 year
flux = 1e14
initial_conc = 1e20

gd155_remaining = []
for T in temperatures:
    conc = gd_depletion.deplete(gd155, initial_conc, flux, time, temperature=T)
    gd155_remaining.append(conc / initial_conc * 100)

plt.figure(figsize=(8, 6))
plt.plot(temperatures, gd155_remaining, 'bo-', linewidth=2, markersize=8)
plt.xlabel('Temperature [K]')
plt.ylabel('Gd-155 Remaining After 1 Year [%]')
plt.title('Temperature Dependence of Gadolinium Depletion')
plt.grid(True)
plt.savefig('gd_temperature_dependence.png', dpi=300)
plt.show()
```

---

## Assembly-Wise Burnup Tracking

### Basic Assembly Tracking

Track burnup distribution across a square lattice core:

```python
from smrforge.burnup.lwr_burnup import AssemblyWiseBurnupTracker
import numpy as np
import matplotlib.pyplot as plt

# Create tracker for NuScale (37 assemblies in ~6x6 grid)
tracker = AssemblyWiseBurnupTracker(n_assemblies=37)

# Simulate burnup for each assembly
# In practice, this would come from neutronics calculations
for assembly_id in range(37):
    position = tracker.get_assembly_position(assembly_id)
    
    # Calculate burnup (simplified - in practice use neutronics solver)
    # Higher burnup in center, lower at edges
    row, col = position
    center_row, center_col = 3, 3  # Approximate center
    distance = np.sqrt((row - center_row)**2 + (col - center_col)**2)
    
    # Burnup decreases with distance from center
    burnup = 60.0 - distance * 5.0  # MWd/kgU
    burnup = max(20.0, burnup)  # Minimum 20 MWd/kgU
    
    # Update tracker
    tracker.update_assembly(
        assembly_id=assembly_id,
        position=position,
        burnup=burnup,
        enrichment=0.045,  # 4.5% enrichment
        peak_power=40.0,  # W/cm³
    )

# Get burnup distribution
distribution = tracker.get_burnup_distribution()

# Visualize
plt.figure(figsize=(10, 8))
im = plt.imshow(distribution, cmap='viridis', origin='lower')
plt.colorbar(im, label='Burnup [MWd/kgU]')
plt.xlabel('Assembly Column')
plt.ylabel('Assembly Row')
plt.title('Assembly-Wise Burnup Distribution (NuScale SMR)')

# Add text annotations
for assembly_id in range(37):
    position = tracker.get_assembly_position(assembly_id)
    row, col = position
    if 0 <= row < distribution.shape[0] and 0 <= col < distribution.shape[1]:
        plt.text(col, row, f'{distribution[row, col]:.0f}', 
                ha='center', va='center', color='white', fontweight='bold')

plt.savefig('assembly_burnup_distribution.png', dpi=300)
plt.show()

# Print statistics
print(f"Average burnup: {tracker.get_average_burnup():.2f} MWd/kgU")
print(f"Peak burnup: {tracker.get_peak_burnup():.2f} MWd/kgU")
print(f"Burnup spread: {tracker.get_peak_burnup() - np.min(distribution[distribution > 0]):.2f} MWd/kgU")
```

### Time-Dependent Assembly Tracking

Track assembly burnup evolution over multiple cycles:

```python
from smrforge.burnup.lwr_burnup import AssemblyWiseBurnupTracker
import numpy as np
import matplotlib.pyplot as plt

# Create tracker
tracker = AssemblyWiseBurnupTracker(n_assemblies=37)

# Time points (3-year cycle, 6-month intervals)
time_points = np.arange(0, 3.5, 0.5)  # years
burnup_history = []

for t in time_points:
    # Simulate burnup increment (simplified)
    burnup_increment = 10.0 * 0.5  # 10 MWd/kgU per 6 months
    
    # Update each assembly
    for assembly_id in range(37):
        position = tracker.get_assembly_position(assembly_id)
        
        # Get current burnup (or initialize)
        if assembly_id in tracker.assemblies:
            current_burnup = tracker.assemblies[assembly_id].burnup
        else:
            current_burnup = 0.0
        
        # Add increment (with spatial variation)
        row, col = position
        center_row, center_col = 3, 3
        distance = np.sqrt((row - center_row)**2 + (col - center_col)**2)
        spatial_factor = 1.0 - distance * 0.1  # Center assemblies burn faster
        spatial_factor = max(0.5, spatial_factor)
        
        new_burnup = current_burnup + burnup_increment * spatial_factor
        
        tracker.update_assembly(
            assembly_id=assembly_id,
            position=position,
            burnup=new_burnup,
            enrichment=0.045,
        )
    
    # Record distribution
    distribution = tracker.get_burnup_distribution()
    burnup_history.append(distribution.copy())

# Create animation-like visualization
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for i, (t, dist) in enumerate(zip(time_points[:6], burnup_history[:6])):
    im = axes[i].imshow(dist, cmap='viridis', origin='lower', vmin=0, vmax=60)
    axes[i].set_title(f'Year {t:.1f}')
    axes[i].set_xlabel('Column')
    axes[i].set_ylabel('Row')
    plt.colorbar(im, ax=axes[i], label='Burnup [MWd/kgU]')

plt.tight_layout()
plt.savefig('assembly_burnup_evolution.png', dpi=300)
plt.show()

# Plot average and peak burnup over time
avg_burnup = [np.mean(d[d > 0]) for d in burnup_history]
peak_burnup = [np.max(d) for d in burnup_history]

plt.figure(figsize=(10, 6))
plt.plot(time_points, avg_burnup, 'b-o', label='Average', linewidth=2, markersize=6)
plt.plot(time_points, peak_burnup, 'r-s', label='Peak', linewidth=2, markersize=6)
plt.xlabel('Time [years]')
plt.ylabel('Burnup [MWd/kgU]')
plt.title('Assembly Burnup Evolution (3-Year Cycle)')
plt.legend()
plt.grid(True)
plt.savefig('assembly_burnup_timeseries.png', dpi=300)
plt.show()
```

---

## Rod-Wise Burnup Tracking

### Basic Rod Tracking

Track burnup within a single fuel assembly:

```python
from smrforge.burnup.lwr_burnup import RodWiseBurnupTracker
import numpy as np
import matplotlib.pyplot as plt

# Create tracker for 17x17 assembly (NuScale)
tracker = RodWiseBurnupTracker(assembly_size=(17, 17))

# Control rod positions (typical pattern: guide tubes)
control_rod_positions = [
    (8, 8),   # Center
    (2, 8),   # North
    (14, 8),  # South
    (8, 2),   # West
    (8, 14),  # East
]

# Simulate burnup for each rod
for rod_id in range(17 * 17):
    position = tracker.get_rod_position(rod_id)
    row, col = position
    
    # Calculate shadowing factor
    shadowing = tracker.calculate_shadowing_factor(
        position, control_rod_positions, pitch=1.26  # cm
    )
    
    # Base burnup (higher in center)
    center_row, center_col = 8, 8
    distance_from_center = np.sqrt((row - center_row)**2 + (col - center_col)**2)
    base_burnup = 50.0 - distance_from_center * 2.0
    
    # Apply shadowing (rods near control rods have lower burnup)
    burnup = base_burnup * shadowing
    burnup = max(20.0, burnup)
    
    # Enrichment (can vary by rod)
    enrichment = 0.045  # 4.5% (can be higher in some rods)
    
    # Gadolinium content (typically in some rods)
    if distance_from_center < 3:
        gadolinium = 1e20  # atoms/cm³
    else:
        gadolinium = 0.0
    
    # Update tracker
    tracker.update_rod(
        rod_id=rod_id,
        position=position,
        burnup=burnup,
        enrichment=enrichment,
        gadolinium_content=gadolinium,
        shadowing_factor=shadowing,
    )

# Get burnup distribution
distribution = tracker.get_burnup_distribution()

# Visualize
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Burnup distribution
im1 = axes[0].imshow(distribution, cmap='viridis', origin='lower')
axes[0].set_title('Rod-Wise Burnup Distribution [MWd/kgU]')
axes[0].set_xlabel('Rod Column')
axes[0].set_ylabel('Rod Row')
plt.colorbar(im1, ax=axes[0])

# Mark control rod positions
for cr_pos in control_rod_positions:
    axes[0].plot(cr_pos[1], cr_pos[0], 'rx', markersize=15, markeredgewidth=3)

# Shadowing factor distribution
shadowing_dist = np.zeros((17, 17))
for rod_id, rod in tracker.rods.items():
    row, col = rod.position
    shadowing_dist[row, col] = rod.shadowing_factor

im2 = axes[1].imshow(shadowing_dist, cmap='RdYlGn', origin='lower', vmin=0, vmax=1)
axes[1].set_title('Control Rod Shadowing Factor')
axes[1].set_xlabel('Rod Column')
axes[1].set_ylabel('Rod Row')
plt.colorbar(im2, ax=axes[1], label='Shadowing Factor')

# Mark control rod positions
for cr_pos in control_rod_positions:
    axes[1].plot(cr_pos[1], cr_pos[0], 'kx', markersize=15, markeredgewidth=3)

plt.tight_layout()
plt.savefig('rod_burnup_distribution.png', dpi=300)
plt.show()

print(f"Average rod burnup: {tracker.get_average_burnup():.2f} MWd/kgU")
print(f"Peak rod burnup: {tracker.get_peak_burnup():.2f} MWd/kgU")
print(f"Average shadowing factor: {np.mean(shadowing_dist):.3f}")
print(f"Minimum shadowing factor: {np.min(shadowing_dist):.3f}")
```

### Combined Gadolinium and Shadowing Effects

```python
from smrforge.burnup.lwr_burnup import (
    RodWiseBurnupTracker,
    GadoliniumDepletion,
)
from smrforge.core.reactor_core import Nuclide, NuclearDataCache
import numpy as np
import matplotlib.pyplot as plt

# Initialize
cache = NuclearDataCache()
gd_depletion = GadoliniumDepletion(cache)
tracker = RodWiseBurnupTracker(assembly_size=(17, 17))

gd155 = Nuclide(Z=64, A=155)
gd157 = Nuclide(Z=64, A=157)

# Control rod positions
control_rod_positions = [(8, 8), (2, 8), (14, 8), (8, 2), (8, 14)]

# Time evolution (1 year)
time_points = np.linspace(0, 365 * 24 * 3600, 12)  # Monthly
flux = 1e14

# Initial gadolinium loading
initial_gd = 1e20  # atoms/cm³

# Track burnup and gadolinium depletion
for t_idx, t in enumerate(time_points):
    for rod_id in range(17 * 17):
        position = tracker.get_rod_position(rod_id)
        row, col = position
        
        # Calculate shadowing
        shadowing = tracker.calculate_shadowing_factor(
            position, control_rod_positions, pitch=1.26
        )
        
        # Effective flux (reduced by shadowing)
        effective_flux = flux * shadowing
        
        # Gadolinium depletion
        if t_idx == 0:
            gd_conc = initial_gd
        else:
            # Get previous concentration
            prev_rod = tracker.rods.get(rod_id)
            if prev_rod:
                gd_conc = prev_rod.gadolinium_content
            else:
                gd_conc = initial_gd
        
        # Deplete gadolinium
        gd_remaining = gd_depletion.deplete(gd155, gd_conc, effective_flux, 
                                            time_points[1] - time_points[0])
        
        # Burnup (increases with time, reduced by shadowing and gadolinium)
        base_burnup = (t / (365 * 24 * 3600)) * 50.0  # 50 MWd/kgU per year
        burnup = base_burnup * shadowing * (1.0 - gd_remaining / initial_gd * 0.2)
        
        # Update tracker
        tracker.update_rod(
            rod_id=rod_id,
            position=position,
            burnup=burnup,
            enrichment=0.045,
            gadolinium_content=gd_remaining,
            shadowing_factor=shadowing,
        )
    
    # Visualize at key time points
    if t_idx in [0, 3, 6, 11]:  # 0, 3, 6, 12 months
        distribution = tracker.get_burnup_distribution()
        
        plt.figure(figsize=(10, 8))
        im = plt.imshow(distribution, cmap='viridis', origin='lower')
        plt.colorbar(im, label='Burnup [MWd/kgU]')
        plt.title(f'Rod Burnup Distribution at {t_idx + 1} Months')
        plt.xlabel('Rod Column')
        plt.ylabel('Rod Row')
        
        # Mark control rods
        for cr_pos in control_rod_positions:
            plt.plot(cr_pos[1], cr_pos[0], 'rx', markersize=15, markeredgewidth=3)
        
        plt.savefig(f'rod_burnup_month_{t_idx + 1}.png', dpi=300)
        plt.close()

print("Rod-wise burnup tracking with gadolinium depletion complete!")
print(f"Final average burnup: {tracker.get_average_burnup():.2f} MWd/kgU")
```

---

## Complete Workflow

### Full LWR SMR Fuel Cycle Analysis

```python
"""
Complete LWR SMR Fuel Cycle Analysis
Combines gadolinium depletion, assembly tracking, and rod tracking
"""

from smrforge.burnup.lwr_burnup import (
    GadoliniumDepletion,
    GadoliniumPoison,
    AssemblyWiseBurnupTracker,
    RodWiseBurnupTracker,
)
from smrforge.core.reactor_core import Nuclide, NuclearDataCache
import numpy as np
import matplotlib.pyplot as plt

# Initialize
cache = NuclearDataCache()
gd_depletion = GadoliniumDepletion(cache)

# Create trackers
assembly_tracker = AssemblyWiseBurnupTracker(n_assemblies=37)
rod_tracker = RodWiseBurnupTracker(assembly_size=(17, 17))

# Gadolinium configuration
gd155 = Nuclide(Z=64, A=155)
gd157 = Nuclide(Z=64, A=157)
initial_gd = 1e20

gd_poison = GadoliniumPoison(
    nuclides=[gd155, gd157],
    initial_concentrations=np.array([initial_gd, initial_gd]),
)

# Control rod positions
control_rod_positions = [(8, 8), (2, 8), (14, 8), (8, 2), (8, 14)]

# Time evolution (3-year cycle, monthly steps)
time_points = np.linspace(0, 3 * 365 * 24 * 3600, 36)  # 36 months
flux = 1e14

# Storage for results
assembly_burnup_history = []
rod_burnup_history = []
gd_worth_history = []

for t_idx, t in enumerate(time_points):
    # 1. Update gadolinium depletion
    gd_worth = gd_depletion.calculate_reactivity_worth(gd_poison, flux, t)
    gd_worth_history.append(gd_worth * 1000)  # m$
    
    # 2. Update assembly burnup
    for assembly_id in range(37):
        position = assembly_tracker.get_assembly_position(assembly_id)
        
        # Get current burnup
        if assembly_id in assembly_tracker.assemblies:
            current_burnup = assembly_tracker.assemblies[assembly_id].burnup
        else:
            current_burnup = 0.0
        
        # Burnup increment (spatial variation)
        row, col = position
        center_row, center_col = 3, 3
        distance = np.sqrt((row - center_row)**2 + (col - center_col)**2)
        spatial_factor = 1.0 - distance * 0.1
        spatial_factor = max(0.5, spatial_factor)
        
        burnup_increment = (time_points[1] - time_points[0]) / (365 * 24 * 3600) * 50.0
        new_burnup = current_burnup + burnup_increment * spatial_factor
        
        assembly_tracker.update_assembly(
            assembly_id=assembly_id,
            position=position,
            burnup=new_burnup,
            enrichment=0.045,
        )
    
    # 3. Update rod burnup (for center assembly)
    center_assembly_rod_id = 8 * 17 + 8  # Center rod of center assembly
    for rod_id in range(17 * 17):
        position = rod_tracker.get_rod_position(rod_id)
        
        shadowing = rod_tracker.calculate_shadowing_factor(
            position, control_rod_positions, pitch=1.26
        )
        
        effective_flux = flux * shadowing
        
        # Gadolinium depletion
        if t_idx == 0:
            gd_conc = initial_gd
        else:
            prev_rod = rod_tracker.rods.get(rod_id)
            gd_conc = prev_rod.gadolinium_content if prev_rod else initial_gd
        
        gd_remaining = gd_depletion.deplete(gd155, gd_conc, effective_flux,
                                            time_points[1] - time_points[0])
        
        # Burnup
        if t_idx == 0:
            current_rod_burnup = 0.0
        else:
            prev_rod = rod_tracker.rods.get(rod_id)
            current_rod_burnup = prev_rod.burnup if prev_rod else 0.0
        
        burnup_increment = (time_points[1] - time_points[0]) / (365 * 24 * 3600) * 50.0
        new_rod_burnup = current_rod_burnup + burnup_increment * shadowing
        
        rod_tracker.update_rod(
            rod_id=rod_id,
            position=position,
            burnup=new_rod_burnup,
            enrichment=0.045,
            gadolinium_content=gd_remaining,
            shadowing_factor=shadowing,
        )
    
    # Record distributions
    assembly_burnup_history.append(assembly_tracker.get_burnup_distribution().copy())
    rod_burnup_history.append(rod_tracker.get_burnup_distribution().copy())

# Create comprehensive visualization
fig = plt.figure(figsize=(16, 12))

# Assembly burnup at end of cycle
ax1 = plt.subplot(2, 3, 1)
im1 = ax1.imshow(assembly_burnup_history[-1], cmap='viridis', origin='lower')
plt.colorbar(im1, ax=ax1, label='Burnup [MWd/kgU]')
ax1.set_title('Assembly Burnup (End of Cycle)')
ax1.set_xlabel('Column')
ax1.set_ylabel('Row')

# Rod burnup at end of cycle
ax2 = plt.subplot(2, 3, 2)
im2 = ax2.imshow(rod_burnup_history[-1], cmap='viridis', origin='lower')
plt.colorbar(im2, ax=ax2, label='Burnup [MWd/kgU]')
ax2.set_title('Rod Burnup (End of Cycle)')
ax2.set_xlabel('Column')
ax2.set_ylabel('Row')

# Average burnup evolution
ax3 = plt.subplot(2, 3, 3)
time_years = time_points / (365 * 24 * 3600)
avg_assembly = [np.mean(d[d > 0]) for d in assembly_burnup_history]
avg_rod = [np.mean(d[d > 0]) for d in rod_burnup_history]
ax3.plot(time_years, avg_assembly, 'b-o', label='Assembly Average', linewidth=2)
ax3.plot(time_years, avg_rod, 'r-s', label='Rod Average', linewidth=2)
ax3.set_xlabel('Time [years]')
ax3.set_ylabel('Burnup [MWd/kgU]')
ax3.set_title('Average Burnup Evolution')
ax3.legend()
ax3.grid(True)

# Gadolinium reactivity worth
ax4 = plt.subplot(2, 3, 4)
ax4.plot(time_years, gd_worth_history, 'g-', linewidth=2)
ax4.set_xlabel('Time [years]')
ax4.set_ylabel('Reactivity Worth [m$]')
ax4.set_title('Gadolinium Reactivity Worth')
ax4.grid(True)

# Burnup spread (peak - minimum)
ax5 = plt.subplot(2, 3, 5)
assembly_spread = [np.max(d) - np.min(d[d > 0]) for d in assembly_burnup_history]
rod_spread = [np.max(d) - np.min(d[d > 0]) for d in rod_burnup_history]
ax5.plot(time_years, assembly_spread, 'b-o', label='Assembly Spread', linewidth=2)
ax5.plot(time_years, rod_spread, 'r-s', label='Rod Spread', linewidth=2)
ax5.set_xlabel('Time [years]')
ax5.set_ylabel('Burnup Spread [MWd/kgU]')
ax5.set_title('Burnup Distribution Spread')
ax5.legend()
ax5.grid(True)

# Summary statistics
ax6 = plt.subplot(2, 3, 6)
ax6.axis('off')
summary_text = f"""
Fuel Cycle Analysis Summary
(3-Year Cycle)

Assembly Statistics:
  Initial avg: {avg_assembly[0]:.1f} MWd/kgU
  Final avg: {avg_assembly[-1]:.1f} MWd/kgU
  Peak: {np.max(assembly_burnup_history[-1]):.1f} MWd/kgU
  Spread: {assembly_spread[-1]:.1f} MWd/kgU

Rod Statistics:
  Initial avg: {avg_rod[0]:.1f} MWd/kgU
  Final avg: {avg_rod[-1]:.1f} MWd/kgU
  Peak: {np.max(rod_burnup_history[-1]):.1f} MWd/kgU
  Spread: {rod_spread[-1]:.1f} MWd/kgU

Gadolinium:
  Initial worth: {gd_worth_history[0]:.1f} m$
  Final worth: {gd_worth_history[-1]:.1f} m$
  Depletion: {(1 - gd_worth_history[-1]/gd_worth_history[0])*100:.1f}%
"""
ax6.text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
         verticalalignment='center')

plt.tight_layout()
plt.savefig('complete_fuel_cycle_analysis.png', dpi=300)
plt.show()

print("=" * 60)
print("Complete LWR SMR Fuel Cycle Analysis")
print("=" * 60)
print(summary_text)
```

---

## Advanced Techniques

### Coupling with Neutronics Solver

For production analysis, couple burnup tracking with neutronics:

```python
from smrforge.burnup.solver import BurnupSolver, BurnupOptions
from smrforge.burnup.lwr_burnup import AssemblyWiseBurnupTracker
from smrforge.neutronics.solver import MultiGroupDiffusion
# ... (setup neutronics solver)

# Create burnup solver
burnup_options = BurnupOptions(
    time_steps=[0, 365, 730, 1095],  # 0, 1, 2, 3 years
    power_density=1e6,  # W/cm³
    initial_enrichment=0.045,
)

burnup_solver = BurnupSolver(neutronics_solver, burnup_options)

# Solve burnup
inventory = burnup_solver.solve()

# Extract assembly-wise burnup from neutronics results
# (This would use flux distribution from neutronics solver)
assembly_tracker = AssemblyWiseBurnupTracker(n_assemblies=37)

# Update assemblies based on neutronics results
for assembly_id in range(37):
    # Get flux/power from neutronics solver for this assembly
    # Calculate burnup from power history
    # Update tracker
    pass
```

### Optimization: Finding Optimal Gadolinium Loading

```python
from scipy.optimize import minimize_scalar

def objective_function(gd_loading):
    """Minimize peak-to-average power ratio with gadolinium loading"""
    # Run burnup calculation with given loading
    # Calculate peak-to-average power ratio
    # Return ratio (to minimize)
    pass

# Find optimal loading
result = minimize_scalar(objective_function, bounds=(1e19, 2e20), method='bounded')
optimal_loading = result.x

print(f"Optimal gadolinium loading: {optimal_loading:.2e} atoms/cm³")
```

---

## Best Practices

1. **Use appropriate time steps** - Monthly steps for long cycles, weekly for detailed analysis
2. **Account for spatial variation** - Flux gradients affect burnup distribution
3. **Consider control rod shadowing** - Important for accurate rod-level tracking
4. **Track gadolinium depletion** - Critical for reactivity control
5. **Validate with neutronics** - Couple with neutronics solver for production analysis
6. **Visualize distributions** - Use plots to understand burnup patterns

---

## References

- IAEA-TECDOC-1349: "Use of Burnable Poisons in Nuclear Reactors"
- NUREG-0800: Standard Review Plan for LWRs
- ANSI/ANS-5.1-2014: Decay Heat Power in Light Water Reactors

---

**See Also:**
- [LWR SMR Transient Analysis Guide](lwr-smr-transient-analysis.md) - For safety analysis
- [Data Downloader Guide](data-downloader-guide.md) - For setting up ENDF data
- [Usage Guide](usage.md) - For general SMRForge usage
