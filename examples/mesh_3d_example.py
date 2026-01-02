"""
Example: 3D Mesh Extraction and Visualization

Demonstrates how to extract 3D meshes from reactor geometry for visualization.
"""

import numpy as np

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from smrforge.geometry import PrismaticCore
from smrforge.geometry.mesh_extraction import (
    extract_block_mesh,
    extract_core_surface_mesh,
    extract_core_volume_mesh,
    extract_material_boundaries,
)


def main():
    """Demonstrate 3D mesh extraction."""
    print("=" * 60)
    print("3D Mesh Extraction Example")
    print("=" * 60)
    
    # Create a simple prismatic core
    print("\n1. Creating prismatic core...")
    core = PrismaticCore(name="TestCore")
    core.build_hexagonal_lattice(
        n_rings=3,
        pitch=40.0,
        block_height=80.0,
        n_axial=2,
        flat_to_flat=36.0,
    )
    
    print(f"   Created core with {len(core.blocks)} blocks")
    
    # Extract mesh for a single block
    print("\n2. Extracting mesh for single block...")
    if core.blocks:
        block = core.blocks[0]
        block_mesh = extract_block_mesh(block)
        print(f"   Block mesh: {block_mesh.n_vertices} vertices, "
              f"{block_mesh.n_faces} faces, {block_mesh.n_cells} cells")
        print(f"   Material: {block_mesh.cell_materials[0] if block_mesh.cell_materials is not None else 'None'}")
    
    # Extract volume mesh for entire core
    print("\n3. Extracting volume mesh for core...")
    volume_mesh = extract_core_volume_mesh(core, include_channels=False)
    print(f"   Volume mesh: {volume_mesh.n_vertices} vertices, "
          f"{volume_mesh.n_faces} faces, {volume_mesh.n_cells} cells")
    
    # Extract surface mesh
    print("\n4. Extracting surface mesh...")
    surface_mesh = extract_core_surface_mesh(core)
    print(f"   Surface mesh: {surface_mesh.n_vertices} vertices, "
          f"{surface_mesh.n_faces} faces")
    
    # Extract material boundaries
    print("\n5. Extracting material boundaries...")
    boundaries = extract_material_boundaries(core)
    print(f"   Found {len(boundaries)} material boundaries")
    for i, boundary in enumerate(boundaries):
        print(f"   Boundary {i+1}: {boundary.material_id}, "
              f"{boundary.n_vertices} vertices, {boundary.n_faces} faces")
    
    # Add flux data to mesh (example)
    print("\n6. Adding flux data to mesh...")
    # Create dummy flux data
    n_blocks = len(core.blocks)
    flux = np.ones((n_blocks, 2)) * 1e14  # [n_blocks, n_groups]
    
    # Note: This is a simplified example - in practice, you'd map flux
    # from the neutronics solver to the mesh cells properly
    print(f"   Created flux array: shape {flux.shape}")
    print("   (In practice, would map flux from solver to mesh cells)")
    
    # Get mesh bounds
    print("\n7. Mesh bounds and center...")
    min_bounds, max_bounds = volume_mesh.get_bounds()
    center = volume_mesh.get_center()
    print(f"   Bounds: [{min_bounds[0]:.1f}, {min_bounds[1]:.1f}, {min_bounds[2]:.1f}] "
          f"to [{max_bounds[0]:.1f}, {max_bounds[1]:.1f}, {max_bounds[2]:.1f}]")
    print(f"   Center: [{center[0]:.1f}, {center[1]:.1f}, {center[2]:.1f}]")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Use Mesh3D with plotly or pyvista for 3D visualization")
    print("  - Add flux/power data from neutronics solver")
    print("  - Create interactive 3D plots")
    print("  - Export to VTK format for ParaView")


if __name__ == "__main__":
    main()

