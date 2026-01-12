# smrforge/geometry/lwr_smr.py
"""
Light Water Reactor (LWR) Small Modular Reactor (SMR) geometry support.

This module provides geometry classes for LWR-based SMRs including:
- Square lattice fuel assemblies
- Fuel rod arrays
- Water moderator/coolant channels
- Control rod clusters (PWR)
- Control blades (BWR)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

from .core_geometry import MaterialRegion, Point3D


class AssemblyType(Enum):
    """Types of fuel assemblies for LWR SMRs."""

    FUEL = "fuel"
    CONTROL = "control"
    INSTRUMENTATION = "instrumentation"
    BURNABLE_POISON = "burnable_poison"


@dataclass
class FuelRod:
    """
    Individual fuel rod for LWR SMR assemblies.
    
    Represents a cylindrical fuel pin with fuel pellets, cladding, and gap.
    Used in square lattice fuel assemblies for PWR and BWR SMRs.
    
    Attributes:
        id: Unique identifier for the fuel rod
        position: Center position of the rod (x, y, z)
        fuel_radius: Fuel pellet radius [cm]
        cladding_radius: Outer cladding radius [cm]
        gap_thickness: Gap between fuel and cladding [cm]
        height: Active fuel height [cm]
        material_region: Fuel material composition
        enrichment: U-235 enrichment fraction (e.g., 0.045 for 4.5%)
        burnup: Current burnup [MWd/kg]
        power_density: Power density [W/cm³]
    """

    id: int
    position: Point3D
    fuel_radius: float  # cm
    cladding_radius: float  # cm
    gap_thickness: float = 0.0082  # cm (typical gap)
    height: float = 365.76  # cm (12 feet, typical PWR)
    material_region: Optional[MaterialRegion] = None
    enrichment: float = 0.045  # 4.5% typical for PWR
    burnup: float = 0.0  # MWd/kg
    power_density: float = 0.0  # W/cm³

    def fuel_volume(self) -> float:
        """Volume of fuel pellets."""
        return np.pi * self.fuel_radius**2 * self.height

    def cladding_volume(self) -> float:
        """Volume of cladding material."""
        inner_radius = self.fuel_radius + self.gap_thickness
        return np.pi * (self.cladding_radius**2 - inner_radius**2) * self.height

    def total_volume(self) -> float:
        """Total rod volume (cladding outer radius)."""
        return np.pi * self.cladding_radius**2 * self.height

    def power(self) -> float:
        """Total power in rod [W]."""
        return self.power_density * self.fuel_volume()


@dataclass
class SpacerGrid:
    """
    Spacer grid for fuel assembly support.
    
    Provides structural support and maintains fuel rod spacing in LWR assemblies.
    
    Attributes:
        id: Unique identifier
        z_position: Axial position [cm]
        grid_type: Type of spacer grid (e.g., "spring", "rigid")
        n_rods: Number of rods supported
    """

    id: int
    z_position: float  # cm
    grid_type: str = "spring"  # "spring", "rigid", "hybrid"
    n_rods: int = 0


@dataclass
class FuelAssembly:
    """
    Square lattice fuel assembly for LWR SMRs.
    
    Represents a fuel assembly with square lattice arrangement of fuel rods.
    Used in PWR and BWR SMRs (e.g., NuScale 17x17, mPower 15x15).
    
    Attributes:
        id: Unique identifier
        position: Center position of assembly (x, y, z)
        assembly_type: Type of assembly (fuel, control, etc.)
        lattice_size: Square lattice size (e.g., 17 for 17x17)
        pitch: Rod-to-rod pitch [cm]
        height: Assembly height [cm]
        fuel_rods: List of fuel rods in assembly
        spacer_grids: List of spacer grids
        guide_tubes: Positions for control rods or instrumentation
        water_fraction: Volume fraction of water in assembly
    """

    id: int
    position: Point3D
    assembly_type: AssemblyType = AssemblyType.FUEL
    lattice_size: int = 17  # 17x17 typical for NuScale
    pitch: float = 1.26  # cm (typical PWR pitch)
    height: float = 365.76  # cm (12 feet)
    fuel_rods: List[FuelRod] = field(default_factory=list)
    spacer_grids: List[SpacerGrid] = field(default_factory=list)
    guide_tubes: List[Point3D] = field(default_factory=list)
    water_fraction: float = 0.4  # Typical water fraction in PWR assembly

    def n_rods(self) -> int:
        """Total number of fuel rod positions."""
        return self.lattice_size * self.lattice_size

    def assembly_pitch(self) -> float:
        """Assembly-to-assembly pitch [cm]."""
        # Typical PWR: ~21.5 cm
        return self.lattice_size * self.pitch * 1.1  # Add 10% for structure

    def total_fuel_volume(self) -> float:
        """Total fuel volume in assembly."""
        return sum(rod.fuel_volume() for rod in self.fuel_rods)

    def total_power(self) -> float:
        """Total power in assembly [W]."""
        return sum(rod.power() for rod in self.fuel_rods)

    def build_square_lattice(
        self,
        fuel_rod_radius: float = 0.4096,  # cm (typical PWR)
        cladding_thickness: float = 0.05715,  # cm
        enrichment: float = 0.045,
        guide_tube_positions: Optional[List[Tuple[int, int]]] = None,
    ):
        """
        Build square lattice of fuel rods in assembly.
        
        Args:
            fuel_rod_radius: Outer radius of fuel rod [cm]
            cladding_thickness: Cladding wall thickness [cm]
            enrichment: U-235 enrichment fraction
            guide_tube_positions: List of (i, j) positions for guide tubes
                (control rod or instrumentation positions)
        """
        self.fuel_rods.clear()
        self.guide_tubes.clear()

        rod_id = 0
        cladding_radius = fuel_rod_radius
        fuel_radius = cladding_radius - cladding_thickness - 0.0082  # gap

        # Build square lattice
        for i in range(self.lattice_size):
            for j in range(self.lattice_size):
                # Calculate rod position in assembly-local coordinates
                x_local = (i - (self.lattice_size - 1) / 2) * self.pitch
                y_local = (j - (self.lattice_size - 1) / 2) * self.pitch

                # Convert to global coordinates
                x = self.position.x + x_local
                y = self.position.y + y_local
                z = self.position.z

                rod_position = Point3D(x, y, z)

                # Check if this is a guide tube position
                is_guide_tube = guide_tube_positions and (i, j) in guide_tube_positions

                if is_guide_tube:
                    # Store guide tube position
                    self.guide_tubes.append(rod_position)
                else:
                    # Create fuel rod
                    rod = FuelRod(
                        id=rod_id,
                        position=rod_position,
                        fuel_radius=fuel_radius,
                        cladding_radius=cladding_radius,
                        height=self.height,
                        enrichment=enrichment,
                    )
                    self.fuel_rods.append(rod)
                    rod_id += 1

        # Add typical spacer grids (every ~50 cm)
        n_grids = int(self.height / 50.0) + 1
        for i in range(n_grids):
            z_pos = i * (self.height / n_grids)
            grid = SpacerGrid(
                id=i,
                z_position=z_pos,
                n_rods=len(self.fuel_rods),
            )
            self.spacer_grids.append(grid)


@dataclass
class WaterChannel:
    """
    Water moderator/coolant channel for LWR SMRs.
    
    Represents water flow paths in LWR cores (PWR or BWR).
    
    Attributes:
        id: Unique identifier
        position: Center position
        flow_area: Flow area [cm²]
        height: Channel height [cm]
        temperature: Water temperature [K]
        pressure: Pressure [Pa]
        mass_flow_rate: Mass flow rate [kg/s]
        void_fraction: Void fraction (for two-phase flow, BWR)
    """

    id: int
    position: Point3D
    flow_area: float  # cm²
    height: float  # cm
    temperature: float = 573.15  # K (300°C typical PWR)
    pressure: float = 15.5e6  # Pa (15.5 MPa typical PWR)
    mass_flow_rate: float = 0.0  # kg/s
    void_fraction: float = 0.0  # For two-phase (BWR)


@dataclass
class ControlRodCluster:
    """
    Control rod cluster assembly (RCCA) for PWR SMRs.
    
    Represents a cluster of control rods that insert together.
    Used in PWR designs (e.g., NuScale, mPower).
    
    Attributes:
        id: Unique identifier
        position: Center position of cluster
        n_rods: Number of control rods in cluster
        rod_radius: Control rod radius [cm]
        height: Rod length [cm]
        insertion: Current insertion fraction (0.0 = fully withdrawn, 1.0 = fully inserted)
        worth: Reactivity worth [dk/k]
    """

    id: int
    position: Point3D
    n_rods: int = 20  # Typical PWR cluster
    rod_radius: float = 0.48  # cm
    height: float = 365.76  # cm
    insertion: float = 0.0  # 0.0 = out, 1.0 = in
    worth: float = 0.0  # dk/k


@dataclass
class ControlBlade:
    """
    Control blade for BWR SMRs.
    
    Represents a cruciform control blade used in BWR designs.
    
    Attributes:
        id: Unique identifier
        position: Center position
        width: Blade width [cm]
        thickness: Blade thickness [cm]
        height: Blade length [cm]
        insertion: Current insertion fraction
        worth: Reactivity worth [dk/k]
    """

    id: int
    position: Point3D
    width: float = 5.0  # cm
    thickness: float = 0.5  # cm
    height: float = 365.76  # cm
    insertion: float = 0.0
    worth: float = 0.0


class PWRSMRCore:
    """
    Pressurized Water Reactor (PWR) Small Modular Reactor core.
    
    Represents a PWR-based SMR core with square lattice fuel assemblies.
    Suitable for modeling NuScale, mPower, CAREM, SMR-160, etc.
    
    Attributes:
        name: Core name
        assemblies: List of fuel assemblies
        control_rod_clusters: List of control rod clusters
        core_height: Core height [cm]
        core_diameter: Core diameter [cm]
        assembly_pitch: Assembly-to-assembly pitch [cm]
        n_assemblies: Number of fuel assemblies
        water_channels: Water moderator/coolant channels
    """

    def __init__(self, name: str = "PWR-SMR"):
        self.name = name
        self.assemblies: List[FuelAssembly] = []
        self.control_rod_clusters: List[ControlRodCluster] = []
        self.core_height: float = 0.0  # cm
        self.core_diameter: float = 0.0  # cm
        self.assembly_pitch: float = 21.5  # cm (typical PWR)
        self.n_assemblies: int = 0
        self.water_channels: List[WaterChannel] = []

        # Mesh for neutronics
        self.radial_mesh: Optional[np.ndarray] = None
        self.axial_mesh: Optional[np.ndarray] = None

        # Temperature distribution
        self.temperature_field: Optional[np.ndarray] = None

    def build_square_lattice_core(
        self,
        n_assemblies_x: int,
        n_assemblies_y: int,
        assembly_pitch: float = 21.5,  # cm
        assembly_height: float = 365.76,  # cm
        lattice_size: int = 17,  # 17x17 for NuScale
        rod_pitch: float = 1.26,  # cm
    ):
        """
        Build square lattice core of fuel assemblies.
        
        Args:
            n_assemblies_x: Number of assemblies in x-direction
            n_assemblies_y: Number of assemblies in y-direction
            assembly_pitch: Assembly-to-assembly pitch [cm]
            assembly_height: Assembly height [cm]
            lattice_size: Fuel rod lattice size (e.g., 17 for 17x17)
            rod_pitch: Fuel rod pitch [cm]
        """
        self.assembly_pitch = assembly_pitch
        self.core_height = assembly_height
        self.n_assemblies = n_assemblies_x * n_assemblies_y

        # Calculate core dimensions
        self.core_diameter = max(n_assemblies_x, n_assemblies_y) * assembly_pitch

        assembly_id = 0

        # Build square lattice of assemblies
        for i in range(n_assemblies_x):
            for j in range(n_assemblies_y):
                # Calculate assembly position
                x = (i - (n_assemblies_x - 1) / 2) * assembly_pitch
                y = (j - (n_assemblies_y - 1) / 2) * assembly_pitch
                z = assembly_height / 2

                position = Point3D(x, y, z)

                # Create fuel assembly
                assembly = FuelAssembly(
                    id=assembly_id,
                    position=position,
                    lattice_size=lattice_size,
                    pitch=rod_pitch,
                    height=assembly_height,
                )

                # Build fuel rod lattice in assembly
                # Typical guide tube positions for 17x17: corners and center
                guide_tubes = []
                if lattice_size == 17:
                    # Typical 17x17 pattern: 4 corners + center
                    guide_tubes = [(0, 0), (0, 16), (16, 0), (16, 16), (8, 8)]

                assembly.build_square_lattice(guide_tube_positions=guide_tubes)
                self.assemblies.append(assembly)
                assembly_id += 1

    def total_fuel_volume(self) -> float:
        """Total fuel volume in core."""
        return sum(assembly.total_fuel_volume() for assembly in self.assemblies)

    def total_power(self) -> float:
        """Total core power [W]."""
        return sum(assembly.total_power() for assembly in self.assemblies)

    def generate_mesh(self, n_radial: int = 30, n_axial: int = 50):
        """Generate computational mesh for neutronics."""
        r_max = self.core_diameter / 2
        self.radial_mesh = np.linspace(0, r_max, n_radial + 1)
        self.axial_mesh = np.linspace(0, self.core_height, n_axial + 1)

    def to_dataframe(self):
        """Export core geometry to DataFrame."""
        import polars as pl

        records = []
        for assembly in self.assemblies:
            records.append(
                {
                    "assembly_id": assembly.id,
                    "x": assembly.position.x,
                    "y": assembly.position.y,
                    "z": assembly.position.z,
                    "type": assembly.assembly_type.value,
                    "lattice_size": assembly.lattice_size,
                    "n_rods": len(assembly.fuel_rods),
                    "fuel_volume": assembly.total_fuel_volume(),
                    "power": assembly.total_power(),
                }
            )
        return pl.DataFrame(records)


class BWRSMRCore:
    """
    Boiling Water Reactor (BWR) Small Modular Reactor core.
    
    Similar to PWR but with different control systems (control blades instead of clusters)
    and two-phase flow regions.
    
    Attributes:
        name: Core name
        assemblies: List of fuel assemblies
        control_blades: List of control blades
        core_height: Core height [cm]
        core_diameter: Core diameter [cm]
        water_channels: Water channels (with two-phase regions)
    """

    def __init__(self, name: str = "BWR-SMR"):
        self.name = name
        self.assemblies: List[FuelAssembly] = []
        self.control_blades: List[ControlBlade] = []
        self.core_height: float = 0.0
        self.core_diameter: float = 0.0
        self.water_channels: List[WaterChannel] = []

        # Mesh for neutronics
        self.radial_mesh: Optional[np.ndarray] = None
        self.axial_mesh: Optional[np.ndarray] = None

    def build_square_lattice_core(
        self,
        n_assemblies_x: int,
        n_assemblies_y: int,
        assembly_pitch: float = 21.5,
        assembly_height: float = 365.76,
        lattice_size: int = 10,  # BWR typically 10x10
        rod_pitch: float = 1.63,  # cm (larger than PWR)
    ):
        """Build BWR core with square lattice assemblies."""
        # Similar to PWR but with BWR-specific parameters
        # Implementation similar to PWRSMRCore
        pass


@dataclass
class SteamGeneratorTube:
    """
    Individual steam generator tube for in-vessel steam generators.
    
    Represents a U-tube or straight tube in an integral PWR steam generator.
    Primary coolant flows on the outside (shell side), secondary water/steam
    flows on the inside (tube side).
    
    Attributes:
        id: Unique identifier
        position: Center position of tube
        outer_diameter: Outer diameter [cm]
        inner_diameter: Inner diameter [cm]
        length: Tube length [cm]
        tube_type: "U-tube" or "straight"
        material: Tube material (typically Inconel-690 or Inconel-600)
    """
    
    id: int
    position: Point3D
    outer_diameter: float  # cm
    inner_diameter: float  # cm
    length: float  # cm
    tube_type: str = "U-tube"  # "U-tube" or "straight"
    material: str = "Inconel-690"
    
    def flow_area_primary(self) -> float:
        """Flow area for primary coolant (shell side) [cm²]."""
        # Simplified: assume tube bundle arrangement
        return np.pi * (self.outer_diameter / 2) ** 2
    
    def flow_area_secondary(self) -> float:
        """Flow area for secondary water/steam (tube side) [cm²]."""
        return np.pi * (self.inner_diameter / 2) ** 2
    
    def heat_transfer_area(self) -> float:
        """Heat transfer surface area [cm²]."""
        return np.pi * self.outer_diameter * self.length


@dataclass
class InVesselSteamGenerator:
    """
    In-vessel steam generator for integral PWR SMR designs.
    
    Represents a steam generator located inside the reactor pressure vessel,
    as used in integral PWR SMRs like CAREM, SMART, and NuScale.
    
    Primary coolant (hot water from core) flows on shell side.
    Secondary water/steam flows on tube side.
    
    Attributes:
        id: Unique identifier
        position: Center position in vessel
        n_tubes: Number of steam generator tubes
        tube_bundle_diameter: Diameter of tube bundle [cm]
        height: Height of steam generator [cm]
        tubes: List of steam generator tubes
        primary_inlet_temp: Primary coolant inlet temperature [K]
        primary_outlet_temp: Primary coolant outlet temperature [K]
        secondary_pressure: Secondary side pressure [Pa]
        secondary_inlet_temp: Secondary water inlet temperature [K]
        secondary_outlet_temp: Secondary steam outlet temperature [K]
        heat_transfer_rate: Heat transfer rate [W]
    """
    
    id: int
    position: Point3D
    n_tubes: int
    tube_bundle_diameter: float  # cm
    height: float  # cm
    tubes: List[SteamGeneratorTube] = field(default_factory=list)
    primary_inlet_temp: float = 573.15  # K (300°C typical PWR)
    primary_outlet_temp: float = 523.15  # K (250°C typical PWR)
    secondary_pressure: float = 6.0e6  # Pa (6 MPa typical)
    secondary_inlet_temp: float = 433.15  # K (160°C feedwater)
    secondary_outlet_temp: float = 553.15  # K (280°C steam)
    heat_transfer_rate: float = 0.0  # W
    
    def total_heat_transfer_area(self) -> float:
        """Total heat transfer area of all tubes [cm²]."""
        return sum(tube.heat_transfer_area() for tube in self.tubes)
    
    def build_tube_bundle(
        self,
        tube_outer_diameter: float = 1.9,  # cm (typical)
        tube_inner_diameter: float = 1.7,  # cm
        tube_length: float = 600.0,  # cm
        tube_pitch: float = 2.5,  # cm (center-to-center spacing)
        tube_type: str = "U-tube",
    ):
        """
        Build a tube bundle for the steam generator.
        
        Args:
            tube_outer_diameter: Outer diameter of tubes [cm]
            tube_inner_diameter: Inner diameter of tubes [cm]
            tube_length: Length of each tube [cm]
            tube_pitch: Center-to-center spacing of tubes [cm]
            tube_type: "U-tube" or "straight"
        """
        self.tubes = []
        
        # Calculate number of tubes that fit in bundle
        # Simplified: assume square pitch arrangement
        n_tubes_per_row = int(self.tube_bundle_diameter / tube_pitch)
        n_rows = int(self.height / tube_pitch)
        max_tubes = n_tubes_per_row * n_rows
        
        # Limit to specified number
        n_tubes_to_build = min(self.n_tubes, max_tubes)
        
        tube_id = 0
        for row in range(n_rows):
            for col in range(n_tubes_per_row):
                if tube_id >= n_tubes_to_build:
                    break
                
                # Calculate tube position (relative to bundle center)
                x = (col - (n_tubes_per_row - 1) / 2) * tube_pitch
                y = (row - (n_rows - 1) / 2) * tube_pitch
                z = self.position.z
                
                tube = SteamGeneratorTube(
                    id=tube_id,
                    position=Point3D(
                        self.position.x + x,
                        self.position.y + y,
                        z,
                    ),
                    outer_diameter=tube_outer_diameter,
                    inner_diameter=tube_inner_diameter,
                    length=tube_length,
                    tube_type=tube_type,
                )
                self.tubes.append(tube)
                tube_id += 1
        
        # Update actual number of tubes
        self.n_tubes = len(self.tubes)


@dataclass
class IntegratedPrimarySystem:
    """
    Integrated primary system for integral PWR SMR designs.
    
    Represents a complete primary system within a single pressure vessel,
    including core, steam generators, and pumps. Used in integral PWR SMRs
    like CAREM, SMART, and NuScale.
    
    Attributes:
        name: System name
        vessel_diameter: Reactor pressure vessel diameter [cm]
        vessel_height: Reactor pressure vessel height [cm]
        core: PWR SMR core
        steam_generators: List of in-vessel steam generators
        primary_pumps: Number of primary coolant pumps (if any)
        pressurizer_volume: Pressurizer volume [m³] (if separate)
        integrated_pressurizer: True if pressurizer is integrated in vessel
    """
    
    name: str
    vessel_diameter: float  # cm
    vessel_height: float  # cm
    core: Optional["PWRSMRCore"] = None
    steam_generators: List[InVesselSteamGenerator] = field(default_factory=list)
    primary_pumps: int = 0
    pressurizer_volume: float = 0.0  # m³
    integrated_pressurizer: bool = True
    
    def total_steam_generator_heat_transfer(self) -> float:
        """Total heat transfer rate from all steam generators [W]."""
        return sum(sg.heat_transfer_rate for sg in self.steam_generators)
    
    def vessel_volume(self) -> float:
        """Total vessel volume [cm³]."""
        return np.pi * (self.vessel_diameter / 2) ** 2 * self.vessel_height
    
    def add_steam_generator(self, sg: InVesselSteamGenerator):
        """Add a steam generator to the system."""
        self.steam_generators.append(sg)
    
    def get_steam_generators_by_position(
        self, min_z: float, max_z: float
    ) -> List[InVesselSteamGenerator]:
        """Get steam generators within a z-range."""
        return [
            sg
            for sg in self.steam_generators
            if min_z <= sg.position.z <= max_z
        ]
