"""
Thermal-Hydraulics Analysis Example
===================================

This example demonstrates thermal-hydraulics analysis for a reactor
coolant channel, including temperature and pressure distributions.
"""

import numpy as np
from smrforge.thermal.hydraulics import (
    ChannelThermalHydraulics,
    ChannelGeometry,
)


def create_channel_geometry():
    """
    Create geometry for a coolant channel.
    
    Returns:
        ChannelGeometry object
    """
    # Channel parameters (typical HTGR values)
    channel_diameter = 1.0  # cm (hydraulic diameter)
    channel_length = 400.0  # cm
    
    # For circular channel
    radius = channel_diameter / 2
    flow_area = np.pi * radius**2  # cm²
    heated_perimeter = np.pi * channel_diameter  # cm
    
    geometry = ChannelGeometry(
        length=channel_length,
        diameter=channel_diameter,
        flow_area=flow_area,
        heated_perimeter=heated_perimeter,
    )
    
    return geometry


def create_power_profile(geometry, profile_type="cosine"):
    """
    Create axial power profile.
    
    Args:
        geometry: ChannelGeometry object
        profile_type: Type of profile ("uniform", "cosine", "chopped")
    
    Returns:
        numpy array of linear power density [W/cm]
    """
    n_points = 100  # Number of axial points
    z = np.linspace(0, geometry.length, n_points + 1)
    
    if profile_type == "uniform":
        q_linear = np.ones(n_points + 1) * 500.0  # W/cm
    
    elif profile_type == "cosine":
        # Cosine profile (typical for reactors)
        peak_power = 1000.0  # W/cm
        q_linear = peak_power * np.cos(np.pi * z / geometry.length)
        q_linear = np.maximum(q_linear, 0)  # No negative power
    
    elif profile_type == "chopped":
        # Chopped cosine (more realistic)
        peak_power = 1000.0  # W/cm
        z_norm = z / geometry.length
        q_linear = peak_power * np.cos(np.pi * (z_norm - 0.5))
        q_linear[z_norm < 0.1] = 0  # No power in bottom 10%
        q_linear[z_norm > 0.9] = 0  # No power in top 10%
        q_linear = np.maximum(q_linear, 0)
    
    else:
        raise ValueError(f"Unknown profile type: {profile_type}")
    
    return q_linear


def run_thermal_analysis():
    """Run thermal-hydraulics analysis."""
    
    print("=" * 60)
    print("Thermal-Hydraulics Analysis")
    print("=" * 60)
    print()
    
    # Step 1: Create geometry
    print("1. Creating channel geometry...")
    geometry = create_channel_geometry()
    print(f"   Channel length: {geometry.length} cm")
    print(f"   Hydraulic diameter: {geometry.diameter} cm")
    print(f"   Flow area: {geometry.flow_area:.4f} cm²")
    print(f"   Heated perimeter: {geometry.heated_perimeter:.4f} cm")
    print(f"   Hydraulic diameter: {geometry.hydraulic_diameter:.4f} cm")
    print()
    
    # Step 2: Define inlet conditions
    print("2. Setting inlet conditions...")
    inlet_conditions = {
        'temperature': 823.15,  # K (550°C)
        'pressure': 7.0e6,      # Pa (7 MPa)
        'mass_flow_rate': 0.1,  # kg/s
    }
    
    print(f"   Inlet temperature: {inlet_conditions['temperature'] - 273.15:.1f} °C")
    print(f"   Inlet pressure: {inlet_conditions['pressure'] / 1e6:.1f} MPa")
    print(f"   Mass flow rate: {inlet_conditions['mass_flow_rate']:.3f} kg/s")
    print()
    
    # Step 3: Create thermal-hydraulics solver
    print("3. Creating thermal-hydraulics solver...")
    th = ChannelThermalHydraulics(
        geometry=geometry,
        inlet_conditions=inlet_conditions
    )
    print(f"   Number of nodes: {th.nz + 1}")
    print()
    
    # Step 4: Set power profile
    print("4. Setting power profile...")
    power_profile = create_power_profile(geometry, profile_type="chopped")
    th.set_power_profile(power_profile)
    
    total_power = np.trapz(power_profile, th.z)  # W
    print(f"   Total channel power: {total_power / 1e3:.2f} kW")
    print(f"   Peak linear power: {np.max(power_profile):.1f} W/cm")
    print()
    
    # Step 5: Solve steady-state
    print("5. Solving steady-state thermal-hydraulics...")
    try:
        results = th.solve_steady_state()
        
        print()
        print("=" * 60)
        print("RESULTS")
        print("=" * 60)
        
        # Extract results
        T_coolant = results.get('T_coolant', th.T_coolant)
        P_coolant = results.get('P_coolant', th.P_coolant)
        
        print(f"Coolant Temperature:")
        print(f"   Inlet: {T_coolant[0] - 273.15:.1f} °C")
        print(f"   Outlet: {T_coolant[-1] - 273.15:.1f} °C")
        print(f"   Maximum: {np.max(T_coolant) - 273.15:.1f} °C")
        print(f"   Temperature rise: {T_coolant[-1] - T_coolant[0]:.1f} K")
        print()
        
        print(f"Coolant Pressure:")
        print(f"   Inlet: {P_coolant[0] / 1e6:.4f} MPa")
        print(f"   Outlet: {P_coolant[-1] / 1e6:.4f} MPa")
        print(f"   Pressure drop: {(P_coolant[0] - P_coolant[-1]) / 1e6:.4f} MPa")
        print()
        
        # Compute heat transfer coefficient if available
        if hasattr(th, 'h_conv'):
            print(f"Heat Transfer:")
            print(f"   Average h: {np.mean(th.h_conv):.1f} W/m²-K")
            print()
        
        print("=" * 60)
        print("Analysis complete!")
        print("=" * 60)
        
    except NotImplementedError:
        print("   ⚠ Thermal-hydraulics solve not fully implemented yet")
        print("   This is a placeholder example")
    except Exception as e:
        print(f"   Error: {e}")


def compare_power_profiles():
    """Compare different power profiles."""
    print()
    print("=" * 60)
    print("Power Profile Comparison")
    print("=" * 60)
    print()
    
    geometry = create_channel_geometry()
    
    profile_types = ["uniform", "cosine", "chopped"]
    
    for profile_type in profile_types:
        power_profile = create_power_profile(geometry, profile_type)
        total_power = np.trapz(power_profile, np.linspace(0, geometry.length, len(power_profile)))
        
        print(f"{profile_type.capitalize()} profile:")
        print(f"   Total power: {total_power / 1e3:.2f} kW")
        print(f"   Peak power: {np.max(power_profile):.1f} W/cm")
        print(f"   Average power: {np.mean(power_profile):.1f} W/cm")
        print()


def main():
    """Main function."""
    run_thermal_analysis()
    compare_power_profiles()
    
    print()
    print("Next steps:")
    print("  - Couple with neutronics for full-core analysis")
    print("  - Add fuel temperature calculation")
    print("  - Include transient analysis")


if __name__ == "__main__":
    main()

