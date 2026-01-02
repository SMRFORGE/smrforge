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
        n_nuclides = len(self.nuclides)
        n_times = len(self.time_steps_sec)
        self.concentrations = np.zeros((n_nuclides, n_times))
        
        # Initialize burnup tracking
        self.burnup_mwd_per_kg = np.zeros(n_times)
        
        # Fission yield data cache
        self._fission_yield_cache: Dict[Nuclide, Optional[Any]] = {}
        
        logger.info(
            f"Initialized burnup solver: {n_nuclides} nuclides, "
            f"{n_times} time steps, {options.time_steps[-1]:.0f} days total"
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
        
        # Set initial concentrations
        self._set_initial_concentrations()
    
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
            # (This is a simplified approach - full implementation would
            #  recalculate cross-sections based on new nuclide concentrations)
            # For now, we'll skip this and use constant cross-sections
            
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
        Build production vector from fission yields.
        
        Args:
            time_index: Time step index for flux calculation
        
        Returns:
            Production vector [n_nuclides]
        """
        P = np.zeros(len(self.nuclides))
        
        # Get flux (simplified - use average flux)
        # Full implementation would integrate over space
        if self.neutronics.flux is None:
            return P
        
        # Average flux over all groups and space
        avg_flux = np.mean(self.neutronics.flux)
        
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
            
            # Get fission cross-section (simplified - use average)
            # Full implementation would use group-dependent cross-sections
            sigma_f_avg = 1.0  # Placeholder - should come from neutronics
            
            # Fission rate: R_f = sigma_f * flux * N
            fission_rate = sigma_f_avg * avg_flux * N_fissile
            
            # Add production from yields
            for product, yield_val in yield_data.yields.items():
                if product in self.nuclides:
                    idx_product = self.nuclides.index(product)
                    # Production = yield * fission_rate
                    P[idx_product] += yield_val.cumulative_yield * fission_rate
        
        return P
    
    def _build_capture_matrix(self, time_index: int) -> csr_matrix:
        """
        Build capture/destruction matrix.
        
        Args:
            time_index: Time step index
        
        Returns:
            Sparse matrix D where capture destruction is D*N
        """
        from scipy.sparse import diags
        
        n = len(self.nuclides)
        
        # Simplified: capture rates (full implementation would use flux and cross-sections)
        # For now, return zero matrix (capture effects not included)
        capture_rates = np.zeros(n)
        
        return diags(capture_rates, format="csr")
    
    def _get_fission_yield_data(self, nuclide: Nuclide):
        """Get fission yield data for a nuclide (with caching)."""
        if nuclide in self._fission_yield_cache:
            return self._fission_yield_cache[nuclide]
        
        yield_data = get_fission_yield_data(nuclide, cache=self.cache)
        self._fission_yield_cache[nuclide] = yield_data
        return yield_data
    
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

