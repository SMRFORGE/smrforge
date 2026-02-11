"""
3D mesh representation and extraction for geometry visualization.

Provides 3D unstructured mesh data structures and methods to extract
3D meshes from reactor geometry for advanced visualization.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np


@dataclass
class Mesh3D:
    """
    3D unstructured mesh representation.

    Attributes:
        vertices: Vertex coordinates [n_vertices, 3] (x, y, z)
        faces: Face connectivity [n_faces, 3] (triangles) or [n_faces, 4] (quads)
        cells: Cell connectivity [n_cells, 4] (tetrahedra) or [n_cells, 8] (hexahedra)
        cell_materials: Material ID for each cell [n_cells]
        cell_data: Scalar fields on cells (e.g., flux, power, temperature)
        face_data: Scalar fields on faces (e.g., heat flux)
    """

    vertices: np.ndarray  # [n_vertices, 3]
    faces: Optional[np.ndarray] = None  # [n_faces, 3 or 4]
    cells: Optional[np.ndarray] = None  # [n_cells, 4 or 8]
    cell_materials: Optional[np.ndarray] = None  # [n_cells]
    cell_data: Dict[str, np.ndarray] = field(
        default_factory=dict
    )  # {field_name: [n_cells]}
    face_data: Dict[str, np.ndarray] = field(
        default_factory=dict
    )  # {field_name: [n_faces]}

    def __post_init__(self):
        """Validate mesh data."""
        if len(self.vertices.shape) != 2 or self.vertices.shape[1] != 3:
            raise ValueError("Vertices must be [n_vertices, 3] array")

        if self.faces is not None:
            if len(self.faces.shape) != 2:
                raise ValueError("Faces must be 2D array")
            if self.faces.shape[1] not in [3, 4]:
                raise ValueError("Faces must have 3 or 4 vertices")

        if self.cells is not None:
            if len(self.cells.shape) != 2:
                raise ValueError("Cells must be 2D array")
            if self.cells.shape[1] not in [4, 8]:
                raise ValueError("Cells must have 4 (tet) or 8 (hex) vertices")

    @property
    def n_vertices(self) -> int:
        """Number of vertices."""
        return len(self.vertices)

    @property
    def n_faces(self) -> int:
        """Number of faces."""
        return len(self.faces) if self.faces is not None else 0

    @property
    def n_cells(self) -> int:
        """Number of cells."""
        return len(self.cells) if self.cells is not None else 0

    def add_cell_data(self, name: str, data: np.ndarray):
        """
        Add scalar field data to cells.

        Args:
            name: Field name (e.g., "flux", "power", "temperature")
            data: Data array [n_cells]
        """
        if self.cells is None:
            raise ValueError("No cells defined in mesh")
        if len(data) != self.n_cells:
            raise ValueError(
                f"Data length {len(data)} does not match cell count {self.n_cells}"
            )
        self.cell_data[name] = data

    def add_face_data(self, name: str, data: np.ndarray):
        """
        Add scalar field data to faces.

        Args:
            name: Field name (e.g., "heat_flux")
            data: Data array [n_faces]
        """
        if self.faces is None:
            raise ValueError("No faces defined in mesh")
        if len(data) != self.n_faces:
            raise ValueError(
                f"Data length {len(data)} does not match face count {self.n_faces}"
            )
        self.face_data[name] = data

    def get_bounds(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get bounding box of mesh.

        Returns:
            Tuple of (min_bounds, max_bounds) [3]
        """
        min_bounds = np.min(self.vertices, axis=0)
        max_bounds = np.max(self.vertices, axis=0)
        return min_bounds, max_bounds

    def get_center(self) -> np.ndarray:
        """
        Get center of mesh.

        Returns:
            Center point [3]
        """
        return np.mean(self.vertices, axis=0)


@dataclass
class Surface:
    """
    Surface representation (for boundaries, material interfaces, etc.).

    Attributes:
        vertices: Vertex coordinates [n_vertices, 3]
        faces: Face connectivity [n_faces, 3] (triangles)
        material_id: Material ID on this surface (if applicable)
        surface_type: Type of surface (e.g., "boundary", "material_interface", "control_rod")
    """

    vertices: np.ndarray  # [n_vertices, 3]
    faces: np.ndarray  # [n_faces, 3]
    material_id: Optional[str] = None
    surface_type: str = "boundary"

    def __post_init__(self):
        """Validate surface data."""
        if len(self.vertices.shape) != 2 or self.vertices.shape[1] != 3:
            raise ValueError("Vertices must be [n_vertices, 3] array")
        if len(self.faces.shape) != 2 or self.faces.shape[1] != 3:
            raise ValueError("Faces must be [n_faces, 3] array")

    @property
    def n_vertices(self) -> int:
        """Number of vertices."""
        return len(self.vertices)

    @property
    def n_faces(self) -> int:
        """Number of faces."""
        return len(self.faces)

    def to_mesh3d(self) -> Mesh3D:
        """Convert surface to Mesh3D (surface mesh only)."""
        return Mesh3D(
            vertices=self.vertices,
            faces=self.faces,
            cell_materials=(
                np.array([self.material_id] * self.n_faces)
                if self.material_id
                else None
            ),
        )


def extract_hexagonal_prism_mesh(
    center: np.ndarray,
    flat_to_flat: float,
    height: float,
    n_segments: int = 6,
) -> Mesh3D:
    """
    Extract 3D mesh for a hexagonal prism (block).

    Args:
        center: Center point [3] (x, y, z)
        flat_to_flat: Flat-to-flat distance [cm]
        height: Prism height [cm]
        n_segments: Number of segments per hex edge (for refinement)

    Returns:
        Mesh3D instance with vertices, faces, and cells
    """
    # Hexagon radius
    radius = flat_to_flat / np.sqrt(3)

    # Generate hexagon vertices in x-y plane
    angles = np.linspace(0, 2 * np.pi, 7)[:-1]  # 6 vertices
    hex_vertices_2d = np.column_stack(
        [
            radius * np.cos(angles),
            radius * np.sin(angles),
        ]
    )

    # Create top and bottom hexagons
    z_bottom = center[2] - height / 2
    z_top = center[2] + height / 2

    vertices = []
    vertex_map = {}  # Track vertex indices

    # Bottom hexagon vertices
    bottom_start = len(vertices)
    for i, (x, y) in enumerate(hex_vertices_2d):
        vertex = np.array([center[0] + x, center[1] + y, z_bottom])
        vertices.append(vertex)
        vertex_map[("bottom", i)] = len(vertices) - 1

    # Top hexagon vertices
    top_start = len(vertices)
    for i, (x, y) in enumerate(hex_vertices_2d):
        vertex = np.array([center[0] + x, center[1] + y, z_top])
        vertices.append(vertex)
        vertex_map[("top", i)] = len(vertices) - 1

    # Create faces
    faces = []

    # Bottom face (hexagon)
    for i in range(6):
        v0 = bottom_start + i
        v1 = bottom_start + (i + 1) % 6
        v2 = bottom_start  # Center (we'll add center vertex)
        # For now, use triangle fan
        if i < 5:
            faces.append([v0, v1, bottom_start])

    # Top face (hexagon)
    for i in range(6):
        v0 = top_start + i
        v1 = top_start + (i + 1) % 6
        if i < 5:
            faces.append([v0, top_start, v1])  # Reversed for outward normal

    # Side faces (6 rectangular faces)
    for i in range(6):
        v0_bottom = bottom_start + i
        v1_bottom = bottom_start + (i + 1) % 6
        v0_top = top_start + i
        v1_top = top_start + (i + 1) % 6

        # Two triangles per rectangular face
        faces.append([v0_bottom, v1_bottom, v0_top])
        faces.append([v1_bottom, v1_top, v0_top])

    # Create cells (hexahedra - simplified as two triangular prisms)
    # For simplicity, we'll create tetrahedra from the hexagon
    cells = []

    # Bottom tetrahedra (from center to hexagon)
    center_bottom = len(vertices)
    vertices.append(np.array([center[0], center[1], z_bottom]))

    center_top = len(vertices)
    vertices.append(np.array([center[0], center[1], z_top]))

    # Create cells connecting hexagon to center
    for i in range(6):
        v0 = bottom_start + i
        v1 = bottom_start + (i + 1) % 6
        v2 = top_start + i
        v3 = top_start + (i + 1) % 6

        # Two tetrahedra per segment
        cells.append([center_bottom, v0, v1, center_top])
        cells.append([v0, v1, v2, v3])
        cells.append([v1, v2, v3, center_top])

    vertices_array = np.array(vertices)
    faces_array = np.array(faces)
    cells_array = np.array(cells)

    return Mesh3D(
        vertices=vertices_array,
        faces=faces_array,
        cells=cells_array,
    )


def extract_cylinder_mesh(
    center: np.ndarray,
    radius: float,
    height: float,
    n_segments: int = 16,
) -> Mesh3D:
    """
    Extract 3D mesh for a cylinder (fuel/coolant channel, control rod).

    Args:
        center: Center point [3] (x, y, z)
        radius: Cylinder radius [cm]
        height: Cylinder height [cm]
        n_segments: Number of segments around circumference

    Returns:
        Mesh3D instance
    """
    # Generate circle vertices
    angles = np.linspace(0, 2 * np.pi, n_segments + 1)[:-1]

    z_bottom = center[2] - height / 2
    z_top = center[2] + height / 2

    vertices = []

    # Bottom circle
    for angle in angles:
        x = center[0] + radius * np.cos(angle)
        y = center[1] + radius * np.sin(angle)
        vertices.append([x, y, z_bottom])

    # Top circle
    for angle in angles:
        x = center[0] + radius * np.cos(angle)
        y = center[1] + radius * np.sin(angle)
        vertices.append([x, y, z_top])

    # Center points
    center_bottom = len(vertices)
    vertices.append([center[0], center[1], z_bottom])

    center_top = len(vertices)
    vertices.append([center[0], center[1], z_top])

    # Create faces
    faces = []

    # Bottom face
    for i in range(n_segments):
        v0 = i
        v1 = (i + 1) % n_segments
        faces.append([v0, v1, center_bottom])

    # Top face
    for i in range(n_segments):
        v0 = n_segments + i
        v1 = n_segments + (i + 1) % n_segments
        faces.append([v0, center_top, v1])

    # Side faces
    for i in range(n_segments):
        v0_bottom = i
        v1_bottom = (i + 1) % n_segments
        v0_top = n_segments + i
        v1_top = n_segments + (i + 1) % n_segments

        faces.append([v0_bottom, v1_bottom, v0_top])
        faces.append([v1_bottom, v1_top, v0_top])

    # Create cells (tetrahedra)
    cells = []
    for i in range(n_segments):
        v0 = i
        v1 = (i + 1) % n_segments
        v2 = n_segments + i
        v3 = n_segments + (i + 1) % n_segments

        # Two tetrahedra per segment
        cells.append([center_bottom, v0, v1, center_top])
        cells.append([v0, v1, v2, v3])
        cells.append([v1, v2, v3, center_top])

    vertices_array = np.array(vertices)
    faces_array = np.array(faces)
    cells_array = np.array(cells)

    return Mesh3D(
        vertices=vertices_array,
        faces=faces_array,
        cells=cells_array,
    )


def extract_sphere_mesh(
    center: np.ndarray,
    radius: float,
    n_segments: int = 16,
) -> Mesh3D:
    """
    Extract 3D mesh for a sphere (pebble).

    Args:
        center: Center point [3] (x, y, z)
        radius: Sphere radius [cm]
        n_segments: Number of segments (controls resolution)

    Returns:
        Mesh3D instance
    """
    # Generate sphere using icosahedron subdivision (simplified)
    # For now, use a simple approximation with lat/lon grid

    vertices = []
    faces = []

    # Generate vertices on sphere
    n_lat = n_segments
    n_lon = n_segments * 2

    for i in range(n_lat + 1):
        theta = np.pi * i / n_lat  # Latitude angle
        for j in range(n_lon):
            phi = 2 * np.pi * j / n_lon  # Longitude angle

            x = center[0] + radius * np.sin(theta) * np.cos(phi)
            y = center[1] + radius * np.sin(theta) * np.sin(phi)
            z = center[2] + radius * np.cos(theta)

            vertices.append([x, y, z])

    # Create faces
    for i in range(n_lat):
        for j in range(n_lon):
            v0 = i * n_lon + j
            v1 = i * n_lon + (j + 1) % n_lon
            v2 = (i + 1) * n_lon + j
            v3 = (i + 1) * n_lon + (j + 1) % n_lon

            # Two triangles per quad
            faces.append([v0, v1, v2])
            faces.append([v1, v3, v2])

    vertices_array = np.array(vertices)
    faces_array = np.array(faces)

    return Mesh3D(
        vertices=vertices_array,
        faces=faces_array,
    )


def combine_meshes(meshes: List[Mesh3D]) -> Mesh3D:
    """
    Combine multiple meshes into a single mesh.

    Args:
        meshes: List of Mesh3D instances

    Returns:
        Combined Mesh3D
    """
    if not meshes:
        raise ValueError("No meshes to combine")

    all_vertices = []
    all_faces = []
    all_cells = []
    all_materials = []
    all_cell_data = {}

    vertex_offset = 0

    # Determine target cell shape (use largest if mixed)
    max_cell_size = 0
    for mesh in meshes:
        if mesh.cells is not None and len(mesh.cells) > 0:
            max_cell_size = max(max_cell_size, mesh.cells.shape[1])

    # If no cells found, max_cell_size stays 0
    if max_cell_size == 0:
        max_cell_size = 8  # Default to hexahedral

    for mesh in meshes:
        # Add vertices
        all_vertices.append(mesh.vertices)

        # Add faces with offset
        if mesh.faces is not None:
            offset_faces = mesh.faces + vertex_offset
            all_faces.append(offset_faces)

        # Add cells with offset, normalize to max_cell_size
        if mesh.cells is not None:
            offset_cells = mesh.cells + vertex_offset
            # Pad tetrahedral (4) to hexahedral (8) if needed
            if max_cell_size == 8 and offset_cells.shape[1] == 4:
                # Pad by repeating last vertex 4 times
                last_vertex = offset_cells[:, -1:]
                padding = np.repeat(last_vertex, 4, axis=1)
                offset_cells = np.hstack([offset_cells, padding])
            all_cells.append(offset_cells)

        # Add materials
        if mesh.cell_materials is not None:
            all_materials.append(mesh.cell_materials)

        # Combine cell data
        for name, data in mesh.cell_data.items():
            if name not in all_cell_data:
                all_cell_data[name] = []
            all_cell_data[name].append(data)

        vertex_offset += mesh.n_vertices

    # Combine arrays
    combined_vertices = np.vstack(all_vertices)
    combined_faces = np.vstack(all_faces) if all_faces else None
    combined_cells = np.vstack(all_cells) if all_cells else None
    combined_materials = np.concatenate(all_materials) if all_materials else None

    # Combine cell data
    combined_cell_data = {
        name: np.concatenate(data_list) for name, data_list in all_cell_data.items()
    }

    return Mesh3D(
        vertices=combined_vertices,
        faces=combined_faces,
        cells=combined_cells,
        cell_materials=combined_materials,
        cell_data=combined_cell_data,
    )
