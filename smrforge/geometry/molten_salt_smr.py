"""
Molten Salt Reactor (MSR) SMR geometry support.

Provides geometry components for Molten Salt Small Modular Reactors:
- Molten salt channels (liquid fuel/coolant)
- Graphite moderator blocks (for thermal MSRs)
- Fuel salt circulation loops
- Freeze plugs (safety systems)
- MSR core geometry
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import numpy as np

from ..utils.logging import get_logger
from .core_geometry import Point3D

logger = get_logger("smrforge.geometry.molten_salt_smr")


class MSRType(Enum):
    """Types of Molten Salt Reactors."""

    LIQUID_FUEL = "liquid_fuel"  # Fuel dissolved in salt
    SOLID_FUEL = "solid_fuel"  # Fuel in graphite, salt coolant
    FAST = "fast"  # Fast spectrum MSR (no moderator)
    THERMAL = "thermal"  # Thermal spectrum MSR (graphite moderator)


@dataclass
class MoltenSaltChannel:
    """
    Molten salt channel for MSR SMRs.

    Represents a flow path for molten salt (fuel salt or coolant salt).
    In liquid fuel MSRs, the salt contains dissolved fuel.
    In solid fuel MSRs, the salt is pure coolant.

    Attributes:
        id: Unique identifier
        position: Center position
        inner_radius: Inner radius [cm]
        outer_radius: Outer radius [cm]
        height: Channel height [cm]
        salt_type: Salt type ("fuel_salt", "coolant_salt")
        salt_composition: Salt composition (e.g., "FLiBe", "NaCl")
        temperature: Salt temperature [K]
        mass_flow_rate: Mass flow rate [kg/s]
        fuel_dissolved: True if fuel is dissolved in salt (liquid fuel MSR)
        fuel_concentration: Fuel concentration [g/L] (if fuel_dissolved)
    """

    id: int
    position: Point3D
    inner_radius: float  # cm
    outer_radius: float  # cm
    height: float  # cm
    salt_type: str = "fuel_salt"  # "fuel_salt" or "coolant_salt"
    salt_composition: str = "FLiBe"  # FLiBe, NaCl, etc.
    temperature: float = 973.15  # K (700°C typical MSR)
    mass_flow_rate: float = 0.0  # kg/s
    fuel_dissolved: bool = True  # True for liquid fuel MSR
    fuel_concentration: float = 0.0  # g/L (if fuel_dissolved)

    def flow_area(self) -> float:
        """Calculate flow area [cm²]."""
        return np.pi * self.inner_radius**2

    def volume(self) -> float:
        """Calculate channel volume [cm³]."""
        return self.flow_area() * self.height

    def fuel_mass(self) -> float:
        """Calculate fuel mass in channel [g]."""
        if self.fuel_dissolved:
            return self.fuel_concentration * self.volume() / 1000.0  # Convert L to cm³
        return 0.0


@dataclass
class GraphiteModeratorBlock:
    """
    Graphite moderator block for thermal MSRs.

    Used in thermal MSRs to moderate neutrons.
    Blocks are typically hexagonal or square.

    Attributes:
        id: Unique identifier
        position: Center position
        shape: Block shape ("hexagonal", "square", "circular")
        size: Block size [cm] (hex pitch, square side, or radius)
        height: Block height [cm]
        salt_channels: List of salt channels passing through block
        graphite_density: Graphite density [g/cm³]
    """

    id: int
    position: Point3D
    shape: str = "hexagonal"  # "hexagonal", "square", "circular"
    size: float = 20.0  # cm (hex pitch, square side, or radius)
    height: float = 400.0  # cm
    salt_channels: List[MoltenSaltChannel] = field(default_factory=list)
    graphite_density: float = 1.7  # g/cm³

    def volume(self) -> float:
        """Calculate block volume [cm³]."""
        if self.shape == "hexagonal":
            # Hexagonal volume = (3√3/2) * a² * h, where a is half the pitch
            a = self.size / 2.0
            base_area = (3.0 * np.sqrt(3.0) / 2.0) * a**2
        elif self.shape == "square":
            base_area = self.size**2
        elif self.shape == "circular":
            base_area = np.pi * self.size**2
        else:
            base_area = self.size**2  # Default to square

        return base_area * self.height

    def mass(self) -> float:
        """Calculate block mass [g]."""
        return self.volume() * self.graphite_density


@dataclass
class FreezePlug:
    """
    Freeze plug for MSR safety systems.

    Freeze plugs are passive safety systems that melt if temperature
    rises too high, allowing fuel salt to drain to a safe storage tank.

    Attributes:
        id: Unique identifier
        position: Position in drain line
        diameter: Plug diameter [cm]
        thickness: Plug thickness [cm]
        material: Plug material (typically same as salt)
        freeze_temperature: Temperature at which plug freezes [K]
        melt_temperature: Temperature at which plug melts [K]
        current_temperature: Current temperature [K]
        is_frozen: True if plug is currently frozen
    """

    id: int
    position: Point3D
    diameter: float  # cm
    thickness: float  # cm
    material: str = "FLiBe"  # Salt material
    freeze_temperature: float = 733.15  # K (460°C, typical FLiBe)
    melt_temperature: float = 873.15  # K (600°C, typical FLiBe)
    current_temperature: float = 733.15  # K
    is_frozen: bool = True

    def check_melt_condition(self) -> bool:
        """
        Check if plug should melt based on temperature.

        Returns:
            True if plug should melt (temperature > melt_temperature)
        """
        if self.current_temperature > self.melt_temperature:
            self.is_frozen = False
            return True
        elif self.current_temperature < self.freeze_temperature:
            self.is_frozen = True
            return False
        return not self.is_frozen

    def volume(self) -> float:
        """Calculate plug volume [cm³]."""
        return np.pi * (self.diameter / 2) ** 2 * self.thickness


@dataclass
class SaltCirculationLoop:
    """
    Salt circulation loop for MSR.

    Represents a complete circulation loop including:
    - Core channels
    - Heat exchangers
    - Pumps
    - Piping

    Attributes:
        id: Unique identifier
        name: Loop name
        channels: List of salt channels in loop
        heat_exchangers: List of heat exchanger positions
        pump_positions: List of pump positions
        total_flow_rate: Total flow rate [kg/s]
        loop_type: Loop type ("primary", "secondary", "drain")
    """

    id: int
    name: str
    channels: List[MoltenSaltChannel] = field(default_factory=list)
    heat_exchangers: List[Point3D] = field(default_factory=list)
    pump_positions: List[Point3D] = field(default_factory=list)
    total_flow_rate: float = 0.0  # kg/s
    loop_type: str = "primary"  # "primary", "secondary", "drain"

    def total_volume(self) -> float:
        """Calculate total loop volume [cm³]."""
        return sum(channel.volume() for channel in self.channels)

    def total_fuel_mass(self) -> float:
        """Calculate total fuel mass in loop [g]."""
        return sum(channel.fuel_mass() for channel in self.channels)


class MSRSMRCore:
    """
    Molten Salt Reactor Small Modular Reactor core.

    Represents an MSR SMR core with liquid or solid fuel.
    Supports both fast and thermal spectrum designs.

    Attributes:
        name: Core name
        msr_type: MSR type (liquid_fuel, solid_fuel, fast, thermal)
        salt_channels: List of salt channels
        graphite_blocks: List of graphite moderator blocks (thermal MSRs)
        circulation_loops: List of salt circulation loops
        freeze_plugs: List of freeze plugs
        core_height: Core height [cm]
        core_diameter: Core diameter [cm]
        salt_composition: Primary salt composition
    """

    def __init__(
        self,
        name: str = "MSR-SMR",
        msr_type: MSRType = MSRType.LIQUID_FUEL,
    ):
        """Initialize MSR SMR core."""
        self.name = name
        self.msr_type = msr_type
        self.salt_channels: List[MoltenSaltChannel] = []
        self.graphite_blocks: List[GraphiteModeratorBlock] = []
        self.circulation_loops: List[SaltCirculationLoop] = []
        self.freeze_plugs: List[FreezePlug] = []
        self.core_height: float = 400.0  # cm
        self.core_diameter: float = 300.0  # cm
        self.salt_composition: str = "FLiBe"  # FLiBe, NaCl, etc.

        # Mesh for neutronics
        self.radial_mesh: Optional[np.ndarray] = None
        self.axial_mesh: Optional[np.ndarray] = None

        # Temperature distribution
        self.temperature_field: Optional[np.ndarray] = None

    def add_salt_channel(self, channel: MoltenSaltChannel) -> None:
        """
        Add a salt channel to the core.

        Args:
            channel: MoltenSaltChannel instance to add
        """
        self.salt_channels.append(channel)

    def add_graphite_block(self, block: GraphiteModeratorBlock) -> None:
        """
        Add a graphite moderator block (for thermal MSRs).

        Args:
            block: GraphiteModeratorBlock instance to add
        """
        self.graphite_blocks.append(block)

    def add_circulation_loop(self, loop: SaltCirculationLoop) -> None:
        """
        Add a salt circulation loop.

        Args:
            loop: SaltCirculationLoop instance to add
        """
        self.circulation_loops.append(loop)

    def add_freeze_plug(self, plug: FreezePlug) -> None:
        """
        Add a freeze plug.

        Args:
            plug: FreezePlug instance to add
        """
        self.freeze_plugs.append(plug)

    def build_liquid_fuel_core(
        self,
        n_channels: int = 100,
        channel_radius: float = 5.0,  # cm
        channel_pitch: float = 15.0,  # cm
        core_height: float = 400.0,  # cm
        fuel_concentration: float = 1.0,  # g/L
    ):
        """
        Build liquid fuel MSR core.

        Liquid fuel MSRs have fuel dissolved in the salt.
        No solid fuel elements - fuel flows with the salt.

        Args:
            n_channels: Number of fuel salt channels
            channel_radius: Channel radius [cm]
            channel_pitch: Channel pitch (center-to-center) [cm]
            core_height: Core height [cm]
            fuel_concentration: Fuel concentration [g/L]
        """
        self.msr_type = MSRType.LIQUID_FUEL
        self.core_height = core_height

        # Create channels in hexagonal pattern
        n_rings = int(np.sqrt(n_channels / np.pi)) + 1

        channel_id = 0
        for ring in range(n_rings):
            n_in_ring = 6 * ring if ring > 0 else 1

            for i in range(n_in_ring):
                if channel_id >= n_channels:
                    break

                angle = 2 * np.pi * i / n_in_ring if n_in_ring > 0 else 0
                radius = ring * channel_pitch

                x = radius * np.cos(angle)
                y = radius * np.sin(angle)

                channel = MoltenSaltChannel(
                    id=channel_id,
                    position=Point3D(x, y, core_height / 2),
                    inner_radius=channel_radius,
                    outer_radius=channel_radius + 0.5,  # Wall thickness
                    height=core_height,
                    salt_type="fuel_salt",
                    fuel_dissolved=True,
                    fuel_concentration=fuel_concentration,
                )

                self.add_salt_channel(channel)
                channel_id += 1

        # Calculate core diameter
        self.core_diameter = 2 * (n_rings - 1) * channel_pitch + 2 * channel_radius

        logger.info(
            f"Built liquid fuel MSR core: {len(self.salt_channels)} channels, "
            f"diameter={self.core_diameter:.1f} cm"
        )

    def build_thermal_msr_core(
        self,
        n_blocks: int = 37,
        block_size: float = 20.0,  # cm
        block_height: float = 400.0,  # cm
        n_channels_per_block: int = 7,
        channel_radius: float = 2.0,  # cm
    ):
        """
        Build thermal MSR core with graphite moderator.

        Thermal MSRs use graphite blocks to moderate neutrons.
        Salt flows through channels in the graphite blocks.

        Args:
            n_blocks: Number of graphite blocks
            block_size: Block size [cm]
            block_height: Block height [cm]
            n_channels_per_block: Number of salt channels per block
            channel_radius: Salt channel radius [cm]
        """
        self.msr_type = MSRType.THERMAL
        self.core_height = block_height

        # Create graphite blocks in hexagonal pattern
        n_rings = int(np.sqrt(n_blocks / np.pi)) + 1

        block_id = 0
        for ring in range(n_rings):
            n_in_ring = 6 * ring if ring > 0 else 1

            for i in range(n_in_ring):
                if block_id >= n_blocks:
                    break

                angle = 2 * np.pi * i / n_in_ring if n_in_ring > 0 else 0
                radius = ring * block_size * 1.2  # Spacing

                x = radius * np.cos(angle)
                y = radius * np.sin(angle)

                # Create graphite block
                block = GraphiteModeratorBlock(
                    id=block_id,
                    position=Point3D(x, y, block_height / 2),
                    shape="hexagonal",
                    size=block_size,
                    height=block_height,
                )

                # Add salt channels to block
                for ch in range(n_channels_per_block):
                    ch_angle = 2 * np.pi * ch / n_channels_per_block
                    ch_radius = block_size * 0.3
                    ch_x = x + ch_radius * np.cos(ch_angle)
                    ch_y = y + ch_radius * np.sin(ch_angle)

                    channel = MoltenSaltChannel(
                        id=block_id * n_channels_per_block + ch,
                        position=Point3D(ch_x, ch_y, block_height / 2),
                        inner_radius=channel_radius,
                        outer_radius=channel_radius + 0.2,
                        height=block_height,
                        salt_type="coolant_salt",
                        fuel_dissolved=False,  # Solid fuel MSR
                    )

                    block.salt_channels.append(channel)
                    self.add_salt_channel(channel)

                self.add_graphite_block(block)
                block_id += 1

        # Calculate core diameter
        self.core_diameter = 2 * (n_rings - 1) * block_size * 1.2 + block_size

        logger.info(
            f"Built thermal MSR core: {len(self.graphite_blocks)} blocks, "
            f"{len(self.salt_channels)} channels, diameter={self.core_diameter:.1f} cm"
        )

    def get_total_fuel_mass(self) -> float:
        """Get total fuel mass in core [g]."""
        return sum(channel.fuel_mass() for channel in self.salt_channels)

    def get_total_salt_volume(self) -> float:
        """Get total salt volume in core [cm³]."""
        return sum(channel.volume() for channel in self.salt_channels)

    def check_freeze_plugs(self) -> Dict[int, bool]:
        """
        Check freeze plug status.

        Returns:
            Dictionary mapping plug ID to melt status (True = melted)
        """
        status = {}
        for plug in self.freeze_plugs:
            status[plug.id] = plug.check_melt_condition()
        return status


def create_liquid_fuel_msr_core() -> MSRSMRCore:
    """
    Create a typical liquid fuel MSR SMR core.

    Returns:
        MSRSMRCore configured for liquid fuel design
    """
    core = MSRSMRCore(name="Liquid-Fuel-MSR", msr_type=MSRType.LIQUID_FUEL)
    core.build_liquid_fuel_core(
        n_channels=100,
        channel_radius=5.0,  # cm
        channel_pitch=15.0,  # cm
        core_height=400.0,  # cm
        fuel_concentration=1.0,  # g/L
    )
    return core


def create_thermal_msr_core() -> MSRSMRCore:
    """
    Create a typical thermal MSR SMR core with graphite moderator.

    Returns:
        MSRSMRCore configured for thermal design
    """
    core = MSRSMRCore(name="Thermal-MSR", msr_type=MSRType.THERMAL)
    core.build_thermal_msr_core(
        n_blocks=37,
        block_size=20.0,  # cm
        block_height=400.0,  # cm
        n_channels_per_block=7,
        channel_radius=2.0,  # cm
    )
    return core
