"""
Advanced mesh generation with quality metrics and adaptive refinement.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

import numpy as np
from scipy.spatial import Delaunay


class MeshType(Enum):
    """Types of mesh generation."""

    STRUCTURED = "structured"  # Regular grid
    UNSTRUCTURED = "unstructured"  # Triangular/tetrahedral
    HYBRID = "hybrid"  # Combination


@dataclass
class MeshQuality:
    """Mesh quality metrics."""

    min_angle: float  # Minimum angle (degrees)
    max_angle: float  # Maximum angle (degrees)
    aspect_ratio: float  # Max/min edge length ratio
    skewness: float  # Mesh skewness metric
    jacobian: float  # Minimum Jacobian (for non-orthogonal elements)

    def is_good(self) -> bool:
        """Check if mesh quality is acceptable."""
        return (
            self.min_angle > 10.0
            and self.max_angle < 170.0
            and self.aspect_ratio < 10.0
            and self.skewness > 0.3
        )


class AdvancedMeshGenerator:
    """
    Advanced mesh generation with quality control and adaptive refinement.
    """

    def __init__(self, mesh_type: MeshType = MeshType.STRUCTURED):
        self.mesh_type = mesh_type

    def generate_radial_mesh(
        self,
        core_diameter: float,
        n_points: int = 50,
        refinement_regions: Optional[List[Tuple[float, float, int]]] = None,
    ) -> np.ndarray:
        """
        Generate radial mesh with optional local refinement.

        Args:
            core_diameter: Core diameter [cm]
            n_points: Base number of mesh points
            refinement_regions: List of (r_min, r_max, n_refine) for local refinement

        Returns:
            Radial mesh points [cm]
        """
        r_max = core_diameter / 2.0

        if refinement_regions is None:
            # Uniform mesh
            return np.linspace(0, r_max, n_points)

        # Start with base mesh
        mesh = np.linspace(0, r_max, n_points)

        # Add refinement in specified regions
        for r_min, r_max_refine, n_refine in refinement_regions:
            # Generate fine mesh in this region
            fine_mesh = np.linspace(r_min, r_max_refine, n_refine)
            mesh = np.concatenate([mesh, fine_mesh])
            mesh = np.unique(np.sort(mesh))  # Remove duplicates and sort

        return mesh

    def generate_axial_mesh(
        self,
        core_height: float,
        n_points: int = 50,
        refinement_regions: Optional[List[Tuple[float, float, int]]] = None,
    ) -> np.ndarray:
        """
        Generate axial mesh with optional local refinement.

        Args:
            core_height: Core height [cm]
            n_points: Base number of mesh points
            refinement_regions: List of (z_min, z_max, n_refine) for local refinement

        Returns:
            Axial mesh points [cm]
        """
        if refinement_regions is None:
            return np.linspace(0, core_height, n_points)

        # Similar to radial mesh generation
        mesh = np.linspace(0, core_height, n_points)

        for z_min, z_max_refine, n_refine in refinement_regions:
            fine_mesh = np.linspace(z_min, z_max_refine, n_refine)
            mesh = np.concatenate([mesh, fine_mesh])
            mesh = np.unique(np.sort(mesh))

        return mesh

    def generate_2d_unstructured_mesh(
        self,
        points: np.ndarray,
        boundary_points: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate 2D unstructured triangular mesh.

        Args:
            points: Interior points (N x 2)
            boundary_points: Boundary points (M x 2)

        Returns:
            Tuple of (vertices, triangles)
        """
        if boundary_points is not None:
            all_points = np.vstack([boundary_points, points])
        else:
            all_points = points

        # Use Delaunay triangulation
        tri = Delaunay(all_points)
        vertices = tri.points
        triangles = tri.simplices

        return vertices, triangles

    def evaluate_mesh_quality(
        self, vertices: np.ndarray, triangles: np.ndarray
    ) -> MeshQuality:
        """
        Evaluate quality of triangular mesh.

        Args:
            vertices: Vertex coordinates (N x 2 or N x 3)
            triangles: Triangle connectivity (M x 3)

        Returns:
            MeshQuality object
        """
        angles = []
        edge_lengths = []

        for triangle in triangles:
            # Get triangle vertices
            v0, v1, v2 = vertices[triangle]

            # Calculate edge lengths
            e0 = np.linalg.norm(v1 - v0)
            e1 = np.linalg.norm(v2 - v1)
            e2 = np.linalg.norm(v0 - v2)
            edge_lengths.extend([e0, e1, e2])

            # Calculate angles using law of cosines
            if len(v0) == 2:  # 2D
                # Angle at v0
                cos_angle0 = (e0**2 + e2**2 - e1**2) / (2 * e0 * e2)
                angle0 = np.arccos(np.clip(cos_angle0, -1, 1)) * 180 / np.pi

                # Angle at v1
                cos_angle1 = (e0**2 + e1**2 - e2**2) / (2 * e0 * e1)
                angle1 = np.arccos(np.clip(cos_angle1, -1, 1)) * 180 / np.pi

                # Angle at v2
                cos_angle2 = (e1**2 + e2**2 - e0**2) / (2 * e1 * e2)
                angle2 = np.arccos(np.clip(cos_angle2, -1, 1)) * 180 / np.pi

                angles.extend([angle0, angle1, angle2])

        edge_lengths = np.array(edge_lengths)
        angles = np.array(angles)

        min_angle = np.min(angles)
        max_angle = np.max(angles)
        aspect_ratio = np.max(edge_lengths) / np.min(edge_lengths) if np.min(edge_lengths) > 0 else np.inf

        # Skewness (simplified - ratio of min to ideal angle for equilateral triangle)
        ideal_angle = 60.0  # For equilateral triangle
        skewness = min_angle / ideal_angle

        return MeshQuality(
            min_angle=min_angle,
            max_angle=max_angle,
            aspect_ratio=aspect_ratio,
            skewness=skewness,
            jacobian=1.0,  # Simplified - would need actual Jacobian calculation
        )

    def refine_mesh(
        self,
        vertices: np.ndarray,
        triangles: np.ndarray,
        refinement_criteria: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Refine mesh based on criteria (e.g., error indicators).

        This is a simplified implementation that splits triangles with high
        refinement criteria by adding midpoints on each edge.

        Args:
            vertices: Current vertex coordinates (n_vertices, 2)
            triangles: Current triangle connectivity (n_triangles, 3)
            refinement_criteria: Array of refinement indicators per triangle (n_triangles,)

        Returns:
            Tuple of (refined_vertices, refined_triangles)

        Note:
            This is a basic implementation. For production use, consider
            specialized mesh refinement libraries (e.g., meshio, gmsh) for
            more sophisticated refinement strategies.
        """
        if refinement_criteria is None:
            # No refinement
            return vertices, triangles

        if len(refinement_criteria) != len(triangles):
            raise ValueError(
                f"refinement_criteria length ({len(refinement_criteria)}) must match "
                f"number of triangles ({len(triangles)})"
            )

        # Determine threshold for refinement
        # Use median * 1.5 for multiple values, or a fixed multiplier for single value
        if len(refinement_criteria) > 1:
            threshold = np.median(refinement_criteria) * 1.5
        else:
            # For single value, use a threshold that allows refinement for values > median
            # Use a fraction that's less than 1.0 so values above the median will refine
            threshold = refinement_criteria[0] * 0.8

        # Identify triangles to refine
        to_refine = refinement_criteria > threshold

        if not np.any(to_refine):
            # No triangles need refinement
            return vertices, triangles

        # Start with existing vertices
        new_vertices = vertices.tolist()
        new_triangles = []

        # Map to track midpoints we've already created (edge -> vertex_index)
        edge_midpoint_map = {}

        def get_or_create_midpoint(v1_idx: int, v2_idx: int) -> int:
            """Get or create midpoint vertex for an edge."""
            # Use sorted indices as edge key (order-independent)
            edge_key = tuple(sorted([v1_idx, v2_idx]))

            if edge_key in edge_midpoint_map:
                return edge_midpoint_map[edge_key]

            # Create new midpoint
            v1 = vertices[v1_idx]
            v2 = vertices[v2_idx]
            midpoint = ((v1[0] + v2[0]) / 2, (v1[1] + v2[1]) / 2)
            midpoint_idx = len(new_vertices)
            new_vertices.append(midpoint)
            edge_midpoint_map[edge_key] = midpoint_idx
            return midpoint_idx

        # Process each triangle
        for tri_idx, (tri, refine) in enumerate(zip(triangles, to_refine)):
            v0, v1, v2 = int(tri[0]), int(tri[1]), int(tri[2])

            if not refine:
                # Keep original triangle
                new_triangles.append([v0, v1, v2])
            else:
                # Split triangle into 4 sub-triangles using edge midpoints
                m01 = get_or_create_midpoint(v0, v1)
                m12 = get_or_create_midpoint(v1, v2)
                m20 = get_or_create_midpoint(v2, v0)

                # Create 4 sub-triangles
                new_triangles.append([v0, m01, m20])
                new_triangles.append([v1, m12, m01])
                new_triangles.append([v2, m20, m12])
                new_triangles.append([m01, m12, m20])

        return np.array(new_vertices), np.array(new_triangles, dtype=int)


def compute_mesh_gradient(
    field: np.ndarray, mesh: np.ndarray, method: str = "central"
) -> np.ndarray:
    """
    Compute gradient of field on mesh.

    Args:
        field: Field values
        mesh: Mesh coordinates
        method: Difference method ('forward', 'backward', 'central')

    Returns:
        Gradient values
    """
    if method == "central":
        gradient = np.gradient(field, mesh, edge_order=2)
    elif method == "forward":
        gradient = np.diff(field) / np.diff(mesh)
        gradient = np.concatenate([[gradient[0]], gradient])  # Extend
    elif method == "backward":
        gradient = np.diff(field) / np.diff(mesh)
        gradient = np.concatenate([gradient, [gradient[-1]]])  # Extend
    else:
        raise ValueError(f"Unknown method: {method}")

    return gradient

