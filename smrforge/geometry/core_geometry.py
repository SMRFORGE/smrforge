# smrforge/geometry/core_geometry.py
"""
Comprehensive geometry module for HTGR cores.
Supports prismatic block, pebble bed, and hybrid designs.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Union
from enum import Enum
import polars as pl
from numba import njit, prange
from scipy.spatial import KDTree
import json
from pathlib import Path


class CoreType(Enum):
    """Types of HTGR core configurations."""
    PRISMATIC = "prismatic"
    PEBBLE_BED = "pebble_bed"
    ANNULAR = "annular"
    HYBRID = "hybrid"


class LatticeType(Enum):
    """Lattice symmetries."""
    HEXAGONAL = "hexagonal"
    SQUARE = "square"
    TRIANGULAR = "triangular"


@dataclass
class Point3D:
    """3D point in space."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def distance_to(self, other: 'Point3D') -> float:
        """Euclidean distance to another point."""
        return np.sqrt((self.x - other.x)**2 + 
                      (self.y - other.y)**2 + 
                      (self.z - other.z)**2)
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([self.x, self.y, self.z])
    
    def __add__(self, other):
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Point3D(self.x - other.x, self.y - other.y, self.z - other.z)


@dataclass
class MaterialRegion:
    """Defines a material region with composition and temperature."""
    material_id: str
    composition: Dict[str, float]  # {nuclide: atom_density [atoms/b-cm]}
    temperature: float  # K
    density: float  # g/cm³
    volume: float = 0.0  # cm³
    
    def total_number_density(self) -> float:
        """Total atomic number density."""
        return sum(self.composition.values())


@dataclass
class FuelChannel:
    """Represents a single fuel channel in prismatic block."""
    id: int
    position: Point3D  # Center position
    radius: float  # cm
    height: float  # cm
    material_region: MaterialRegion
    power_density: float = 0.0  # W/cm³
    
    def volume(self) -> float:
        """Channel volume."""
        return np.pi * self.radius**2 * self.height


@dataclass
class CoolantChannel:
    """Coolant channel (helium flow path)."""
    id: int
    position: Point3D
    radius: float
    height: float
    flow_area: float  # cm²
    mass_flow_rate: float = 0.0  # kg/s
    inlet_temp: float = 573.0  # K (300°C)
    outlet_temp: float = 1023.0  # K (750°C)


@dataclass
class GraphiteBlock:
    """Hexagonal graphite fuel block (prismatic design)."""
    id: int
    position: Point3D  # Center position
    flat_to_flat: float  # cm (hex dimension)
    height: float  # cm
    fuel_channels: List[FuelChannel] = field(default_factory=list)
    coolant_channels: List[CoolantChannel] = field(default_factory=list)
    moderator_material: MaterialRegion = None
    block_type: str = "fuel"  # "fuel", "reflector", "control"
    
    def vertices(self) -> np.ndarray:
        """Get hexagon vertices in x-y plane."""
        angles = np.linspace(0, 2*np.pi, 7)[:-1]  # 6 vertices
        radius = self.flat_to_flat / np.sqrt(3)
        x = self.position.x + radius * np.cos(angles)
        y = self.position.y + radius * np.sin(angles)
        return np.column_stack([x, y])
    
    def total_fuel_volume(self) -> float:
        """Total fuel volume in block."""
        return sum(ch.volume() for ch in self.fuel_channels)
    
    def power(self) -> float:
        """Total power in block [W]."""
        return sum(ch.power_density * ch.volume() for ch in self.fuel_channels)


@dataclass
class Pebble:
    """Fuel pebble for pebble-bed design."""
    id: int
    position: Point3D
    radius: float = 3.0  # cm (6 cm diameter)
    fuel_zone_radius: float = 2.5  # cm (5 cm fuel zone)
    material_region: MaterialRegion = None
    burnup: float = 0.0  # MWd/kg
    residence_time: float = 0.0  # days
    
    def volume(self) -> float:
        """Pebble volume."""
        return (4/3) * np.pi * self.radius**3
    
    def fuel_volume(self) -> float:
        """Fuel zone volume."""
        return (4/3) * np.pi * self.fuel_zone_radius**3


class PrismaticCore:
    """
    Prismatic block HTGR core (e.g., GT-MHR, Valar Atomics style).
    """
    
    def __init__(self, name: str = "Prismatic-HTGR"):
        self.name = name
        self.blocks: List[GraphiteBlock] = []
        self.core_height: float = 0.0  # cm
        self.core_diameter: float = 0.0  # cm
        self.lattice_pitch: float = 0.0  # cm (block-to-block)
        self.n_rings: int = 0  # Number of hexagonal rings
        self.reflector_thickness: float = 0.0  # cm
        
        # Mesh for neutronics
        self.radial_mesh: Optional[np.ndarray] = None
        self.axial_mesh: Optional[np.ndarray] = None
        
        # Temperature distribution
        self.temperature_field: Optional[np.ndarray] = None
        
    def build_hexagonal_lattice(self, n_rings: int, pitch: float, 
                                block_height: float, n_axial: int,
                                flat_to_flat: float = 36.0):
        """
        Build hexagonal lattice of fuel blocks.
        
        Args:
            n_rings: Number of hexagonal rings (1 = center only)
            pitch: Block-to-block pitch [cm]
            block_height: Height of each block [cm]
            n_axial: Number of axial layers
            flat_to_flat: Block flat-to-flat distance [cm]
        """
        self.n_rings = n_rings
        self.lattice_pitch = pitch
        self.core_height = block_height * n_axial
        
        block_id = 0
        
        # Generate hexagonal positions
        hex_positions = self._generate_hex_positions(n_rings, pitch)
        
        # Create blocks at each position and axial level
        for i_axial in range(n_axial):
            z_center = (i_axial + 0.5) * block_height
            
            for x, y in hex_positions:
                position = Point3D(x, y, z_center)
                
                # Determine block type based on radius
                r = np.sqrt(x**2 + y**2)
                if r > (n_rings - 1) * pitch:
                    block_type = "reflector"
                else:
                    block_type = "fuel"
                
                block = GraphiteBlock(
                    id=block_id,
                    position=position,
                    flat_to_flat=flat_to_flat,
                    height=block_height,
                    block_type=block_type
                )
                
                # Add fuel/coolant channels if fuel block
                if block_type == "fuel":
                    self._add_channels_to_block(block)
                
                self.blocks.append(block)
                block_id += 1
        
        # Estimate core diameter
        self.core_diameter = 2 * n_rings * pitch
    
    def _generate_hex_positions(self, n_rings: int, pitch: float) -> List[Tuple[float, float]]:
        """Generate hexagonal lattice positions."""
        positions = [(0.0, 0.0)]  # Center
        
        for ring in range(1, n_rings + 1):
            n_positions = 6 * ring
            for i in range(n_positions):
                angle = 2 * np.pi * i / n_positions
                x = ring * pitch * np.cos(angle)
                y = ring * pitch * np.sin(angle)
                positions.append((x, y))
        
        return positions
    
    def _add_channels_to_block(self, block: GraphiteBlock, 
                               n_fuel: int = 210, n_coolant: int = 102):
        """
        Add fuel and coolant channels to block in triangular pattern.
        Typical GT-MHR: 210 fuel, 102 coolant channels.
        """
        # Simplified: arrange in concentric rings
        fuel_radius = 0.635  # cm (1/2" diameter)
        coolant_radius = 0.794  # cm (5/8" diameter)
        channel_pitch = 1.88  # cm
        
        # Fuel channels in hexagonal pattern
        positions = self._generate_hex_positions(8, channel_pitch)
        
        for i, (x, y) in enumerate(positions[:n_fuel]):
            ch_pos = block.position + Point3D(x, y, 0)
            
            # Create material region (would be populated from composition)
            mat_region = MaterialRegion(
                material_id=f"fuel_{block.id}_{i}",
                composition={'U235': 0.0005, 'U238': 0.002, 'C': 0.08},
                temperature=1200.0,
                density=1.74
            )
            
            channel = FuelChannel(
                id=i,
                position=ch_pos,
                radius=fuel_radius,
                height=block.height,
                material_region=mat_region
            )
            block.fuel_channels.append(channel)
        
        # Coolant channels
        coolant_positions = self._generate_hex_positions(6, channel_pitch)
        
        for i, (x, y) in enumerate(coolant_positions[:n_coolant]):
            ch_pos = block.position + Point3D(x, y, 0)
            
            channel = CoolantChannel(
                id=i,
                position=ch_pos,
                radius=coolant_radius,
                height=block.height,
                flow_area=np.pi * coolant_radius**2
            )
            block.coolant_channels.append(channel)
    
    def get_block_by_position(self, x: float, y: float, z: float) -> Optional[GraphiteBlock]:
        """Find block containing given position."""
        for block in self.blocks:
            # Check z range
            z_min = block.position.z - block.height / 2
            z_max = block.position.z + block.height / 2
            if not (z_min <= z <= z_max):
                continue
            
            # Check if inside hexagon (simplified)
            dx = abs(x - block.position.x)
            dy = abs(y - block.position.y)
            r_hex = block.flat_to_flat / np.sqrt(3)
            
            if dx < r_hex and dy < r_hex:
                return block
        
        return None
    
    def total_fuel_volume(self) -> float:
        """Total fuel volume in core."""
        return sum(block.total_fuel_volume() for block in self.blocks)
    
    def total_power(self) -> float:
        """Total core power [W]."""
        return sum(block.power() for block in self.blocks)
    
    def generate_mesh(self, n_radial: int = 20, n_axial: int = 50):
        """Generate computational mesh for neutronics."""
        # Radial mesh (cylindrical approximation)
        r_max = self.core_diameter / 2 + self.reflector_thickness
        self.radial_mesh = np.linspace(0, r_max, n_radial + 1)
        
        # Axial mesh
        self.axial_mesh = np.linspace(0, self.core_height, n_axial + 1)
        
    def to_dataframe(self) -> pl.DataFrame:
        """Export core geometry to DataFrame."""
        records = []
        for block in self.blocks:
            records.append({
                'block_id': block.id,
                'x': block.position.x,
                'y': block.position.y,
                'z': block.position.z,
                'type': block.block_type,
                'n_fuel_channels': len(block.fuel_channels),
                'n_coolant_channels': len(block.coolant_channels),
                'fuel_volume': block.total_fuel_volume(),
                'power': block.power()
            })
        return pl.DataFrame(records)


class PebbleBedCore:
    """
    Pebble bed HTGR core (e.g., HTR-PM, PBMR).
    """
    
    def __init__(self, name: str = "PebbleBed-HTGR"):
        self.name = name
        self.pebbles: List[Pebble] = []
        self.core_height: float = 0.0  # cm
        self.core_diameter: float = 0.0  # cm
        self.annular_inner_diameter: float = 0.0  # cm (0 for solid bed)
        self.packing_fraction: float = 0.61  # Typical random packing
        
        # For continuous refueling simulation
        self.recirculation_pattern: Optional[np.ndarray] = None
    
    def build_random_packing(self, core_height: float, core_diameter: float,
                            pebble_radius: float = 3.0, 
                            annular_inner_diameter: float = 0.0):
        """
        Build randomly packed pebble bed.
        Uses simplified algorithm - production would use DEM simulation.
        
        Args:
            core_height: Core height [cm]
            core_diameter: Outer diameter [cm]
            pebble_radius: Pebble radius [cm]
            annular_inner_diameter: Inner diameter for annular core [cm]
        """
        self.core_height = core_height
        self.core_diameter = core_diameter
        self.annular_inner_diameter = annular_inner_diameter
        
        # Estimate number of pebbles
        core_volume = np.pi * (core_diameter/2)**2 * core_height
        if annular_inner_diameter > 0:
            core_volume -= np.pi * (annular_inner_diameter/2)**2 * core_height
        
        pebble_volume = (4/3) * np.pi * pebble_radius**3
        n_pebbles = int(core_volume * self.packing_fraction / pebble_volume)
        
        # Generate random positions (simplified - real DEM is more complex)
        pebble_id = 0
        
        for _ in range(n_pebbles):
            # Random position in cylindrical core
            valid = False
            while not valid:
                # Random radius (accounting for annular geometry)
                r_min = annular_inner_diameter / 2 + pebble_radius
                r_max = core_diameter / 2 - pebble_radius
                r = np.random.uniform(r_min, r_max)
                theta = np.random.uniform(0, 2*np.pi)
                
                x = r * np.cos(theta)
                y = r * np.sin(theta)
                z = np.random.uniform(pebble_radius, core_height - pebble_radius)
                
                position = Point3D(x, y, z)
                
                # Check for overlaps (simplified)
                valid = self._check_no_overlap(position, pebble_radius)
                
                if valid:
                    mat_region = MaterialRegion(
                        material_id=f"pebble_{pebble_id}",
                        composition={'U235': 0.0005, 'U238': 0.002, 'C': 0.08},
                        temperature=1100.0,
                        density=1.74
                    )
                    
                    pebble = Pebble(
                        id=pebble_id,
                        position=position,
                        radius=pebble_radius,
                        material_region=mat_region
                    )
                    self.pebbles.append(pebble)
                    pebble_id += 1
                    break
    
    def _check_no_overlap(self, position: Point3D, radius: float, 
                         min_separation: float = 0.1) -> bool:
        """Check if position overlaps with existing pebbles."""
        # Only check last few pebbles for speed (simplified)
        check_last = min(100, len(self.pebbles))
        
        for pebble in self.pebbles[-check_last:]:
            dist = position.distance_to(pebble.position)
            if dist < 2 * radius + min_separation:
                return False
        return True
    
    def build_structured_packing(self, core_height: float, core_diameter: float,
                                pebble_radius: float = 3.0,
                                lattice_type: LatticeType = LatticeType.HEXAGONAL):
        """
        Build structured (FCC or HCP) pebble packing.
        Higher packing fraction (~0.74) than random.
        """
        self.core_height = core_height
        self.core_diameter = core_diameter
        self.packing_fraction = 0.74  # FCC/HCP packing
        
        pebble_id = 0
        spacing = 2 * pebble_radius * 1.05  # Small gap
        
        if lattice_type == LatticeType.HEXAGONAL:
            # HCP stacking
            n_z = int(core_height / spacing)
            
            for i_z in range(n_z):
                z = (i_z + 0.5) * spacing
                
                # Alternate between A and B layers
                offset_x = (i_z % 2) * spacing / 2
                offset_y = (i_z % 2) * spacing * np.sqrt(3) / 6
                
                # Hexagonal arrangement in x-y
                n_rows = int(core_diameter / spacing)
                for i_row in range(-n_rows, n_rows):
                    y = i_row * spacing * np.sqrt(3) / 2 + offset_y
                    
                    n_cols = int(core_diameter / spacing)
                    for i_col in range(-n_cols, n_cols):
                        x = i_col * spacing + offset_x
                        
                        # Check if inside core
                        r = np.sqrt(x**2 + y**2)
                        if r < core_diameter / 2 - pebble_radius:
                            position = Point3D(x, y, z)
                            
                            mat_region = MaterialRegion(
                                material_id=f"pebble_{pebble_id}",
                                composition={'U235': 0.0005, 'U238': 0.002, 'C': 0.08},
                                temperature=1100.0,
                                density=1.74
                            )
                            
                            pebble = Pebble(
                                id=pebble_id,
                                position=position,
                                radius=pebble_radius,
                                material_region=mat_region
                            )
                            self.pebbles.append(pebble)
                            pebble_id += 1
    
    def simulate_recirculation(self, n_passes: int = 10, 
                              discharge_burnup: float = 90.0):
        """
        Simulate continuous recirculation of pebbles.
        Fresh pebbles enter at top, discharged at bottom.
        
        Args:
            n_passes: Number of passes through core
            discharge_burnup: Burnup threshold for discharge [MWd/kg]
        """
        # Simplified flow model - assume downward drift
        # Real simulation would use DEM + CFD
        
        # Sort pebbles by z (height)
        self.pebbles.sort(key=lambda p: p.position.z, reverse=True)
        
        # Move pebbles down, recirculate or discharge
        dz_per_day = 5.0  # cm/day (typical drift velocity)
        
        for pebble in self.pebbles:
            pebble.position.z -= dz_per_day
            pebble.residence_time += 1.0  # days
            
            # If reaches bottom
            if pebble.position.z < 0:
                if pebble.burnup < discharge_burnup:
                    # Recirculate to top
                    pebble.position.z = self.core_height
                else:
                    # Discharge (would remove from list in real sim)
                    pass
    
    def get_pebble_neighbors(self, pebble_id: int, radius: float = 10.0) -> List[Pebble]:
        """Find neighboring pebbles within radius using KD-tree."""
        if not hasattr(self, '_kdtree'):
            # Build KD-tree for fast spatial queries
            positions = np.array([p.position.to_array() for p in self.pebbles])
            self._kdtree = KDTree(positions)
        
        pebble = self.pebbles[pebble_id]
        indices = self._kdtree.query_ball_point(pebble.position.to_array(), radius)
        
        return [self.pebbles[i] for i in indices if i != pebble_id]
    
    def to_dataframe(self) -> pl.DataFrame:
        """Export pebble data to DataFrame."""
        records = []
        for pebble in self.pebbles:
            records.append({
                'pebble_id': pebble.id,
                'x': pebble.position.x,
                'y': pebble.position.y,
                'z': pebble.position.z,
                'burnup': pebble.burnup,
                'residence_time': pebble.residence_time,
                'temperature': pebble.material_region.temperature if pebble.material_region else 0.0
            })
        return pl.DataFrame(records)


@njit(parallel=True, cache=True)
def compute_distance_matrix(positions: np.ndarray) -> np.ndarray:
    """
    Fast distance matrix computation using Numba.
    
    Args:
        positions: Nx3 array of positions
    
    Returns:
        NxN distance matrix
    """
    n = positions.shape[0]
    dist = np.zeros((n, n))
    
    for i in prange(n):
        for j in range(i+1, n):
            dx = positions[i, 0] - positions[j, 0]
            dy = positions[i, 1] - positions[j, 1]
            dz = positions[i, 2] - positions[j, 2]
            d = np.sqrt(dx*dx + dy*dy + dz*dz)
            dist[i, j] = d
            dist[j, i] = d
    
    return dist


class GeometryExporter:
    """Export geometry to various formats."""
    
    @staticmethod
    def to_vtk(core: Union[PrismaticCore, PebbleBedCore], filepath: Path):
        """Export to VTK for visualization in ParaView."""
        import pyvista as pv
        
        if isinstance(core, PrismaticCore):
            # Create hexagonal blocks as polydata
            mesh = pv.PolyData()
            
            for block in core.blocks:
                vertices = block.vertices()
                # Create hexagonal prism
                # ... (implementation details)
            
        elif isinstance(core, PebbleBedCore):
            # Create sphere cloud
            points = np.array([p.position.to_array() for p in core.pebbles])
            mesh = pv.PolyData(points)
            mesh['burnup'] = [p.burnup for p in core.pebbles]
            mesh['temperature'] = [p.material_region.temperature 
                                  if p.material_region else 0.0 
                                  for p in core.pebbles]
        
        mesh.save(filepath)
    
    @staticmethod
    def to_json(core: Union[PrismaticCore, PebbleBedCore], filepath: Path):
        """Export geometry to JSON."""
        data = {
            'name': core.name,
            'type': core.__class__.__name__,
            'core_height': core.core_height,
            'core_diameter': core.core_diameter,
        }
        
        if isinstance(core, PrismaticCore):
            data['blocks'] = [
                {
                    'id': b.id,
                    'position': [b.position.x, b.position.y, b.position.z],
                    'type': b.block_type,
                    'n_fuel_channels': len(b.fuel_channels),
                }
                for b in core.blocks
            ]
        elif isinstance(core, PebbleBedCore):
            data['n_pebbles'] = len(core.pebbles)
            data['packing_fraction'] = core.packing_fraction
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


if __name__ == "__main__":
    from rich.console import Console
    console = Console()
    
    console.print("[bold cyan]HTGR Core Geometry Module Demo[/bold cyan]\n")
    
    # Example 1: Prismatic Core
    console.print("[bold]1. Prismatic Block Core[/bold]")
    prismatic = PrismaticCore(name="Valar-10MW")
    prismatic.build_hexagonal_lattice(
        n_rings=3,
        pitch=40.0,  # cm
        block_height=79.3,  # cm
        n_axial=10,
        flat_to_flat=36.0
    )
    
    console.print(f"   Blocks: {len(prismatic.blocks)}")
    console.print(f"   Core height: {prismatic.core_height:.1f} cm")
    console.print(f"   Core diameter: {prismatic.core_diameter:.1f} cm")
    console.print(f"   Fuel volume: {prismatic.total_fuel_volume():.1f} cm³")
    
    # Example 2: Pebble Bed Core
    console.print("\n[bold]2. Pebble Bed Core[/bold]")
    pebble_bed = PebbleBedCore(name="HTR-PM-Style")
    pebble_bed.build_structured_packing(
        core_height=1100.0,  # cm
        core_diameter=300.0,  # cm
        pebble_radius=3.0
    )
    
    console.print(f"   Pebbles: {len(pebble_bed.pebbles)}")
    console.print(f"   Packing fraction: {pebble_bed.packing_fraction:.3f}")
    console.print(f"   Core volume: {np.pi * (pebble_bed.core_diameter/2)**2 * pebble_bed.core_height:.0f} cm³")
    
    console.print("\n[bold green]Geometry module ready![/bold green]")
