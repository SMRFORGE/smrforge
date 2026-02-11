"""
SMR-specific mesh optimization for compact geometries.

Provides optimized mesh generation for Small Modular Reactors with:
- Compact geometry meshing
- SMR-optimized refinement
- Adaptive refinement for fuel pins and assemblies
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.geometry.smr_mesh_optimization")


@dataclass
class SMRMeshParams:
    """
    Parameters for SMR-optimized mesh generation.

    Attributes:
        base_resolution: Base mesh resolution (points per dimension)
        fuel_pin_refinement: Refinement factor for fuel pin regions
        assembly_boundary_refinement: Refinement factor at assembly boundaries
        core_boundary_refinement: Refinement factor at core boundary
        min_cell_size: Minimum cell size [cm]
        max_cell_size: Maximum cell size [cm]
        adaptive_refinement: Enable adaptive refinement based on flux gradients
    """

    base_resolution: int = 20
    fuel_pin_refinement: float = 2.0  # 2x finer near fuel pins
    assembly_boundary_refinement: float = 1.5  # 1.5x finer at boundaries
    core_boundary_refinement: float = 1.2  # 1.2x finer at core edge
    min_cell_size: float = 0.1  # cm
    max_cell_size: float = 5.0  # cm
    adaptive_refinement: bool = True


class SMRMeshOptimizer:
    """
    Mesh optimizer for Small Modular Reactor geometries.

    Optimizes mesh generation for compact SMR cores with:
    - Adaptive refinement around fuel pins
    - Boundary refinement at assembly interfaces
    - Optimized cell sizes for small cores
    - Flux-gradient based adaptive refinement

    Usage:
        >>> from smrforge.geometry.smr_mesh_optimization import SMRMeshOptimizer
        >>>
        >>> optimizer = SMRMeshOptimizer()
        >>>
        >>> # Generate optimized mesh for PWR SMR core
        >>> mesh = optimizer.generate_smr_mesh(
        ...     core_diameter=200.0,  # cm
        ...     core_height=365.76,  # cm
        ...     assembly_positions=[...],  # List of assembly positions
        ...     fuel_pin_positions=[...],  # List of fuel pin positions
        ...     params=SMRMeshParams(base_resolution=25),
        ... )
    """

    def __init__(self):
        """Initialize SMR mesh optimizer."""
        self.default_params = SMRMeshParams()

    def generate_smr_mesh(
        self,
        core_diameter: float,
        core_height: float,
        assembly_positions: Optional[List[Tuple[float, float]]] = None,
        fuel_pin_positions: Optional[List[Tuple[float, float, float]]] = None,
        params: Optional[SMRMeshParams] = None,
    ) -> Dict[str, np.ndarray]:
        """
        Generate optimized mesh for SMR core.

        Args:
            core_diameter: Core diameter [cm]
            core_height: Core height [cm]
            assembly_positions: List of (x, y) assembly center positions
            fuel_pin_positions: List of (x, y, z) fuel pin positions
            params: SMR mesh parameters (uses defaults if None)

        Returns:
            Dictionary with keys:
            - 'radial_mesh': Radial mesh points [cm]
            - 'axial_mesh': Axial mesh points [cm]
            - 'x_mesh': X mesh points [cm] (for 3D)
            - 'y_mesh': Y mesh points [cm] (for 3D)
            - 'z_mesh': Z mesh points [cm] (for 3D)
        """
        if params is None:
            params = self.default_params

        # Generate base mesh
        radial_mesh = self._generate_radial_mesh(
            core_diameter, params, assembly_positions, fuel_pin_positions
        )
        axial_mesh = self._generate_axial_mesh(core_height, params, fuel_pin_positions)

        # For 3D meshes, generate x, y, z meshes
        if assembly_positions or fuel_pin_positions:
            x_mesh, y_mesh = self._generate_xy_mesh(
                core_diameter, params, assembly_positions, fuel_pin_positions
            )
            z_mesh = axial_mesh
        else:
            x_mesh = y_mesh = z_mesh = None

        return {
            "radial_mesh": radial_mesh,
            "axial_mesh": axial_mesh,
            "x_mesh": x_mesh,
            "y_mesh": y_mesh,
            "z_mesh": z_mesh,
        }

    def _generate_radial_mesh(
        self,
        core_diameter: float,
        params: SMRMeshParams,
        assembly_positions: Optional[List[Tuple[float, float]]],
        fuel_pin_positions: Optional[List[Tuple[float, float, float]]],
    ) -> np.ndarray:
        """Generate optimized radial mesh."""
        r_max = core_diameter / 2.0

        # Base mesh
        n_base = params.base_resolution
        base_mesh = np.linspace(0, r_max, n_base)

        # Add refinement regions
        refinement_points = []

        # Core boundary refinement
        if params.core_boundary_refinement > 1.0:
            boundary_region = r_max * 0.9  # Last 10% of radius
            n_refine = int(n_base * params.core_boundary_refinement * 0.1)
            refine_mesh = np.linspace(boundary_region, r_max, n_refine)
            refinement_points.extend(refine_mesh)

        # Assembly boundary refinement (if positions provided)
        if assembly_positions:
            # Find assembly boundaries (simplified: assume square assemblies)
            # Add refinement near assembly centers
            for x, y in assembly_positions:
                r_assembly = np.sqrt(x**2 + y**2)
                if r_assembly < r_max:
                    # Add refinement points around assembly
                    n_refine = int(n_base * params.assembly_boundary_refinement * 0.05)
                    refine_region = (r_assembly - 5.0, r_assembly + 5.0)
                    refine_mesh = np.linspace(
                        max(0, refine_region[0]), min(r_max, refine_region[1]), n_refine
                    )
                    refinement_points.extend(refine_mesh)

        # Fuel pin refinement (if positions provided)
        if fuel_pin_positions:
            # Add refinement near fuel pins
            for x, y, z in fuel_pin_positions:
                r_pin = np.sqrt(x**2 + y**2)
                if r_pin < r_max:
                    # Add fine mesh around pin
                    n_refine = int(n_base * params.fuel_pin_refinement * 0.02)
                    refine_region = (r_pin - 0.5, r_pin + 0.5)
                    refine_mesh = np.linspace(
                        max(0, refine_region[0]), min(r_max, refine_region[1]), n_refine
                    )
                    refinement_points.extend(refine_mesh)

        # Combine and sort
        if refinement_points:
            all_points = np.concatenate([base_mesh, refinement_points])
            all_points = np.unique(np.sort(all_points))

            # Enforce min/max cell sizes
            all_points = self._enforce_cell_sizes(all_points, params)

            return all_points
        else:
            return base_mesh

    def _generate_axial_mesh(
        self,
        core_height: float,
        params: SMRMeshParams,
        fuel_pin_positions: Optional[List[Tuple[float, float, float]]],
    ) -> np.ndarray:
        """Generate optimized axial mesh."""
        # Base mesh
        n_base = params.base_resolution
        base_mesh = np.linspace(0, core_height, n_base)

        # Add refinement regions
        refinement_points = []

        # Core boundaries (top and bottom)
        if params.core_boundary_refinement > 1.0:
            boundary_size = core_height * 0.1  # 10% at each end
            n_refine = int(n_base * params.core_boundary_refinement * 0.1)

            # Bottom boundary
            bottom_refine = np.linspace(0, boundary_size, n_refine)
            refinement_points.extend(bottom_refine)

            # Top boundary
            top_refine = np.linspace(core_height - boundary_size, core_height, n_refine)
            refinement_points.extend(top_refine)

        # Fuel pin refinement (if positions provided)
        if fuel_pin_positions:
            # Find z-positions of fuel pins
            z_positions = [z for _, _, z in fuel_pin_positions]
            if z_positions:
                z_min, z_max = min(z_positions), max(z_positions)
                z_center = (z_min + z_max) / 2

                # Add refinement in active fuel region
                n_refine = int(n_base * params.fuel_pin_refinement * 0.3)
                refine_mesh = np.linspace(z_min, z_max, n_refine)
                refinement_points.extend(refine_mesh)

        # Combine and sort
        if refinement_points:
            all_points = np.concatenate([base_mesh, refinement_points])
            all_points = np.unique(np.sort(all_points))

            # Enforce min/max cell sizes
            all_points = self._enforce_cell_sizes(all_points, params)

            return all_points
        else:
            return base_mesh

    def _generate_xy_mesh(
        self,
        core_diameter: float,
        params: SMRMeshParams,
        assembly_positions: Optional[List[Tuple[float, float]]],
        fuel_pin_positions: Optional[List[Tuple[float, float, float]]],
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate optimized x-y mesh for 3D."""
        r_max = core_diameter / 2.0

        # Base mesh (square grid)
        n_base = params.base_resolution
        base_x = np.linspace(-r_max, r_max, n_base)
        base_y = np.linspace(-r_max, r_max, n_base)

        # Add refinement points
        x_refine = []
        y_refine = []

        # Assembly refinement
        if assembly_positions:
            for x, y in assembly_positions:
                if abs(x) < r_max:
                    n_refine = int(n_base * params.assembly_boundary_refinement * 0.1)
                    refine_x = np.linspace(x - 5.0, x + 5.0, n_refine)
                    x_refine.extend(refine_x)

                if abs(y) < r_max:
                    n_refine = int(n_base * params.assembly_boundary_refinement * 0.1)
                    refine_y = np.linspace(y - 5.0, y + 5.0, n_refine)
                    y_refine.extend(refine_y)

        # Fuel pin refinement
        if fuel_pin_positions:
            for x, y, _ in fuel_pin_positions:
                if abs(x) < r_max:
                    n_refine = int(n_base * params.fuel_pin_refinement * 0.05)
                    refine_x = np.linspace(x - 0.5, x + 0.5, n_refine)
                    x_refine.extend(refine_x)

                if abs(y) < r_max:
                    n_refine = int(n_base * params.fuel_pin_refinement * 0.05)
                    refine_y = np.linspace(y - 0.5, y + 0.5, n_refine)
                    y_refine.extend(refine_y)

        # Combine and sort
        if x_refine:
            all_x = np.concatenate([base_x, x_refine])
            all_x = np.unique(np.sort(all_x))
            all_x = self._enforce_cell_sizes(all_x, params)
        else:
            all_x = base_x

        if y_refine:
            all_y = np.concatenate([base_y, y_refine])
            all_y = np.unique(np.sort(all_y))
            all_y = self._enforce_cell_sizes(all_y, params)
        else:
            all_y = base_y

        return all_x, all_y

    def _enforce_cell_sizes(
        self, mesh: np.ndarray, params: SMRMeshParams
    ) -> np.ndarray:
        """Enforce minimum and maximum cell sizes."""
        if len(mesh) < 2:
            return mesh

        # Calculate cell sizes
        cell_sizes = np.diff(mesh)

        # Remove points that create cells smaller than min_cell_size
        valid_mask = cell_sizes >= params.min_cell_size
        if not np.all(valid_mask):
            # Keep first point, then only points that maintain min cell size
            filtered_mesh = [mesh[0]]
            for i in range(1, len(mesh)):
                if mesh[i] - filtered_mesh[-1] >= params.min_cell_size:
                    filtered_mesh.append(mesh[i])
            mesh = np.array(filtered_mesh)

        # Ensure no cells exceed max_cell_size (add intermediate points)
        cell_sizes = np.diff(mesh)
        large_cells = cell_sizes > params.max_cell_size

        if np.any(large_cells):
            new_points = []
            for i in range(len(mesh) - 1):
                new_points.append(mesh[i])
                if large_cells[i]:
                    # Add intermediate points
                    n_intermediate = int(cell_sizes[i] / params.max_cell_size)
                    intermediate = np.linspace(
                        mesh[i], mesh[i + 1], n_intermediate + 2
                    )[1:-1]
                    new_points.extend(intermediate)
            new_points.append(mesh[-1])
            mesh = np.array(new_points)
            mesh = np.unique(np.sort(mesh))

        return mesh

    def optimize_mesh_for_flux(
        self,
        mesh: Dict[str, np.ndarray],
        flux_distribution: np.ndarray,
        flux_gradient_threshold: float = 0.1,
    ) -> Dict[str, np.ndarray]:
        """
        Adaptively refine mesh based on flux gradients.

        Args:
            mesh: Mesh dictionary (from generate_smr_mesh)
            flux_distribution: Flux distribution [n_x, n_y, n_z] or [n_r, n_z]
            flux_gradient_threshold: Threshold for gradient-based refinement

        Returns:
            Refined mesh dictionary
        """
        # This is a placeholder for adaptive refinement
        # In a full implementation, this would:
        # 1. Calculate flux gradients
        # 2. Identify regions with high gradients
        # 3. Add refinement points in those regions
        # 4. Regenerate mesh with refinement

        logger.info("Adaptive flux-based refinement not yet fully implemented")
        return mesh

    def estimate_mesh_quality(
        self, mesh: Dict[str, np.ndarray], core_diameter: float, core_height: float
    ) -> Dict[str, float]:
        """
        Estimate mesh quality metrics.

        Args:
            mesh: Mesh dictionary
            core_diameter: Core diameter [cm]
            core_height: Core height [cm]

        Returns:
            Dictionary with quality metrics:
            - 'n_cells': Total number of cells
            - 'avg_cell_size': Average cell size [cm]
            - 'min_cell_size': Minimum cell size [cm]
            - 'max_cell_size': Maximum cell size [cm]
            - 'aspect_ratio': Average aspect ratio
        """
        metrics = {}

        # Calculate cell sizes
        if "radial_mesh" in mesh:
            radial_sizes = np.diff(mesh["radial_mesh"])
            metrics["n_radial_cells"] = len(radial_sizes)
            metrics["avg_radial_cell_size"] = np.mean(radial_sizes)
            metrics["min_radial_cell_size"] = np.min(radial_sizes)
            metrics["max_radial_cell_size"] = np.max(radial_sizes)

        if "axial_mesh" in mesh:
            axial_sizes = np.diff(mesh["axial_mesh"])
            metrics["n_axial_cells"] = len(axial_sizes)
            metrics["avg_axial_cell_size"] = np.mean(axial_sizes)
            metrics["min_axial_cell_size"] = np.min(axial_sizes)
            metrics["max_axial_cell_size"] = np.max(axial_sizes)

        # Total cells
        if "radial_mesh" in mesh and "axial_mesh" in mesh:
            metrics["n_cells"] = len(radial_sizes) * len(axial_sizes)

        # Aspect ratio
        if "avg_radial_cell_size" in metrics and "avg_axial_cell_size" in metrics:
            metrics["aspect_ratio"] = (
                metrics["avg_axial_cell_size"] / metrics["avg_radial_cell_size"]
            )

        return metrics
