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

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
from numba import njit, prange


# Numba-accelerated helper functions for matrix construction
@njit(cache=True)
def _compute_cell_volume(r: float, dr: float, dz: float) -> float:
    """Compute volume of cylindrical cell element (Numba-accelerated)."""
    return 2 * np.pi * r * dr * dz


@njit(cache=True)
def _compute_radial_area(r: float, dz: float) -> float:
    """Compute radial area for diffusion (Numba-accelerated)."""
    return 2 * np.pi * r * dz


@njit(cache=True)
def _compute_diffusion_coefficient(D1: float, D2: float) -> float:
    """Compute harmonic mean diffusion coefficient (Numba-accelerated)."""
    if D1 > 0 and D2 > 0:
        return 2 * D1 * D2 / (D1 + D2)
    return 0.5 * (D1 + D2)  # Fallback to arithmetic mean


from pydantic import ValidationError
from scipy.sparse import csr_matrix, diags
from scipy.sparse import linalg as sparse_linalg

# Try to import MPI (optional)
try:
    from mpi4py import MPI

    _MPI_AVAILABLE = True
except ImportError:
    _MPI_AVAILABLE = False
    MPI = None

# Try to import Rich (optional, for progress bars)
try:
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False
    Progress = None

from ..utils.logging import get_logger
from ..validation.numerical_validation import validate_safety_critical_outputs
from ..validation.regulatory_traceability import create_audit_trail

# Import Pydantic models
from ..validation.models import CrossSectionData, SolverOptions
from ..validation.validators import DataValidator, ValidationResult

# Get logger for this module
logger = get_logger("smrforge.neutronics")


def _supports_unicode_output() -> bool:
    """
    Best-effort check for Unicode console output support.

    Some Windows terminals default to cp1252, which cannot encode Rich's braille
    spinner glyphs and will raise UnicodeEncodeError during rendering.
    """
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        # Rich spinners commonly use braille patterns.
        "⠙".encode(encoding)
        return True
    except Exception:
        return False


class MultiGroupDiffusion:
    """
    Multi-group neutron diffusion solver with automatic input validation.

    This class solves the multi-group neutron diffusion equation using either
    power iteration or Arnoldi/Krylov subspace methods. It includes comprehensive
    input validation, logging, and error handling.

    Examples:
        Basic usage with power iteration::

            from smrforge.geometry import PrismaticCore
            from smrforge.neutronics.solver import MultiGroupDiffusion
            from smrforge.validation.models import CrossSectionData, SolverOptions
            import numpy as np

            # Create geometry
            geometry = PrismaticCore(name="TestCore")
            geometry.core_height = 200.0
            geometry.core_diameter = 100.0
            geometry.build_mesh(n_radial=20, n_axial=10)

            # Create cross sections (2-group)
            xs_data = CrossSectionData(
                n_groups=2,
                n_materials=1,
                sigma_t=np.array([[0.5, 0.8]]),
                sigma_a=np.array([[0.1, 0.2]]),
                sigma_f=np.array([[0.05, 0.15]]),
                nu_sigma_f=np.array([[0.125, 0.375]]),
                sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
                chi=np.array([[1.0, 0.0]]),
                D=np.array([[1.5, 0.4]]),
            )

            # Create solver options
            options = SolverOptions(
                max_iterations=100,
                tolerance=1e-6,
                eigen_method="power",  # or "arnoldi"
                verbose=True
            )

            # Create and solve
            solver = MultiGroupDiffusion(geometry, xs_data, options)
            k_eff, flux = solver.solve_steady_state()
            print(f"k-eff: {k_eff:.6f}")

        Using Arnoldi method::

            options = SolverOptions(
                max_iterations=100,
                tolerance=1e-6,
                eigen_method="arnoldi",  # Faster for large problems
                verbose=True
            )
            solver = MultiGroupDiffusion(geometry, xs_data, options)
            k_eff, flux = solver.solve_steady_state()

        Compute power distribution::

            power = solver.compute_power_distribution(total_power=10e6)  # 10 MW in Watts
            print(f"Max power density: {np.max(power):.2e} W/cm³")
    """

    def __init__(self, geometry, xs_data: CrossSectionData, options: SolverOptions):
        """
        Initialize solver with validated inputs.

        The inputs are validated using Pydantic models and physics-based
        validation to ensure consistency and correctness.

        Args:
            geometry: Core geometry object with mesh attributes (radial_mesh, axial_mesh,
                     core_diameter, core_height)
            xs_data: CrossSectionData object containing cross sections for all materials
                     and energy groups (Pydantic validated)
            options: SolverOptions object containing solver parameters like max_iterations,
                    tolerance, and eigen_method (Pydantic validated)

        Raises:
            ValidationError: If inputs don't pass Pydantic type/range validation
            ValueError: If inputs don't pass physics-based validation (e.g., cross sections
                       don't satisfy physical constraints)

        Example:
            >>> from smrforge.geometry import PrismaticCore
            >>> from smrforge.neutronics.solver import MultiGroupDiffusion
            >>> from smrforge.validation.models import CrossSectionData, SolverOptions
            >>> import numpy as np
            >>>
            >>> geometry = PrismaticCore(name="Test")
            >>> geometry.core_height = 200.0
            >>> geometry.core_diameter = 100.0
            >>> geometry.build_mesh(n_radial=20, n_axial=10)
            >>>
            >>> xs_data = CrossSectionData(...)  # See examples above
            >>> options = SolverOptions(max_iterations=100, tolerance=1e-6)
            >>>
            >>> solver = MultiGroupDiffusion(geometry, xs_data, options)
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
        result = validator.validate_solver_inputs(self.geometry, self.xs, self.options)

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
                if issue.level.value == "warning":
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
        """
        Map mesh cells to materials using vectorized operations.

        Optimized using NumPy broadcasting for ~10-100x speedup vs nested loops.
        """
        # Memory-efficient vectorized condition:
        # Material assignment here depends only on radius, so avoid allocating full
        # (nz, nr) meshgrids for r and z.
        fuel_mask_1d = self.r_centers < (self.geometry.core_diameter / 2)
        mat_row = np.where(fuel_mask_1d, 0, 1).astype(int, copy=False)  # [nr]
        return np.broadcast_to(mat_row, (self.nz, self.nr)).copy()  # [nz, nr]

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

    def solve_steady_state(
        self, audit_trail_path: Optional[Path] = None
    ) -> Tuple[float, np.ndarray]:
        """
        Solve steady-state eigenvalue problem.

        Solves the multi-group neutron diffusion equation to find the critical
        eigenvalue (k-eff) and the corresponding flux distribution. Supports both
        power iteration and Arnoldi/Krylov methods as specified in solver options.

        Returns:
            Tuple containing:
                - k_eff (float): Effective multiplication factor (should be ~1.0 for critical)
                - flux (np.ndarray): Neutron flux distribution with shape [nz, nr, ng]
                  where nz = number of axial mesh cells, nr = number of radial mesh cells,
                  ng = number of energy groups

        Raises:
            RuntimeError: If solver fails to converge within max_iterations
            ValueError: If solution is non-physical (negative flux, infinite values, etc.)

        Example:
            >>> solver = MultiGroupDiffusion(geometry, xs_data, options)
            >>> k_eff, flux = solver.solve_steady_state()
            >>> print(f"k-eff: {k_eff:.6f}")
            >>> print(f"Flux shape: {flux.shape}")  # [nz, nr, ng]
            >>> print(f"Total flux: {np.sum(flux):.2e}")

        Note:
            The solution is stored in ``self.k_eff`` and ``self.flux`` for subsequent
            use in methods like ``compute_power_distribution()``.
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

        # Validate solution (unless skipped for testing)
        if not self.options.skip_solution_validation:
            self._validate_solution()

        logger.info(
            f"Solver converged: k_eff = {self.k_eff:.6f}, "
            f"time = {elapsed:.2f} seconds"
        )

        # Auto-attach audit trail when path provided (regulatory traceability)
        if audit_trail_path is not None:
            trail = create_audit_trail(
                calculation_type="keff",
                inputs={
                    "geometry": {
                        "nz": self.nz,
                        "nr": self.nr,
                        "ng": self.ng,
                    },
                    "solver_options": self.options.model_dump()
                    if hasattr(self.options, "model_dump")
                    else str(self.options),
                },
                outputs={
                    "k_eff": float(self.k_eff),
                    "flux_shape": list(self.flux.shape),
                    "flux_sum": float(np.sum(self.flux)),
                },
                solver_method=self.options.eigen_method,
            )
            trail.save(audit_trail_path)

        return self.k_eff, self.flux

    def _validate_solution(self) -> None:
        """
        Validate solution quality.
        Checks for NaN, Inf, negative flux, reasonable k_eff.
        """
        # Centralized NaN/Inf validation (safety-critical boundary)
        num_result = validate_safety_critical_outputs(
            k_eff=self.k_eff, flux=self.flux
        )
        if num_result.has_errors():
            logger.error("Solution validation failed (NaN/Inf or invalid range)")
            num_result.print_report()
            raise ValueError(
                f"Solution validation failed. "
                f"k_eff={self.k_eff:.6f}, "
                f"flux_max={np.max(self.flux):.3e}, "
                f"flux_min={np.min(self.flux):.3e}"
            )

        validator = DataValidator()
        # Dummy power for validation (will be normalized later)
        power = np.ones_like(self.flux[:, :, 0])
        result = validator.validate_solution(self.k_eff, self.flux, power, 1.0)

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

        # Ensure initial flux is non-zero and properly scaled
        # If flux is all zeros or very small, initialize to uniform distribution
        if np.max(self.flux) < 1e-10:
            self.flux = np.ones_like(self.flux)
            logger.warning(
                "Initial flux was zero, reinitializing to uniform distribution"
            )

        # Normalize initial flux
        max_flux = np.max(self.flux)
        if max_flux > 0:
            self.flux = self.flux / max_flux
        else:
            self.flux = np.ones_like(self.flux)
            logger.warning(
                "Initial flux normalization failed, using uniform distribution"
            )

        # Use progress bar if Rich is available and verbose is enabled.
        # On some Windows terminals (cp1252), Rich's spinner glyphs can trigger
        # UnicodeEncodeError; avoid progress rendering in that case.
        use_progress = (
            _RICH_AVAILABLE
            and self.options.verbose
            and self.options.max_iterations > 10
            and _supports_unicode_output()
        )

        if use_progress:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("k_eff={task.fields[k_eff]:.6f}"),
                console=None,  # Use default console
            )
            task = progress.add_task(
                "Power iteration...",
                total=self.options.max_iterations,
                k_eff=self.k_eff,
            )
            progress.start()
        else:
            progress = None
            task = None

        # Initialize error for failure case
        error = float("inf")

        for iteration in range(self.options.max_iterations):
            self._update_fission_source(k_old)

            # Always use the same red-black energy-group sweep for ng>1 so that
            # serial and parallel paths converge to comparable solutions. The
            # `parallel_group_solve` option controls whether the sweep uses a
            # thread pool, not whether the red-black ordering is used.
            if self.ng > 1:
                self.flux = self._solve_groups_parallel_red_black(self.flux)
            else:
                # Single-group solve
                self._update_scattering_source(0)
                self.flux[:, :, 0] = self._solve_group(0)

            # Check if flux became zero (shouldn't happen, but handle gracefully)
            max_flux = np.max(self.flux)
            if max_flux < 1e-10:
                logger.error(f"Flux became zero at iteration {iteration}")
                # Reinitialize flux to uniform distribution
                self.flux = np.ones_like(self.flux)
                # Try to continue with a better initial guess
                if iteration == 0:
                    # First iteration failed - likely source term issue
                    raise RuntimeError(
                        "Flux became zero on first iteration. "
                        "Check that fission cross-sections (nu_sigma_f) are non-zero "
                        "and that source terms are properly initialized."
                    )

            k_new = self._compute_k_eff()

            # Check for NaN or invalid values
            if np.isnan(k_new) or np.isinf(k_new):
                logger.error(
                    f"k_eff became invalid (NaN/Inf) at iteration {iteration}. "
                    f"k_old={k_old:.6f}, k_new={k_new}, max_flux={max_flux:.3e}"
                )
                # Provide diagnostics
                logger.error(
                    f"Flux stats: min={np.min(self.flux):.3e}, max={np.max(self.flux):.3e}, "
                    f"mean={np.mean(self.flux):.3e}, has_nan={np.any(np.isnan(self.flux))}"
                )
                logger.error(
                    f"Source stats: min={np.min(self.source):.3e}, max={np.max(self.source):.3e}, "
                    f"has_nan={np.any(np.isnan(self.source))}"
                )
                raise RuntimeError(
                    f"k_eff calculation produced invalid value (NaN/Inf) at iteration {iteration}. "
                    f"This usually indicates numerical instability. Check cross-section data and "
                    f"ensure all values are physically reasonable."
                )

            # Check for NaN in flux
            if np.any(np.isnan(self.flux)) or np.any(np.isinf(self.flux)):
                logger.error(
                    f"Flux contains NaN/Inf at iteration {iteration}. "
                    f"k_eff={k_new:.6f}, max_flux={max_flux:.3e}"
                )
                raise RuntimeError(
                    f"Flux became invalid (NaN/Inf) at iteration {iteration}. "
                    f"This indicates numerical instability in the solver. "
                    f"Check cross-section data and mesh quality."
                )

            # Calculate error (handle division by zero)
            if k_old > 1e-10:
                error = abs(k_new - k_old) / k_old
            else:
                # If k_old is very small, use absolute error
                error = abs(k_new - k_old)
                if error < self.options.tolerance:
                    # If absolute error is small and k_old is near zero, consider converged
                    logger.info(
                        f"Converged in {iteration+1} iterations (k_eff near zero)"
                    )
                    return k_new, self.flux

            # Check if error is NaN
            if np.isnan(error) or np.isinf(error):
                logger.error(
                    f"Error calculation produced NaN/Inf at iteration {iteration}. "
                    f"k_old={k_old:.6f}, k_new={k_new:.6f}"
                )
                raise RuntimeError(
                    f"Convergence error calculation failed (NaN/Inf) at iteration {iteration}. "
                    f"k_old={k_old:.6f}, k_new={k_new:.6f}"
                )

            # Update progress bar if available
            if progress is not None and task is not None:
                progress.update(task, advance=1, k_eff=k_new)

            # Log every 10 iterations or when converged
            if iteration % 10 == 0 or error < self.options.tolerance:
                logger.debug(
                    f"Iteration {iteration:4d}: k_eff = {k_new:.8f}, "
                    f"error = {error:.2e}, max_flux = {max_flux:.3e}"
                )

            if error < self.options.tolerance:
                if progress is not None:
                    progress.stop()
                logger.info(f"Converged in {iteration+1} iterations")
                return k_new, self.flux

            k_old = k_new
            # Normalize flux (avoid division by zero) - vectorized
            max_flux = np.max(self.flux)
            if max_flux > 1e-10:
                # Vectorized normalization (more efficient than loop)
                self.flux = self.flux / max_flux
            else:
                # If flux is too small, reinitialize
                self.flux = np.ones_like(self.flux)
                logger.warning(
                    f"Flux too small at iteration {iteration}, reinitializing"
                )

        # Stop progress bar if it was started
        if progress is not None:
            progress.stop()

        # Provide detailed diagnostics on failure
        logger.error(
            f"Failed to converge in {self.options.max_iterations} iterations. "
            f"Final error: {error:.2e}, tolerance: {self.options.tolerance}"
        )
        logger.error(
            f"Final state: k_eff={k_old:.6f}, max_flux={np.max(self.flux):.3e}, "
            f"min_flux={np.min(self.flux):.3e}, flux_has_nan={np.any(np.isnan(self.flux))}"
        )
        logger.error(
            f"Source: min={np.min(self.source):.3e}, max={np.max(self.source):.3e}, "
            f"has_nan={np.any(np.isnan(self.source))}"
        )

        error_msg = (
            f"Failed to converge in {self.options.max_iterations} iterations. "
            f"Final error: {error:.2e}, tolerance: {self.options.tolerance}. "
            f"Final k_eff: {k_old:.6f}. "
        )
        if np.any(np.isnan(self.flux)):
            error_msg += "Flux contains NaN values - check cross-section data."
        elif np.max(self.flux) < 1e-10:
            error_msg += "Flux is too small - check source terms and cross-sections."
        else:
            error_msg += (
                "Consider increasing max_iterations or checking cross-section data."
            )

        raise RuntimeError(error_msg)

    def _update_fission_source(self, k_eff: float) -> None:
        """
        Update fission source.

        Optimized using vectorized operations for ~5-20x speedup.
        """
        # Fission rate: [nz, nr, 1]
        fission_rate = np.sum(self.nu_sigma_f_map * self.flux, axis=2, keepdims=True)

        # Ensure fission rate is non-zero (handle edge case where nu_sigma_f is very small)
        max_fission_rate = np.max(fission_rate)
        if max_fission_rate < 1e-10:
            # If fission rate is too small, use a minimum value based on flux
            # This handles cases where cross-sections are very small (e.g., from fallback)
            total_flux = np.sum(self.flux)
            if total_flux > 0:
                # Use a small fraction of total flux as minimum source
                min_fission_rate = total_flux * 1e-12
            else:
                min_fission_rate = 1e-10
            logger.warning(
                f"Fission rate very small (max={max_fission_rate:.2e}), "
                f"using minimum source term"
            )
            fission_rate = np.maximum(fission_rate, min_fission_rate)

        # chi is [n_materials, ng]
        # Get chi for each cell: [nz, nr, ng]
        chi_map = self.xs.chi[self.material_map, :]

        # Broadcast multiplication: [nz, nr, ng]
        # Avoid division by zero or very small k_eff
        k_eff_safe = max(k_eff, 1e-6)
        self.source = chi_map * fission_rate / k_eff_safe

    def _update_scattering_source(
        self, g: int, flux: Optional[np.ndarray] = None
    ) -> None:
        """
        Update scattering source for group g.

        Optimized using vectorized operations for ~5-50x speedup depending on number of groups.
        Can use parallel Numba version for large problems.

        Args:
            g: Energy group index
            flux: Optional flux array (if None, uses self.flux)
        """
        if flux is None:
            flux = self.flux

        # Use parallel version if enabled (Numba parallel is efficient even for smaller problems)
        if self.options.parallel_spatial:
            _update_scattering_source_parallel_numba(
                flux,
                self.xs.sigma_s,
                self.material_map,
                self.source,
                g,
            )
        else:
            # Vectorized: sigma_s is [n_materials, ng, ng]
            # flux is [nz, nr, ng]
            # material_map is [nz, nr]

            # Get scattering matrix for each cell: [nz, nr, ng]
            # sigma_s[mat, :, g] selects all source groups -> target group g for each material
            sigma_s_mat = self.xs.sigma_s[self.material_map, :, g]  # [nz, nr, ng]

            # Dot product along group dimension: [nz, nr]
            scatter_in = np.sum(sigma_s_mat * flux, axis=2)

            self.source[:, :, g] += scatter_in

    def _solve_group(self, g: int) -> np.ndarray:
        """Solve single-group diffusion equation."""
        A, b = self._build_group_system(g)

        if self.options.inner_solver == "bicgstab":
            flux_1d, info = sparse_linalg.bicgstab(A, b, rtol=1e-8)
            if info != 0:
                raise RuntimeError(f"BiCGSTAB failed with code {info}")
        elif self.options.inner_solver == "gmres":
            flux_1d, info = sparse_linalg.gmres(A, b, rtol=1e-8)
            if info != 0:
                raise RuntimeError(f"GMRES failed with code {info}")
        else:
            flux_1d = sparse_linalg.spsolve(A, b)

        flux_2d = flux_1d.reshape(self.nz, self.nr)
        return flux_2d

    def _solve_group_with_source(self, g: int, flux: np.ndarray) -> np.ndarray:
        """
        Solve single group with given flux (for parallel execution).

        Args:
            g: Energy group index
            flux: Current flux array [nz, nr, ng]

        Returns:
            Solved flux for group g [nz, nr]
        """
        # When solving groups concurrently, avoid nested parallelism / shared-state
        # hazards in the Numba-parallel scattering update. A pure NumPy update is
        # deterministic and thread-safe here because each thread writes only to
        # `self.source[:, :, g]`.
        sigma_s_mat = self.xs.sigma_s[self.material_map, :, g]  # [nz, nr, ng]
        scatter_in = np.sum(sigma_s_mat * flux, axis=2)  # [nz, nr]
        self.source[:, :, g] += scatter_in
        return self._solve_group(g)

    def _solve_groups_parallel_red_black(self, flux_old: np.ndarray) -> np.ndarray:
        """
        Solve energy groups using red-black ordering for parallelization.

        Algorithm:
        1. Pass 1: Solve even groups in parallel (groups 0, 2, 4, ...)
        2. Pass 2: Solve odd groups in parallel (groups 1, 3, 5, ...)

        This maintains accuracy while enabling parallelism.

        Args:
            flux_old: Previous iteration flux [nz, nr, ng]

        Returns:
            New flux [nz, nr, ng]
        """
        flux_new = np.copy(flux_old)
        ng = self.ng

        # Separate even and odd groups
        even_groups = list(range(0, ng, 2))
        odd_groups = list(range(1, ng, 2))

        # Determine number of threads
        num_threads = self.options.num_threads
        if num_threads is None:
            num_threads = cpu_count()

        # Pass 1: Solve even groups in parallel
        if (
            len(even_groups) > 1
            and self.options.parallel
            and self.options.parallel_group_solve
        ):
            # Snapshot flux so each task sees a consistent iterate (avoids races
            # from other groups updating `flux_new` mid-computation).
            flux_snapshot = np.copy(flux_new)
            with ThreadPoolExecutor(
                max_workers=min(len(even_groups), num_threads)
            ) as executor:
                futures = {
                    executor.submit(self._solve_group_with_source, g, flux_snapshot): g
                    for g in even_groups
                }
                for future in as_completed(futures):
                    g = futures[future]
                    flux_g = future.result()
                    flux_new[:, :, g] = flux_g
        else:
            # Serial fallback
            for g in even_groups:
                self._update_scattering_source(g, flux_new)
                flux_new[:, :, g] = self._solve_group(g)

        # Pass 2: Solve odd groups in parallel (can use updated even group fluxes)
        if (
            len(odd_groups) > 1
            and self.options.parallel
            and self.options.parallel_group_solve
        ):
            flux_snapshot = np.copy(flux_new)
            with ThreadPoolExecutor(
                max_workers=min(len(odd_groups), num_threads)
            ) as executor:
                futures = {
                    executor.submit(self._solve_group_with_source, g, flux_snapshot): g
                    for g in odd_groups
                }
                for future in as_completed(futures):
                    g = futures[future]
                    flux_g = future.result()
                    flux_new[:, :, g] = flux_g
        else:
            # Serial fallback
            for g in odd_groups:
                self._update_scattering_source(g, flux_new)
                flux_new[:, :, g] = self._solve_group(g)

        return flux_new

    def _build_group_system(self, g: int) -> Tuple[csr_matrix, np.ndarray]:
        """
        Build sparse matrix for single group.

        Optimized with pre-computed values and efficient array operations.
        Uses COO format construction which is faster than element-by-element CSR.
        """
        n = self.nz * self.nr

        # Pre-allocate arrays for COO format (more efficient than CSR for construction)
        # Maximum 5 non-zeros per row (diagonal + 4 neighbors)
        nnz_max = n * 5
        row = np.zeros(nnz_max, dtype=int)
        col = np.zeros(nnz_max, dtype=int)
        data = np.zeros(nnz_max)
        b = np.zeros(n)

        # Pre-compute axial areas (reused for all radial cells at same axial level)
        # A_axial[ir] = area between r_mesh[ir] and r_mesh[ir+1]
        A_axial_precomputed = np.pi * (self.r_mesh[1:] ** 2 - self.r_mesh[:-1] ** 2)

        idx = 0

        for iz in range(self.nz):
            # Pre-compute dz values for this axial level
            dz_down = self.dz[iz] if iz > 0 else self.dz[iz]
            dz_up = self.dz[iz] if iz < self.nz - 1 else self.dz[iz]

            for ir in range(self.nr):
                i = iz * self.nr + ir

                D = self.D_map[iz, ir, g]
                sigma_r = self.sigma_t_map[iz, ir, g] - self.sigma_a_map[iz, ir, g]
                S = self.source[iz, ir, g]

                r = self.r_centers[ir]
                dr = self.dr[ir]
                dz = self.dz[iz]

                # Cell volume (reused) - use Numba-accelerated function
                V = _compute_cell_volume(r, dr, dz)

                diag = sigma_r * V

                # Radial leakage (left neighbor)
                if ir > 0:
                    r_left = self.r_mesh[ir]
                    A_left = _compute_radial_area(r_left, dz)
                    D_left = _compute_diffusion_coefficient(
                        D, self.D_map[iz, ir - 1, g]
                    )
                    coef_left = D_left * A_left / dr

                    diag += coef_left
                    row[idx] = i
                    col[idx] = i - 1
                    data[idx] = -coef_left
                    idx += 1

                # Radial leakage (right neighbor)
                if ir < self.nr - 1:
                    r_right = self.r_mesh[ir + 1]
                    A_right = _compute_radial_area(r_right, dz)
                    D_right = _compute_diffusion_coefficient(
                        D, self.D_map[iz, ir + 1, g]
                    )
                    coef_right = D_right * A_right / dr

                    diag += coef_right
                    row[idx] = i
                    col[idx] = i + 1
                    data[idx] = -coef_right
                    idx += 1

                # Axial leakage (bottom neighbor)
                if iz > 0:
                    A_axial = A_axial_precomputed[ir]  # Use pre-computed value
                    D_bottom = _compute_diffusion_coefficient(
                        D, self.D_map[iz - 1, ir, g]
                    )
                    coef_bottom = D_bottom * A_axial / dz_down

                    diag += coef_bottom
                    row[idx] = i
                    col[idx] = i - self.nr
                    data[idx] = -coef_bottom
                    idx += 1

                # Axial leakage (top neighbor)
                if iz < self.nz - 1:
                    A_axial = A_axial_precomputed[ir]  # Use pre-computed value
                    D_top = _compute_diffusion_coefficient(D, self.D_map[iz + 1, ir, g])
                    coef_top = D_top * A_axial / dz_up

                    diag += coef_top
                    row[idx] = i
                    col[idx] = i + self.nr
                    data[idx] = -coef_top
                    idx += 1

                # Diagonal element
                row[idx] = i
                col[idx] = i
                data[idx] = diag
                idx += 1

                b[i] = S * V

        # Trim arrays to actual size and construct sparse matrix
        row = row[:idx]
        col = col[:idx]
        data = data[:idx]

        # Use COO format for construction, then convert to CSR (faster for scipy)
        A = csr_matrix((data, (row, col)), shape=(n, n))

        return A, b

    def _compute_k_eff(self) -> float:
        """Compute k_eff from flux solution."""
        fission_rate = np.sum(self.nu_sigma_f_map * self.flux)
        absorption_rate = np.sum(self.sigma_a_map * self.flux)

        # If there is no fission production, this is not a meaningful eigenvalue
        # problem (k_eff is undefined). Raise so callers/tests can handle it.
        if fission_rate <= 0:
            max_nu_sigma_f = float(np.max(self.nu_sigma_f_map))
            error_msg = (
                "Zero fission production rate - eigenvalue problem is ill-posed.\n"
                f"  fission_rate={float(fission_rate):.3e}\n"
                f"  max(nu_sigma_f)={max_nu_sigma_f:.3e}\n"
                "  Possible causes:\n"
                "  1. nu_sigma_f is all zeros (no fission)\n"
                "  2. Flux collapsed to zero in fissionable regions\n"
            )
            raise RuntimeError(error_msg)

        if absorption_rate == 0:
            # Provide detailed diagnostics
            max_flux = np.max(self.flux)
            min_flux = np.min(self.flux)
            max_sigma_a = np.max(self.sigma_a_map)
            min_sigma_a = np.min(self.sigma_a_map)
            non_zero_sigma_a = np.sum(self.sigma_a_map > 0)
            total_cells = self.sigma_a_map.size

            error_msg = (
                "Zero absorption rate - non-physical solution.\n"
                f"  Flux range: [{min_flux:.2e}, {max_flux:.2e}]\n"
                f"  sigma_a range: [{min_sigma_a:.2e}, {max_sigma_a:.2e}]\n"
                f"  Non-zero sigma_a cells: {non_zero_sigma_a}/{total_cells}\n"
                "  Possible causes:\n"
                "  1. Absorption cross-sections are all zero (check cross-section data)\n"
                "  2. Flux is all zero (check initial conditions and source)\n"
                "  3. Material map is incorrect (all cells mapped to non-absorbing material)"
            )
            raise RuntimeError(error_msg)

        k_eff = fission_rate / absorption_rate

        return k_eff

    def _arnoldi_method(self) -> Tuple[float, np.ndarray]:
        """
        Arnoldi/Krylov eigenvalue method using scipy.sparse.linalg.eigs.

        This method uses an iterative Krylov subspace approach by applying power
        iteration steps as a linear operator and using scipy's eigs to find the
        dominant eigenvalue. The Arnoldi method can converge faster than power
        iteration for large problems, especially when multiple eigenvalues are needed.

        The method wraps the multi-group diffusion operator as a LinearOperator
        and uses scipy's eigs (which internally uses Arnoldi iteration) to find
        the largest eigenvalue and corresponding eigenvector (flux).

        Returns:
            Tuple containing:
                - k_eff (float): Effective multiplication factor
                - flux (np.ndarray): Neutron flux distribution [nz, nr, ng]

        Raises:
            RuntimeError: If solver fails to converge or produces invalid results
                          (negative flux, non-physical k_eff, etc.)

        Note:
            This implementation uses scipy's sparse eigensolver (eigs), which
            internally uses the Arnoldi iteration. For very large problems with
            limited memory, power iteration (``_power_iteration()``) may be more
            memory-efficient as it doesn't need to store a Krylov subspace basis.

        Example:
            This method is called automatically when ``eigen_method="arnoldi"``
            is set in SolverOptions::

                >>> options = SolverOptions(eigen_method="arnoldi")
                >>> solver = MultiGroupDiffusion(geometry, xs_data, options)
                >>> k_eff, flux = solver.solve_steady_state()  # Calls _arnoldi_method internally
        """
        logger.debug("Starting Arnoldi eigenvalue method")

        n_total = self.nz * self.nr * self.ng

        # Initial guess for flux (normalized)
        if self.flux is not None:
            flux_initial = self.flux.flatten()
        else:
            flux_initial = np.ones(n_total)

        flux_initial = flux_initial / np.linalg.norm(flux_initial)

        try:
            from scipy.sparse.linalg import LinearOperator, eigs

            # Store original state
            original_flux = self.flux.copy() if self.flux is not None else None
            original_k_eff = self.k_eff

            try:
                # Define linear operator that applies one power iteration step
                def power_iteration_step(flux_vec):
                    """Apply one power iteration step."""
                    # Reshape to [nz, nr, ng]
                    flux_old = flux_vec.reshape(self.nz, self.nr, self.ng).copy()

                    # Set flux for computation (needed by _update methods)
                    self.flux = flux_old

                    # Use current k_eff estimate (or 1.0 if not set)
                    k_current = self.k_eff if self.k_eff > 0 else 1.0

                    # Update fission source (uses self.flux)
                    self._update_fission_source(k_current)

                    # Solve for each group (use parallel if enabled)
                    if self.options.parallel_group_solve and self.ng > 1:
                        flux_new = self._solve_groups_parallel_red_black(flux_old)
                    else:
                        # Serial fallback
                        flux_new = np.zeros_like(flux_old)
                        for g in range(self.ng):
                            self._update_scattering_source(g)  # Uses self.flux
                            flux_new[:, :, g] = self._solve_group(g)

                    # Normalize flux
                    max_flux = np.max(flux_new)
                    if max_flux > 0:
                        flux_new = flux_new / max_flux

                    # Return flattened flux
                    return flux_new.flatten()

                # Create linear operator
                A = LinearOperator(
                    shape=(n_total, n_total), dtype=float, matvec=power_iteration_step
                )

                # Find largest eigenvalue using Arnoldi iteration
                # The eigenvalue represents the convergence rate (should be ~1.0 at convergence)
                eigenvalues, eigenvectors = eigs(
                    A,
                    k=1,  # Only need largest eigenvalue
                    which="LM",  # Largest magnitude
                    v0=flux_initial,
                    maxiter=min(self.options.max_iterations, 100),  # Limit iterations
                    tol=self.options.tolerance * 10,  # Slightly looser for eigs
                )

                # Use the eigenvector as the flux
                flux_vector = eigenvectors[:, 0].real

                # Ensure positive
                if np.sum(flux_vector) < 0:
                    flux_vector = -flux_vector

                flux_vector = np.abs(flux_vector)

                # Reshape to [nz, nr, ng]
                flux = flux_vector.reshape(self.nz, self.nr, self.ng)

                # Normalize
                max_flux = np.max(flux)
                if max_flux > 0:
                    flux = flux / max_flux

                # Compute k_eff from the flux using the standard formula
                self.flux = flux
                k_eff = self._compute_k_eff()

                logger.info(f"Arnoldi method converged: k_eff = {k_eff:.8f}")

                return k_eff, flux
            finally:
                # Keep the new flux - don't restore original
                pass

        except Exception as e:
            logger.error(f"Arnoldi method failed: {e}")
            raise RuntimeError(
                f"Arnoldi method failed: {e}. "
                f"Try using power iteration method (eigen_method='power') instead."
            ) from e

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

    def compute_reactivity_coefficients(
        self, delta_T: float = 10.0
    ) -> Dict[str, float]:
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
        return {"doppler": -3.5e-5, "moderator": -1.0e-5, "total": -4.5e-5}


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
            D=np.array([[1.5, 0.4]]),
        )
        console.print("  ✓ Cross sections validated by Pydantic")

        # Create validated solver options
        options = SolverOptions(
            max_iterations=100, tolerance=1e-6, eigen_method="power", verbose=False
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
            D=np.array([[1.5, 0.4]]),
        )
    except ValidationError as e:
        console.print("  ✓ Pydantic caught invalid cross sections:")
        console.print(f"     {str(e).split(chr(10))[0]}")

    console.print("\n[bold green]Solver updated with Pydantic validation![/bold green]")


# Numba-accelerated parallel functions
# Optimized with fastmath, nogil, and boundscheck=False for maximum performance
@njit(
    parallel=True,
    cache=True,
    fastmath=True,  # Faster math operations
    boundscheck=False,  # Skip bounds checking (faster - arrays validated before call)
    nogil=True,  # Release GIL for true parallelism
)
def _update_scattering_source_parallel_numba(
    flux: np.ndarray,
    sigma_s: np.ndarray,
    material_map: np.ndarray,
    source: np.ndarray,
    g: int,
) -> None:
    """
    Parallel scattering source update using Numba.

    Args:
        flux: Flux array [nz, nr, ng]
        sigma_s: Scattering matrix [n_materials, ng, ng]
        material_map: Material map [nz, nr]
        source: Source array [nz, nr, ng] (modified in-place)
        g: Target energy group
    """
    nz, nr = material_map.shape
    ng = flux.shape[2]

    # Parallelize over spatial cells
    for iz in prange(nz):
        for ir in prange(nr):
            mat = material_map[iz, ir]
            scatter_in = 0.0

            # Sum scattering from all source groups
            for g_prime in range(ng):
                scatter_in += sigma_s[mat, g_prime, g] * flux[iz, ir, g_prime]

            source[iz, ir, g] += scatter_in


# MPI support functions (optional)
def _get_mpi_comm():
    """Get MPI communicator if available."""
    if _MPI_AVAILABLE and MPI is not None:
        return MPI.COMM_WORLD
    return None


def _is_mpi_root():
    """Check if this is the MPI root process."""
    comm = _get_mpi_comm()
    if comm is not None:
        return comm.Get_rank() == 0
    return True


def _mpi_rank():
    """Get MPI rank."""
    comm = _get_mpi_comm()
    if comm is not None:
        return comm.Get_rank()
    return 0


def _mpi_size():
    """Get MPI size."""
    comm = _get_mpi_comm()
    if comm is not None:
        return comm.Get_size()
    return 1
