"""
3D mesh extraction from reactor geometry.

Provides methods to extract 3D meshes from PrismaticCore and PebbleBedCore
for visualization and analysis.
"""

from typing import Dict, List, Optional

import numpy as np

from .core_geometry import GraphiteBlock, Pebble, PebbleBedCore, PrismaticCore
from .mesh_3d import (
    Mesh3D,
    Surface,
    combine_meshes,
    extract_cylinder_mesh,
    extract_hexagonal_prism_mesh,
    extract_sphere_mesh,
)


def extract_block_mesh(block: GraphiteBlock) -> Mesh3D:
    """
    Extract 3D mesh for a single graphite block.
    
    Args:
        block: GraphiteBlock instance
    
    Returns:
        Mesh3D instance representing the block
    """
    center = block.position.to_array()
    mesh = extract_hexagonal_prism_mesh(
        center=center,
        flat_to_flat=block.flat_to_flat,
        height=block.height,
    )
    
    # Set material ID (optimized: use np.full instead of list multiplication)
    if mesh.cells is not None:
        mesh.cell_materials = np.full(mesh.n_cells, block.block_type, dtype=object)
    
    return mesh


def extract_fuel_channel_mesh(channel) -> Mesh3D:
    """
    Extract 3D mesh for a fuel channel.
    
    Args:
        channel: FuelChannel instance
    
    Returns:
        Mesh3D instance
    """
    center = channel.position.to_array()
    mesh = extract_cylinder_mesh(
        center=center,
        radius=channel.radius,
        height=channel.height,
    )
    
    # Set material ID (optimized: use np.full instead of list multiplication)
    if mesh.cells is not None:
        material_id = channel.material_region.material_id if channel.material_region else "fuel"
        mesh.cell_materials = np.full(mesh.n_cells, material_id, dtype=object)
    
    return mesh


def extract_coolant_channel_mesh(channel) -> Mesh3D:
    """
    Extract 3D mesh for a coolant channel.
    
    Args:
        channel: CoolantChannel instance
    
    Returns:
        Mesh3D instance
    """
    center = channel.position.to_array()
    mesh = extract_cylinder_mesh(
        center=center,
        radius=channel.radius,
        height=channel.height,
    )
    
    # Set material ID (optimized: use np.full instead of list multiplication)
    if mesh.cells is not None:
        mesh.cell_materials = np.full(mesh.n_cells, "coolant", dtype=object)
    
    return mesh


def extract_pebble_mesh(pebble: Pebble) -> Mesh3D:
    """
    Extract 3D mesh for a pebble.
    
    Args:
        pebble: Pebble instance
    
    Returns:
        Mesh3D instance
    """
    center = pebble.position.to_array()
    mesh = extract_sphere_mesh(
        center=center,
        radius=pebble.radius,
    )
    
    # Set material ID (optimized: use np.full instead of list multiplication)
    if mesh.cells is not None:
        material_id = pebble.material_region.material_id if pebble.material_region else "pebble"
        mesh.cell_materials = np.full(mesh.n_cells, material_id, dtype=object)
    
    return mesh


def extract_core_surface_mesh(core: PrismaticCore) -> Surface:
    """
    Extract surface mesh for the outer boundary of a prismatic core.
    
    Args:
        core: PrismaticCore instance
    
    Returns:
        Surface instance
    """
    # Get outer blocks (reflector blocks)
    outer_blocks = [b for b in core.blocks if b.block_type == "reflector"]
    
    if not outer_blocks:
        # Use all blocks if no reflector
        outer_blocks = core.blocks
    
    # Extract surfaces from outer blocks (optimized: pre-allocate if possible)
    # For small numbers of blocks, list append is fine; for large, could pre-allocate
    vertices = []
    faces = []
    vertex_offset = 0
    
    for block in outer_blocks:
        block_mesh = extract_block_mesh(block)
        
        # Get outer faces (simplified - use top and side faces)
        if block_mesh.faces is not None and block_mesh.faces.size > 0:
            # Add vertices
            vertices.append(block_mesh.vertices)
            
            # Add faces with offset (optimized: avoid copy if possible)
            offset_faces = block_mesh.faces + vertex_offset
            faces.append(offset_faces)
            
            vertex_offset += block_mesh.n_vertices
    
    if not vertices:
        # Return empty surface
        return Surface(
            vertices=np.array([]).reshape(0, 3),
            faces=np.array([]).reshape(0, 3),
        )
    
    # Optimized: use np.concatenate for better performance with many blocks
    if len(vertices) == 1:
        combined_vertices = vertices[0]
        combined_faces = faces[0]
    else:
        combined_vertices = np.concatenate(vertices, axis=0)
        combined_faces = np.concatenate(faces, axis=0)
    
    return Surface(
        vertices=combined_vertices,
        faces=combined_faces,
        surface_type="boundary",
    )


def extract_core_volume_mesh(
    core: PrismaticCore,
    include_channels: bool = False,
    material_filter: Optional[List[str]] = None,
) -> Mesh3D:
    """
    Extract volume mesh for a prismatic core.
    
    Args:
        core: PrismaticCore instance
        include_channels: Whether to include fuel/coolant channels
        material_filter: Optional list of material IDs to include
    
    Returns:
        Mesh3D instance
    """
    meshes = []
    
    # Extract block meshes
    for block in core.blocks:
        # Apply material filter if specified
        if material_filter and block.block_type not in material_filter:
            continue
        
        block_mesh = extract_block_mesh(block)
        meshes.append(block_mesh)
        
        # Add channels if requested
        if include_channels:
            # Fuel channels
            for channel in block.fuel_channels:
                channel_mesh = extract_fuel_channel_mesh(channel)
                meshes.append(channel_mesh)
            
            # Coolant channels
            for channel in block.coolant_channels:
                channel_mesh = extract_coolant_channel_mesh(channel)
                meshes.append(channel_mesh)
    
    if not meshes:
        # Return empty mesh
        return Mesh3D(
            vertices=np.array([]).reshape(0, 3),
            faces=None,
            cells=None,
        )
    
    # Combine all meshes
    return combine_meshes(meshes)


def extract_pebble_bed_volume_mesh(
    core: PebbleBedCore,
    material_filter: Optional[List[str]] = None,
) -> Mesh3D:
    """
    Extract volume mesh for a pebble bed core.
    
    Args:
        core: PebbleBedCore instance
        material_filter: Optional list of material IDs to include
    
    Returns:
        Mesh3D instance
    """
    meshes = []
    
    # Extract pebble meshes
    for pebble in core.pebbles:
        # Apply material filter if specified
        if material_filter:
            material_id = pebble.material_region.material_id if pebble.material_region else "pebble"
            if material_id not in material_filter:
                continue
        
        pebble_mesh = extract_pebble_mesh(pebble)
        meshes.append(pebble_mesh)
    
    if not meshes:
        return Mesh3D(
            vertices=np.array([]).reshape(0, 3),
            faces=None,
            cells=None,
        )
    
    return combine_meshes(meshes)


def extract_material_boundaries(
    core: PrismaticCore,
) -> List[Surface]:
    """
    Extract surfaces at material boundaries.
    
    Args:
        core: PrismaticCore instance
    
    Returns:
        List of Surface instances, one per material boundary
    """
    # Group blocks by material type
    material_groups: Dict[str, List[GraphiteBlock]] = {}
    
    for block in core.blocks:
        material_id = block.block_type
        if material_id not in material_groups:
            material_groups[material_id] = []
        material_groups[material_id].append(block)
    
    # Extract surfaces for each material group
    surfaces = []
    
    for material_id, blocks in material_groups.items():
        meshes = [extract_block_mesh(block) for block in blocks]
        if meshes:
            combined_mesh = combine_meshes(meshes)
            
            # Convert to surface (use faces)
            if combined_mesh.faces is not None:
                surface = Surface(
                    vertices=combined_mesh.vertices,
                    faces=combined_mesh.faces,
                    material_id=material_id,
                    surface_type="material_interface",
                )
                surfaces.append(surface)
    
    return surfaces


def add_flux_to_mesh(
    mesh: Mesh3D,
    flux: np.ndarray,
    geometry: PrismaticCore,
    group: int = 0,
) -> Mesh3D:
    """
    Add flux data to mesh cells.
    
    Args:
        mesh: Mesh3D instance
        flux: Flux array [nz, nr, ng] or [n_blocks, ng]
        geometry: PrismaticCore instance
        group: Energy group index
    
    Returns:
        Mesh3D with flux data added
    """
    # Map flux to mesh cells
    # This is simplified - in practice, would need proper spatial mapping
    if mesh.cells is None:
        return mesh
    
    # For now, assign average flux per block
    if flux.ndim == 3:
        # [nz, nr, ng] - need to map to blocks
        flux_1d = flux[:, :, group].flatten()
    else:
        flux_1d = flux[:, group] if flux.ndim == 2 else flux
    
    # Assign flux to cells (simplified - would need proper mapping)
    n_cells = mesh.n_cells
    if len(flux_1d) >= n_cells:
        cell_flux = flux_1d[:n_cells]
    else:
        # Repeat or interpolate
        cell_flux = np.tile(flux_1d, (n_cells // len(flux_1d) + 1))[:n_cells]
    
    mesh.add_cell_data("flux", cell_flux)
    
    return mesh


def add_power_to_mesh(
    mesh: Mesh3D,
    power: np.ndarray,
    geometry: PrismaticCore,
) -> Mesh3D:
    """
    Add power data to mesh cells.
    
    Args:
        mesh: Mesh3D instance
        power: Power array [nz, nr] or [n_blocks]
        geometry: PrismaticCore instance
    
    Returns:
        Mesh3D with power data added
    """
    if mesh.cells is None:
        return mesh
    
    # Map power to mesh cells
    power_1d = power.flatten() if power.ndim > 1 else power
    
    n_cells = mesh.n_cells
    if len(power_1d) >= n_cells:
        cell_power = power_1d[:n_cells]
    else:
        cell_power = np.tile(power_1d, (n_cells // len(power_1d) + 1))[:n_cells]
    
    mesh.add_cell_data("power", cell_power)
    
    return mesh

