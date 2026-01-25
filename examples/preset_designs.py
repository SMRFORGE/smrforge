"""
Preset Reactor Designs Example
==============================

This example demonstrates how to use SMRForge's preset reactor designs.
Preset designs provide validated reference configurations that you can use
directly or as starting points for your own designs.
"""

from smrforge.presets.htgr import DesignLibrary


def list_available_designs():
    """List all available preset designs."""
    print("=" * 60)
    print("Available Preset Designs")
    print("=" * 60)
    print()
    
    library = DesignLibrary()
    
    # Get all designs
    designs = library.list_designs()
    
    print(f"Total designs available: {len(designs)}")
    print()
    
    for design_name in designs:
        spec = library.get_design(design_name)
        
        print(f"Design: {spec.name}")
        print(f"  Type: {spec.reactor_type.value}")
        print(f"  Power: {spec.power_thermal / 1e6:.1f} MW")
        print(f"  Core height: {spec.core_height} cm")
        print(f"  Core diameter: {spec.core_diameter} cm")
        print(f"  Enrichment: {spec.enrichment * 100:.1f}%")
        print(f"  Fuel type: {spec.fuel_type.value}")
        print()
    
    return designs


def analyze_preset_design(design_name: str = "valar-10"):
    """
    Analyze a preset reactor design.
    
    Args:
        design_name: Name of the design to analyze
    """
    print("=" * 60)
    print(f"Analyzing Design: {design_name}")
    print("=" * 60)
    print()
    
    # Load preset design
    print("1. Loading preset design...")
    library = DesignLibrary()
    spec = library.get_design(design_name)
    
    print(f"   Name: {spec.name}")
    print(f"   Power: {spec.power_thermal / 1e6:.1f} MW thermal")
    print(f"   Type: {spec.reactor_type.value}")
    print()
    
    # Display key parameters
    print("2. Design Parameters:")
    print(f"   Core dimensions:")
    print(f"     Height: {spec.core_height} cm")
    print(f"     Diameter: {spec.core_diameter} cm")
    print(f"     Reflector thickness: {spec.reflector_thickness} cm")
    print()
    print(f"   Fuel properties:")
    print(f"     Type: {spec.fuel_type.value}")
    print(f"     Enrichment: {spec.enrichment * 100:.1f}%")
    print(f"     Heavy metal loading: {spec.heavy_metal_loading} g/block")
    print()
    print(f"   Operating conditions:")
    print(f"     Inlet temperature: {spec.inlet_temperature - 273.15:.1f} °C")
    print(f"     Outlet temperature: {spec.outlet_temperature - 273.15:.1f} °C")
    print(f"     Pressure: {spec.primary_pressure / 1e6:.1f} MPa")
    print(f"     Flow rate: {spec.coolant_flow_rate} kg/s")
    print()
    print(f"   Design targets:")
    print(f"     Cycle length: {spec.cycle_length} days")
    print(f"     Target burnup: {spec.target_burnup} GWd/tU")
    print(f"     Capacity factor: {spec.capacity_factor * 100:.1f}%")
    print()
    
    # Validate design
    print("3. Validating design...")
    is_valid = library.validate_all_designs()
    if is_valid:
        print("   ✓ Design validation passed")
    else:
        print("   ✗ Design validation failed")
    print()
    
    print("=" * 60)
    print("Design summary complete!")
    print("=" * 60)
    print()
    print("Note: To run neutronics analysis, see basic_neutronics.py example")


def compare_designs(design_names=None):
    """
    Compare multiple preset designs side-by-side.
    
    Args:
        design_names: List of design names to compare. If None, compares all.
    """
    if design_names is None:
        library = DesignLibrary()
        design_names = library.list_designs()
    
    print("=" * 60)
    print("Design Comparison")
    print("=" * 60)
    print()
    
    library = DesignLibrary()
    
    # Create comparison table
    print(f"{'Design':<20} {'Power (MW)':<12} {'Height (cm)':<12} {'Dia (cm)':<12} {'Enrich (%)':<12}")
    print("-" * 70)
    
    for name in design_names:
        spec = library.get_design(name)
        print(f"{spec.name:<20} {spec.power_thermal/1e6:<12.1f} {spec.core_height:<12.1f} "
              f"{spec.core_diameter:<12.1f} {spec.enrichment*100:<12.1f}")
    
    print()


def main():
    """Main function demonstrating preset design usage."""
    
    # List all available designs
    designs = list_available_designs()
    
    print()
    
    # Analyze a specific design
    if "valar-10" in designs:
        analyze_preset_design("valar-10")
        print()
    
    # Compare designs
    if len(designs) > 1:
        compare_designs(designs[:3])  # Compare first 3


if __name__ == "__main__":
    main()

