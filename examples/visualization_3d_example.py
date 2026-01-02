"""
Example: 3D Visualization using Mesh3D

Demonstrates how to create 3D visualizations of reactor geometry
using the new 3D mesh support.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np

from smrforge.geometry import PrismaticCore
from smrforge.geometry.mesh_extraction import (
    extract_core_surface_mesh,
    extract_core_volume_mesh,
    extract_material_boundaries,
)

# Try to import visualization functions
try:
    from smrforge.visualization.mesh_3d import (
        export_mesh_to_vtk,
        plot_mesh3d_plotly,
        plot_surface_plotly,
    )

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Note: plotly not available. Install with: pip install plotly")

try:
    from smrforge.visualization.mesh_3d import plot_mesh3d_pyvista

    PYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False
    print("Note: pyvista not available. Install with: pip install pyvista")


def main():
    """Demonstrate 3D visualization."""
    print("=" * 60)
    print("3D Visualization Example")
    print("=" * 60)
    
    # Create a prismatic core
    print("\n1. Creating prismatic core...")
    core = PrismaticCore(name="VisualizationCore")
    core.build_hexagonal_lattice(
        n_rings=3,
        pitch=40.0,
        block_height=80.0,
        n_axial=2,
        flat_to_flat=36.0,
    )
    print(f"   Created core with {len(core.blocks)} blocks")
    
    # Extract volume mesh
    print("\n2. Extracting volume mesh...")
    volume_mesh = extract_core_volume_mesh(core, include_channels=False)
    print(f"   Volume mesh: {volume_mesh.n_vertices} vertices, "
          f"{volume_mesh.n_cells} cells")
    
    # Extract surface mesh
    print("\n3. Extracting surface mesh...")
    surface_mesh = extract_core_surface_mesh(core)
    print(f"   Surface mesh: {surface_mesh.n_vertices} vertices, "
          f"{surface_mesh.n_faces} faces")
    
    # Extract material boundaries
    print("\n4. Extracting material boundaries...")
    boundaries = extract_material_boundaries(core)
    print(f"   Found {len(boundaries)} material boundaries")
    
    # Add dummy flux data
    print("\n5. Adding flux data to mesh...")
    n_blocks = len(core.blocks)
    flux = np.ones((n_blocks, 2)) * 1e14  # [n_blocks, n_groups]
    # In practice, this would come from the neutronics solver
    volume_mesh.add_cell_data("flux", np.ones(volume_mesh.n_cells) * 1e14)
    print("   Added flux data to mesh")
    
    # Visualize with plotly
    if PLOTLY_AVAILABLE:
        print("\n6. Creating plotly visualization...")
        try:
            fig = plot_mesh3d_plotly(
                volume_mesh,
                color_by="material",
                show_edges=False,
                opacity=0.8,
                title="Reactor Core 3D Mesh",
            )
            print("   ✓ Plotly figure created")
            print("   Use fig.show() to display in browser")
            # Uncomment to show:
            # fig.show()
        except Exception as e:
            print(f"   Warning: Error creating plotly visualization: {e}")
    
    # Visualize with pyvista
    if PYVISTA_AVAILABLE:
        print("\n7. Creating pyvista visualization...")
        try:
            plotter = plot_mesh3d_pyvista(
                volume_mesh,
                color_by="material",
                show_edges=False,
                opacity=0.8,
            )
            print("   ✓ Pyvista plotter created")
            print("   Use plotter.show() to display")
            # Uncomment to show:
            # plotter.show()
        except Exception as e:
            print(f"   Warning: Error creating pyvista visualization: {e}")
    
    # Export to VTK
    if PYVISTA_AVAILABLE:
        print("\n8. Exporting to VTK format...")
        try:
            export_mesh_to_vtk(volume_mesh, "core_mesh.vtu")
            print("   ✓ Exported to core_mesh.vtu")
            print("   Open in ParaView to visualize")
        except Exception as e:
            print(f"   Warning: Error exporting to VTK: {e}")
    
    # Plot material boundaries
    if PLOTLY_AVAILABLE and boundaries:
        print("\n9. Plotting material boundaries...")
        try:
            for i, boundary in enumerate(boundaries[:2]):  # Plot first 2
                fig = plot_surface_plotly(
                    boundary,
                    color="lightblue" if i == 0 else "lightcoral",
                    opacity=0.6,
                    title=f"Material Boundary: {boundary.material_id}",
                )
                print(f"   ✓ Created plot for {boundary.material_id} boundary")
                # Uncomment to show:
                # fig.show()
        except Exception as e:
            print(f"   Warning: Error plotting boundaries: {e}")
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Install plotly: pip install plotly")
    print("  - Install pyvista: pip install pyvista")
    print("  - Use fig.show() or plotter.show() to visualize")
    print("  - Export to VTK for ParaView visualization")


if __name__ == "__main__":
    main()

