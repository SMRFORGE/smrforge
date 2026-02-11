"""
Fast Reactor Small Modular Reactor (SMR) geometry support.

This module provides geometry classes for fast reactor SMRs including:
- Sodium-cooled fast reactor (SFR) cores
- Hexagonal fuel assemblies (different from HTGR hexagons)
- Wire-wrap spacers
- Liquid metal coolant channels
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import numpy as np

from .core_geometry import MaterialRegion, Point3D


class FastReactorType(Enum):
    """Types of fast reactor SMR designs."""

    SODIUM_COOLED = "sodium_cooled"  # SFR (Natrium, PRISM)
    LEAD_COOLED = "lead_cooled"  # LFR
    GAS_COOLED = "gas_cooled"  # GFR


@dataclass
class WireWrapSpacer:
    """
    Wire-wrap spacer for fast reactor fuel pins.

    Wire-wrap spacers are helical wires wrapped around fuel pins to maintain
    spacing and enhance heat transfer in liquid metal-cooled fast reactors.

    Attributes:
        id: Unique identifier
        wire_diameter: Wire diameter [cm]
        wire_pitch: Helical pitch (distance for one full turn) [cm]
        wire_material: Wire material (typically stainless steel)
        height: Height of wire-wrap region [cm]
    """

    id: int
    wire_diameter: float  # cm
    wire_pitch: float  # cm (helical pitch)
    wire_material: str = "StainlessSteel-316"
    height: float = 0.0  # cm

    def wire_length(self, pin_height: float) -> float:
        """
        Calculate total wire length for a given pin height.

        Args:
            pin_height: Fuel pin height [cm]

        Returns:
            Total wire length [cm]
        """
        if self.wire_pitch <= 0:
            return 0.0

        # Number of turns
        n_turns = pin_height / self.wire_pitch

        # Circumference per turn (approximate)
        circumference = np.pi * 0.96  # Assume ~0.96 cm pin diameter

        # Total length
        return n_turns * np.sqrt(circumference**2 + self.wire_pitch**2)


@dataclass
class FastReactorFuelPin:
    """
    Fuel pin for fast reactor SMR assemblies.

    Fast reactor pins are similar to LWR pins but optimized for fast neutron
    spectrum. Typically use MOX (mixed oxide) or metal fuel.

    Attributes:
        id: Unique identifier
        position: Center position relative to assembly origin
        fuel_radius: Fuel pellet radius [cm]
        cladding_radius: Outer cladding radius [cm]
        height: Active fuel height [cm]
        material_fuel: Fuel material (MOX or metal)
        material_clad: Cladding material (typically stainless steel)
        wire_wrap: Optional wire-wrap spacer
        enrichment: Pu-239 enrichment fraction (for MOX)
    """

    id: int
    position: Point3D
    fuel_radius: float  # cm
    cladding_radius: float  # cm
    height: float  # cm
    material_fuel: MaterialRegion
    material_clad: MaterialRegion
    wire_wrap: Optional[WireWrapSpacer] = None
    enrichment: float = 0.0  # Pu-239 fraction for MOX

    def fuel_volume(self) -> float:
        """Fuel volume [cm³]."""
        return np.pi * self.fuel_radius**2 * self.height

    def clad_volume(self) -> float:
        """Cladding volume [cm³]."""
        inner_radius = self.fuel_radius + 0.0082  # Gap
        return np.pi * (self.cladding_radius**2 - inner_radius**2) * self.height


@dataclass
class FastReactorAssembly:
    """
    Hexagonal fuel assembly for fast reactor SMRs.

    Fast reactor assemblies use hexagonal geometry (different from HTGR hexagons)
    with wire-wrap spacers. Used in sodium-cooled fast reactors like Natrium and PRISM.

    Attributes:
        id: Unique identifier
        position: Center position in core
        flat_to_flat: Hexagonal flat-to-flat distance [cm]
        height: Assembly height [cm]
        n_pins: Number of fuel pins in assembly
        pin_pitch: Pin pitch (center-to-center) [cm]
        fuel_pins: List of fuel pins
        wire_wrap_pitch: Wire-wrap helical pitch [cm]
        coolant_material: Coolant material (sodium, lead, etc.)
    """

    id: int
    position: Point3D
    flat_to_flat: float  # cm
    height: float  # cm
    n_pins: int
    pin_pitch: float  # cm
    fuel_pins: List[FastReactorFuelPin] = field(default_factory=list)
    wire_wrap_pitch: float = 30.0  # cm (typical for SFR)
    coolant_material: MaterialRegion = None

    def build_hexagonal_lattice(
        self,
        fuel_pin_params: Dict,
        coolant_material: MaterialRegion,
    ):
        """
        Build hexagonal lattice of fuel pins with wire-wrap spacers.

        Args:
            fuel_pin_params: Dictionary with fuel pin parameters
            coolant_material: Coolant material (sodium, lead, etc.)
        """
        self.coolant_material = coolant_material

        # Calculate number of rings
        # For hexagonal lattice: n_pins = 3*N*(N+1) + 1 where N is number of rings
        n_rings = int(np.sqrt(self.n_pins / 3))
        if 3 * n_rings * (n_rings + 1) + 1 < self.n_pins:
            n_rings += 1

        # Build pins in hexagonal pattern
        pin_id = 0
        for ring in range(n_rings):
            if pin_id >= self.n_pins:
                break

            if ring == 0:
                # Center pin
                pin = FastReactorFuelPin(
                    id=pin_id,
                    position=Point3D(0, 0, self.height / 2),
                    fuel_radius=fuel_pin_params.get("fuel_radius", 0.3),
                    cladding_radius=fuel_pin_params.get("cladding_radius", 0.35),
                    height=self.height,
                    material_fuel=fuel_pin_params.get("material_fuel"),
                    material_clad=fuel_pin_params.get("material_clad"),
                )

                # Add wire-wrap
                if self.wire_wrap_pitch > 0:
                    wire_wrap = WireWrapSpacer(
                        id=pin_id,
                        wire_diameter=0.1,  # cm
                        wire_pitch=self.wire_wrap_pitch,
                        height=self.height,
                    )
                    pin.wire_wrap = wire_wrap

                self.fuel_pins.append(pin)
                pin_id += 1
            else:
                # Ring pins
                n_pins_in_ring = 6 * ring
                angle_step = 2 * np.pi / n_pins_in_ring
                radius = ring * self.pin_pitch

                for i in range(n_pins_in_ring):
                    if pin_id >= self.n_pins:
                        break

                    angle = i * angle_step
                    x = radius * np.cos(angle)
                    y = radius * np.sin(angle)

                    pin = FastReactorFuelPin(
                        id=pin_id,
                        position=Point3D(x, y, self.height / 2),
                        fuel_radius=fuel_pin_params.get("fuel_radius", 0.3),
                        cladding_radius=fuel_pin_params.get("cladding_radius", 0.35),
                        height=self.height,
                        material_fuel=fuel_pin_params.get("material_fuel"),
                        material_clad=fuel_pin_params.get("material_clad"),
                    )

                    # Add wire-wrap
                    if self.wire_wrap_pitch > 0:
                        wire_wrap = WireWrapSpacer(
                            id=pin_id,
                            wire_diameter=0.1,
                            wire_pitch=self.wire_wrap_pitch,
                            height=self.height,
                        )
                        pin.wire_wrap = wire_wrap

                    self.fuel_pins.append(pin)
                    pin_id += 1

    def total_fuel_volume(self) -> float:
        """Total fuel volume in assembly [cm³]."""
        return sum(pin.fuel_volume() for pin in self.fuel_pins)

    def assembly_pitch(self) -> float:
        """Assembly pitch (center-to-center) [cm]."""
        return self.flat_to_flat * 1.1  # Approximate


@dataclass
class LiquidMetalChannel:
    """
    Liquid metal coolant channel for fast reactors.

    Represents sodium, lead, or other liquid metal coolant flow paths.

    Attributes:
        id: Unique identifier
        position: Center position
        flow_area: Flow area [cm²]
        height: Channel height [cm]
        temperature: Coolant temperature [K]
        mass_flow_rate: Mass flow rate [kg/s]
        coolant_type: Type of coolant ("sodium", "lead", "lead-bismuth")
    """

    id: int
    position: Point3D
    flow_area: float  # cm²
    height: float  # cm
    temperature: float = 773.15  # K (500°C typical SFR)
    mass_flow_rate: float = 0.0  # kg/s
    coolant_type: str = "sodium"  # "sodium", "lead", "lead-bismuth"


class FastReactorSMRCore:
    """
    Fast reactor SMR core geometry.

    Represents sodium-cooled fast reactor (SFR) SMR cores like Natrium and PRISM.
    Uses hexagonal fuel assemblies with wire-wrap spacers.

    Attributes:
        name: Core name
        reactor_type: Type of fast reactor
        assemblies: List of fuel assemblies
        core_height: Core height [cm]
        core_diameter: Core diameter [cm]
        assembly_pitch: Assembly pitch [cm]
        coolant_channels: List of liquid metal coolant channels
    """

    def __init__(
        self,
        name: str = "Fast-Reactor-SMR",
        reactor_type: FastReactorType = FastReactorType.SODIUM_COOLED,
    ):
        self.name = name
        self.reactor_type = reactor_type
        self.assemblies: List[FastReactorAssembly] = []
        self.core_height: float = 0.0  # cm
        self.core_diameter: float = 0.0  # cm
        self.assembly_pitch: float = 0.0  # cm
        self.coolant_channels: List[LiquidMetalChannel] = []

    def build_hexagonal_core_lattice(
        self,
        n_rings: int,
        assembly_pitch: float,
        assembly_height: float,
        assembly_flat_to_flat: float,
        n_pins_per_assembly: int,
        pin_pitch: float,
        fuel_pin_params: Dict,
        coolant_material: MaterialRegion,
    ):
        """
        Build hexagonal lattice of fast reactor assemblies.

        Args:
            n_rings: Number of hexagonal rings
            assembly_pitch: Assembly pitch [cm]
            assembly_height: Assembly height [cm]
            assembly_flat_to_flat: Assembly flat-to-flat [cm]
            n_pins_per_assembly: Number of pins per assembly
            pin_pitch: Pin pitch [cm]
            fuel_pin_params: Fuel pin parameters dictionary
            coolant_material: Coolant material
        """
        self.assembly_pitch = assembly_pitch
        self.core_height = assembly_height

        # Calculate core diameter
        self.core_diameter = 2 * n_rings * assembly_pitch

        assembly_id = 0

        # Build hexagonal lattice
        for ring in range(n_rings):
            if ring == 0:
                # Center assembly
                assembly = FastReactorAssembly(
                    id=assembly_id,
                    position=Point3D(0, 0, assembly_height / 2),
                    flat_to_flat=assembly_flat_to_flat,
                    height=assembly_height,
                    n_pins=n_pins_per_assembly,
                    pin_pitch=pin_pitch,
                )
                assembly.build_hexagonal_lattice(fuel_pin_params, coolant_material)
                self.assemblies.append(assembly)
                assembly_id += 1
            else:
                # Ring assemblies
                n_assemblies_in_ring = 6 * ring
                angle_step = 2 * np.pi / n_assemblies_in_ring
                radius = ring * assembly_pitch

                for i in range(n_assemblies_in_ring):
                    angle = i * angle_step
                    x = radius * np.cos(angle)
                    y = radius * np.sin(angle)

                    assembly = FastReactorAssembly(
                        id=assembly_id,
                        position=Point3D(x, y, assembly_height / 2),
                        flat_to_flat=assembly_flat_to_flat,
                        height=assembly_height,
                        n_pins=n_pins_per_assembly,
                        pin_pitch=pin_pitch,
                    )
                    assembly.build_hexagonal_lattice(fuel_pin_params, coolant_material)
                    self.assemblies.append(assembly)
                    assembly_id += 1

    def total_fuel_volume(self) -> float:
        """Total fuel volume in core [cm³]."""
        return sum(assembly.total_fuel_volume() for assembly in self.assemblies)

    def n_assemblies(self) -> int:
        """Number of assemblies in core."""
        return len(self.assemblies)
