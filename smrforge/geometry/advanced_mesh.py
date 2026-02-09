"""
Advanced 3D mesh generation utilities.

Provides enhanced mesh generation capabilities including:
- 3D structured and unstructured mesh generation
- Hybrid mesh generation
- Parallel mesh generation
- Mesh conversion utilities
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy.spatial import Delaunay

try:
    from joblib import Parallel, delayed

    _JOBLIB_AVAILABLE = True
except ImportError:  # pragma: no cover
    _JOBLIB_AVAILABLE = False
    Parallel = None  # type: ignore
    delayed = None  # type: ignore

try:
    import meshio

    _MESHIO_AVAILABLE = True
except ImportError:  # pragma: no cover
    _MESHIO_AVAILABLE = False
    meshio = None  # type: ignore

try:
    import pyvista as pv

    _PYVISTA_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYVISTA_AVAILABLE = False
    pv = None  # type: ignore

from smrforge.geometry.mesh_3d import Mesh3D
from smrforge.geometry.mesh_generation import AdvancedMeshGenerator, MeshType


class StructuredMesh3D:
    """3D structured mesh (regular grid)."""

    def __init__(self, nx: int, ny: int, nz: int, bounds: Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]):
        """
        Create 3D structured mesh.

        Args:
            nx, ny, nz: Number of cells in each direction
            bounds: ((x_min, x_max), (y_min, y_max), (z_min, z_max))
        """
        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.bounds = bounds

        # Generate grid points
        x = np.linspace(bounds[0][0], bounds[0][1], nx + 1)
        y = np.linspace(bounds[1][0], bounds[1][1], ny + 1)
        z = np.linspace(bounds[2][0], bounds[2][1], nz + 1)

        # Create 3D grid
        self.x, self.y, self.z = np.meshgrid(x, y, z, indexing="ij")
        self.vertices = np.stack([self.x.ravel(), self.y.ravel(), self.z.ravel()], axis=1)

        # Generate hexahedral cells
        self.cells = []
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    # Hexahedral cell vertices (8 corners)
                    v0 = i * (ny + 1) * (nz + 1) + j * (nz + 1) + k
                    v1 = (i + 1) * (ny + 1) * (nz + 1) + j * (nz + 1) + k
                    v2 = (i + 1) * (ny + 1) * (nz + 1) + (j + 1) * (nz + 1) + k
                    v3 = i * (ny + 1) * (nz + 1) + (j + 1) * (nz + 1) + k
                    v4 = i * (ny + 1) * (nz + 1) + j * (nz + 1) + k + 1
                    v5 = (i + 1) * (ny + 1) * (nz + 1) + j * (nz + 1) + k + 1
                    v6 = (i + 1) * (ny + 1) * (nz + 1) + (j + 1) * (nz + 1) + k + 1
                    v7 = i * (ny + 1) * (nz + 1) + (j + 1) * (nz + 1) + k + 1

                    self.cells.append([v0, v1, v2, v3, v4, v5, v6, v7])

        self.cells = np.array(self.cells, dtype=np.int64)

    def to_mesh3d(self, cell_materials: Optional[np.ndarray] = None) -> Mesh3D:
        """Convert to Mesh3D format."""
        return Mesh3D(
            vertices=self.vertices,
            cells=self.cells,
            cell_materials=cell_materials,
        )


class AdvancedMeshGenerator3D:
    """
    Advanced 3D mesh generator with support for structured, unstructured, and hybrid meshes.
    """

    def __init__(self, mesh_type: MeshType = MeshType.UNSTRUCTURED, n_jobs: int = 1):
        """
        Initialize 3D mesh generator.

        Args:
            mesh_type: Type of mesh to generate
            n_jobs: Number of parallel jobs (1 = sequential, -1 = all cores)
        """
        self.mesh_type = mesh_type
        self.n_jobs = n_jobs

    def generate_structured_3d(
        self,
        bounds: Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]],
        resolution: Union[int, Tuple[int, int, int]] = (50, 50, 50),
    ) -> StructuredMesh3D:
        """
        Generate 3D structured mesh (regular hexahedral grid).

        Args:
            bounds: ((x_min, x_max), (y_min, y_max), (z_min, z_max))
            resolution: Number of cells (int or (nx, ny, nz))

        Returns:
            StructuredMesh3D instance

        Examples:
            >>> from smrforge.geometry.advanced_mesh import AdvancedMeshGenerator3D
            >>> 
            >>> generator = AdvancedMeshGenerator3D(mesh_type=MeshType.STRUCTURED)
            >>> mesh = generator.generate_structured_3d(
            ...     bounds=((0, 150), (0, 150), (0, 793)),
            ...     resolution=(30, 30, 40)
            ... )
            >>> mesh3d = mesh.to_mesh3d()
        """
        if isinstance(resolution, int):
            nx = ny = nz = resolution
        else:
            nx, ny, nz = resolution

        return StructuredMesh3D(nx, ny, nz, bounds)

    def generate_unstructured_3d(
        self,
        points: np.ndarray,
        boundary_points: Optional[np.ndarray] = None,
        method: str = "delaunay",
    ) -> Mesh3D:
        """
        Generate 3D unstructured mesh (tetrahedral).

        Args:
            points: Interior points [n_points, 3]
            boundary_points: Boundary points [n_boundary, 3]
            method: Meshing method ('delaunay', 'constrained_delaunay')

        Returns:
            Mesh3D instance with tetrahedral cells

        Examples:
            >>> import numpy as np
            >>> from smrforge.geometry.advanced_mesh import AdvancedMeshGenerator3D
            >>> 
            >>> generator = AdvancedMeshGenerator3D()
            >>> # Generate interior points
            >>> points = np.random.rand(100, 3) * 100
            >>> mesh = generator.generate_unstructured_3d(points)
        """
        if boundary_points is not None:
            all_points = np.vstack([boundary_points, points])
        else:
            all_points = points

        if method == "delaunay":
            # 3D Delaunay triangulation (tetrahedralization)
            from scipy.spatial import ConvexHull

            try:
                # Try Delaunay triangulation
                tri = Delaunay(all_points)
                # Extract tetrahedra (simplices in 3D)
                cells = tri.simplices  # [n_tets, 4]
                vertices = tri.points
            except Exception:  # pragma: no cover
                # Fallback: Use convex hull faces
                hull = ConvexHull(all_points)
                # Convert hull to surface mesh (faces only, no cells)
                faces = hull.simplices
                vertices = hull.points
                cells = None

            return Mesh3D(vertices=vertices, cells=cells, faces=faces if cells is None else None)
        else:
            raise ValueError(f"Unknown method: {method}")

    def generate_hybrid_3d(
        self,
        core_region: Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]],
        refinement_regions: List[Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float], int]],
        base_resolution: int = 20,
    ) -> Mesh3D:
        """
        Generate hybrid 3D mesh (structured core + unstructured refinement regions).

        Args:
            core_region: Core mesh region ((x_min, x_max), (y_min, y_max), (z_min, z_max))
            refinement_regions: List of (bounds, resolution) for unstructured refinement
            base_resolution: Base resolution for structured core

        Returns:
            Mesh3D instance with hybrid structure

        Examples:
            >>> from smrforge.geometry.advanced_mesh import AdvancedMeshGenerator3D
            >>> 
            >>> generator = AdvancedMeshGenerator3D(mesh_type=MeshType.HYBRID)
            >>> core = ((0, 150), (0, 150), (0, 793))
            >>> refinement = [(((0, 50), (0, 50), (0, 200), 30))]  # Fine mesh in center
            >>> mesh = generator.generate_hybrid_3d(core, refinement, base_resolution=20)
        """
        # Generate structured core mesh
        core_mesh = self.generate_structured_3d(core_region, resolution=base_resolution)
        core_mesh3d = core_mesh.to_mesh3d()

        # Generate unstructured refinement regions
        refinement_meshes = []
        if self.n_jobs > 1 and _JOBLIB_AVAILABLE:
            # Parallel generation
            refinement_meshes = Parallel(n_jobs=self.n_jobs)(
                delayed(self._generate_refinement_region)(region) for region in refinement_regions
            )
        else:
            # Sequential generation
            for region in refinement_regions:
                refinement_mesh = self._generate_refinement_region(region)
                if refinement_mesh:
                    refinement_meshes.append(refinement_mesh)

        # Combine meshes
        from smrforge.geometry.mesh_3d import combine_meshes

        if refinement_meshes:
            all_meshes = [core_mesh3d] + refinement_meshes
            combined = combine_meshes(all_meshes)
            return combined
        else:
            return core_mesh3d

    def _generate_refinement_region(
        self, region: Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float], int]
    ) -> Optional[Mesh3D]:
        """Generate unstructured mesh for a refinement region."""
        bounds = (region[0], region[1], region[2])
        resolution = region[3]

        # Generate points in region
        x_min, x_max = bounds[0]
        y_min, y_max = bounds[1]
        z_min, z_max = bounds[2]

        # Create point cloud
        n_points = resolution**3
        points = np.random.uniform(
            low=[x_min, y_min, z_min],
            high=[x_max, y_max, z_max],
            size=(n_points, 3),
        )

        # Generate unstructured mesh
        try:
            return self.generate_unstructured_3d(points)
        except Exception:  # pragma: no cover
            return None

    def generate_parallel(
        self,
        regions: List[Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]],
        resolution: Union[int, List[int]] = 30,
        mesh_type: Optional[MeshType] = None,
    ) -> List[Mesh3D]:
        """
        Generate meshes for multiple regions in parallel.

        Args:
            regions: List of region bounds
            resolution: Resolution per region (int or list of ints)
            mesh_type: Optional mesh type override

        Returns:
            List of Mesh3D instances

        Examples:
            >>> from smrforge.geometry.advanced_mesh import AdvancedMeshGenerator3D
            >>> 
            >>> generator = AdvancedMeshGenerator3D(n_jobs=-1)  # Use all cores
            >>> regions = [
            ...     ((0, 50), (0, 50), (0, 200)),
            ...     ((50, 150), (50, 150), (200, 400))
            ... ]
            >>> meshes = generator.generate_parallel(regions, resolution=30)
        """
        if mesh_type is None:
            mesh_type = self.mesh_type

        if isinstance(resolution, int):
            resolutions = [resolution] * len(regions)
        else:
            resolutions = resolution

        if self.n_jobs > 1 and _JOBLIB_AVAILABLE:
            # Parallel generation
            meshes = Parallel(n_jobs=self.n_jobs)(
                delayed(self._generate_mesh_for_region)(region, res, mesh_type)
                for region, res in zip(regions, resolutions)
            )
        else:
            # Sequential generation
            meshes = [
                self._generate_mesh_for_region(region, res, mesh_type)
                for region, res in zip(regions, resolutions)
            ]

        return [m for m in meshes if m is not None]

    def _generate_mesh_for_region(
        self,
        bounds: Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]],
        resolution: int,
        mesh_type: MeshType,
    ) -> Optional[Mesh3D]:
        """Generate mesh for a single region."""
        try:
            if mesh_type == MeshType.STRUCTURED:
                mesh = self.generate_structured_3d(bounds, resolution=resolution)
                return mesh.to_mesh3d()
            elif mesh_type == MeshType.UNSTRUCTURED:
                # Generate random points in region
                n_points = resolution**3
                points = np.random.uniform(
                    low=[b[0] for b in bounds],
                    high=[b[1] for b in bounds],
                    size=(n_points, 3),
                )
                return self.generate_unstructured_3d(points)
            else:
                # Default to structured
                mesh = self.generate_structured_3d(bounds, resolution=resolution)
                return mesh.to_mesh3d()
        except Exception:  # pragma: no cover
            return None


class MeshConverter:
    """
    Utilities for converting meshes between different formats.
    """

    @staticmethod
    def convert_to_format(
        mesh: Mesh3D,
        output_path: Path,
        output_format: str,
        **kwargs,
    ) -> bool:
        """
        Convert Mesh3D to various formats.

        Args:
            mesh: Mesh3D instance
            output_path: Output file path
            output_format: Format ('vtk', 'vtu', 'xdmf', 'stl', 'obj', 'ply', 'msh', 'med')

        Returns:
            True if conversion successful

        Examples:
            >>> from pathlib import Path
            >>> from smrforge.geometry.advanced_mesh import MeshConverter
            >>> from smrforge.geometry.mesh_extraction import extract_core_volume_mesh
            >>> 
            >>> mesh = extract_core_volume_mesh(core)
            >>> MeshConverter.convert_to_format(mesh, Path("output.vtk"), "vtk")
        """
        output_format = output_format.lower()

        if output_format in ["vtk", "vtu"]:
            return MeshConverter._export_to_vtk(mesh, output_path, output_format, **kwargs)
        elif output_format == "stl":
            return MeshConverter._export_to_stl(mesh, output_path, **kwargs)
        elif output_format in ["xdmf", "obj", "ply", "msh", "med"]:
            if _MESHIO_AVAILABLE:
                return MeshConverter._export_with_meshio(mesh, output_path, output_format, **kwargs)
            else:
                raise ImportError(
                    f"meshio is required for {output_format} export. "
                    "Install with: pip install meshio"
                )
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    @staticmethod
    def _export_to_vtk(mesh: Mesh3D, output_path: Path, format: str = "vtk", **kwargs) -> bool:
        """Export to VTK format."""
        if _PYVISTA_AVAILABLE:
            from smrforge.visualization.mesh_3d import export_mesh_to_vtk

            export_mesh_to_vtk(mesh, str(output_path))
            return True
        elif _MESHIO_AVAILABLE:
            return MeshConverter._export_with_meshio(mesh, output_path, format, **kwargs)
        else:
            raise ImportError(
                "PyVista or meshio is required for VTK export. "
                "Install with: pip install pyvista or pip install meshio"
            )

    @staticmethod
    def _export_to_stl(mesh: Mesh3D, output_path: Path, **kwargs) -> bool:
        """Export to STL format (surface mesh only)."""
        if mesh.faces is None:
            raise ValueError("STL export requires faces (surface mesh)")

        if _MESHIO_AVAILABLE:
            # Use meshio for STL export
            cells = {"triangle": mesh.faces}
            point_data = {}
            cell_data = {}

            # Add face data if available
            if mesh.face_data:
                for name, data in mesh.face_data.items():
                    cell_data[name] = [data]

            mesh_data = meshio.Mesh(
                points=mesh.vertices,
                cells=cells,
                point_data=point_data,
                cell_data=cell_data,
            )
            meshio.write(str(output_path), mesh_data, file_format="stl")
            return True
        else:
            # Fallback: Use trimesh if available
            try:
                import trimesh

                # Create trimesh surface
                trimesh_mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces)
                trimesh_mesh.export(str(output_path))
                return True
            except ImportError:  # pragma: no cover
                raise ImportError(
                    "meshio or trimesh is required for STL export. "
                    "Install with: pip install meshio[all] or pip install trimesh"
                )

    @staticmethod
    def _export_with_meshio(mesh: Mesh3D, output_path: Path, format: str, **kwargs) -> bool:
        """Export using meshio library."""
        if not _MESHIO_AVAILABLE:
            raise ImportError("meshio is required. Install with: pip install meshio[all]")

        # Prepare cells
        cells = {}
        if mesh.cells is not None:
            if mesh.cells.shape[1] == 4:
                cells["tetra"] = mesh.cells
            elif mesh.cells.shape[1] == 8:
                cells["hexahedron"] = mesh.cells
        elif mesh.faces is not None:
            if mesh.faces.shape[1] == 3:
                cells["triangle"] = mesh.faces
            elif mesh.faces.shape[1] == 4:
                cells["quad"] = mesh.faces

        # Prepare point data
        point_data = {}

        # Prepare cell data
        cell_data = {}
        if mesh.cell_data:
            for name, data in mesh.cell_data.items():
                if mesh.cells is not None:
                    cell_key = "tetra" if mesh.cells.shape[1] == 4 else "hexahedron"
                    cell_data[name] = [data]
        if mesh.face_data:
            for name, data in mesh.face_data.items():
                if mesh.faces is not None:
                    cell_key = "triangle" if mesh.faces.shape[1] == 3 else "quad"
                    cell_data[name] = [data]

        # Add material IDs
        if mesh.cell_materials is not None and mesh.cells is not None:
            cell_key = "tetra" if mesh.cells.shape[1] == 4 else "hexahedron"
            cell_data["material"] = [mesh.cell_materials]

        # Create meshio mesh
        mesh_data = meshio.Mesh(
            points=mesh.vertices,
            cells=list(cells.items()),
            point_data=point_data,
            cell_data=cell_data,
        )

        # Write file
        meshio.write(str(output_path), mesh_data, file_format=format)
        return True

    @staticmethod
    def convert_between_formats(input_path: Path, output_path: Path, input_format: Optional[str] = None, output_format: Optional[str] = None) -> bool:
        """
        Convert mesh between different file formats.

        Args:
            input_path: Path to input mesh file
            output_path: Path to output mesh file
            input_format: Optional input format (auto-detected if None)
            output_format: Optional output format (auto-detected from extension if None)

        Returns:
            True if conversion successful

        Examples:
            >>> from pathlib import Path
            >>> from smrforge.geometry.advanced_mesh import MeshConverter
            >>> 
            >>> MeshConverter.convert_between_formats(
            ...     Path("input.vtk"),
            ...     Path("output.stl"),
            ...     output_format="stl"
            ... )
        """
        if not _MESHIO_AVAILABLE:
            raise ImportError("meshio is required for format conversion. Install with: pip install meshio[all]")

        # Auto-detect formats if not provided
        if input_format is None:
            input_format = input_path.suffix[1:].lower()  # Remove leading dot
        if output_format is None:
            output_format = output_path.suffix[1:].lower()

        # Read input mesh
        mesh_data = meshio.read(str(input_path), file_format=input_format)

        # Write output mesh
        meshio.write(str(output_path), mesh_data, file_format=output_format)

        return True

    @staticmethod
    def get_supported_formats() -> Dict[str, List[str]]:
        """
        Get list of supported input/output formats.

        Returns:
            Dictionary with 'input' and 'output' format lists
        """
        formats = {"input": [], "output": []}

        if _MESHIO_AVAILABLE:
            # Get formats from meshio
            formats["input"] = list(meshio.helpers.input_filetypes.keys())
            formats["output"] = list(meshio.helpers.output_filetypes.keys())

        # Add VTK-specific formats
        if _PYVISTA_AVAILABLE or _MESHIO_AVAILABLE:
            formats["input"].extend(["vtk", "vtu"])
            formats["output"].extend(["vtk", "vtu"])

        # Remove duplicates
        formats["input"] = sorted(list(set(formats["input"])))
        formats["output"] = sorted(list(set(formats["output"])))

        return formats

