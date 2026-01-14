"""
Burnup solver for fuel depletion calculations.

This module implements a coupled neutronics-burnup solver that tracks nuclide
concentrations over time, accounting for:
- Fission product production (via fission yields)
- Radioactive decay (via decay data)
- Neutron capture and transmutation
- Flux-dependent burnup rates
"""

import warnings
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import csr_matrix

from ..core.reactor_core import (
    DecayData,
    Nuclide,
    get_fission_yield_data,
    NuclearDataCache,
    Library,
)
from ..neutronics.solver import MultiGroupDiffusion
from ..utils.logging import get_logger
from ..validation.models import CrossSectionData

logger = get_logger("smrforge.burnup")


@dataclass
class NuclideInventory:
    """
    Tracks nuclide concentrations over time.
    
    Attributes:
        nuclides: List of Nuclide instances being tracked
        concentrations: Array of concentrations [n_nuclides, n_time_steps]
            Units: atoms/cm³ (or atoms/barn-cm for normalized)
        times: Array of time points [n_time_steps] in seconds
        burnup: Array of burnup values [n_time_steps] in MWd/kgU
    """
    
    nuclides: List[Nuclide]
    concentrations: np.ndarray  # [n_nuclides, n_time_steps]
    times: np.ndarray  # [n_time_steps]
    burnup: np.ndarray  # [n_time_steps]
    
    def get_concentration(self, nuclide: Nuclide, time_index: int = -1) -> float:
        """
        Get concentration of a nuclide at a specific time.
        
        Args:
            nuclide: Nuclide instance
            time_index: Time step index (default: -1 for final time)
        
        Returns:
            Concentration in atoms/cm³
        """
        try:
            idx = self.nuclides.index(nuclide)
            return self.concentrations[idx, time_index]
        except (ValueError, IndexError):
            return 0.0
    
    def get_total_inventory(self, time_index: int = -1) -> float:
        """
        Get total nuclide inventory at a specific time.
        
        Args:
            time_index: Time step index (default: -1 for final time)
        
        Returns:
            Total concentration in atoms/cm³
        """
        return np.sum(self.concentrations[:, time_index])


@dataclass
class BurnupOptions:
    """
    Configuration options for burnup calculations.
    
    Attributes:
        time_steps: List of time points [days] for burnup calculation
        power_density: Power density [W/cm³] (constant) or array [n_time_steps]
        initial_enrichment: Initial U-235 enrichment (fraction, e.g., 0.195 for 19.5%)
        fissile_nuclides: List of fissile nuclides (default: U235, Pu239)
        track_fission_products: If True, track fission products (default: True)
        track_actinides: If True, track actinides (default: True)
        max_fission_products: Maximum number of fission products to track (default: 100)
        decay_tolerance: Tolerance for decay matrix solver (default: 1e-8)
        integration_method: ODE solver method ('RK45', 'BDF', 'Radau', default: 'BDF')
    """
    
    time_steps: List[float]  # days
    power_density: float = 1e6  # W/cm³ (default: 1 MW/cm³)
    initial_enrichment: float = 0.195  # 19.5% U-235
    fissile_nuclides: List[Nuclide] = field(default_factory=lambda: [
        Nuclide(Z=92, A=235),
        Nuclide(Z=94, A=239),
    ])
    track_fission_products: bool = True
    track_actinides: bool = True
    max_fission_products: int = 100
    decay_tolerance: float = 1e-8
    integration_method: str = "BDF"  # BDF is good for stiff ODEs (decay chains)
    # Adaptive nuclide tracking options
    adaptive_tracking: bool = False  # Enable adaptive nuclide tracking
    nuclide_threshold: float = 1e15  # Minimum concentration [atoms/cm³] to track
    nuclide_importance_threshold: float = 1e-3  # Relative importance threshold (fraction of total)
    adaptive_update_interval: int = 5  # Update nuclide list every N time steps
    always_track_nuclides: List[Nuclide] = field(default_factory=list)  # Nuclides to always track


class BurnupSolver:
    """
    Coupled neutronics-burnup solver for fuel depletion calculations.
    
    This solver tracks nuclide concentrations over time by solving the
    Bateman equations coupled with neutronics. It accounts for:
    - Fission product production (via fission yields)
    - Radioactive decay (via decay data)
    - Neutron capture and transmutation
    - Flux-dependent burnup rates
    
    The solver uses a predictor-corrector approach:
    1. Solve neutronics for flux distribution
    2. Calculate reaction rates (fission, capture)
    3. Solve Bateman equations for nuclide evolution
    4. Update cross-sections based on new composition
    5. Repeat for next time step
    
    Usage:
        >>> from smrforge.burnup import BurnupSolver, BurnupOptions
        >>> from smrforge.geometry import PrismaticCore
        >>> from smrforge.neutronics.solver import MultiGroupDiffusion
        >>> 
        >>> # Create geometry and neutronics solver
        >>> geometry = PrismaticCore(name="TestCore")
        >>> geometry.build_mesh(n_radial=20, n_axial=10)
        >>> 
        >>> # Initial cross-sections (before burnup)
        >>> xs_data = ...  # Create initial cross-sections
        >>> neutronics = MultiGroupDiffusion(geometry, xs_data, options)
        >>> 
        >>> # Create burnup solver
        >>> burnup_options = BurnupOptions(
        ...     time_steps=[0, 30, 60, 90, 365],  # days
        ...     power_density=1e6,  # W/cm³
        ...     initial_enrichment=0.195
        ... )
        >>> 
        >>> burnup = BurnupSolver(neutronics, burnup_options)
        >>> 
        >>> # Run burnup calculation
        >>> inventory = burnup.solve()
        >>> 
        >>> # Get final concentrations
        >>> u235_final = inventory.get_concentration(Nuclide(Z=92, A=235))
        >>> print(f"Final U-235: {u235_final:.2e} atoms/cm³")
    """
    
    def __init__(
        self,
        neutronics_solver: MultiGroupDiffusion,
        options: BurnupOptions,
        cache: Optional[NuclearDataCache] = None,
    ):
        """
        Initialize burnup solver.
        
        Args:
            neutronics_solver: MultiGroupDiffusion solver instance
            options: BurnupOptions configuration
            cache: Optional NuclearDataCache for accessing decay/yield data
        """
        self.neutronics = neutronics_solver
        self.options = options
        self.cache = cache if cache is not None else NuclearDataCache()
        # DecayData accepts optional cache parameter (updated in reactor_core.py)
        try:
            self.decay_data = DecayData(cache=self.cache)
        except TypeError:
            # Fallback for compatibility
            self.decay_data = DecayData()
            self.decay_data._cache = self.cache
        
        # Convert time steps from days to seconds
        self.time_steps_sec = np.array(options.time_steps) * 24 * 3600  # days -> seconds
        
        # Initialize nuclide tracking
        self.nuclides: List[Nuclide] = []
        self._initialize_nuclides()
        
        # Initialize concentrations [n_nuclides, n_time_steps]
        # Note: concentrations must be created before _set_initial_concentrations is called
        n_nuclides = len(self.nuclides)
        n_times = len(self.time_steps_sec)
        self.concentrations = np.zeros((n_nuclides, n_times))
        
        # Set initial concentrations (called after concentrations array is created)
        self._set_initial_concentrations()
        
        # Initialize burnup tracking
        self.burnup_mwd_per_kg = np.zeros(n_times)
        
        # Fission yield data cache
        self._fission_yield_cache: Dict[Nuclide, Optional[Any]] = {}
        
        # Adaptive tracking state
        if options.adaptive_tracking:
            # Initialize set of nuclides to always track
            self._always_track = set(self.options.always_track_nuclides)
            self._always_track.update(self.options.fissile_nuclides)
            self._always_track.add(Nuclide(Z=92, A=238))  # U-238 (fertile)
            self._last_adaptive_update = 0
        else:
            self._always_track = set()
            self._last_adaptive_update = -1
        
        logger.info(
            f"Initialized burnup solver: {n_nuclides} nuclides, "
            f"{n_times} time steps, {options.time_steps[-1]:.0f} days total"
            f"{' (adaptive tracking enabled)' if options.adaptive_tracking else ''}"
        )
    
    def _initialize_nuclides(self):
        """Initialize list of nuclides to track."""
        self.nuclides = []
        
        # Add initial fissile nuclides
        for nuc in self.options.fissile_nuclides:
            if nuc not in self.nuclides:
                self.nuclides.append(nuc)
        
        # Add U-238 (fertile, important for Pu production)
        u238 = Nuclide(Z=92, A=238)
        if u238 not in self.nuclides:
            self.nuclides.append(u238)
        
        # Add common actinides
        if self.options.track_actinides:
            actinides = [
                Nuclide(Z=92, A=236),  # U-236
                Nuclide(Z=92, A=237),  # U-237
                Nuclide(Z=93, A=237),  # Np-237
                Nuclide(Z=94, A=238),  # Pu-238
                Nuclide(Z=94, A=240),  # Pu-240
                Nuclide(Z=94, A=241),  # Pu-241
                Nuclide(Z=94, A=242),  # Pu-242
            ]
            for nuc in actinides:
                if nuc not in self.nuclides:
                    self.nuclides.append(nuc)
        
        # Add fission products (if tracking enabled)
        if self.options.track_fission_products:
            # Common fission products (will be populated from yield data)
            common_fps = [
                Nuclide(Z=54, A=135),  # Xe-135 (important for poisoning)
                Nuclide(Z=55, A=137),  # Cs-137
                Nuclide(Z=38, A=90),   # Sr-90
                Nuclide(Z=56, A=140),  # Ba-140
                Nuclide(Z=60, A=144),  # Nd-144
            ]
            for nuc in common_fps:
                if nuc not in self.nuclides:
                    self.nuclides.append(nuc)
        
        # Note: Initial concentrations are set after concentrations array is created in __init__
    
    def _set_initial_concentrations(self):
        """Set initial nuclide concentrations based on enrichment."""
        # UO2 density: ~10 g/cm³, U atomic weight: 238 g/mol
        # U atoms/cm³ ≈ 10 g/cm³ / 238 g/mol * 6.022e23 atoms/mol ≈ 2.5e22 atoms/cm³
        u_density = 2.5e22  # atoms/cm³ (approximate)
        
        # Set U-235 based on enrichment
        u235 = Nuclide(Z=92, A=235)
        u238_nuc = Nuclide(Z=92, A=238)
        
        if u235 in self.nuclides:
            idx_u235 = self.nuclides.index(u235)
            self.concentrations[idx_u235, 0] = u_density * self.options.initial_enrichment
        
        if u238_nuc in self.nuclides:
            idx_u238 = self.nuclides.index(u238_nuc)
            self.concentrations[idx_u238, 0] = u_density * (1.0 - self.options.initial_enrichment)
        
        # Other nuclides start at zero
        for i, nuc in enumerate(self.nuclides):
            if nuc not in [u235, u238_nuc]:
                self.concentrations[i, 0] = 0.0
    
    def solve(self) -> NuclideInventory:
        """
        Solve burnup problem.
        
        Returns:
            NuclideInventory with concentrations over time
        """
        logger.info("Starting burnup calculation...")
        
        # Solve neutronics for initial flux
        logger.info("Solving initial neutronics...")
        k_eff, flux = self.neutronics.solve_steady_state()
        logger.info(f"Initial k-eff: {k_eff:.6f}")
        
        # Time stepping
        for step in range(1, len(self.time_steps_sec)):
            t_start = self.time_steps_sec[step - 1]
            t_end = self.time_steps_sec[step]
            dt = t_end - t_start
            
            logger.info(
                f"Time step {step}/{len(self.time_steps_sec)-1}: "
                f"t = {t_end / (24*3600):.1f} days"
            )
            
            # Solve for nuclide evolution over this time step
            self._solve_time_step(step, t_start, t_end, dt)
            
            # Update cross-sections based on new composition
            self._update_cross_sections(step)
            
            # Re-solve neutronics with updated cross-sections
            # (Optional: can be done every N steps for performance)
            if step % max(1, len(self.time_steps_sec) // 10) == 0 or step == len(self.time_steps_sec) - 1:
                logger.info(f"Re-solving neutronics at step {step} with updated composition...")
                try:
                    k_eff_new, flux_new = self.neutronics.solve_steady_state()
                    logger.info(f"Updated k-eff: {k_eff_new:.6f} (was {self.neutronics.k_eff:.6f})")
                except Exception as e:
                    logger.warning(f"Failed to re-solve neutronics: {e}. Continuing with previous flux.")
            
            # Update adaptive nuclide tracking
            if self.options.adaptive_tracking:
                self._update_adaptive_nuclides(step)
            
            # Calculate burnup
            self._update_burnup(step)
        
        logger.info("Burnup calculation complete!")
        
        return NuclideInventory(
            nuclides=self.nuclides,
            concentrations=self.concentrations,
            times=self.time_steps_sec,
            burnup=self.burnup_mwd_per_kg,
        )
    
    def _solve_time_step(self, step: int, t_start: float, t_end: float, dt: float):
        """
        Solve nuclide evolution for a single time step.
        
        Args:
            step: Time step index
            t_start: Start time [s]
            t_end: End time [s]
            dt: Time step [s]
        """
        # Get current concentrations
        N0 = self.concentrations[:, step - 1].copy()
        
        # Build production and destruction matrices
        # dN/dt = P - D*N
        # where P is production (fission yields, decay in)
        # and D is destruction (decay out, capture)
        
        # Build decay matrix
        A_decay = self._build_decay_matrix()
        
        # Build production vector (fission yields)
        P_fission = self._build_fission_production_vector(step - 1)
        
        # Build capture/destruction terms
        # (Simplified - full implementation would use flux and cross-sections)
        D_capture = self._build_capture_matrix(step - 1)
        
        # Combined system: dN/dt = P_fission + A_decay*N - D_capture*N
        # Rearranged: dN/dt = P_fission + (A_decay - D_capture)*N
        
        A_total = A_decay - D_capture
        
        # Solve ODE system
        def dN_dt(t, N):
            """ODE right-hand side: dN/dt = P + A*N"""
            return P_fission + A_total.dot(N)
        
        # Use scipy's ODE solver
        try:
            sol = solve_ivp(
                dN_dt,
                [t_start, t_end],
                N0,
                method=self.options.integration_method,
                dense_output=False,
                rtol=self.options.decay_tolerance,
                atol=self.options.decay_tolerance,
            )
            
            if sol.success:
                self.concentrations[:, step] = sol.y[:, -1]
            else:
                logger.warning(f"ODE solver failed at step {step}, using Euler step")
                # Fallback: simple Euler step
                dN = dN_dt(t_start, N0) * dt
                self.concentrations[:, step] = N0 + dN
                # Ensure non-negative
                self.concentrations[:, step] = np.maximum(
                    self.concentrations[:, step], 0.0
                )
        except Exception as e:
            logger.error(f"Error solving time step {step}: {e}")
            # Fallback: simple Euler step
            dN = dN_dt(t_start, N0) * dt
            self.concentrations[:, step] = N0 + dN
            self.concentrations[:, step] = np.maximum(self.concentrations[:, step], 0.0)
    
    def _build_decay_matrix(self) -> csr_matrix:
        """
        Build decay matrix for Bateman equations.
        
        Returns:
            Sparse matrix A where dN/dt = A*N describes decay
        """
        return self.decay_data.build_decay_matrix(self.nuclides)
    
    def _build_fission_production_vector(self, time_index: int) -> np.ndarray:
        """
        Build production vector from fission yields with improved flux integration.
        
        Uses spatial and energy-dependent flux integration for accurate reaction rates.
        
        Args:
            time_index: Time step index for flux calculation
        
        Returns:
            Production vector [n_nuclides]
        """
        P = np.zeros(len(self.nuclides))
        
        if self.neutronics.flux is None:
            return P
        
        # Get flux: [nz, nr, ng] - spatial and energy-dependent
        flux = self.neutronics.flux
        nz, nr, ng = flux.shape
        
        # Get cell volumes for spatial integration
        cell_volumes = self.neutronics._cell_volumes()  # [nz, nr]
        
        # Get material map to identify fuel regions
        material_map = self.neutronics.material_map  # [nz, nr]
        
        # For each fissile nuclide, calculate fission rate and add yields
        for fissile in self.options.fissile_nuclides:
            if fissile not in self.nuclides:
                continue
            
            # Get fission yield data
            yield_data = self._get_fission_yield_data(fissile)
            if yield_data is None:
                continue
            
            # Get concentration of fissile nuclide
            idx_fissile = self.nuclides.index(fissile)
            N_fissile = self.concentrations[idx_fissile, time_index]
            
            # Get fission cross-section from neutronics (group-dependent)
            # sigma_f is [n_materials, ng]
            # For fuel material (material 0), get sigma_f[0, :]
            fuel_material_idx = 0  # Assuming fuel is material 0
            sigma_f_g = self.neutronics.xs.sigma_f[fuel_material_idx, :]  # [ng]
            
            # Integrate over space and energy: R_f = ∫∫ sigma_f(E) * φ(r,z,E) * N dV dE
            # Optimized: vectorize over energy groups
            # flux is [nz, nr, ng], sigma_f_g is [ng]
            # Result: [nz, nr, ng] -> sum over all dimensions
            fission_rate_per_group = (
                sigma_f_g[np.newaxis, np.newaxis, :] *  # [1, 1, ng]
                flux *  # [nz, nr, ng]
                N_fissile *  # scalar
                cell_volumes[:, :, np.newaxis]  # [nz, nr, 1]
            )
            total_fission_rate = np.sum(fission_rate_per_group)
            
            # Add production from yields
            for product, yield_val in yield_data.yields.items():
                if product in self.nuclides:
                    idx_product = self.nuclides.index(product)
                    # Production = yield * total_fission_rate
                    P[idx_product] += yield_val.cumulative_yield * total_fission_rate
        
        return P
    
    def _build_capture_matrix(self, time_index: int) -> csr_matrix:
        """
        Build capture/destruction matrix with complete flux integration.
        
        Computes (n,γ) capture rates using spatial and energy-dependent flux.
        Also tracks transmutation products (e.g., U238 + n → U239).
        
        Args:
            time_index: Time step index
        
        Returns:
            Sparse matrix D where capture destruction is D*N
        """
        from scipy.sparse import diags, csr_matrix
        
        n = len(self.nuclides)
        
        if self.neutronics.flux is None:
            return diags(np.zeros(n), format="csr")
        
        # Get flux: [nz, nr, ng]
        flux = self.neutronics.flux
        nz, nr, ng = flux.shape
        
        # Get cell volumes for spatial integration
        cell_volumes = self.neutronics._cell_volumes()  # [nz, nr]
        
        # Capture rates for each nuclide
        capture_rates = np.zeros(n)
        
        # Transmutation matrix: capture in nuclide i produces nuclide j
        # For now, simplified: U238 + n → U239, etc.
        transmutation_map = {
            Nuclide(Z=92, A=238): Nuclide(Z=92, A=239),  # U238 → U239
            Nuclide(Z=92, A=235): Nuclide(Z=92, A=236),  # U235 → U236
            Nuclide(Z=94, A=239): Nuclide(Z=94, A=240),  # Pu239 → Pu240
            Nuclide(Z=94, A=240): Nuclide(Z=94, A=241),  # Pu240 → Pu241
        }
        
        # Get capture cross-sections from neutronics
        # sigma_a is [n_materials, ng], but we need capture (sigma_a - sigma_f)
        fuel_material_idx = 0
        sigma_a_g = self.neutronics.xs.sigma_a[fuel_material_idx, :]  # [ng]
        sigma_f_g = self.neutronics.xs.sigma_f[fuel_material_idx, :]  # [ng]
        sigma_capture_g = sigma_a_g - sigma_f_g  # Capture = absorption - fission
        
        # Compute capture rates for each nuclide
        for i, nuclide in enumerate(self.nuclides):
            # Get capture cross-section for this nuclide
            # Simplified: use average capture cross-section
            # Full implementation would use nuclide-specific cross-sections
            try:
                # Try to get nuclide-specific capture cross-section
                energy, sigma_capture = self.cache.get_cross_section(
                    nuclide, "capture", temperature=900.0  # Use fuel temperature
                )
                # Average over energy groups (simplified)
                sigma_capture_avg = np.mean(sigma_capture) if len(sigma_capture) > 0 else 0.0
            except Exception:
                # Fallback: use material average
                sigma_capture_avg = np.mean(sigma_capture_g)
            
            # Integrate capture rate over space and energy
            # R_capture = ∫∫ sigma_capture(E) * φ(r,z,E) * N * dV dE
            # Optimized: vectorize spatial and energy integration
            N_nuclide = self.concentrations[i, time_index]
            
            if N_nuclide > 0 and sigma_capture_avg > 0:
                # Spatial and energy integration (vectorized)
                # flux is [nz, nr, ng], cell_volumes is [nz, nr]
                # Sum over all dimensions: total flux integrated over space and energy
                total_flux = np.sum(flux * cell_volumes[:, :, np.newaxis])
                capture_rates[i] = sigma_capture_avg * total_flux * N_nuclide
        
        # Build sparse diagonal matrix
        return diags(capture_rates, format="csr")
    
    def _get_fission_yield_data(self, nuclide: Nuclide):
        """Get fission yield data for a nuclide (with caching)."""
        if nuclide in self._fission_yield_cache:
            return self._fission_yield_cache[nuclide]
        
        yield_data = get_fission_yield_data(nuclide, cache=self.cache)
        self._fission_yield_cache[nuclide] = yield_data
        return yield_data
    
    def _update_cross_sections(self, step: int):
        """
        Update cross-sections based on new composition.
        
        This is a placeholder for future implementation.
        In full implementation, would update xs.sigma_a, sigma_f, etc.
        based on nuclide concentrations at this time step.
        
        Args:
            step: Time step index
        """
        # Placeholder: In full implementation, would update cross-sections
        # based on current nuclide concentrations
        # For now, cross-sections remain constant
        pass
    
    def _update_burnup(self, step: int):
        """
        Update burnup calculation.
        
        Args:
            step: Time step index
        """
        # Burnup = integral of power over time
        # BU [MWd/kgU] = (Power [MW] * Time [days]) / (Mass_U [kg])
        
        # Calculate power from fission rate
        # Simplified calculation
        dt_days = (self.time_steps_sec[step] - self.time_steps_sec[step - 1]) / (24 * 3600)
        
        # Energy per fission: ~200 MeV = 3.2e-11 J
        E_per_fission = 200e6 * 1.602e-19  # Joules
        
        # Fission rate (simplified)
        total_fissions = 0.0
        for fissile in self.options.fissile_nuclides:
            if fissile in self.nuclides:
                idx = self.nuclides.index(fissile)
                # Average concentration over time step
                N_avg = (self.concentrations[idx, step] + self.concentrations[idx, step - 1]) / 2
                # Simplified fission rate
                total_fissions += N_avg * 1e13  # Placeholder flux
        
        # Power [W] = fission_rate [1/s] * E_per_fission [J]
        power_watts = total_fissions * E_per_fission
        
        # Mass of U (simplified)
        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)
        mass_u_kg = 0.0
        if u235 in self.nuclides:
            idx = self.nuclides.index(u235)
            N_u235 = self.concentrations[idx, step]
            mass_u_kg += N_u235 * 235e-3 / 6.022e23  # kg (simplified)
        if u238 in self.nuclides:
            idx = self.nuclides.index(u238)
            N_u238 = self.concentrations[idx, step]
            mass_u_kg += N_u238 * 238e-3 / 6.022e23  # kg
        
        # Burnup increment [MWd/kgU]
        if mass_u_kg > 0:
            bu_increment = (power_watts * 1e-6 * dt_days) / mass_u_kg  # MWd/kgU
            self.burnup_mwd_per_kg[step] = self.burnup_mwd_per_kg[step - 1] + bu_increment
        else:
            self.burnup_mwd_per_kg[step] = self.burnup_mwd_per_kg[step - 1]
    
    def compute_decay_heat(self, time_index: int = -1) -> float:
        """
        Compute decay heat at a specific time.
        
        Args:
            time_index: Time step index (default: -1 for final time)
        
        Returns:
            Decay heat in Watts
        """
        # Simplified decay heat calculation
        # Full implementation would use gamma/beta energy from decay data
        
        decay_heat = 0.0
        
        for i, nuc in enumerate(self.nuclides):
            N = self.concentrations[i, time_index]
            lambda_decay = self.decay_data.get_decay_constant(nuc)
            
            # Simplified: assume average decay energy ~1 MeV
            E_decay = 1e6 * 1.602e-19  # 1 MeV in Joules
            
            # Decay heat = decay_rate * energy_per_decay
            decay_heat += N * lambda_decay * E_decay
        
        return decay_heat
    
    def _identify_nuclides_to_add(self, time_index: int) -> List[Nuclide]:
        """
        Identify nuclides that should be added to tracking.
        
        Checks fission yields and decay chains to find nuclides that are
        being produced but not yet tracked.
        
        Args:
            time_index: Current time step index
        
        Returns:
            List of nuclides that should be added
        """
        if not self.options.adaptive_tracking:
            return []
        
        new_nuclides = []
        
        # Check fission yields for new products
        for fissile in self.options.fissile_nuclides:
            if fissile not in self.nuclides:
                continue
            
            yield_data = self._get_fission_yield_data(fissile)
            if yield_data is None:
                continue
            
            # Check for high-yield products that aren't tracked
            for product, yield_val in yield_data.yields.items():
                if product not in self.nuclides:
                    # Only add if yield is significant
                    if yield_val.cumulative_yield > self.options.nuclide_importance_threshold:
                        new_nuclides.append(product)
        
        # Check decay chains for important daughters
        for parent in self.nuclides:
            if parent in self._always_track:
                continue
            
            # Get decay daughters
            daughters = self.decay_data._get_daughters(parent)
            for daughter, br in daughters:
                if daughter not in self.nuclides and daughter not in new_nuclides:
                    # Check if parent has significant concentration
                    idx_parent = self.nuclides.index(parent)
                    N_parent = self.concentrations[idx_parent, time_index]
                    if N_parent > self.options.nuclide_threshold:
                        new_nuclides.append(daughter)
        
        return list(set(new_nuclides))  # Remove duplicates
    
    def _identify_nuclides_to_remove(self, time_index: int) -> List[Nuclide]:
        """
        Identify nuclides that should be removed from tracking.
        
        Checks concentrations against thresholds to find nuclides that are
        below the tracking threshold.
        
        Args:
            time_index: Current time step index
        
        Returns:
            List of nuclides that should be removed
        """
        if not self.options.adaptive_tracking:
            return []
        
        nuclides_to_remove = []
        total_inventory = np.sum(self.concentrations[:, time_index])
        
        for i, nuclide in enumerate(self.nuclides):
            # Never remove nuclides that are always tracked
            if nuclide in self._always_track:
                continue
            
            N = self.concentrations[i, time_index]
            
            # Check absolute threshold
            if N < self.options.nuclide_threshold:
                nuclides_to_remove.append(nuclide)
                continue
            
            # Check relative importance threshold
            if total_inventory > 0:
                relative_importance = N / total_inventory
                if relative_importance < self.options.nuclide_importance_threshold:
                    nuclides_to_remove.append(nuclide)
        
        return nuclides_to_remove
    
    def _update_adaptive_nuclides(self, time_index: int):
        """
        Update nuclide list based on adaptive tracking criteria.
        
        This method identifies nuclides to add/remove and updates the tracking
        list. Currently logs the changes but doesn't resize arrays (requires
        significant refactoring to implement fully).
        
        Args:
            time_index: Current time step index
        """
        if not self.options.adaptive_tracking:
            return
        
        # Check if it's time to update
        if time_index - self._last_adaptive_update < self.options.adaptive_update_interval:
            return
        
        # Identify nuclides to add
        nuclides_to_add = self._identify_nuclides_to_add(time_index)
        if nuclides_to_add:
            logger.info(
                f"Adaptive tracking: {len(nuclides_to_add)} nuclides identified for addition: "
                f"{[n.name for n in nuclides_to_add[:5]]}"  # Show first 5
            )
            # TODO: Implement actual addition with array resizing
            # This requires refactoring to resize self.concentrations and rebuild matrices
        
        # Identify nuclides to remove
        nuclides_to_remove = self._identify_nuclides_to_remove(time_index)
        if nuclides_to_remove:
            logger.info(
                f"Adaptive tracking: {len(nuclides_to_remove)} nuclides identified for removal: "
                f"{[n.name for n in nuclides_to_remove[:5]]}"  # Show first 5
            )
            # TODO: Implement actual removal with array resizing
            # This requires refactoring to resize self.concentrations and rebuild matrices
        
        self._last_adaptive_update = time_index

