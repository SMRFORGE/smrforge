"""
Visualization Examples

This script demonstrates how to use the SMRForge visualization module
for plotting reactor geometry, flux distributions, power, and temperature.
"""

import numpy as np
from smrforge.geometry import PrismaticCore, PebbleBedCore
from smrforge.visualization.geometry import (
    plot_core_layout,
    plot_flux_on_geometry,
    plot_power_distribution,
    plot_temperature_distribution,
)


def example_prismatic_core_layout():
    """Example: Plot prismatic core layout."""
    print("Creating prismatic core...")
    core = PrismaticCore(name="Example-Prismatic")
    core.build_hexagonal_lattice(
        n_rings=3,
        pitch=40.0,
        block_height=79.3,
        n_axial=10,
        flat_to_flat=36.0,
    )

    # Plot top view
    print("Plotting top view (xy)...")
    fig, ax = plot_core_layout(core, view="xy", show_labels=True)
    fig.savefig("output/prismatic_top_view.png", dpi=150)
    print("Saved: output/prismatic_top_view.png")

    # Plot side view
    print("Plotting side view (xz)...")
    fig, ax = plot_core_layout(core, view="xz", show_labels=False)
    fig.savefig("output/prismatic_side_view.png", dpi=150)
    print("Saved: output/prismatic_side_view.png")


def example_pebble_bed_layout():
    """Example: Plot pebble bed core layout."""
    print("\nCreating pebble bed core...")
    core = PebbleBedCore(name="Example-Pebble")
    core.build_structured_packing(
        core_height=500.0,
        core_diameter=200.0,
        pebble_radius=3.0,
    )

    # Plot top view
    print("Plotting top view...")
    fig, ax = plot_core_layout(core, view="xy", show_labels=True)
    fig.savefig("output/pebble_bed_top_view.png", dpi=150)
    print("Saved: output/pebble_bed_top_view.png")


def example_flux_distribution():
    """Example: Plot flux distribution on geometry."""
    print("\nCreating core for flux visualization...")
    core = PrismaticCore(name="Flux-Example")
    core.build_hexagonal_lattice(n_rings=2, pitch=40.0, block_height=79.3, n_axial=3)

    # Generate mesh
    core.generate_mesh(n_radial=20, n_axial=30)

    # Create dummy flux distribution (2D: radial x axial)
    # In practice, this would come from neutronics solver
    if core.radial_mesh is not None and core.axial_mesh is not None:
        r_mesh = core.radial_mesh
        z_mesh = core.axial_mesh
        R, Z = np.meshgrid(r_mesh, z_mesh)

        # Create flux distribution (e.g., cosine shape)
        flux = np.cos(np.pi * Z / Z.max()) * np.exp(-R / R.max())
        flux = flux.T  # Transpose to match expected shape

        print("Plotting flux distribution (side view)...")
        fig, ax = plot_flux_on_geometry(flux, core, view="xz", cmap="viridis")
        fig.savefig("output/flux_distribution.png", dpi=150)
        print("Saved: output/flux_distribution.png")
    else:
        print("Core mesh not generated. Skipping flux plot.")


def example_power_distribution():
    """Example: Plot power distribution."""
    print("\nCreating core for power visualization...")
    core = PrismaticCore(name="Power-Example")
    core.build_hexagonal_lattice(n_rings=2, pitch=40.0, block_height=79.3, n_axial=3)
    core.generate_mesh(n_radial=20, n_axial=30)

    if core.radial_mesh is not None and core.axial_mesh is not None:
        r_mesh = core.radial_mesh
        z_mesh = core.axial_mesh
        R, Z = np.meshgrid(r_mesh, z_mesh)

        # Create power distribution (W/cm³)
        power = 1e6 * np.cos(np.pi * Z / Z.max()) * np.exp(-R / R.max())
        power = power.T  # Transpose

        print("Plotting power distribution...")
        fig, ax = plot_power_distribution(power, core, view="xz", cmap="hot")
        fig.savefig("output/power_distribution.png", dpi=150)
        print("Saved: output/power_distribution.png")
    else:
        print("Core mesh not generated. Skipping power plot.")


def example_temperature_distribution():
    """Example: Plot temperature distribution."""
    print("\nCreating core for temperature visualization...")
    core = PrismaticCore(name="Temperature-Example")
    core.build_hexagonal_lattice(n_rings=2, pitch=40.0, block_height=79.3, n_axial=3)
    core.generate_mesh(n_radial=20, n_axial=30)

    if core.radial_mesh is not None and core.axial_mesh is not None:
        r_mesh = core.radial_mesh
        z_mesh = core.axial_mesh
        R, Z = np.meshgrid(r_mesh, z_mesh)

        # Create temperature distribution (K)
        # Example: base temperature + power-dependent increase
        T_base = 1200.0  # K
        T_increase = 200.0 * np.cos(np.pi * Z / Z.max()) * np.exp(-R / R.max())
        temperature = T_base + T_increase
        temperature = temperature.T  # Transpose

        print("Plotting temperature distribution...")
        fig, ax = plot_temperature_distribution(
            temperature, core, view="xz", cmap="coolwarm"
        )
        fig.savefig("output/temperature_distribution.png", dpi=150)
        print("Saved: output/temperature_distribution.png")
    else:
        print("Core mesh not generated. Skipping temperature plot.")


if __name__ == "__main__":
    import os

    # Create output directory
    os.makedirs("output", exist_ok=True)

    print("=" * 60)
    print("SMRForge Visualization Examples")
    print("=" * 60)

    # Run examples
    example_prismatic_core_layout()
    example_pebble_bed_layout()
    example_flux_distribution()
    example_power_distribution()
    example_temperature_distribution()

    print("\n" + "=" * 60)
    print("All visualization examples completed!")
    print("Check the output/ directory for generated plots.")
    print("=" * 60)

