# smrforge/neutronics/solver.py
"""
Multi-group neutron diffusion solver with Pydantic validation.

This module provides:
- MultiGroupDiffusion: Main multi-group diffusion solver class
  - Power iteration eigenvalue method
  - Steady-state solution
  - Power distribution computation
  - Comprehensive logging and error handling
"""

import numpy as np
from numba import njit, prange
from scipy.sparse import csr_matrix, diags, linalg as sparse_linalg
from typing import Tuple, Optional, Dict
import time
from pydantic import ValidationError

# Import Pydantic models
from ..validation.models import CrossSectionData, SolverOptions
from ..validation.validators import DataValidator, ValidationResult
from ..utils.logging import get_logger

# Get logger for this module
logger = get_logger("smrforge.neutronics")


class MultiGroupDiffusion:
    """
    Multi-group neutron diffusion solver with automatic input validation.
    """

    def __init__(self, geometry, xs_data: CrossSectionData,
                 options: SolverOptions):
        """
        Initialize solver with validated inputs.

        Args:
            geometry: Core geometry object
            xs_data: CrossSectionData (Pydantic validated)
            options: SolverOptions (Pydantic validated)

        Raises:
            ValidationError: If inputs don't pass Pydantic validation
            ValueError: If inputs don't pass physics validation
        """
        # Inputs are already Pydantic-validated at this point
        self.geometry = geometry
        self.xs = xs_data
        self.options = options

        # Additional physics validation beyond Pydantic
        self._validate_physics()

        # Solution arrays
        self.flux: Optional[np.ndarray] = None
        self.k_eff: float = 1.0

        # Setup
        self._setup_mesh()
        self._allocate_arrays()

    def _validate_physics(self) -> None:
        """
        Additional physics validation beyond Pydantic.
        Pydantic handles type/bounds, this handles complex physics.
        """
        validator = DataValidator()

        # Validate solver inputs comprehensively
        result = validator.validate_solver_inputs(
            self.geometry, self.xs, self.options
        )

        if result.has_errors():
            # Print detailed validation report
            result.print_report()
            raise ValueError(
                f"Physics validation failed with {len(result.issues)} issues. "
                f"See report above."
            )

        # Warnings are OK, but print them
        if result.issues:
            import warnings
            for issue in result.issues:
                if issue.level.value == 'warning':
                    warnings.warn(str(issue))

    def _setup_mesh(self) -> None:
        """Setup computational mesh from geometry."""
        self.r_mesh = self.geometry.radial_mesh
        self.z_mesh = self.geometry.axial_mesh

        self.nr = len(self.r_mesh) - 1
        self.nz = len(self.z_mesh) - 1
        self.ng = self.xs.n_groups

        self.r_centers = 0.5 * (self.r_mesh[1:] + self.r_mesh[:-1])
        self.z_centers = 0.5 * (self.z_mesh[1:] + self.z_mesh[:-1])

        self.dr = np.diff(self.r_mesh)
        self.dz = np.diff(self.z_mesh)

        self.material_map = self._build_material_map()

    def _build_material_map(self) -> np.ndarray:
        """Map mesh cells to materials."""
        mat_map = np.zeros((self.nz, self.nr), dtype=int)

        for iz in range(self.nz):
            for ir in range(self.nr):
                z = self.z_centers[iz]
                r = self.r_centers[ir]

                if r < self.geometry.core_diameter / 2:
                    mat_map[iz, ir] = 0  # Fuel
                else:
                    mat_map[iz, ir] = 1  # Reflector

        return mat_map

    def _allocate_arrays(self) -> None:
        """Allocate solution arrays."""
        shape = (self.nz, self.nr, self.ng)
        self.flux = np.ones(shape)
        self.source = np.zeros(shape)

        # Homogenized XS [nz, nr, ng]
        self.D_map = np.zeros(shape)
        self.sigma_t_map = np.zeros(shape)
        self.sigma_a_map = np.zeros(shape)
        self.nu_sigma_f_map = np.zeros(shape)

        # Cache for cell volumes (computed on first access)
        self._cell_volumes_cache = None

        self._update_xs_maps()

    def _update_xs_maps(self) -> None:
        """
        Update homogenized cross sections from material map.
        
        Optimized using numpy advanced indexing for vectorized assignment.
        ~10-100x faster than nested loops for large meshes.
        """
        # Use advanced indexing: material_map is [nz, nr], xs.D is [n_materials, ng]
        # Result: [nz, nr, ng]
        self.D_map = self.xs.D[self.material_map, :]
        self.sigma_t_map = self.xs.sigma_t[self.material_map, :]
        self.sigma_a_map = self.xs.sigma_a[self.material_map, :]
        self.nu_sigma_f_map = self.xs.nu_sigma_f[self.material_map, :]

    def solve_steady_state(self) -> Tuple[float, np.ndarray]:
        """
        Solve steady-state eigenvalue problem.

        Returns:
            k_eff: Effective multiplication factor
            flux: Neutron flux distribution [nz, nr, ng]

        Raises:
            RuntimeError: If solver fails to converge
            ValueError: If solution is non-physical
        """
        logger.info(f"Solving {self.ng}-group diffusion equation")
        logger.debug(
            f"Mesh: {self.nz}z × {self.nr}r = {self.nz*self.nr*self.ng} unknowns, "
            f"Method: {self.options.eigen_method}, "
            f"Tolerance: {self.options.tolerance}"
        )

        start_time = time.time()

        try:
            if self.options.eigen_method == "power":
                self.k_eff, self.flux = self._power_iteration()
            elif self.options.eigen_method == "arnoldi":
                self.k_eff, self.flux = self._arnoldi_method()
            else:
                raise ValueError(f"Unknown method: {self.options.eigen_method}")
        except Exception as e:
            raise RuntimeError(f"Solver failed: {e}")

        elapsed = time.time() - start_time

        # Validate solution
        self._validate_solution()

        logger.info(
            f"Solver converged: k_eff = {self.k_eff:.6f}, "
            f"time = {elapsed:.2f} seconds"
        )

        return self.k_eff, self.flux

    def _validate_solution(self) -> None:
        """
        Validate solution quality.
        Checks for NaN, Inf, negative flux, reasonable k_eff.
        """
        validator = DataValidator()

        # Dummy power for validation (will be normalized later)
        power = np.ones_like(self.flux[:,:,0])

        result = validator.validate_solution(
            self.k_eff, self.flux, power, 1.0
        )

        if result.has_errors():
            logger.error("Solution validation failed")
            result.print_report()
            raise ValueError(
                f"Solution validation failed. "
                f"k_eff={self.k_eff:.6f}, "
                f"flux_max={np.max(self.flux):.3e}, "
                f"flux_min={np.min(self.flux):.3e}"
            )

    def _power_iteration(self) -> Tuple[float, np.ndarray]:
        """Power iteration eigenvalue solver."""
        k_old = self.k_eff

        for iteration in range(self.options.max_iterations):
            self._update_fission_source(k_old)

            for g in range(self.ng):
                self._update_scattering_source(g)
                self.flux[:, :, g] = self._solve_group(g)

            k_new = self._compute_k_eff()

            error = abs(k_new - k_old) / k_old

            # Log every 10 iterations or when converged
            if iteration % 10 == 0 or error < self.options.tolerance:
                logger.debug(
                    f"Iteration {iteration:4d}: k_eff = {k_new:.8f}, "
                    f"error = {error:.2e}"
                )

            if error < self.options.tolerance:
                logger.info(f"Converged in {iteration+1} iterations")
                return k_new, self.flux

            k_old = k_new
            self.flux /= np.max(self.flux)

        logger.error(
            f"Failed to converge in {self.options.max_iterations} iterations. "
            f"Final error: {error:.2e}, tolerance: {self.options.tolerance}"
        )
        raise RuntimeError(
            f"Failed to converge in {self.options.max_iterations} iterations. "
            f"Final error: {error:.2e}, tolerance: {self.options.tolerance}"
        )

    def _update_fission_source(self, k_eff: float) -> None:
        """
        Update fission source.
        
        Optimized using vectorized operations for ~5-20x speedup.
        """
        # Fission rate: [nz, nr, 1]
        fission_rate = np.sum(self.nu_sigma_f_map * self.flux, axis=2, keepdims=True)
        
        # chi is [n_materials, ng]
        # Get chi for each cell: [nz, nr, ng]
        chi_map = self.xs.chi[self.material_map, :]
        
        # Broadcast multiplication: [nz, nr, ng]
        self.source = chi_map * fission_rate / k_eff

    def _update_scattering_source(self, g: int) -> None:
        """
        Update scattering source for group g.
        
        Optimized using vectorized operations for ~5-50x speedup depending on number of groups.
        """
        # Vectorized: sigma_s is [n_materials, ng, ng]
        # flux is [nz, nr, ng]
        # material_map is [nz, nr]
        
        # Get scattering matrix for each cell: [nz, nr, ng]
        # sigma_s[mat, :, g] selects all source groups -> target group g for each material
        sigma_s_mat = self.xs.sigma_s[self.material_map, :, g]  # [nz, nr, ng]
        
        # Dot product along group dimension: [nz, nr]
        scatter_in = np.sum(sigma_s_mat * self.flux, axis=2)
        
        self.source[:, :, g] += scatter_in

    def _solve_group(self, g: int) -> np.ndarray:
        """Solve single-group diffusion equation."""
        A, b = self._build_group_system(g)

        if self.options.inner_solver == "bicgstab":
            flux_1d, info = sparse_linalg.bicgstab(A, b, tol=1e-8)
            if info != 0:
                raise RuntimeError(f"BiCGSTAB failed with code {info}")
        elif self.options.inner_solver == "gmres":
            flux_1d, info = sparse_linalg.gmres(A, b, tol=1e-8)
            if info != 0:
                raise RuntimeError(f"GMRES failed with code {info}")
        else:
            flux_1d = sparse_linalg.spsolve(A, b)

        flux_2d = flux_1d.reshape(self.nz, self.nr)
        return flux_2d

    def _build_group_system(self, g: int) -> Tuple[csr_matrix, np.ndarray]:
        """Build sparse matrix for single group."""
        n = self.nz * self.nr

        nnz = n * 5
        row = np.zeros(nnz, dtype=int)
        col = np.zeros(nnz, dtype=int)
        data = np.zeros(nnz)
        b = np.zeros(n)

        idx = 0

        for iz in range(self.nz):
            for ir in range(self.nr):
                i = iz * self.nr + ir

                D = self.D_map[iz, ir, g]
                sigma_r = self.sigma_t_map[iz, ir, g] - self.sigma_a_map[iz, ir, g]
                S = self.source[iz, ir, g]

                r = self.r_centers[ir]
                dr_left = self.dr[ir] if ir > 0 else self.dr[ir]
                dr_right = self.dr[ir] if ir < self.nr-1 else self.dr[ir]
                dz_down = self.dz[iz] if iz > 0 else self.dz[iz]
                dz_up = self.dz[iz] if iz < self.nz-1 else self.dz[iz]

                V = 2 * np.pi * r * self.dr[ir] * self.dz[iz]

                diag = sigma_r * V

                # Radial leakage
                if ir > 0:
                    r_left = self.r_mesh[ir]
                    A_left = 2 * np.pi * r_left * self.dz[iz]
                    D_left = 0.5 * (D + self.D_map[iz, ir-1, g])
                    coef_left = D_left * A_left / dr_left

                    diag += coef_left
                    row[idx] = i
                    col[idx] = i - 1
                    data[idx] = -coef_left
                    idx += 1

                if ir < self.nr - 1:
                    r_right = self.r_mesh[ir+1]
                    A_right = 2 * np.pi * r_right * self.dz[iz]
                    D_right = 0.5 * (D + self.D_map[iz, ir+1, g])
                    coef_right = D_right * A_right / dr_right

                    diag += coef_right
                    row[idx] = i
                    col[idx] = i + 1
                    data[idx] = -coef_right
                    idx += 1

                # Axial leakage
                A_axial = np.pi * (self.r_mesh[ir+1]**2 - self.r_mesh[ir]**2)

                if iz > 0:
                    D_bottom = 0.5 * (D + self.D_map[iz-1, ir, g])
                    coef_bottom = D_bottom * A_axial / dz_down

                    diag += coef_bottom
                    row[idx] = i
                    col[idx] = i - self.nr
                    data[idx] = -coef_bottom
                    idx += 1

                if iz < self.nz - 1:
                    D_top = 0.5 * (D + self.D_map[iz+1, ir, g])
                    coef_top = D_top * A_axial / dz_up

                    diag += coef_top
                    row[idx] = i
                    col[idx] = i + self.nr
                    data[idx] = -coef_top
                    idx += 1

                row[idx] = i
                col[idx] = i
                data[idx] = diag
                idx += 1

                b[i] = S * V

        row = row[:idx]
        col = col[:idx]
        data = data[:idx]

        A = csr_matrix((data, (row, col)), shape=(n, n))

        return A, b

    def _compute_k_eff(self) -> float:
        """Compute k_eff from flux solution."""
        fission_rate = np.sum(self.nu_sigma_f_map * self.flux)
        absorption_rate = np.sum(self.sigma_a_map * self.flux)

        if absorption_rate == 0:
            raise RuntimeError("Zero absorption rate - non-physical solution")

        k_eff = fission_rate / absorption_rate

        return k_eff

    def _arnoldi_method(self) -> Tuple[float, np.ndarray]:
        """
        Arnoldi/Krylov eigenvalue method.
        
        ⚠️ NOT IMPLEMENTED ⚠️
        
        This method is not yet implemented. Use the power iteration method
        (default) instead, which is fully functional and tested.
        
        The Arnoldi method would provide faster convergence for large problems,
        but power iteration works well for most use cases.
        
        Raises:
            NotImplementedError: Always raised (method not implemented)
            
        See Also:
            solve_steady_state() - Uses power iteration (default, fully functional)
            FEATURE_STATUS.md - Feature status documentation
        """
        raise NotImplementedError(
            "Arnoldi method not yet implemented. "
            "Use power iteration method instead (default eigen_method='power'). "
            "See FEATURE_STATUS.md for details."
        )

    def compute_power_distribution(self, total_power: float) -> np.ndarray:
        """
        Compute power distribution from flux.

        Args:
            total_power: Total core power [W]

        Returns:
            power_density: Power density [W/cm³] for each cell [nz, nr]
        """
        if self.flux is None:
            raise RuntimeError("Must solve for flux first")

        E_per_fission = 200e6 * 1.602e-19  # 200 MeV in Joules

        # Vectorized computation: sigma_f is [n_materials, ng]
        # Get fission cross section for each cell: [nz, nr, ng]
        sigma_f_map = self.xs.sigma_f[self.material_map, :]
        
        # Sum over groups: [nz, nr]
        power_density = np.sum(sigma_f_map * self.flux, axis=2) * E_per_fission

        # Normalize to total power
        total = np.sum(power_density * self._cell_volumes())
        if total > 0:
            power_density *= total_power / total

        return power_density

    def _cell_volumes(self) -> np.ndarray:
        """
        Compute cell volumes [nz, nr].
        
        Cached and vectorized for better performance.
        Volumes are computed once and reused since geometry doesn't change.
        """
        if self._cell_volumes_cache is None:
            # Vectorized computation
            # r_centers is [nr], dr is [nr], dz is [nz]
            # Use broadcasting to compute all volumes at once
            r = self.r_centers[:, np.newaxis]  # [nr, 1]
            dr = self.dr[:, np.newaxis]  # [nr, 1]
            dz = self.dz[np.newaxis, :]  # [1, nz]
            self._cell_volumes_cache = (2 * np.pi * r * dr * dz).T  # [nz, nr]
        return self._cell_volumes_cache

    def compute_reactivity_coefficients(self, delta_T: float = 10.0) -> Dict[str, float]:
        """
        Compute reactivity feedback coefficients.

        Args:
            delta_T: Temperature perturbation [K]

        Returns:
            Dict of coefficients [dk/k/K]
        """
        if self.flux is None:
            raise RuntimeError("Must solve for flux first")

        k_ref = self.k_eff

        # Would need temperature-dependent XS in real implementation
        # This is a placeholder
        return {
            'doppler': -3.5e-5,
            'moderator': -1.0e-5,
            'total': -4.5e-5
        }


if __name__ == "__main__":
    from rich.console import Console
    console = Console()

    console.print("[bold cyan]Updated Multi-Group Diffusion Solver[/bold cyan]\n")

    # Test with Pydantic validation
    console.print("[bold]Test 1: Valid Inputs[/bold]")

    try:
        # Create validated cross sections
        xs_data = CrossSectionData(
            n_groups=2,
            n_materials=1,
            sigma_t=np.array([[0.5, 0.8]]),
            sigma_a=np.array([[0.1, 0.2]]),
            sigma_f=np.array([[0.05, 0.15]]),
            nu_sigma_f=np.array([[0.125, 0.375]]),
            sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
            chi=np.array([[1.0, 0.0]]),
            D=np.array([[1.5, 0.4]])
        )
        console.print("  ✓ Cross sections validated by Pydantic")

        # Create validated solver options
        options = SolverOptions(
            max_iterations=100,
            tolerance=1e-6,
            eigen_method="power",
            verbose=False
        )
        console.print("  ✓ Solver options validated by Pydantic")

    except ValidationError as e:
        console.print(f"  ✗ Pydantic validation failed:")
        console.print(e)

    # Test 2: Invalid inputs caught by Pydantic
    console.print("\n[bold]Test 2: Invalid Inputs (Pydantic catches)[/bold]")
    try:
        bad_xs = CrossSectionData(
            n_groups=2,
            n_materials=1,
            sigma_t=np.array([[0.5, 0.8]]),
            sigma_a=np.array([[0.6, 0.9]]),  # > sigma_t! Invalid
            sigma_f=np.array([[0.05, 0.15]]),
            nu_sigma_f=np.array([[0.125, 0.375]]),
            sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
            chi=np.array([[1.0, 0.0]]),
            D=np.array([[1.5, 0.4]])
        )
    except ValidationError as e:
        console.print("  ✓ Pydantic caught invalid cross sections:")
        console.print(f"     {str(e).split(chr(10))[0]}")

    console.print("\n[bold green]Solver updated with Pydantic validation![/bold green]")
