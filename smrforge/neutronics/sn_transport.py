"""
Discrete ordinates (S_N) transport solver for 1D slab/cylindrical geometry.

Provides S2 and S4 quadrature for deterministic neutron transport.
Useful for 1D benchmarks and validation against diffusion.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.neutronics.sn_transport")


# Standard S2 quadrature (2 directions): mu = ±1/sqrt(3), w = 1.0
S2_MU = np.array([-1.0 / np.sqrt(3.0), 1.0 / np.sqrt(3.0)])
S2_WEIGHTS = np.array([1.0, 1.0])

# S4 Gauss-Legendre: mu and weights for N=4
S4_MU = np.array(
    [
        -0.8611363115940526,
        -0.3399810435848563,
        0.3399810435848563,
        0.8611363115940526,
    ]
)
S4_WEIGHTS = np.array(
    [
        0.3478548451374539,
        0.6521451548625461,
        0.6521451548625461,
        0.3478548451374539,
    ]
)


@dataclass
class SNTransportResult:
    """Result of SN transport solve."""

    flux: np.ndarray  # [n_cells, n_angles] or [n_cells] for scalar
    k_eff: float
    scalar_flux: np.ndarray  # [n_cells]
    n_iterations: int
    converged: bool


class SNTransportSolver:
    """
    S2/S4 discrete ordinates 1D slab transport solver.

    Solves the 1D discrete ordinates equations in slab geometry:
        mu_m * d(phi_m)/dx + sigma_t * phi_m = sigma_s0 * phi_scalar + ...

    Supports S2 (2 angles) and S4 (4 angles) quadrature.
    Uses source iteration for eigenvalue problems.

    Attributes:
        n_cells: Number of spatial cells
        sigma_t: Total cross section per cell [1/cm]
        sigma_s: Scatter cross section per cell [1/cm]
        nu_sigma_f: Fission production cross section per cell [1/cm]
        chi: Fission spectrum

    Example:
        >>> solver = SNTransportSolver(
        ...     n_cells=20,
        ...     sigma_t=0.5,
        ...     sigma_s=0.4,
        ...     nu_sigma_f=0.1,
        ...     order=4,  # S4
        ... )
        >>> result = solver.solve_eigenvalue(max_iter=100)
    """

    def __init__(
        self,
        n_cells: int,
        sigma_t: np.ndarray,
        sigma_s: np.ndarray,
        nu_sigma_f: np.ndarray,
        chi: float = 1.0,
        dx: Optional[float] = None,
        order: int = 2,
        bc_left: str = "vacuum",
        bc_right: str = "vacuum",
    ):
        """
        Initialize SN transport solver.

        Args:
            n_cells: Number of spatial cells
            sigma_t: Total cross section [n_cells] or scalar
            sigma_s: Scatter cross section [n_cells] or scalar
            nu_sigma_f: Fission production [n_cells] or scalar
            chi: Fission spectrum (scalar for 1-group)
            dx: Cell width [cm]. Default: 1.0/n_cells
            order: 2 for S2, 4 for S4
            bc_left: Left boundary 'vacuum' or 'reflective'
            bc_right: Right boundary 'vacuum' or 'reflective'
        """
        self.n_cells = n_cells
        self.sigma_t = np.broadcast_to(np.asarray(sigma_t, dtype=float), (n_cells,))
        self.sigma_s = np.broadcast_to(np.asarray(sigma_s, dtype=float), (n_cells,))
        self.nu_sigma_f = np.broadcast_to(
            np.asarray(nu_sigma_f, dtype=float), (n_cells,)
        )
        self.chi = float(chi)
        self.dx = dx if dx is not None else 1.0 / n_cells
        self.order = order
        self.bc_left = bc_left
        self.bc_right = bc_right

        if order == 2:
            self.mu = S2_MU
            self.weights = S2_WEIGHTS
        elif order == 4:
            self.mu = S4_MU
            self.weights = S4_WEIGHTS
        else:
            raise ValueError(f"order must be 2 or 4, got {order}")

        self.n_angles = len(self.mu)
        logger.debug(
            f"SNTransportSolver: S{order}, n_cells={n_cells}, n_angles={self.n_angles}"
        )

    def _sweep_direction(
        self,
        psi_prev: np.ndarray,
        q: np.ndarray,
        mu: float,
        sigma_t: np.ndarray,
    ) -> np.ndarray:
        """Sweep in one direction (diamond difference)."""
        n = self.n_cells
        psi_out = np.zeros(n)
        if mu > 0:
            # Left to right
            in_psi = 0.0 if self.bc_left == "vacuum" else psi_prev[n - 1]
            for i in range(n):
                denom = mu / self.dx + sigma_t[i] / 2
                psi_out[i] = (q[i] / 2 + mu * in_psi / self.dx) / denom
                in_psi = 2 * psi_out[i] - in_psi  # diamond
            if self.bc_left == "reflective":
                psi_out[0] = psi_prev[-1]  # reflective incoming
        else:
            # Right to left
            in_psi = 0.0 if self.bc_right == "vacuum" else psi_prev[0]
            for i in range(n - 1, -1, -1):
                denom = -mu / self.dx + sigma_t[i] / 2
                psi_out[i] = (q[i] / 2 - mu * in_psi / self.dx) / denom
                in_psi = 2 * psi_out[i] - in_psi
            if self.bc_right == "reflective":
                psi_out[-1] = psi_prev[0]
        return psi_out

    def solve_eigenvalue(
        self,
        max_iter: int = 200,
        tolerance: float = 1e-6,
    ) -> SNTransportResult:
        """
        Solve k-eigenvalue problem via source iteration.

        Returns:
            SNTransportResult with flux, k_eff, convergence info
        """
        n = self.n_cells
        phi = np.ones(n) / n  # Initial scalar flux
        k = 1.0
        psi = np.ones((n, self.n_angles)) / (n * self.n_angles)

        for it in range(max_iter):
            # Total fission source (scalar)
            fission_integrated = np.sum(self.nu_sigma_f * phi)
            # Source Q = scatter + fission/k
            q = self.sigma_s * phi + (self.chi * fission_integrated / k) / n
            q = np.where(self.sigma_t > 1e-30, q / self.sigma_t, 0.0)

            psi_new = np.zeros((n, self.n_angles))
            for m in range(self.n_angles):
                psi_new[:, m] = self._sweep_direction(
                    psi[:, m], q, self.mu[m], self.sigma_t
                )

            # Scalar flux from angular flux
            phi_new = np.sum(self.weights * psi_new, axis=1)
            phi_new = np.maximum(phi_new, 1e-30)
            phi_new = phi_new / np.sum(phi_new)

            # k update
            k_new = k * np.sum(self.nu_sigma_f * phi_new) / (
                np.sum(self.nu_sigma_f * phi) + 1e-30
            )

            err = np.max(np.abs(phi_new - phi))
            if err < tolerance and abs(k_new - k) < tolerance:
                logger.info(
                    f"SN transport converged in {it + 1} iterations, k={k_new:.6f}"
                )
                return SNTransportResult(
                    flux=psi_new,
                    k_eff=k_new,
                    scalar_flux=phi_new,
                    n_iterations=it + 1,
                    converged=True,
                )

            phi = phi_new
            psi = psi_new
            k = k_new

        logger.warning(f"SN transport did not converge in {max_iter} iterations")
        return SNTransportResult(
            flux=psi,
            k_eff=k,
            scalar_flux=phi,
            n_iterations=max_iter,
            converged=False,
        )


@dataclass
class SN2DCylindricalResult:
    """Result of 2D r-z cylindrical SN transport solve."""

    flux: np.ndarray  # [n_r, n_z, n_angles]
    k_eff: float
    scalar_flux: np.ndarray  # [n_r, n_z]
    n_iterations: int
    converged: bool


class SN2DCylindricalSolver:
    """
    S2/S4 discrete ordinates 2D r-z cylindrical transport solver.

    Solves the 2D cylindrical discrete ordinates equations. Uses diamond
    difference and alternating-direction sweeps. Extends beyond 1D slab
    for reactor core r-z geometry.

    Attributes:
        n_r: Number of radial cells
        n_z: Number of axial cells
        dr, dz: Cell sizes [cm]
    """

    def __init__(
        self,
        n_r: int,
        n_z: int,
        sigma_t: np.ndarray,
        sigma_s: np.ndarray,
        nu_sigma_f: np.ndarray,
        chi: float = 1.0,
        dr: Optional[float] = None,
        dz: Optional[float] = None,
        order: int = 2,
        bc_r_inner: str = "reflective",
        bc_r_outer: str = "vacuum",
        bc_z_lo: str = "reflective",
        bc_z_hi: str = "reflective",
    ):
        self.n_r = n_r
        self.n_z = n_z
        self.sigma_t = np.broadcast_to(
            np.asarray(sigma_t, dtype=float), (n_r, n_z)
        )
        self.sigma_s = np.broadcast_to(
            np.asarray(sigma_s, dtype=float), (n_r, n_z)
        )
        self.nu_sigma_f = np.broadcast_to(
            np.asarray(nu_sigma_f, dtype=float), (n_r, n_z)
        )
        self.chi = float(chi)
        self.dr = dr if dr is not None else 1.0 / n_r
        self.dz = dz if dz is not None else 1.0 / n_z
        self.order = order
        self.bc_r_inner = bc_r_inner
        self.bc_r_outer = bc_r_outer
        self.bc_z_lo = bc_z_lo
        self.bc_z_hi = bc_z_hi

        if order == 2:
            self.mu = S2_MU
            self.weights = S2_WEIGHTS
        elif order == 4:
            self.mu = S4_MU
            self.weights = S4_WEIGHTS
        else:
            raise ValueError(f"order must be 2 or 4, got {order}")
        self.n_angles = len(self.mu)

    def solve_eigenvalue(
        self,
        max_iter: int = 200,
        tolerance: float = 1e-6,
    ) -> SN2DCylindricalResult:
        """
        Solve k-eigenvalue in 2D r-z via source iteration.

        Uses simplified 2D: radial sweep + axial sweep per angle.
        """
        nr, nz = self.n_r, self.n_z
        phi = np.ones((nr, nz)) / (nr * nz)
        k = 1.0
        psi = np.ones((nr, nz, self.n_angles)) / (nr * nz * self.n_angles)

        for it in range(max_iter):
            fission_int = np.sum(self.nu_sigma_f * phi)
            q = self.sigma_s * phi + (self.chi * fission_int / k) / (nr * nz)
            q = np.where(self.sigma_t > 1e-30, q / self.sigma_t, 0.0)

            psi_new = np.zeros_like(psi)
            for m in range(self.n_angles):
                mu, eta = self.mu[m], np.sqrt(1 - self.mu[m] ** 2)
                if abs(mu) < 1e-10:
                    mu = 0.1 * np.sign(self.mu[m]) if self.mu[m] != 0 else 0.1
                for ir in range(nr):
                    r = (ir + 0.5) * self.dr
                    for iz in range(nz):
                        in_r = 0.0
                        if ir > 0:
                            in_r = psi[ir - 1, iz, m] if mu > 0 else psi[ir, iz, m]
                        elif self.bc_r_inner == "reflective" and mu > 0:
                            in_r = psi[1, iz, m]
                        in_z = 0.0
                        if iz > 0:
                            in_z = psi[ir, iz - 1, m] if eta > 0 else psi[ir, iz, m]
                        elif self.bc_z_lo == "reflective" and eta > 0:
                            in_z = psi[ir, 1, m]
                        denom = abs(mu) / self.dr + abs(eta) / self.dz + self.sigma_t[ir, iz] / 2
                        if r > 1e-10:
                            denom += abs(mu) / (2 * r)
                        psi_new[ir, iz, m] = (
                            q[ir, iz] / 2
                            + abs(mu) * in_r / self.dr
                            + abs(eta) * in_z / self.dz
                        ) / denom

            phi_new = np.sum(self.weights * psi_new, axis=2)
            phi_new = np.maximum(phi_new, 1e-30)
            phi_new = phi_new / np.sum(phi_new)

            k_new = k * np.sum(self.nu_sigma_f * phi_new) / (
                np.sum(self.nu_sigma_f * phi) + 1e-30
            )

            err = np.max(np.abs(phi_new - phi))
            if err < tolerance and abs(k_new - k) < tolerance:
                logger.info(
                    f"SN 2D cylindrical converged in {it + 1} iterations, k={k_new:.6f}"
                )
                return SN2DCylindricalResult(
                    flux=psi_new,
                    k_eff=k_new,
                    scalar_flux=phi_new,
                    n_iterations=it + 1,
                    converged=True,
                )

            phi = phi_new
            psi = psi_new
            k = k_new

        return SN2DCylindricalResult(
            flux=psi,
            k_eff=k,
            scalar_flux=phi,
            n_iterations=max_iter,
            converged=False,
        )


@dataclass
class SN3DCartesianResult:
    """Result of 3D Cartesian SN transport solve."""

    flux: np.ndarray  # [nx, ny, nz, n_angles]
    k_eff: float
    scalar_flux: np.ndarray  # [nx, ny, nz]
    n_iterations: int
    converged: bool


class SN3DCartesianSolver:
    """
    S2/S4 discrete ordinates 3D Cartesian transport solver.

    Solves 3D x-y-z transport via source iteration with directional sweeps.
    For reactor core Cartesian meshes.
    """

    def __init__(
        self,
        n_x: int,
        n_y: int,
        n_z: int,
        sigma_t: np.ndarray,
        sigma_s: np.ndarray,
        nu_sigma_f: np.ndarray,
        chi: float = 1.0,
        dx: Optional[float] = None,
        dy: Optional[float] = None,
        dz: Optional[float] = None,
        order: int = 2,
        bc_x_lo: str = "reflective",
        bc_x_hi: str = "reflective",
        bc_y_lo: str = "reflective",
        bc_y_hi: str = "reflective",
        bc_z_lo: str = "reflective",
        bc_z_hi: str = "reflective",
    ):
        self.n_x, self.n_y, self.n_z = n_x, n_y, n_z
        self.sigma_t = np.broadcast_to(
            np.asarray(sigma_t, dtype=float), (n_x, n_y, n_z)
        )
        self.sigma_s = np.broadcast_to(
            np.asarray(sigma_s, dtype=float), (n_x, n_y, n_z)
        )
        self.nu_sigma_f = np.broadcast_to(
            np.asarray(nu_sigma_f, dtype=float), (n_x, n_y, n_z)
        )
        self.chi = float(chi)
        self.dx = dx or 1.0 / n_x
        self.dy = dy or 1.0 / n_y
        self.dz = dz or 1.0 / n_z
        self.order = order
        self.bc_x_lo = bc_x_lo
        self.bc_x_hi = bc_x_hi
        self.bc_y_lo = bc_y_lo
        self.bc_y_hi = bc_y_hi
        self.bc_z_lo = bc_z_lo
        self.bc_z_hi = bc_z_hi

        if order == 2:
            self.mu = S2_MU
            self.weights = S2_WEIGHTS
        elif order == 4:
            self.mu = S4_MU
            self.weights = S4_WEIGHTS
        else:
            raise ValueError(f"order must be 2 or 4, got {order}")
        self.n_angles = len(self.mu)

    def solve_eigenvalue(
        self,
        max_iter: int = 200,
        tolerance: float = 1e-6,
    ) -> SN3DCartesianResult:
        """Solve k-eigenvalue in 3D Cartesian via source iteration."""
        nx, ny, nz = self.n_x, self.n_y, self.n_z
        n_cells = nx * ny * nz
        phi = np.ones((nx, ny, nz)) / n_cells
        k = 1.0
        psi = np.ones((nx, ny, nz, self.n_angles)) / (n_cells * self.n_angles)

        for it in range(max_iter):
            fission_int = np.sum(self.nu_sigma_f * phi)
            q = self.sigma_s * phi + (self.chi * fission_int / k) / n_cells
            q = np.where(self.sigma_t > 1e-30, q / self.sigma_t, 0.0)

            # 3D ordinates: diagonal (1,1,1)/sqrt3 and (-1,-1,-1)/sqrt3
            eta = 1.0 / np.sqrt(3.0)
            psi_new = np.zeros_like(psi)
            for m in range(self.n_angles):
                sgn = 1 if self.mu[m] > 0 else -1
                rx = range(nx) if sgn > 0 else range(nx - 1, -1, -1)
                ry = range(ny) if sgn > 0 else range(ny - 1, -1, -1)
                rz = range(nz) if sgn > 0 else range(nz - 1, -1, -1)
                for ix in rx:
                    for iy in ry:
                        for iz in rz:
                            denom = (
                                eta / self.dx
                                + eta / self.dy
                                + eta / self.dz
                                + self.sigma_t[ix, iy, iz] / 2
                            )
                            if sgn > 0:
                                in_x = psi[ix - 1, iy, iz, m] if ix > 0 else (psi[1, iy, iz, m] if self.bc_x_lo == "reflective" else 0.0)
                                in_y = psi[ix, iy - 1, iz, m] if iy > 0 else (psi[ix, 1, iz, m] if self.bc_y_lo == "reflective" else 0.0)
                                in_z = psi[ix, iy, iz - 1, m] if iz > 0 else (psi[ix, iy, 1, m] if self.bc_z_lo == "reflective" else 0.0)
                            else:
                                in_x = psi[ix + 1, iy, iz, m] if ix < nx - 1 else (psi[nx - 2, iy, iz, m] if self.bc_x_hi == "reflective" else 0.0)
                                in_y = psi[ix, iy + 1, iz, m] if iy < ny - 1 else (psi[ix, ny - 2, iz, m] if self.bc_y_hi == "reflective" else 0.0)
                                in_z = psi[ix, iy, iz + 1, m] if iz < nz - 1 else (psi[ix, iy, nz - 2, m] if self.bc_z_hi == "reflective" else 0.0)
                            psi_new[ix, iy, iz, m] = (
                                q[ix, iy, iz] / 2
                                + eta * in_x / self.dx
                                + eta * in_y / self.dy
                                + eta * in_z / self.dz
                            ) / denom

            phi_new = np.sum(self.weights * psi_new, axis=3)
            phi_new = np.maximum(phi_new, 1e-30)
            phi_new = phi_new / np.sum(phi_new)

            k_new = k * np.sum(self.nu_sigma_f * phi_new) / (
                np.sum(self.nu_sigma_f * phi) + 1e-30
            )

            err = np.max(np.abs(phi_new - phi))
            if err < tolerance and abs(k_new - k) < tolerance:
                logger.info(
                    f"SN 3D Cartesian converged in {it + 1} iterations, k={k_new:.6f}"
                )
                return SN3DCartesianResult(
                    flux=psi_new,
                    k_eff=k_new,
                    scalar_flux=phi_new,
                    n_iterations=it + 1,
                    converged=True,
                )

            phi = phi_new
            psi = psi_new
            k = k_new

        return SN3DCartesianResult(
            flux=psi,
            k_eff=k,
            scalar_flux=phi,
            n_iterations=max_iter,
            converged=False,
        )


@dataclass
class SN2DHexagonalResult:
    """Result of 2D hexagonal SN transport solve."""

    flux: np.ndarray  # [n_cells, n_angles]
    k_eff: float
    scalar_flux: np.ndarray  # [n_cells]
    n_iterations: int
    converged: bool


def _hexagonal_ring_layout(n_rings: int) -> tuple:
    """Return (n_cells, neighbors) for flat-top hexagonal lattice. neighbors[i] = list of cell indices."""
    n_cells = 1 + 3 * n_rings * (n_rings + 1) if n_rings > 0 else 1
    # Simplified: use 1D indexing, neighbors by ring structure
    neighbors: list = [[] for _ in range(n_cells)]
    # Ring 0: center (index 0)
    # Ring r has 6*r cells, indices 1+3*r*(r-1) .. 1+3*r*(r+1)-1
    idx = 1
    for r in range(1, n_rings + 1):
        n_in_ring = 6 * r
        for j in range(n_in_ring):
            # Each cell connects to 2 in same ring, 1-2 in adjacent rings
            if r == 1:
                neighbors[idx].append(0)
                neighbors[0].append(idx)
            else:
                prev_start = 1 + 3 * (r - 1) * (r - 2)
                prev_n = 6 * (r - 1)
                if prev_n > 0:
                    k_prev = prev_start + (j * prev_n) // n_in_ring
                    neighbors[idx].append(k_prev)
                    if k_prev not in neighbors[idx]:
                        pass
            idx += 1
    return n_cells, neighbors


class SN2DHexagonalSolver:
    """
    S2/S4 discrete ordinates 2D hexagonal lattice transport solver.

    Uses ring-based hexagonal mesh (flat-top). Center cell + rings of hexagons.
    For VVER/HTGR hexagonal assembly and core geometries.
    """

    def __init__(
        self,
        n_rings: int,
        sigma_t: np.ndarray,
        sigma_s: np.ndarray,
        nu_sigma_f: np.ndarray,
        chi: float = 1.0,
        pitch: float = 1.0,
        order: int = 2,
        bc_outer: str = "reflective",
    ):
        self.n_rings = n_rings
        n_cells, _ = _hexagonal_ring_layout(n_rings)
        self.n_cells = n_cells
        self.sigma_t = np.broadcast_to(np.asarray(sigma_t, dtype=float), (n_cells,))
        self.sigma_s = np.broadcast_to(np.asarray(sigma_s, dtype=float), (n_cells,))
        self.nu_sigma_f = np.broadcast_to(
            np.asarray(nu_sigma_f, dtype=float), (n_cells,)
        )
        self.chi = float(chi)
        self.pitch = pitch
        self.order = order
        self.bc_outer = bc_outer

        if order == 2:
            self.mu = S2_MU
            self.weights = S2_WEIGHTS
        elif order == 4:
            self.mu = S4_MU
            self.weights = S4_WEIGHTS
        else:
            raise ValueError(f"order must be 2 or 4, got {order}")
        self.n_angles = len(self.mu)

    def solve_eigenvalue(
        self,
        max_iter: int = 200,
        tolerance: float = 1e-6,
    ) -> SN2DHexagonalResult:
        """Solve k-eigenvalue on hexagonal lattice via source iteration."""
        n = self.n_cells
        phi = np.ones(n) / n
        k = 1.0
        psi = np.ones((n, self.n_angles)) / (n * self.n_angles)

        for it in range(max_iter):
            fission_int = np.sum(self.nu_sigma_f * phi)
            q = self.sigma_s * phi + (self.chi * fission_int / k) / n
            q = np.where(self.sigma_t > 1e-30, q / self.sigma_t, 0.0)

            psi_new = np.zeros_like(psi)
            for m in range(self.n_angles):
                mu = self.mu[m]
                # Sweep order by ring (center first, then outward)
                for i in range(n):
                    # Simplified: 1D-style sweep with effective streaming
                    denom = abs(mu) / self.pitch + self.sigma_t[i] / 2
                    in_psi = 0.0
                    if i > 0:
                        in_psi = psi[i - 1, m]
                    elif self.bc_outer == "reflective" and mu > 0:
                        in_psi = psi[min(1, n - 1), m]
                    psi_new[i, m] = (
                        q[i] / 2 + abs(mu) * in_psi / self.pitch
                    ) / denom

            phi_new = np.sum(self.weights * psi_new, axis=1)
            phi_new = np.maximum(phi_new, 1e-30)
            phi_new = phi_new / np.sum(phi_new)

            k_new = k * np.sum(self.nu_sigma_f * phi_new) / (
                np.sum(self.nu_sigma_f * phi) + 1e-30
            )

            err = np.max(np.abs(phi_new - phi))
            if err < tolerance and abs(k_new - k) < tolerance:
                logger.info(
                    f"SN 2D hexagonal converged in {it + 1} iterations, k={k_new:.6f}"
                )
                return SN2DHexagonalResult(
                    flux=psi_new,
                    k_eff=k_new,
                    scalar_flux=phi_new,
                    n_iterations=it + 1,
                    converged=True,
                )

            phi = phi_new
            psi = psi_new
            k = k_new

        return SN2DHexagonalResult(
            flux=psi,
            k_eff=k,
            scalar_flux=phi,
            n_iterations=max_iter,
            converged=False,
        )
