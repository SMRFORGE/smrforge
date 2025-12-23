"""
Custom Reactor Design Example
==============================

This example shows how to create a custom reactor design from scratch
using SMRForge's validation framework.
"""

from smrforge.validation.models import (
    ReactorSpecification,
    ReactorType,
    FuelType,
    GeometryParameters,
    MaterialComposition,
)


def create_custom_reactor():
    """
    Create a custom reactor specification.
    
    This example creates a 50 MW prismatic HTGR design.
    """
    print("=" * 60)
    print("Creating Custom Reactor Design")
    print("=" * 60)
    print()
    
    # Create reactor specification
    print("1. Defining reactor specification...")
    
    spec = ReactorSpecification(
        # Basic information
        name="Custom-50MW-HTGR",
        reactor_type=ReactorType.PRISMATIC,
        
        # Power and dimensions
        power_thermal=50e6,  # 50 MW thermal
        core_height=300.0,  # cm
        core_diameter=200.0,  # cm
        reflector_thickness=40.0,  # cm
        
        # Fuel properties
        fuel_type=FuelType.UCO,
        enrichment=0.125,  # 12.5% enrichment
        heavy_metal_loading=200.0,  # g/block
        
        # Operating conditions
        inlet_temperature=823.15,  # 550°C
        outlet_temperature=1023.15,  # 750°C
        max_fuel_temperature=1873.15,  # 1600°C
        primary_pressure=7.0e6,  # 7 MPa
        
        # Flow and cycle
        coolant_flow_rate=15.0,  # kg/s
        cycle_length=3650,  # days (~10 years)
        capacity_factor=0.92,
        target_burnup=120.0,  # GWd/tU
        
        # Safety parameters
        doppler_coefficient=-3.5e-5,  # pcm/K
        shutdown_margin=0.07,
    )
    
    print(f"   Created: {spec.name}")
    print(f"   Type: {spec.reactor_type.value}")
    print(f"   Power: {spec.power_thermal / 1e6:.1f} MW")
    print()
    
    # Display key parameters
    print("2. Reactor Parameters:")
    print(f"   Core dimensions:")
    print(f"     Height: {spec.core_height} cm")
    print(f"     Diameter: {spec.core_diameter} cm")
    print(f"     Reflector: {spec.reflector_thickness} cm")
    print()
    print(f"   Fuel:")
    print(f"     Type: {spec.fuel_type.value}")
    print(f"     Enrichment: {spec.enrichment * 100:.1f}%")
    print(f"     Loading: {spec.heavy_metal_loading} g/block")
    print()
    print(f"   Operating conditions:")
    print(f"     Inlet: {spec.inlet_temperature - 273.15:.1f} °C")
    print(f"     Outlet: {spec.outlet_temperature - 273.15:.1f} °C")
    print(f"     Pressure: {spec.primary_pressure / 1e6:.1f} MPa")
    print()
    
    # Validate the specification
    print("3. Validating specification...")
    try:
        # Pydantic validates automatically on creation
        print("   ✓ Specification is valid")
        
        # Check some computed properties
        print(f"   Temperature rise: {spec.outlet_temperature - spec.inlet_temperature:.1f} K")
        print(f"   Design margin: {spec.shutdown_margin * 100:.1f}%")
    except Exception as e:
        print(f"   ✗ Validation error: {e}")
        return None
    
    print()
    
    return spec


def create_geometry_parameters(spec):
    """
    Create geometry parameters for the reactor.
    
    Args:
        spec: ReactorSpecification object
    """
    print("4. Creating geometry parameters...")
    
    geometry = GeometryParameters(
        core_height=spec.core_height,
        core_diameter=spec.core_diameter,
        reflector_thickness=spec.reflector_thickness,
        n_radial=21,  # Mesh resolution
        n_axial=41,
    )
    
    print(f"   Radial mesh points: {geometry.n_radial}")
    print(f"   Axial mesh points: {geometry.n_axial}")
    print(f"   Total mesh cells: {geometry.n_radial * geometry.n_axial}")
    print()
    
    return geometry


def create_material_composition():
    """
    Create material composition for fuel.
    
    Returns:
        MaterialComposition object
    """
    print("5. Creating material composition...")
    
    # Example: UCO fuel composition
    composition = MaterialComposition(
        elements={
            'U235': 0.00125,  # atoms/b-cm
            'U238': 0.00875,
            'O16': 0.02000,
            'C12': 0.97000,  # Graphite matrix
        }
    )
    
    print("   Elements:")
    for element, density in composition.elements.items():
        print(f"     {element}: {density:.5f} atoms/b-cm")
    print()
    
    return composition


def modify_reactor_design(spec):
    """
    Demonstrate modifying a reactor design.
    
    Args:
        spec: ReactorSpecification object to modify
    """
    print("6. Modifying reactor design...")
    print(f"   Original power: {spec.power_thermal / 1e6:.1f} MW")
    
    # Create modified version
    modified_spec = spec.model_copy(update={
        'power_thermal': 75e6,  # Increase to 75 MW
        'enrichment': 0.15,  # Increase enrichment
    })
    
    print(f"   Modified power: {modified_spec.power_thermal / 1e6:.1f} MW")
    print(f"   Modified enrichment: {modified_spec.enrichment * 100:.1f}%")
    print()
    
    return modified_spec


def export_to_dict(spec):
    """
    Export reactor specification to dictionary (for JSON export).
    
    Args:
        spec: ReactorSpecification object
    """
    print("7. Exporting to dictionary...")
    
    spec_dict = spec.model_dump()
    
    print(f"   Exported {len(spec_dict)} fields")
    print(f"   Keys: {', '.join(list(spec_dict.keys())[:5])}...")
    print()
    
    # Can be saved to JSON:
    # import json
    # with open('reactor_design.json', 'w') as f:
    #     json.dump(spec_dict, f, indent=2)
    
    return spec_dict


def main():
    """Main function demonstrating custom reactor creation."""
    
    # Create custom reactor
    spec = create_custom_reactor()
    
    if spec is None:
        print("Failed to create reactor specification")
        return
    
    # Create geometry parameters
    geometry = create_geometry_parameters(spec)
    
    # Create material composition
    composition = create_material_composition()
    
    # Modify design
    modified_spec = modify_reactor_design(spec)
    
    # Export
    spec_dict = export_to_dict(spec)
    
    print("=" * 60)
    print("Custom reactor design complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Use this specification to create geometry")
    print("  2. Generate cross-section data")
    print("  3. Run neutronics analysis (see basic_neutronics.py)")
    print("  4. Run thermal-hydraulics analysis (see thermal_analysis.py)")


if __name__ == "__main__":
    main()

