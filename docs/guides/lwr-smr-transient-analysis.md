# LWR SMR Transient Analysis Guide

**Last Updated:** January 2026

Comprehensive guide for performing transient safety analysis on Light Water Reactor (LWR) Small Modular Reactors (SMRs) using SMRForge.

---

## Overview

SMRForge provides comprehensive transient analysis capabilities for LWR SMRs, including:

- ✅ **PWR SMR transients** - Steam line breaks, feedwater line breaks, pressurizer transients, LOCA scenarios
- ✅ **BWR SMR transients** - Recirculation pump trips, steam separator issues, BWR-specific LOCA
- ✅ **Integral SMR transients** - In-vessel steam generator tube rupture, integrated primary system transients
- ✅ **Point kinetics solver** - Temperature feedback, delayed neutrons, reactivity insertion
- ✅ **Decay heat calculations** - ANS standard decay heat models

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [PWR SMR Transients](#pwr-smr-transients)
3. [BWR SMR Transients](#bwr-smr-transients)
4. [Integral SMR Transients](#integral-smr-transients)
5. [Advanced Usage](#advanced-usage)
6. [Complete Examples](#complete-examples)

---

## Quick Start

### Basic PWR SMR Transient

```python
from smrforge.safety.transients import (
    TransientType,
    TransientConditions,
    SteamLineBreakTransient,
)
from smrforge.geometry.lwr_smr import PWRSMRCore

# Create PWR SMR core geometry
core = PWRSMRCore(
    name="NuScale-SMR",
    n_assemblies=37,
    assembly_pitch=21.5,  # cm
    active_height=200.0,  # cm
)

# Create reactor specification (simplified)
class ReactorSpec:
    def __init__(self):
        self.name = "NuScale-SMR"
        self.power_thermal = 77e6  # 77 MWth

reactor_spec = ReactorSpec()

# Initialize transient analyzer
slb = SteamLineBreakTransient(reactor_spec, core)

# Define transient conditions
conditions = TransientConditions(
    initial_power=77e6,  # 77 MWth
    initial_temperature=600.0,  # K
    initial_flow_rate=100.0,  # kg/s
    initial_pressure=15.5e6,  # 15.5 MPa
    transient_type=TransientType.STEAM_LINE_BREAK,
    trigger_time=0.0,
    t_end=3600.0,  # 1 hour simulation
    scram_available=True,
    scram_delay=1.0,  # 1 second scram delay
)

# Run simulation
result = slb.simulate(
    conditions,
    break_area=0.01,  # 0.01 m² break
    break_location="main_steam_line",
)

# Analyze results
import matplotlib.pyplot as plt
import numpy as np

plt.figure(figsize=(12, 8))

# Plot power
plt.subplot(2, 2, 1)
plt.plot(result['time'], result['power'] / 1e6, 'b-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Power [MWth]')
plt.title('Reactor Power')
plt.grid(True)

# Plot pressure
plt.subplot(2, 2, 2)
plt.plot(result['time'], result['pressure'] / 1e6, 'r-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Pressure [MPa]')
plt.title('Primary System Pressure')
plt.grid(True)

# Plot temperature
plt.subplot(2, 2, 3)
plt.plot(result['time'], result['temperature'], 'g-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Temperature [K]')
plt.title('Core Temperature')
plt.grid(True)

# Plot steam flow
plt.subplot(2, 2, 4)
plt.plot(result['time'], result['steam_flow'], 'm-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Steam Flow [kg/s]')
plt.title('Steam Flow Through Break')
plt.grid(True)

plt.tight_layout()
plt.savefig('steam_line_break_transient.png', dpi=300)
plt.show()

print(f"Peak power: {np.max(result['power'])/1e6:.2f} MWth")
print(f"Final power: {result['power'][-1]/1e6:.2f} MWth")
print(f"Minimum pressure: {np.min(result['pressure'])/1e6:.2f} MPa")
```

---

## PWR SMR Transients

### 1. Steam Line Break (SLB)

Steam line breaks cause rapid depressurization of the secondary system and increased heat removal from the primary system.

```python
from smrforge.safety.transients import (
    TransientType,
    TransientConditions,
    SteamLineBreakTransient,
)

# Create transient analyzer
slb = SteamLineBreakTransient(reactor_spec, core)

# Small break (0.01 m²)
conditions_small = TransientConditions(
    initial_power=77e6,
    initial_temperature=600.0,
    initial_flow_rate=100.0,
    initial_pressure=15.5e6,
    transient_type=TransientType.STEAM_LINE_BREAK,
    trigger_time=0.0,
    t_end=3600.0,
    scram_available=True,
)

result_small = slb.simulate(conditions_small, break_area=0.01)

# Large break (0.1 m²)
conditions_large = TransientConditions(
    initial_power=77e6,
    initial_temperature=600.0,
    initial_flow_rate=100.0,
    initial_pressure=15.5e6,
    transient_type=TransientType.STEAM_LINE_BREAK,
    trigger_time=0.0,
    t_end=3600.0,
    scram_available=True,
)

result_large = slb.simulate(conditions_large, break_area=0.1)

# Compare results
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.plot(result_small['time'], result_small['pressure'] / 1e6, 'b-', 
         label='Small Break (0.01 m²)', linewidth=2)
plt.plot(result_large['time'], result_large['pressure'] / 1e6, 'r--', 
         label='Large Break (0.1 m²)', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Pressure [MPa]')
plt.title('Steam Line Break: Pressure Response')
plt.legend()
plt.grid(True)
plt.savefig('slb_comparison.png', dpi=300)
plt.show()
```

### 2. Feedwater Line Break

Feedwater line breaks cause loss of feedwater flow and reduced heat removal.

```python
from smrforge.safety.transients import FeedwaterLineBreakTransient

# Create transient analyzer
fwlb = FeedwaterLineBreakTransient(reactor_spec, core)

# Define conditions
conditions = TransientConditions(
    initial_power=77e6,
    initial_temperature=600.0,
    initial_flow_rate=100.0,
    initial_pressure=15.5e6,
    transient_type=TransientType.FEEDWATER_LINE_BREAK,
    trigger_time=0.0,
    t_end=3600.0,
    scram_available=True,
    scram_delay=2.0,  # 2 second scram delay
)

# Run simulation
result = fwlb.simulate(conditions, break_area=0.02)

# Analyze feedwater flow loss
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.plot(result['time'], result['feedwater_flow'], 'b-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Feedwater Flow [kg/s]')
plt.title('Feedwater Flow')
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(result['time'], result['temperature'], 'r-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Temperature [K]')
plt.title('Core Temperature Response')
plt.grid(True)

plt.tight_layout()
plt.savefig('feedwater_line_break.png', dpi=300)
plt.show()

print(f"Feedwater flow loss rate: {(conditions.initial_flow_rate - result['feedwater_flow'][-1]):.2f} kg/s")
print(f"Temperature increase: {(result['temperature'][-1] - conditions.initial_temperature):.1f} K")
```

### 3. Pressurizer Transient

Pressurizer transients model pressure and temperature control in PWR systems.

```python
from smrforge.safety.transients import PressurizerTransient

# Create transient analyzer
press = PressurizerTransient(reactor_spec, core)

# Define conditions with pressure setpoint
conditions = TransientConditions(
    initial_power=77e6,
    initial_temperature=600.0,
    initial_pressure=15.5e6,
    transient_type=TransientType.PRESSURIZER_TRANSIENT,
    trigger_time=0.0,
    t_end=1800.0,  # 30 minutes
)

# Run simulation with pressure control
result = press.simulate(
    conditions,
    pressure_setpoint=15.5e6,  # Target pressure
    pressure_change_rate=1e5,  # 0.1 MPa/s max change rate
)

# Visualize pressurizer response
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.plot(result['time'], result['pressure'] / 1e6, 'b-', linewidth=2, label='Pressure')
plt.axhline(y=15.5, color='r', linestyle='--', label='Setpoint')
plt.xlabel('Time [s]')
plt.ylabel('Pressure [MPa]')
plt.title('Pressurizer Pressure Control')
plt.legend()
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(result['time'], result['spray_flow'], 'g-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Spray Flow [kg/s]')
plt.title('Pressurizer Spray Flow')
plt.grid(True)

plt.tight_layout()
plt.savefig('pressurizer_transient.png', dpi=300)
plt.show()
```

### 4. Loss of Coolant Accident (LOCA)

LOCA scenarios model both small break (SB-LOCA) and large break (LB-LOCA) accidents.

```python
from smrforge.safety.transients import LOCATransientLWR

# Create transient analyzer
loca = LOCATransientLWR(reactor_spec, core)

# Small Break LOCA (SB-LOCA)
conditions_sb = TransientConditions(
    initial_power=77e6,
    initial_temperature=600.0,
    initial_flow_rate=100.0,
    initial_pressure=15.5e6,
    transient_type=TransientType.SB_LOCA,
    trigger_time=0.0,
    t_end=7200.0,  # 2 hours
    scram_available=True,
    scram_delay=1.0,
)

result_sb = loca.simulate(conditions_sb, break_area=0.05, break_type="small")

# Large Break LOCA (LB-LOCA)
conditions_lb = TransientConditions(
    initial_power=77e6,
    initial_temperature=600.0,
    initial_flow_rate=100.0,
    initial_pressure=15.5e6,
    transient_type=TransientType.LB_LOCA,
    trigger_time=0.0,
    t_end=3600.0,  # 1 hour
    scram_available=True,
    scram_delay=1.0,
)

result_lb = loca.simulate(conditions_lb, break_area=0.5, break_type="large")

# Compare SB-LOCA vs LB-LOCA
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Pressure comparison
axes[0, 0].plot(result_sb['time'], result_sb['pressure'] / 1e6, 'b-', 
                label='SB-LOCA', linewidth=2)
axes[0, 0].plot(result_lb['time'], result_lb['pressure'] / 1e6, 'r--', 
                label='LB-LOCA', linewidth=2)
axes[0, 0].set_xlabel('Time [s]')
axes[0, 0].set_ylabel('Pressure [MPa]')
axes[0, 0].set_title('Primary System Pressure')
axes[0, 0].legend()
axes[0, 0].grid(True)

# Temperature comparison
axes[0, 1].plot(result_sb['time'], result_sb['temperature'], 'b-', 
                label='SB-LOCA', linewidth=2)
axes[0, 1].plot(result_lb['time'], result_lb['temperature'], 'r--', 
                label='LB-LOCA', linewidth=2)
axes[0, 1].set_xlabel('Time [s]')
axes[0, 1].set_ylabel('Temperature [K]')
axes[0, 1].set_title('Core Temperature')
axes[0, 1].legend()
axes[0, 1].grid(True)

# Coolant flow comparison
axes[1, 0].plot(result_sb['time'], result_sb['coolant_flow'], 'b-', 
                label='SB-LOCA', linewidth=2)
axes[1, 0].plot(result_lb['time'], result_lb['coolant_flow'], 'r--', 
                label='LB-LOCA', linewidth=2)
axes[1, 0].set_xlabel('Time [s]')
axes[1, 0].set_ylabel('Coolant Flow [kg/s]')
axes[1, 0].set_title('Coolant Flow Rate')
axes[1, 0].legend()
axes[1, 0].grid(True)

# Power comparison
axes[1, 1].plot(result_sb['time'], result_sb['power'] / 1e6, 'b-', 
                label='SB-LOCA', linewidth=2)
axes[1, 1].plot(result_lb['time'], result_lb['power'] / 1e6, 'r--', 
                label='LB-LOCA', linewidth=2)
axes[1, 1].set_xlabel('Time [s]')
axes[1, 1].set_ylabel('Power [MWth]')
axes[1, 1].set_title('Reactor Power')
axes[1, 1].legend()
axes[1, 1].grid(True)

plt.tight_layout()
plt.savefig('loca_comparison.png', dpi=300)
plt.show()

print("SB-LOCA Analysis:")
print(f"  Minimum pressure: {np.min(result_sb['pressure'])/1e6:.2f} MPa")
print(f"  Peak temperature: {np.max(result_sb['temperature']):.1f} K")
print(f"  Final coolant flow: {result_sb['coolant_flow'][-1]:.2f} kg/s")

print("\nLB-LOCA Analysis:")
print(f"  Minimum pressure: {np.min(result_lb['pressure'])/1e6:.2f} MPa")
print(f"  Peak temperature: {np.max(result_lb['temperature']):.1f} K")
print(f"  Final coolant flow: {result_lb['coolant_flow'][-1]:.2f} kg/s")
```

---

## BWR SMR Transients

### 1. Recirculation Pump Trip

Recirculation pump trips cause loss of forced circulation and increased void fraction.

```python
from smrforge.safety.transients import RecirculationPumpTripTransient

# Create transient analyzer
rpt = RecirculationPumpTripTransient(reactor_spec, core)

# Define conditions for BWR SMR
conditions = TransientConditions(
    initial_power=160e6,  # 160 MWth (typical BWR SMR)
    initial_temperature=550.0,  # K (lower than PWR)
    initial_flow_rate=200.0,  # kg/s
    initial_pressure=7.0e6,  # 7 MPa (BWR pressure)
    transient_type=TransientType.RECIRCULATION_PUMP_TRIP,
    trigger_time=0.0,
    t_end=3600.0,
    scram_available=True,
)

# Run simulation
result = rpt.simulate(conditions)

# Analyze void fraction response
import matplotlib.pyplot as plt

plt.figure(figsize=(14, 8))

plt.subplot(2, 2, 1)
plt.plot(result['time'], result['power'] / 1e6, 'b-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Power [MWth]')
plt.title('Reactor Power')
plt.grid(True)

plt.subplot(2, 2, 2)
plt.plot(result['time'], result['flow_rate'], 'r-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Flow Rate [kg/s]')
plt.title('Recirculation Flow Rate')
plt.grid(True)

plt.subplot(2, 2, 3)
plt.plot(result['time'], result['void_fraction'] * 100, 'g-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Void Fraction [%]')
plt.title('Void Fraction')
plt.grid(True)

plt.subplot(2, 2, 4)
plt.plot(result['time'], result['pressure'] / 1e6, 'm-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Pressure [MPa]')
plt.title('System Pressure')
plt.grid(True)

plt.tight_layout()
plt.savefig('recirculation_pump_trip.png', dpi=300)
plt.show()

print(f"Initial void fraction: {result['void_fraction'][0]*100:.1f}%")
print(f"Peak void fraction: {np.max(result['void_fraction'])*100:.1f}%")
print(f"Final void fraction: {result['void_fraction'][-1]*100:.1f}%")
print(f"Power reduction: {(1 - result['power'][-1]/conditions.initial_power)*100:.1f}%")
```

### 2. Steam Separator Issue

Steam separator malfunctions affect steam quality and moisture carryover.

```python
from smrforge.safety.transients import SteamSeparatorIssueTransient

# Create transient analyzer
ssi = SteamSeparatorIssueTransient(reactor_spec, core)

# Define conditions
conditions = TransientConditions(
    initial_power=160e6,
    initial_temperature=550.0,
    initial_pressure=7.0e6,
    transient_type=TransientType.STEAM_SEPARATOR_ISSUE,
    trigger_time=0.0,
    t_end=1800.0,  # 30 minutes
)

# Run simulation with reduced separator efficiency
result = ssi.simulate(conditions, separator_efficiency=0.5)  # 50% efficiency

# Analyze steam quality
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.plot(result['time'], result['steam_quality'] * 100, 'b-', linewidth=2)
plt.axhline(y=99.0, color='r', linestyle='--', label='Normal (99%)')
plt.xlabel('Time [s]')
plt.ylabel('Steam Quality [%]')
plt.title('Steam Quality')
plt.legend()
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(result['time'], result['moisture_carryover'] * 100, 'r-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Moisture Carryover [%]')
plt.title('Moisture Carryover')
plt.grid(True)

plt.tight_layout()
plt.savefig('steam_separator_issue.png', dpi=300)
plt.show()

print(f"Initial steam quality: {result['steam_quality'][0]*100:.2f}%")
print(f"Final steam quality: {result['steam_quality'][-1]*100:.2f}%")
print(f"Peak moisture carryover: {np.max(result['moisture_carryover'])*100:.2f}%")
```

---

## Integral SMR Transients

### Steam Generator Tube Rupture

In-vessel steam generator tube rupture causes primary-to-secondary leakage.

```python
from smrforge.safety.transients import SteamGeneratorTubeRuptureTransient

# Create transient analyzer
sgt = SteamGeneratorTubeRuptureTransient(reactor_spec, core)

# Define conditions for integral SMR
conditions = TransientConditions(
    initial_power=100e6,  # 100 MWth
    initial_temperature=600.0,
    initial_pressure=15.5e6,
    transient_type=TransientType.STEAM_GENERATOR_TUBE_RUPTURE,
    trigger_time=0.0,
    t_end=3600.0,
    scram_available=True,
    scram_delay=1.0,
)

# Run simulation with single tube rupture
result = sgt.simulate(
    conditions,
    tube_rupture_count=1,
    rupture_area_per_tube=1e-4,  # 0.0001 m² per tube
)

# Analyze leakage and pressure response
import matplotlib.pyplot as plt

plt.figure(figsize=(14, 8))

plt.subplot(2, 2, 1)
plt.plot(result['time'], result['power'] / 1e6, 'b-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Power [MWth]')
plt.title('Reactor Power')
plt.grid(True)

plt.subplot(2, 2, 2)
plt.plot(result['time'], result['primary_pressure'] / 1e6, 'r-', 
         label='Primary', linewidth=2)
plt.plot(result['time'], result['secondary_pressure'] / 1e6, 'b--', 
         label='Secondary', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Pressure [MPa]')
plt.title('Primary and Secondary Pressure')
plt.legend()
plt.grid(True)

plt.subplot(2, 2, 3)
plt.plot(result['time'], result['leakage_rate'], 'g-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Leakage Rate [kg/s]')
plt.title('Primary-to-Secondary Leakage')
plt.grid(True)

plt.subplot(2, 2, 4)
pressure_diff = result['primary_pressure'] - result['secondary_pressure']
plt.plot(result['time'], pressure_diff / 1e6, 'm-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Pressure Difference [MPa]')
plt.title('Pressure Difference (Primary - Secondary)')
plt.grid(True)

plt.tight_layout()
plt.savefig('sg_tube_rupture.png', dpi=300)
plt.show()

print(f"Peak leakage rate: {np.max(result['leakage_rate']):.2f} kg/s")
print(f"Primary pressure drop: {(conditions.initial_pressure - result['primary_pressure'][-1])/1e6:.2f} MPa")
print(f"Secondary pressure increase: {(result['secondary_pressure'][-1] - 6.0e6)/1e6:.2f} MPa")
```

---

## Advanced Usage

### Point Kinetics with Temperature Feedback

For more detailed analysis, use the point kinetics solver directly:

```python
from smrforge.safety.transients import (
    PointKineticsSolver,
    PointKineticsParameters,
)
import numpy as np

# Define delayed neutron parameters (6-group for LWR)
beta = np.array([0.00021, 0.00141, 0.00127, 0.00255, 0.00074, 0.00027])
lambda_d = np.array([0.0127, 0.0317, 0.115, 0.311, 1.40, 3.87])

# Create point kinetics parameters
params = PointKineticsParameters(
    beta=beta,
    lambda_d=lambda_d,
    alpha_fuel=-5e-5,  # Fuel temperature coefficient [dk/k/K]
    alpha_moderator=-2e-5,  # Moderator temperature coefficient [dk/k/K]
    Lambda=1e-4,  # Prompt neutron lifetime [s]
    fuel_heat_capacity=1e6,  # J/K
    moderator_heat_capacity=5e5,  # J/K
)

# Create solver
solver = PointKineticsSolver(params)

# Define reactivity insertion (e.g., control rod withdrawal)
def reactivity_insertion(t):
    if t < 0:
        return 0.0
    elif t < 5.0:
        return 0.002 * (t / 5.0)  # Linear insertion over 5 seconds
    else:
        return 0.002  # Constant reactivity

# Define power removal (heat sink)
def power_removal(t, T_fuel, T_mod):
    # Simplified: constant heat removal
    return 0.9 * 77e6  # 90% of initial power

# Initial state
initial_state = {
    "power": 77e6,  # 77 MWth
    "T_fuel": 1200.0,  # K
    "T_moderator": 900.0,  # K
}

# Solve transient
result = solver.solve_transient(
    rho_external=reactivity_insertion,
    power_removal=power_removal,
    initial_state=initial_state,
    t_span=(0.0, 100.0),
    max_step=0.1,
)

# Plot results
import matplotlib.pyplot as plt

plt.figure(figsize=(14, 8))

plt.subplot(2, 2, 1)
plt.plot(result['time'], result['power'] / 1e6, 'b-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Power [MWth]')
plt.title('Reactor Power')
plt.grid(True)

plt.subplot(2, 2, 2)
plt.plot(result['time'], result['reactivity'] * 1000, 'r-', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Reactivity [m$]')
plt.title('Total Reactivity')
plt.grid(True)

plt.subplot(2, 2, 3)
plt.plot(result['time'], result['T_fuel'], 'g-', linewidth=2, label='Fuel')
plt.plot(result['time'], result['T_moderator'], 'm--', linewidth=2, label='Moderator')
plt.xlabel('Time [s]')
plt.ylabel('Temperature [K]')
plt.title('Temperature Response')
plt.legend()
plt.grid(True)

plt.subplot(2, 2, 4)
# Plot delayed neutron precursors (first group)
if len(result['precursors'].shape) > 1:
    plt.plot(result['time'], result['precursors'][0, :], 'c-', linewidth=2)
    plt.xlabel('Time [s]')
    plt.ylabel('Precursor Concentration')
    plt.title('Delayed Neutron Precursors (Group 1)')
    plt.grid(True)

plt.tight_layout()
plt.savefig('point_kinetics_transient.png', dpi=300)
plt.show()

print(f"Peak power: {np.max(result['power'])/1e6:.2f} MWth")
print(f"Final power: {result['power'][-1]/1e6:.2f} MWth")
print(f"Peak fuel temperature: {np.max(result['T_fuel']):.1f} K")
```

### Decay Heat Calculations

Calculate decay heat after shutdown:

```python
from smrforge.safety.transients import decay_heat_ans_standard
import numpy as np
import matplotlib.pyplot as plt

# Time after shutdown [s]
t = np.logspace(0, 6, 1000)  # 1 second to 1 million seconds (~11.6 days)

# Operating power and time
P0 = 77e6  # 77 MWth
t_operate = 365 * 24 * 3600  # 1 year of operation

# Calculate decay heat
P_decay = decay_heat_ans_standard(t, P0, t_operate)

# Plot decay heat
plt.figure(figsize=(10, 6))
plt.loglog(t / 3600, P_decay / 1e6, 'b-', linewidth=2)
plt.xlabel('Time After Shutdown [hours]')
plt.ylabel('Decay Heat [MWth]')
plt.title('Decay Heat After Shutdown (ANS Standard)')
plt.grid(True, which='both', alpha=0.3)
plt.axhline(y=P0 * 0.066 / 1e6, color='r', linestyle='--', 
            label='Initial (6.6% of operating power)')
plt.legend()
plt.savefig('decay_heat.png', dpi=300)
plt.show()

print(f"Decay heat at 1 hour: {P_decay[0]/1e6:.2f} MWth ({P_decay[0]/P0*100:.1f}% of operating power)")
print(f"Decay heat at 24 hours: {np.interp(24*3600, t, P_decay)/1e6:.2f} MWth")
print(f"Decay heat at 1 week: {np.interp(7*24*3600, t, P_decay)/1e6:.2f} MWth")
```

---

## Complete Examples

### Complete PWR SMR Safety Analysis

```python
"""
Complete PWR SMR Safety Analysis
Analyzes multiple design basis accidents for a PWR SMR
"""

from smrforge.safety.transients import (
    TransientType,
    TransientConditions,
    SteamLineBreakTransient,
    FeedwaterLineBreakTransient,
    LOCATransientLWR,
)
from smrforge.geometry.lwr_smr import PWRSMRCore
import numpy as np
import matplotlib.pyplot as plt

# Create reactor
class ReactorSpec:
    def __init__(self):
        self.name = "NuScale-SMR"
        self.power_thermal = 77e6

reactor_spec = ReactorSpec()
core = PWRSMRCore(name="NuScale-SMR", n_assemblies=37)

# Common initial conditions
base_conditions = TransientConditions(
    initial_power=77e6,
    initial_temperature=600.0,
    initial_flow_rate=100.0,
    initial_pressure=15.5e6,
    trigger_time=0.0,
    t_end=3600.0,
    scram_available=True,
    scram_delay=1.0,
)

# 1. Steam Line Break
slb = SteamLineBreakTransient(reactor_spec, core)
conditions_slb = base_conditions
conditions_slb.transient_type = TransientType.STEAM_LINE_BREAK
result_slb = slb.simulate(conditions_slb, break_area=0.01)

# 2. Feedwater Line Break
fwlb = FeedwaterLineBreakTransient(reactor_spec, core)
conditions_fwlb = base_conditions
conditions_fwlb.transient_type = TransientType.FEEDWATER_LINE_BREAK
result_fwlb = fwlb.simulate(conditions_fwlb, break_area=0.02)

# 3. Small Break LOCA
loca = LOCATransientLWR(reactor_spec, core)
conditions_sbloca = base_conditions
conditions_sbloca.transient_type = TransientType.SB_LOCA
result_sbloca = loca.simulate(conditions_sbloca, break_area=0.05, break_type="small")

# Compare all transients
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Power comparison
axes[0, 0].plot(result_slb['time'], result_slb['power'] / 1e6, 'b-', 
                label='SLB', linewidth=2)
axes[0, 0].plot(result_fwlb['time'], result_fwlb['power'] / 1e6, 'r-', 
                label='FWLB', linewidth=2)
axes[0, 0].plot(result_sbloca['time'], result_sbloca['power'] / 1e6, 'g-', 
                label='SB-LOCA', linewidth=2)
axes[0, 0].set_xlabel('Time [s]')
axes[0, 0].set_ylabel('Power [MWth]')
axes[0, 0].set_title('Reactor Power Response')
axes[0, 0].legend()
axes[0, 0].grid(True)

# Pressure comparison
axes[0, 1].plot(result_slb['time'], result_slb['pressure'] / 1e6, 'b-', 
                label='SLB', linewidth=2)
axes[0, 1].plot(result_fwlb['time'], result_fwlb.get('pressure', 
                np.full_like(result_fwlb['time'], 15.5)) / 1e6, 'r-', 
                label='FWLB', linewidth=2)
axes[0, 1].plot(result_sbloca['time'], result_sbloca['pressure'] / 1e6, 'g-', 
                label='SB-LOCA', linewidth=2)
axes[0, 1].set_xlabel('Time [s]')
axes[0, 1].set_ylabel('Pressure [MPa]')
axes[0, 1].set_title('Primary System Pressure')
axes[0, 1].legend()
axes[0, 1].grid(True)

# Temperature comparison
axes[1, 0].plot(result_slb['time'], result_slb['temperature'], 'b-', 
                label='SLB', linewidth=2)
axes[1, 0].plot(result_fwlb['time'], result_fwlb['temperature'], 'r-', 
                label='FWLB', linewidth=2)
axes[1, 0].plot(result_sbloca['time'], result_sbloca['temperature'], 'g-', 
                label='SB-LOCA', linewidth=2)
axes[1, 0].set_xlabel('Time [s]')
axes[1, 0].set_ylabel('Temperature [K]')
axes[1, 0].set_title('Core Temperature')
axes[1, 0].legend()
axes[1, 0].grid(True)

# Summary statistics
transients = ['SLB', 'FWLB', 'SB-LOCA']
results = [result_slb, result_fwlb, result_sbloca]
peak_powers = [np.max(r['power'])/1e6 for r in results]
min_pressures = [np.min(r.get('pressure', np.full_like(r['time'], 15.5e6)))/1e6 
                 for r in results]
peak_temps = [np.max(r['temperature']) for r in results]

axes[1, 1].bar(transients, peak_powers, color=['b', 'r', 'g'], alpha=0.7)
axes[1, 1].set_ylabel('Peak Power [MWth]')
axes[1, 1].set_title('Peak Power Comparison')
axes[1, 1].grid(True, axis='y')

plt.tight_layout()
plt.savefig('complete_safety_analysis.png', dpi=300)
plt.show()

# Print summary
print("=" * 60)
print("PWR SMR Safety Analysis Summary")
print("=" * 60)
for i, name in enumerate(transients):
    print(f"\n{name}:")
    print(f"  Peak power: {peak_powers[i]:.2f} MWth")
    print(f"  Minimum pressure: {min_pressures[i]:.2f} MPa")
    print(f"  Peak temperature: {peak_temps[i]:.1f} K")
```

---

## Best Practices

1. **Always validate inputs** - Check that initial conditions are physically reasonable
2. **Use appropriate time spans** - Different transients require different simulation durations
3. **Consider scram delays** - Account for realistic scram insertion times
4. **Compare scenarios** - Run multiple break sizes or conditions to understand sensitivity
5. **Visualize results** - Use plots to understand transient behavior
6. **Check convergence** - Ensure time steps are small enough for accuracy

---

## References

- ANS Standard for Decay Heat: ANSI/ANS-5.1-2014
- NUREG-0800: Standard Review Plan for LWRs
- NUREG-1826: Probabilistic Risk Assessment for SMRs

---

**See Also:**
- [Data Downloader Guide](data-downloader-guide.md) - For setting up ENDF data
- [LWR SMR Burnup Guide](lwr-smr-burnup-guide.md) - For fuel cycle analysis
- [Usage Guide](usage.md) - For general SMRForge usage
