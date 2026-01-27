"""
Gamma-ray transport solver.

This module implements a multi-group gamma transport solver for:
- Gamma-ray shielding calculations
- Decay heat transport
- Radiation protection analysis
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from scipy.sparse import csr_matrix, diags
from scipy.sparse import linalg as sparse_linalg

from ..core.reactor_core import Nuclide, NuclearDataCache
from ..core.photon_parser import PhotonCrossSection
from ..core.material_mapping import MaterialMapper
from ..geometry import PrismaticCore
from ..utils.logging import get_logger

logger = get_logger("smrforge.gamma_transport")


@dataclass
class GammaTransportOptions:
    """
    Configuration options for gamma transport solver.
    
    Attributes:
        n_groups: Number of energy groups
        max_iterations: Maximum iterations for source iteration
        tolerance: Convergence tolerance
        verbose: If True, print iteration progress
    """
    
    n_groups: int = 20  # Typical: 20-50 groups for gamma transport
    max_iterations: int = 100
    tolerance: float = 1e-6
    verbose: bool = False


@dataclass
class PhotonCrossSectionData:
    """
    Photon cross-section data for a material.
    
    Attributes:
        energy_groups: Energy group boundaries [MeV]
        sigma_total: Total cross-section [1/cm] for each group
        sigma_photoelectric: Photoelectric cross-section [1/cm]
        sigma_compton: Compton scattering cross-section [1/cm]
        sigma_pair: Pair production cross-section [1/cm]
    """
    
    energy_groups: np.ndarray  # [n_groups + 1]
    sigma_total: np.ndarray  # [n_groups]
    sigma_photoelectric: np.ndarray  # [n_groups]
    sigma_compton: np.ndarray  # [n_groups]
    sigma_pair: np.ndarray  # [n_groups]


class GammaTransportSolver:
    """
    Multi-group gamma-ray transport solver.
    
    Solves the gamma transport equation using diffusion approximation:
    -∇·D∇φ + Σ_t φ = S
    
    Where:
    - φ: Gamma flux [photons/cm²/s]
    - D: Diffusion coefficient
    - Σ_t: Total cross-section
    - S: Gamma source term
    
    Usage:
        >>> from smrforge.gamma_transport import GammaTransportSolver, GammaTransportOptions
        >>> from smrforge.geometry import PrismaticCore
        >>> 
        >>> geometry = PrismaticCore(name="Shielding")
        >>> geometry.build_mesh(n_radial=10, n_axial=5)
        >>> 
        >>> options = GammaTransportOptions(n_groups=20)
        >>> solver = GammaTransportSolver(geometry, options)
        >>> 
        >>> # Set gamma source (from decay heat, etc.)
        >>> source = ...  # [nz, nr, ng] gamma source
        >>> 
        >>> # Solve
        >>> flux = solver.solve(source)
    """
    
    def __init__(
        self,
        geometry: PrismaticCore,
        options: GammaTransportOptions,
        cache: Optional[NuclearDataCache] = None,
    ):
        """
        Initialize gamma transport solver.
        
        Args:
            geometry: PrismaticCore geometry instance
            options: GammaTransportOptions configuration
            cache: Optional NuclearDataCache for photon cross-sections
        """
        self.geometry = geometry
        self.options = options
        self.cache = cache if cache is not None else NuclearDataCache()
        
        # Get geometry dimensions from mesh
        if geometry.axial_mesh is not None and geometry.radial_mesh is not None:
            self.nz = len(geometry.axial_mesh) - 1
            self.nr = len(geometry.radial_mesh) - 1
        else:
            # Fallback: try to get from attributes if they exist
            self.nz = getattr(geometry, 'n_axial', 1)
            self.nr = getattr(geometry, 'n_radial', 1)
        self.ng = options.n_groups
        
        # Get mesh
        if geometry.axial_mesh is not None and geometry.radial_mesh is not None:
            self.r_centers = 0.5 * (geometry.radial_mesh[1:] + geometry.radial_mesh[:-1])
            self.z_centers = 0.5 * (geometry.axial_mesh[1:] + geometry.axial_mesh[:-1])
            self.dr = np.diff(geometry.radial_mesh)
            self.dz = np.diff(geometry.axial_mesh)
        else:
            # Fallback: create dummy mesh
            self.r_centers = np.array([25.0])  # Default to radius at center
            self.z_centers = np.array([50.0])  # Default to height at center
            self.dr = np.array([50.0])
            self.dz = np.array([100.0])
        
        # Material map (simplified: assume single material for now)
        self.material_map = np.zeros((self.nz, self.nr), dtype=int)
        
        # Initialize cross-sections (placeholder - would load from photon data)
        self._initialize_cross_sections()
        
        # Flux solution
        self.flux: Optional[np.ndarray] = None  # [nz, nr, ng]
        
        logger.info(
            f"Initialized gamma transport solver: {self.nz}×{self.nr} mesh, "
            f"{self.ng} energy groups"
        )
    
    def _initialize_cross_sections(self, material: str = "H2O"):
        """
        Initialize photon cross-sections from ENDF data or use placeholders.
        
        Uses sophisticated material mapping to handle compound materials.
        For compound materials (e.g., H2O), computes weighted average of
        constituent element cross-sections.
        
        Args:
            material: Material name (e.g., "H2O", "Fe", "UO2"). Uses MaterialMapper
                to determine composition and load appropriate photon data.
                Defaults to "H2O" (water).
        """
        # Energy groups: 0.01 MeV to 10 MeV (typical gamma range)
        self.energy_groups = np.logspace(-2, 1, self.ng + 1)  # [MeV]
        
        # Get material composition
        comp = MaterialMapper.get_composition(material)
        
        # Try to load real photon data from cache
        group_centers = (self.energy_groups[:-1] + self.energy_groups[1:]) / 2
        
        if comp and len(comp.elements) > 1:
            # Compound material - compute weighted average
            cross_sections = {}
            for element in comp.elements:
                # Handle deuterium (use H data)
                element_key = "H" if element == "D" else element
                try:
                    photon_data = self.cache.get_photon_cross_section(element_key)
                    if photon_data:
                        # Interpolate to energy groups
                        xs_array = np.array([
                            photon_data.interpolate(E)[3]  # Total cross-section
                            for E in group_centers
                        ])
                        cross_sections[element] = xs_array
                except Exception:
                    pass
            
            if cross_sections:
                # Compute weighted average
                weighted_xs = MaterialMapper.compute_weighted_cross_section(
                    material, cross_sections, group_centers
                )
                # Use weighted average for all cross-sections (simplified)
                self.sigma_total = weighted_xs
                self.sigma_photoelectric = weighted_xs * 0.3  # Approximate
                self.sigma_compton = weighted_xs * 0.6
                self.sigma_pair = weighted_xs * 0.1
                logger.info(f"Loaded weighted photon cross-sections for {material} from ENDF data")
            else:
                # Fallback to primary element
                element = MaterialMapper.get_primary_element(material)
                photon_data = self._load_photon_data_for_element(element, group_centers)
        else:
            # Simple material - use primary element
            element = MaterialMapper.get_primary_element(material)
            photon_data = self._load_photon_data_for_element(element, group_centers)
        
        if photon_data is None:
            # Placeholder cross-sections
            self.sigma_total = np.ones(self.ng) * 0.1  # [1/cm]
            self.sigma_photoelectric = np.ones(self.ng) * 0.03
            self.sigma_compton = np.ones(self.ng) * 0.06
            self.sigma_pair = np.ones(self.ng) * 0.01
            logger.debug("Using placeholder photon cross-sections")
        
        # Diffusion coefficient: D = 1 / (3 * sigma_t)
        self.D = 1.0 / (3.0 * self.sigma_total)  # [cm]
    
    def _load_photon_data_for_element(
        self, element: str, group_centers: np.ndarray
    ) -> Optional[PhotonCrossSection]:
        """
        Load photon data for an element and convert to solver units.
        
        Args:
            element: Element symbol.
            group_centers: Energy group centers [MeV].
        
        Returns:
            PhotonCrossSection if loaded successfully, None otherwise.
        """
        try:
            photon_data = self.cache.get_photon_cross_section(element)
            if photon_data is None:
                return None
            
            # Interpolate to energy groups
            sigma_pe = np.zeros(self.ng)
            sigma_comp = np.zeros(self.ng)
            sigma_pair = np.zeros(self.ng)
            sigma_total = np.zeros(self.ng)
            
            for i, E in enumerate(group_centers):
                pe, comp, pair, tot = photon_data.interpolate(E)
                sigma_pe[i] = pe
                sigma_comp[i] = comp
                sigma_pair[i] = pair
                sigma_total[i] = tot
            
            # Convert from barn to 1/cm (with material density)
            density = MaterialMapper.get_density("H2O") or 1.0  # Default to water density
            atomic_mass = MaterialMapper.ATOMIC_MASSES.get(element, 1.008)
            avogadro = 6.022e23  # atoms/mol
            
            # Convert: sigma [barn] -> sigma [1/cm] = sigma [barn] * density * N_A / atomic_mass * 1e-24
            conversion = density * avogadro / atomic_mass * 1e-24
            
            self.sigma_photoelectric = sigma_pe * conversion
            self.sigma_compton = sigma_comp * conversion
            self.sigma_pair = sigma_pair * conversion
            self.sigma_total = sigma_total * conversion
            
            logger.info(f"Loaded photon cross-sections for {element} from ENDF data")
            return photon_data
            
        except Exception as e:
            logger.debug(f"Could not load photon data for {element}: {e}")
            return None
    
    def solve(self, source: Union[np.ndarray, Tuple[np.ndarray, np.ndarray]], time: Optional[float] = None) -> np.ndarray:
        """
        Solve gamma transport equation.
        
        Supports both steady-state and time-dependent sources.
        
        Args:
            source: Gamma source term:
                - [nz, nr, ng] for steady-state
                - Tuple of (source_4d, times) for time-dependent: ([n_times, nz, nr, ng], [n_times])
            time: Optional time [s] for time-dependent source. Required if source is tuple.
        
        Returns:
            Gamma flux [nz, nr, ng] [photons/cm²/s]
        """
        # Handle time-dependent source
        if isinstance(source, tuple):
            source_4d, times = source
            if time is None:
                raise ValueError("Time must be provided for time-dependent source")
            
            # Interpolate source to requested time
            source_3d = self._interpolate_time_dependent_source(source_4d, times, time)
        else:
            source_3d = source
        
        if source_3d.shape != (self.nz, self.nr, self.ng):
            raise ValueError(
                f"Source shape {source_3d.shape} does not match expected {(self.nz, self.nr, self.ng)}"
            )
        
        # Initialize flux
        self.flux = np.zeros((self.nz, self.nr, self.ng))
        
        # Source iteration
        for iteration in range(self.options.max_iterations):
            flux_old = self.flux.copy()
            
            # Solve for each energy group
            for g in range(self.ng):
                self.flux[:, :, g] = self._solve_group(g, source_3d[:, :, g])
            
            # Check convergence
            if iteration > 0:
                error = np.max(np.abs(self.flux - flux_old)) / (np.max(np.abs(self.flux)) + 1e-10)
                
                if self.options.verbose and iteration % 10 == 0:
                    logger.debug(f"Gamma transport iteration {iteration}: error = {error:.2e}")
                
                if error < self.options.tolerance:
                    logger.info(f"Gamma transport converged in {iteration+1} iterations")
                    return self.flux
            
            # Normalize flux
            max_flux = np.max(self.flux)
            if max_flux > 0:
                self.flux = self.flux / max_flux
        
        logger.warning(
            f"Gamma transport did not converge in {self.options.max_iterations} iterations"
        )
        return self.flux
    
    def _interpolate_time_dependent_source(
        self, source_4d: np.ndarray, times: np.ndarray, time: float
    ) -> np.ndarray:
        """
        Interpolate time-dependent source to a specific time.
        
        Args:
            source_4d: Time-dependent source [n_times, nz, nr, ng]
            times: Time array [n_times] [s]
            time: Requested time [s]
        
        Returns:
            Source at requested time [nz, nr, ng]
        """
        if source_4d.shape[0] != len(times):
            raise ValueError("Source and times must have same length")
        
        if len(times) == 1:
            return source_4d[0, :, :, :]
        
        # Find time index
        idx = np.searchsorted(times, time)
        
        if idx == 0:
            return source_4d[0, :, :, :]
        if idx >= len(times):
            return source_4d[-1, :, :, :]
        
        # Linear interpolation
        t1, t2 = times[idx - 1], times[idx]
        s1, s2 = source_4d[idx - 1, :, :, :], source_4d[idx, :, :, :]
        
        if t2 > t1:
            frac = (time - t1) / (t2 - t1)
            return s1 + frac * (s2 - s1)
        
        return s1
    
    def _solve_group(self, g: int, source_g: np.ndarray) -> np.ndarray:
        """
        Solve single-group gamma diffusion equation.
        
        Args:
            g: Energy group index
            source_g: Source term for group g [nz, nr]
        
        Returns:
            Flux for group g [nz, nr]
        """
        # Build system: -∇·D∇φ + Σ_t φ = S
        # Discretized: A*φ = b
        
        A, b = self._build_group_system(g, source_g)
        
        # Solve
        flux_1d = sparse_linalg.spsolve(A, b)
        flux_2d = flux_1d.reshape(self.nz, self.nr)
        
        return flux_2d
    
    def _build_group_system(self, g: int, source_g: np.ndarray) -> Tuple[csr_matrix, np.ndarray]:
        """
        Build linear system for group g.
        
        Args:
            g: Energy group index
            source_g: Source term [nz, nr]
        
        Returns:
            Tuple of (A, b) where A*flux = b
        """
        n_cells = self.nz * self.nr
        
        # Build sparse matrix A
        # Diagonal: Σ_t * V (absorption term)
        # Off-diagonal: -D * gradient terms (diffusion)
        
        # Simplified: use 5-point stencil for 2D
        rows = []
        cols = []
        data = []
        
        sigma_t_g = self.sigma_total[g]
        D_g = self.D[g]
        
        # Optimized: pre-compute cell volumes once
        cell_volumes = self._cell_volumes()  # [nz, nr]
        
        # Pre-compute diffusion coefficients for vectorization
        # Radial diffusion coefficients: [nr]
        dr_squared = self.dr ** 2
        radial_diffusion_coef = D_g / dr_squared  # [nr]
        
        # Axial diffusion coefficients: [nz]
        dz_squared = self.dz ** 2
        axial_diffusion_coef = D_g / dz_squared  # [nz]
        
        # Vectorized diagonal computation
        # Base absorption term: [nz, nr]
        diag_base = sigma_t_g * cell_volumes
        
        # Add radial diffusion contributions (vectorized)
        # Inner cells (ir > 0 and ir < nr-1) get contributions from both sides
        radial_contrib = np.zeros((self.nz, self.nr))
        radial_contrib[:, 1:-1] = 2 * radial_diffusion_coef[1:-1, np.newaxis] * cell_volumes[:, 1:-1]  # Inner cells
        radial_contrib[:, 0] = radial_diffusion_coef[0] * cell_volumes[:, 0]  # Left boundary
        radial_contrib[:, -1] = radial_diffusion_coef[-1] * cell_volumes[:, -1]  # Right boundary
        
        # Add axial diffusion contributions (vectorized)
        axial_contrib = np.zeros((self.nz, self.nr))
        axial_contrib[1:-1, :] = 2 * axial_diffusion_coef[1:-1, np.newaxis] * cell_volumes[1:-1, :]  # Inner cells
        axial_contrib[0, :] = axial_diffusion_coef[0] * cell_volumes[0, :]  # Bottom boundary
        axial_contrib[-1, :] = axial_diffusion_coef[-1] * cell_volumes[-1, :]  # Top boundary
        
        # Total diagonal: [nz, nr]
        diag_values = diag_base + radial_contrib + axial_contrib
        
        # Build sparse matrix structure (still need loops for indexing, but computation is vectorized)
        for iz in range(self.nz):
            for ir in range(self.nr):
                idx = iz * self.nr + ir
                rows.append(idx)
                cols.append(idx)
                data.append(diag_values[iz, ir])
                
                # Off-diagonal: diffusion coupling
                # (Simplified - full implementation would use proper finite difference)
        
        A = csr_matrix((data, (rows, cols)), shape=(n_cells, n_cells))
        
        # Right-hand side: source term (optimized: use pre-computed volumes)
        b = source_g.flatten() * cell_volumes.flatten()
        
        return A, b
    
    def _cell_volume(self, iz: int, ir: int) -> float:
        """Get cell volume for cell (iz, ir)."""
        r = self.r_centers[ir]
        dr = self.dr[ir]
        dz = self.dz[iz]
        return 2 * np.pi * r * dr * dz
    
    def _cell_volumes(self) -> np.ndarray:
        """Get all cell volumes [nz, nr] (optimized: vectorized)."""
        # Vectorized computation using broadcasting
        # r_centers is [nr], dr is [nr], dz is [nz]
        # Result: [nz, nr]
        r = self.r_centers[np.newaxis, :]  # [1, nr]
        dr = self.dr[np.newaxis, :]  # [1, nr]
        dz = self.dz[:, np.newaxis]  # [nz, 1]
        
        volumes = 2 * np.pi * r * dr * dz  # [nz, nr]
        return volumes
    
    def compute_dose_rate(self, flux: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Compute dose rate from gamma flux.
        
        Args:
            flux: Gamma flux [nz, nr, ng]. If None, uses self.flux.
        
        Returns:
            Dose rate [nz, nr] [Sv/h]
        """
        if flux is None:
            flux = self.flux
        if flux is None:
            raise RuntimeError("Must solve for flux first or provide flux")
        
        # Dose conversion factors (simplified)
        # Typical: ~1e-12 Sv/h per photon/cm²/s for 1 MeV gammas
        # Optimized: vectorize over energy groups
        # Energy at group centers: [ng]
        E_centers = (self.energy_groups[:-1] + self.energy_groups[1:]) / 2  # [ng] MeV
        
        # Dose conversion factors: [ng]
        conversion_factors = 1e-12 * E_centers  # [ng] Sv/h per photon/cm²/s
        
        # Vectorized: flux is [nz, nr, ng], conversion_factors is [ng]
        # Sum over energy groups: [nz, nr]
        dose_rate = np.sum(flux * conversion_factors[np.newaxis, np.newaxis, :], axis=2)
        
        return dose_rate

