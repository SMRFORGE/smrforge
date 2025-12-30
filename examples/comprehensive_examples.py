"""
Comprehensive SMRForge Examples

This file demonstrates key features and workflows in SMRForge, including:
- Geometry creation and manipulation
- Neutronics calculations
- Thermal-hydraulics analysis
- Geometry import/export
- Integration of multiple modules
"""

import numpy as np
from pathlib import Path

from smrforge.geometry import PrismaticCore, GeometryExporter
from smrforge.geometry.importers import GeometryImporter
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.thermal import ChannelThermalHydraulics, ChannelGeometry
from smrforge.validation.models import CrossSectionData, SolverOptions


def example_geometry_creation():
    """Example: Create and configure a prismatic core geometry."""
    print("=" * 60)
    print("Example 1: Geometry Creation")
    print("=" * 60)

    # Create a prismatic core
    core = PrismaticCore(name="Example-Core")
    core.core_height = 793.0  # cm
    core.core_diameter = 300.0  # cm

    # Build hexagonal lattice
    core.build_hexagonal_lattice(
        n_rings=3,
        pitch=40.0,  # cm
        block_height=79.3,  # cm
        n_axial=10,  # 10 blocks axially
        flat_to_flat=36.0,  # cm
    )

    # Build mesh for neutronics
    core.build_mesh(n_radial=30, n_axial=20)

    print(f"Created core: {core.name}")
    print(f"  Core height: {core.core_height:.1f} cm")
    print(f"  Core diameter: {core.core_diameter:.1f} cm")
    print(f"  Number of blocks: {len(core.blocks)}")
    print(f"  Mesh: {len(core.radial_mesh)-1} radial × {len(core.axial_mesh)-1} axial cells")


def example_neutronics_solver():
    """Example: Solve multi-group diffusion equation."""
    print("\n" + "=" * 60)
    print("Example 2: Neutronics Solver")
    print("=" * 60)

    # Create geometry
    geometry = PrismaticCore(name="Neutronics-Example")
    geometry.core_height = 200.0
    geometry.core_diameter = 100.0
    geometry.build_mesh(n_radial=20, n_axial=10)

    # Create 2-group cross sections
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

    # Create solver options
    options = SolverOptions(
        max_iterations=100,
        tolerance=1e-6,
        eigen_method="power",  # or "arnoldi"
        verbose=True,
    )

    # Create and solve
    solver = MultiGroupDiffusion(geometry, xs_data, options)
    k_eff, flux = solver.solve_steady_state()

    print(f"k-eff: {k_eff:.6f}")
    print(f"Flux shape: {flux.shape}")
    print(f"Total flux: {np.sum(flux):.2e}")
    print(f"Max flux: {np.max(flux):.2e}")


def example_thermal_hydraulics():
    """Example: Thermal-hydraulics analysis."""
    print("\n" + "=" * 60)
    print("Example 3: Thermal-Hydraulics")
    print("=" * 60)

    # Define channel geometry
    geometry = ChannelGeometry(
        length=500.0,  # cm
        diameter=2.0,  # cm
        flow_area=3.14159,  # cm²
        heated_perimeter=6.28318,  # cm
    )

    # Define inlet conditions
    inlet_conditions = {
        "temperature": 773.15,  # K (500°C)
        "pressure": 7.0e6,  # Pa (7 MPa)
        "mass_flow_rate": 0.1,  # kg/s
    }

    # Create solver
    solver = ChannelThermalHydraulics(geometry, inlet_conditions)

    # Set power profile (cosine shape)
    n_nodes = len(solver.z)
    z_normalized = np.linspace(0, 1, n_nodes)
    power_profile = 150.0 * np.cos(np.pi * z_normalized)  # W/cm
    power_profile = np.maximum(power_profile, 0)  # Ensure non-negative
    solver.set_power_profile(power_profile)

    # Solve steady state
    results = solver.solve_steady_state()

    print(f"Inlet temperature: {results['temperature'][0]:.1f} K")
    print(f"Outlet temperature: {results['temperature'][-1]:.1f} K")
    print(f"Temperature rise: {results['temperature'][-1] - results['temperature'][0]:.1f} K")
    print(f"Pressure drop: {(results['pressure'][0] - results['pressure'][-1])/1e3:.2f} kPa")


def example_geometry_import_export():
    """Example: Geometry import/export workflow."""
    print("\n" + "=" * 60)
    print("Example 4: Geometry Import/Export")
    print("=" * 60)

    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Create a core
    core = PrismaticCore(name="Export-Example")
    core.core_height = 200.0
    core.core_diameter = 150.0
    core.build_hexagonal_lattice(n_rings=2, pitch=40.0, block_height=79.3, n_axial=3)

    # Export to JSON
    json_file = output_dir / "exported_core.json"
    GeometryExporter.to_json(core, json_file)
    print(f"Exported core to: {json_file}")

    # Import from JSON
    imported_core = GeometryImporter.from_json(json_file)
    print(f"Imported core: {imported_core.name}")
    print(f"  Blocks: {len(imported_core.blocks)}")
    print(f"  Height: {imported_core.core_height:.1f} cm")

    # Validate
    validation = GeometryImporter.validate_imported_geometry(imported_core)
    if validation["valid"]:
        print("  ✓ Geometry validation passed")
    else:
        print(f"  ✗ Validation errors: {validation['errors']}")


def example_integrated_workflow():
    """Example: Integrated workflow combining multiple modules."""
    print("\n" + "=" * 60)
    print("Example 5: Integrated Workflow")
    print("=" * 60)

    # Step 1: Create geometry
    geometry = PrismaticCore(name="Integrated-Example")
    geometry.core_height = 300.0
    geometry.core_diameter = 200.0
    geometry.build_mesh(n_radial=25, n_axial=15)

    # Step 2: Solve neutronics
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
    options = SolverOptions(max_iterations=100, tolerance=1e-6, eigen_method="power")
    solver = MultiGroupDiffusion(geometry, xs_data, options)
    k_eff, flux = solver.solve_steady_state()

    print(f"Step 1: Neutronics solved")
    print(f"  k-eff: {k_eff:.6f}")

    # Step 3: Thermal-hydraulics (simplified - using averaged power)
    th_geometry = ChannelGeometry(
        length=geometry.core_height,
        diameter=2.0,
        flow_area=3.14159,
        heated_perimeter=6.28318,
    )
    inlet_conditions = {
        "temperature": 773.15,
        "pressure": 7.0e6,
        "mass_flow_rate": 0.15,
    }
    th_solver = ChannelThermalHydraulics(th_geometry, inlet_conditions)

    # Use average power (simplified - in reality would map from flux)
    avg_power = 100.0  # W/cm
    power_profile = np.ones(len(th_solver.z)) * avg_power
    th_solver.set_power_profile(power_profile)
    th_results = th_solver.solve_steady_state()

    print(f"Step 2: Thermal-hydraulics solved")
    print(f"  Outlet temperature: {th_results['temperature'][-1]:.1f} K")
    print(f"  Temperature rise: {th_results['temperature'][-1] - th_results['temperature'][0]:.1f} K")

    print("\nIntegrated workflow completed successfully!")


if __name__ == "__main__":
    # Run all examples
    example_geometry_creation()
    example_neutronics_solver()
    example_thermal_hydraulics()
    example_geometry_import_export()
    example_integrated_workflow()

    print("\n" + "=" * 60)
    print("All comprehensive examples completed!")
    print("=" * 60)

