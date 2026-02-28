"""
Parametric geometry builders for common SMR elements (Community tier).

Provides simple Python API to create fuel pins, moderator blocks, and related
elements for rapid SMR design iteration without CAD. Lowers entry barriers
for academia and labs.
"""

from typing import List, Optional, Tuple

import numpy as np

from .core_geometry import (
    CoolantChannel,
    FuelChannel,
    GraphiteBlock,
    MaterialRegion,
    Point3D,
    PrismaticCore,
)


def create_fuel_pin(
    radius: float = 0.41,
    height: float = 365.0,
    cladding_radius: Optional[float] = None,
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    power_density: float = 0.0,
    material_id: str = "UO2",
    pin_id: int = 0,
) -> FuelChannel:
    """
    Create a parametric fuel pin (LWR/SMR style).

    Typical SMR fuel pin: radius ~0.41 cm, cladding ~0.48 cm, height 200-400 cm.

    Args:
        radius: Fuel pellet radius [cm]
        height: Active fuel height [cm]
        cladding_radius: Outer cladding radius [cm]; defaults to radius + 0.06
        position: (x, y, z) center position [cm]
        power_density: Power density [W/cm³]
        material_id: Material identifier (for reference)
        pin_id: Unique pin identifier

    Returns:
        FuelChannel instance

    Example:
        >>> from smrforge.geometry.parametric_builders import create_fuel_pin
        >>> pin = create_fuel_pin(radius=0.41, height=200.0)
    """
    if cladding_radius is None:
        cladding_radius = radius + 0.06  # Typical gap + cladding
    pt = Point3D(position[0], position[1], position[2])
    # Placeholder material; real composition comes from XS setup
    mat = MaterialRegion(
        material_id=material_id,
        composition={"U235": 1e-3, "U238": 1e-2},
        temperature=900.0,
        density=10.0,
        volume=np.pi * radius**2 * height,
    )
    return FuelChannel(
        id=pin_id,
        position=pt,
        radius=radius,
        height=height,
        material_region=mat,
        power_density=power_density,
    )


def create_moderator_block(
    flat_to_flat: float = 36.0,
    height: float = 80.0,
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    block_type: str = "reflector",
    block_id: int = 0,
) -> GraphiteBlock:
    """
    Create a parametric moderator/reflector block (HTGR style).

    Hexagonal graphite block for thermal moderation and neutron reflection.

    Args:
        flat_to_flat: Hexagon flat-to-flat distance [cm]
        height: Block height [cm]
        position: (x, y, z) center position [cm]
        block_type: 'reflector', 'moderator', or 'control'
        block_id: Unique block identifier

    Returns:
        GraphiteBlock instance

    Example:
        >>> from smrforge.geometry.parametric_builders import create_moderator_block
        >>> block = create_moderator_block(flat_to_flat=36.0, height=80.0)
    """
    pt = Point3D(position[0], position[1], position[2])
    mat = MaterialRegion(
        material_id="Graphite",
        composition={"C0": 8.0e-2},
        temperature=900.0,
        density=1.85,
        volume=flat_to_flat**2 * np.sqrt(3) / 2 * height,
    )
    return GraphiteBlock(
        id=block_id,
        position=pt,
        flat_to_flat=flat_to_flat,
        height=height,
        moderator_material=mat,
        block_type=block_type,
    )


def create_rectangular_fuel_lattice(
    nx: int = 17,
    ny: int = 17,
    pitch: float = 1.26,
    pin_radius: float = 0.41,
    height: float = 200.0,
    origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> List[FuelChannel]:
    """
    Create a rectangular lattice of fuel pins (PWR/BWR SMR style).

    Args:
        nx: Number of pins in x
        ny: Number of pins in y
        pitch: Pin-to-pin pitch [cm]
        pin_radius: Fuel pin radius [cm]
        height: Active fuel height [cm]
        origin: (x, y, z) of lower-left pin center

    Returns:
        List of FuelChannel instances

    Example:
        >>> pins = create_rectangular_fuel_lattice(nx=10, ny=10, pitch=1.26)
    """
    pins: List[FuelChannel] = []
    pin_id = 0
    ox, oy, oz = origin
    for iy in range(ny):
        for ix in range(nx):
            x = ox + ix * pitch
            y = oy + iy * pitch
            z = oz + height / 2
            pin = create_fuel_pin(
                radius=pin_radius,
                height=height,
                position=(x, y, z),
                pin_id=pin_id,
            )
            pins.append(pin)
            pin_id += 1
    return pins


def create_hexagonal_moderator_ring(
    n_blocks: int = 6,
    flat_to_flat: float = 36.0,
    height: float = 80.0,
    ring_radius: float = 50.0,
    z_center: float = 40.0,
) -> List[GraphiteBlock]:
    """
    Create a ring of moderator blocks around a core (HTGR reflector).

    Args:
        n_blocks: Number of blocks in the ring
        flat_to_flat: Block flat-to-flat [cm]
        height: Block height [cm]
        ring_radius: Radius to block centers [cm]
        z_center: Axial center [cm]

    Returns:
        List of GraphiteBlock instances

    Example:
        >>> blocks = create_hexagonal_moderator_ring(n_blocks=6)
    """
    blocks: List[GraphiteBlock] = []
    for i in range(n_blocks):
        angle = 2 * np.pi * i / n_blocks
        x = ring_radius * np.cos(angle)
        y = ring_radius * np.sin(angle)
        block = create_moderator_block(
            flat_to_flat=flat_to_flat,
            height=height,
            position=(x, y, z_center),
            block_type="reflector",
            block_id=i,
        )
        blocks.append(block)
    return blocks


def create_simple_prismatic_core(
    n_rings: int = 2,
    block_flat_to_flat: float = 36.0,
    block_height: float = 80.0,
    pitch: float = 38.0,
    name: str = "Parametric-SMR",
) -> PrismaticCore:
    """
    Create a simple prismatic core from parametric moderator blocks (Community).

    Builds a hexagonal lattice of reflector blocks. Add fuel channels via
    PrismaticCore API or use create_fuel_pin/create_rectangular_fuel_lattice
    for pin-level detail.

    Args:
        n_rings: Number of hexagonal rings
        block_flat_to_flat: Block flat-to-flat [cm]
        block_height: Block height [cm]
        pitch: Block-to-block pitch [cm]
        name: Core name

    Returns:
        PrismaticCore with blocks placed

    Example:
        >>> core = create_simple_prismatic_core(n_rings=2)
    """
    core = PrismaticCore(name=name)
    core.core_height = block_height
    core.core_diameter = 2 * (n_rings - 0.5) * pitch + block_flat_to_flat
    core.n_rings = n_rings
    core.lattice_pitch = pitch

    block_id = 0
    for ring in range(n_rings):
        if ring == 0:
            positions: List[Tuple[float, float]] = [(0.0, 0.0)]
        else:
            n_in_ring = 6 * ring
            positions = []
            for i in range(n_in_ring):
                angle = 2 * np.pi * i / n_in_ring
                radius = ring * pitch
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                positions.append((x, y))
        for x, y in positions:
            z = block_height / 2
            block_type = "reflector" if ring == n_rings - 1 else "fuel"
            block = create_moderator_block(
                flat_to_flat=block_flat_to_flat,
                height=block_height,
                position=(x, y, z),
                block_type=block_type,
                block_id=block_id,
            )
            core.blocks.append(block)
            block_id += 1

    return core
