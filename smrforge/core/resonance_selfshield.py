# nucdata/resonance.py
"""
Fast resonance self-shielding calculations for HTGR applications.
Implements Bondarenko method and subgroup methods with modern algorithms.
"""

import numpy as np
from numba import njit, prange
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
import polars as pl
from scipy.interpolate import interp1d, RectBivariateSpline
from functools import lru_cache


@dataclass
class ResonanceData:
    """Resonance parameters for a nuclide."""
    nuclide: str
    energy: np.ndarray  # Resonance energies [eV]
    gamma_n: np.ndarray  # Neutron width [eV]
    gamma_gamma: np.ndarray  # Gamma width [eV]
    gamma_f: np.ndarray  # Fission width [eV] (if fissile)
    l: np.ndarray  # Angular momentum quantum number
    J: np.ndarray  # Total angular momentum
    statistical_weight: np.ndarray  # (2J+1) / (2I+1)(2i+1)


class BondarenkoMethod:
    """
    Fast Bondarenko self-shielding method.
    Uses pre-tabulated f-factors (shielding factors).
    
    Much faster than resolved resonance integral calculations.
    """
    
    def __init__(self):
        self.f_factors: Dict[str, RectBivariateSpline] = {}
        self._load_f_factors()
    
    def _load_f_factors(self):
        """
        Load pre-tabulated Bondarenko f-factors.
        In production, these would come from processed libraries.
        """
        # Example: U-238 capture f-factors
        # sigma_0 values (background XS) [barns]
        sigma_0_grid = np.array([1, 10, 100, 1000, 10000, 1e5, 1e6, 1e10])
        
        # Temperature grid [K]
        T_grid = np.array([300, 600, 900, 1200, 1500, 1800, 2100])
        
        # f-factor table: f(sigma_0, T)
        # These are illustrative values - real data from ENDF processing
        f_table_u238_capture = np.array([
            # sigma_0 = 1, 10, 100, ...
            [0.95, 0.92, 0.88, 0.84, 0.81, 0.78, 0.76],  # T=300K
            [0.93, 0.89, 0.85, 0.80, 0.76, 0.73, 0.70],  # T=600K
            [0.91, 0.87, 0.82, 0.76, 0.72, 0.68, 0.65],  # T=900K
            [0.89, 0.84, 0.78, 0.72, 0.67, 0.63, 0.60],  # T=1200K
            [0.87, 0.81, 0.75, 0.68, 0.63, 0.58, 0.55],  # T=1500K
            [0.85, 0.79, 0.72, 0.65, 0.59, 0.54, 0.51],  # T=1800K
            [0.83, 0.76, 0.69, 0.62, 0.56, 0.51, 0.48],  # T=2100K
        ])
        
        # Create interpolator (fast 2D spline)
        self.f_factors['U238_capture'] = RectBivariateSpline(
            np.log10(sigma_0_grid), T_grid, f_table_u238_capture.T,
            kx=3, ky=3  # Cubic splines
        )
        
        # Add more nuclides (U-235, Pu-239, etc.)
        # Similar tables for other reactions
        self._add_u235_factors()
        self._add_pu239_factors()
    
    def _add_u235_factors(self):
        """Add U-235 f-factors."""
        sigma_0_grid = np.array([1, 10, 100, 1000, 10000, 1e5, 1e6, 1e10])
        T_grid = np.array([300, 600, 900, 1200, 1500, 1800, 2100])
        
        # U-235 has less self-shielding than U-238
        f_table_u235_fission = np.array([
            [0.98, 0.97, 0.96, 0.95, 0.94, 0.93, 0.92],
            [0.96, 0.95, 0.93, 0.91, 0.89, 0.87, 0.86],
            [0.94, 0.92, 0.90, 0.87, 0.85, 0.82, 0.80],
            [0.92, 0.89, 0.86, 0.83, 0.80, 0.77, 0.75],
            [0.90, 0.87, 0.83, 0.79, 0.76, 0.72, 0.70],
            [0.88, 0.84, 0.80, 0.76, 0.72, 0.68, 0.65],
            [0.86, 0.82, 0.77, 0.72, 0.68, 0.64, 0.61],
        ])
        
        self.f_factors['U235_fission'] = RectBivariateSpline(
            np.log10(sigma_0_grid), T_grid, f_table_u235_fission.T,
            kx=3, ky=3
        )
    
    def _add_pu239_factors(self):
        """Add Pu-239 f-factors."""
        sigma_0_grid = np.array([1, 10, 100, 1000, 10000, 1e5, 1e6, 1e10])
        T_grid = np.array([300, 600, 900, 1200, 1500, 1800, 2100])
        
        f_table_pu239_fission = np.array([
            [0.97, 0.96, 0.95, 0.94, 0.93, 0.92, 0.91],
            [0.95, 0.93, 0.91, 0.89, 0.87, 0.85, 0.84],
            [0.93, 0.90, 0.87, 0.84, 0.81, 0.79, 0.77],
            [0.91, 0.87, 0.83, 0.79, 0.76, 0.73, 0.71],
            [0.89, 0.84, 0.80, 0.75, 0.71, 0.68, 0.65],
            [0.87, 0.82, 0.76, 0.71, 0.67, 0.63, 0.60],
            [0.85, 0.79, 0.73, 0.68, 0.63, 0.59, 0.56],
        ])
        
        self.f_factors['Pu239_fission'] = RectBivariateSpline(
            np.log10(sigma_0_grid), T_grid, f_table_pu239_fission.T,
            kx=3, ky=3
        )
    
    @lru_cache(maxsize=1024)
    def get_f_factor(self, nuclide: str, reaction: str, 
                     sigma_0: float, T: float) -> float:
        """
        Get shielding f-factor for nuclide/reaction at sigma_0 and T.
        
        Args:
            nuclide: Nuclide name (e.g., 'U238')
            reaction: Reaction type (e.g., 'capture', 'fission')
            sigma_0: Background cross section [barns]
            T: Temperature [K]
        
        Returns:
            f-factor (dimensionless, 0-1)
        """
        key = f"{nuclide}_{reaction}"
        
        if key not in self.f_factors:
            # No self-shielding data, assume no shielding
            return 1.0
        
        # Interpolate (use log of sigma_0 for better interpolation)
        log_sigma_0 = np.log10(max(sigma_0, 1.0))
        T_clamped = np.clip(T, 300, 2100)
        
        f = self.f_factors[key](log_sigma_0, T_clamped, grid=False)
        return float(f)
    
    def shield_cross_section(self, xs_inf: float, nuclide: str, 
                             reaction: str, sigma_0: float, T: float) -> float:
        """
        Apply self-shielding to infinite dilution cross section.
        
        xs_shielded = f * xs_inf
        """
        f = self.get_f_factor(nuclide, reaction, sigma_0, T)
        return f * xs_inf
    
    def compute_background_xs(self, composition: Dict[str, float],
                             geometry_factor: float = 1.0,
                             include_moderator: bool = True) -> float:
        """
        Compute background cross section sigma_0.
        
        sigma_0 = (Sum_i N_i * sigma_i + geometry term) / N_resonant
        
        Args:
            composition: Dict of {nuclide: number_density [1/barn-cm]}
            geometry_factor: Dancoff factor or escape probability
            include_moderator: Whether to include moderator in background
        
        Returns:
            Background XS [barns]
        """
        # Simplified - real version would be more sophisticated
        total_xs = 0.0
        for nuc, N in composition.items():
            # Get potential scattering XS (approximate)
            sigma_pot = self._get_potential_xs(nuc)
            total_xs += N * sigma_pot
        
        # Add geometry contribution
        if geometry_factor > 0:
            total_xs += geometry_factor * 1e-3  # Typical escape term
        
        return total_xs
    
    @staticmethod
    def _get_potential_xs(nuclide: str) -> float:
        """Get potential scattering cross section [barns]."""
        # Simplified lookup - would come from nuclear data
        potential_xs = {
            'U235': 10.0,
            'U238': 9.0,
            'Pu239': 11.0,
            'C': 4.8,  # Graphite
            'O': 3.8,
            'He': 1.0,
        }
        return potential_xs.get(nuclide, 5.0)  # Default 5 barns


@njit(cache=True)
def _compute_subgroup_flux(sigma_sg: np.ndarray, w_sg: np.ndarray,
                           sigma_t_background: float, 
                           source: float) -> np.ndarray:
    """
    Compute subgroup fluxes using rational approximation.
    Ultra-fast with Numba.
    
    phi_sg = w_sg * S / (sigma_t_bg + sigma_sg)
    """
    n_sg = len(sigma_sg)
    phi_sg = np.zeros(n_sg)
    
    for i in range(n_sg):
        phi_sg[i] = w_sg[i] * source / (sigma_t_background + sigma_sg[i])
    
    return phi_sg


class SubgroupMethod:
    """
    Subgroup method for resonance self-shielding.
    More accurate than Bondarenko, still fast enough for SMR design.
    
    Divides energy groups into subgroups with representative XS.
    """
    
    def __init__(self, n_subgroups: int = 8):
        self.n_subgroups = n_subgroups
        self.subgroup_data: Dict[str, Dict] = {}
        self._generate_subgroup_parameters()
    
    def _generate_subgroup_parameters(self):
        """
        Generate subgroup parameters (weights and XS).
        These would come from processing ENDF data.
        """
        # Example: U-238 capture in thermal group
        # Subgroup XS [barns]
        sigma_sg = np.array([2.0, 5.0, 15.0, 50.0, 150.0, 500.0, 1500.0, 5000.0])
        # Subgroup weights (sum to 1)
        w_sg = np.array([0.50, 0.25, 0.12, 0.06, 0.04, 0.02, 0.007, 0.003])
        
        self.subgroup_data['U238_capture_thermal'] = {
            'sigma': sigma_sg,
            'weights': w_sg
        }
        
        # Add more energy groups and nuclides
        self._add_fast_subgroups()
    
    def _add_fast_subgroups(self):
        """Add fast spectrum subgroups."""
        # U-238 fission in fast group
        sigma_sg = np.array([0.3, 0.5, 0.8, 1.2, 2.0, 3.5, 6.0, 10.0])
        w_sg = np.array([0.60, 0.20, 0.10, 0.05, 0.03, 0.012, 0.005, 0.003])
        
        self.subgroup_data['U238_fission_fast'] = {
            'sigma': sigma_sg,
            'weights': w_sg
        }
    
    def compute_effective_xs(self, nuclide: str, reaction: str, 
                            energy_group: str, sigma_0: float) -> float:
        """
        Compute effective (shielded) cross section using subgroups.
        
        sigma_eff = Sum_i w_i * sigma_i * phi_i / Sum_i w_i * phi_i
        """
        key = f"{nuclide}_{reaction}_{energy_group}"
        
        if key not in self.subgroup_data:
            # No subgroup data, return unshielded
            return sigma_0
        
        data = self.subgroup_data[key]
        sigma_sg = data['sigma']
        w_sg = data['weights']
        
        # Compute subgroup fluxes
        source = 1.0  # Normalized
        phi_sg = _compute_subgroup_flux(sigma_sg, w_sg, sigma_0, source)
        
        # Flux-weighted average
        sigma_eff = np.sum(w_sg * sigma_sg * phi_sg) / np.sum(w_sg * phi_sg)
        
        return sigma_eff
    
    def tabulate_effective_xs(self, nuclide: str, reaction: str,
                             energy_group: str, 
                             sigma_0_range: np.ndarray) -> np.ndarray:
        """Generate lookup table of effective XS vs sigma_0."""
        n = len(sigma_0_range)
        xs_eff = np.zeros(n)
        
        for i, sigma_0 in enumerate(sigma_0_range):
            xs_eff[i] = self.compute_effective_xs(
                nuclide, reaction, energy_group, sigma_0
            )
        
        return xs_eff


class EquivalenceTheory:
    """
    Equivalence theory for HTGR double heterogeneity.
    
    TRISO particles in fuel element → fuel elements in core
    Uses Dancoff factors and escape probabilities.
    """
    
    @staticmethod
    @njit(cache=True)
    def dancoff_factor_hexagonal(pitch: float, particle_radius: float,
                                 packing_fraction: float) -> float:
        """
        Dancoff factor for hexagonal lattice of particles.
        
        Args:
            pitch: Lattice pitch [cm]
            particle_radius: TRISO radius [cm]
            packing_fraction: Volume fraction of particles
        
        Returns:
            Dancoff factor (0-1)
        """
        # Simplified model - real version uses more complex geometry
        # Based on Sanchez-Pomraning method
        
        # Optical thickness
        mean_free_path = 2.0  # cm, typical for graphite
        tau = 2 * particle_radius / mean_free_path
        
        # Rational approximation for Dancoff factor
        C = packing_fraction * (1 - np.exp(-tau)) / (1 + 0.5 * tau)
        
        return min(C, 0.95)  # Physical limit
    
    @staticmethod
    @njit(cache=True)
    def escape_probability_sphere(sigma_t: float, radius: float) -> float:
        """
        Escape probability from sphere (Wigner rational approximation).
        
        P_esc = 1 / (1 + sigma_t * radius)
        """
        tau = sigma_t * radius
        
        if tau < 0.01:
            # Small optical thickness - use series expansion
            return 1.0 - 0.5 * tau
        elif tau > 10:
            # Large optical thickness - asymptotic
            return 1.0 / tau
        else:
            # Wigner approximation
            return 1.0 / (1.0 + tau)
    
    @staticmethod
    def effective_background_xs(dancoff: float, escape_prob: float,
                               sigma_moderator: float, 
                               N_fuel_to_mod: float) -> float:
        """
        Compute effective background XS for double heterogeneity.
        
        Accounts for both particle-level and lattice-level shielding.
        """
        # Equivalence in transport approximation
        sigma_0_eff = sigma_moderator * (1 - dancoff) / (
            dancoff + (1 - dancoff) * escape_prob * N_fuel_to_mod
        )
        
        return sigma_0_eff
    
    def compute_triso_shielding(self, kernel_radius: float, 
                               buffer_thickness: float,
                               packing_fraction: float,
                               N_graphite: float) -> Dict[str, float]:
        """
        Complete TRISO self-shielding calculation.
        
        Returns:
            Dict with 'sigma_0_kernel' and 'dancoff_factor'
        """
        # Total TRISO radius (simplified - use kernel + buffer)
        triso_radius = kernel_radius + buffer_thickness
        
        # Dancoff factor for TRISO lattice
        pitch = triso_radius / (packing_fraction ** (1/3))
        C = self.dancoff_factor_hexagonal(pitch, triso_radius, packing_fraction)
        
        # Escape probability from kernel
        sigma_t_buffer = 0.5  # 1/cm, typical for buffer
        P_esc = self.escape_probability_sphere(sigma_t_buffer, buffer_thickness)
        
        # Effective sigma_0 for kernel
        sigma_graphite = 0.385  # 1/cm at thermal
        N_ratio = 1.0 / packing_fraction  # Graphite to fuel volume
        
        sigma_0_kernel = self.effective_background_xs(
            C, P_esc, sigma_graphite, N_ratio
        )
        
        return {
            'sigma_0_kernel': sigma_0_kernel,
            'dancoff_factor': C,
            'escape_probability': P_esc
        }


class ResonanceSelfShielding:
    """
    Main interface for resonance self-shielding calculations.
    Combines Bondarenko, subgroup, and equivalence methods.
    """
    
    def __init__(self):
        self.bondarenko = BondarenkoMethod()
        self.subgroup = SubgroupMethod()
        self.equivalence = EquivalenceTheory()
    
    def shield_multigroup_xs(self, 
                            xs_inf: np.ndarray,
                            nuclide: str,
                            reaction: str,
                            temperatures: np.ndarray,
                            sigma_0: float,
                            method: str = 'bondarenko') -> np.ndarray:
        """
        Apply self-shielding to multi-group cross sections.
        
        Args:
            xs_inf: Infinite dilution XS array [n_groups, n_temps]
            nuclide: Nuclide name
            reaction: Reaction type
            temperatures: Temperature array [K]
            sigma_0: Background XS [barns]
            method: 'bondarenko' or 'subgroup'
        
        Returns:
            Shielded XS array [n_groups, n_temps]
        """
        n_groups, n_temps = xs_inf.shape
        xs_shielded = np.zeros_like(xs_inf)
        
        if method == 'bondarenko':
            for g in range(n_groups):
                for t in range(n_temps):
                    xs_shielded[g, t] = self.bondarenko.shield_cross_section(
                        xs_inf[g, t], nuclide, reaction, sigma_0, temperatures[t]
                    )
        
        elif method == 'subgroup':
            # Subgroup method (more accurate, slightly slower)
            for g in range(n_groups):
                group_name = f"group_{g}"
                for t in range(n_temps):
                    xs_shielded[g, t] = self.subgroup.compute_effective_xs(
                        nuclide, reaction, group_name, sigma_0
                    )
        
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return xs_shielded
    
    def htgr_fuel_shielding(self, fuel_composition: Dict[str, float],
                           triso_geometry: Dict[str, float],
                           temperature: float) -> Dict[str, np.ndarray]:
        """
        Complete HTGR fuel self-shielding including double heterogeneity.
        
        Args:
            fuel_composition: {nuclide: atom_density [1/b-cm]}
            triso_geometry: {'kernel_radius', 'buffer_thickness', 'packing_fraction'}
            temperature: Fuel temperature [K]
        
        Returns:
            Dict of shielded cross sections by nuclide
        """
        # Step 1: Compute equivalence theory parameters
        equiv_params = self.equivalence.compute_triso_shielding(
            kernel_radius=triso_geometry['kernel_radius'],
            buffer_thickness=triso_geometry['buffer_thickness'],
            packing_fraction=triso_geometry['packing_fraction'],
            N_graphite=0.08  # atoms/b-cm for graphite
        )
        
        sigma_0_eff = equiv_params['sigma_0_kernel']
        
        # Step 2: Apply Bondarenko self-shielding
        shielded_xs = {}
        
        for nuclide, N in fuel_composition.items():
            # Get infinite dilution XS (would come from nuclear data)
            xs_inf_capture = 100.0  # barns (placeholder)
            xs_inf_fission = 500.0 if 'U235' in nuclide else 0.0
            
            # Shield
            xs_capture = self.bondarenko.shield_cross_section(
                xs_inf_capture, nuclide, 'capture', sigma_0_eff, temperature
            )
            
            if xs_inf_fission > 0:
                xs_fission = self.bondarenko.shield_cross_section(
                    xs_inf_fission, nuclide, 'fission', sigma_0_eff, temperature
                )
            else:
                xs_fission = 0.0
            
            shielded_xs[nuclide] = {
                'capture': xs_capture,
                'fission': xs_fission
            }
        
        return shielded_xs


if __name__ == "__main__":
    # Demonstration
    print("=== Resonance Self-Shielding Demo ===\n")
    
    # Initialize
    shielding = ResonanceSelfShielding()
    
    # Test Bondarenko method
    print("1. Bondarenko Method:")
    sigma_0_values = np.array([1, 10, 100, 1000, 10000])
    T = 1200.0  # HTGR operating temperature
    
    for sigma_0 in sigma_0_values:
        f = shielding.bondarenko.get_f_factor('U238', 'capture', sigma_0, T)
        print(f"   sigma_0 = {sigma_0:>6.0f} b  →  f-factor = {f:.4f}")
    
    print()
    
    # Test equivalence theory for TRISO
    print("2. TRISO Double Heterogeneity:")
    triso_geom = {
        'kernel_radius': 212.5e-4,  # cm
        'buffer_thickness': 100e-4,  # cm
        'packing_fraction': 0.35
    }
    
    equiv_result = shielding.equivalence.compute_triso_shielding(
        **triso_geom, N_graphite=0.08
    )
    
    print(f"   Dancoff factor: {equiv_result['dancoff_factor']:.4f}")
    print(f"   Escape probability: {equiv_result['escape_probability']:.4f}")
    print(f"   Effective sigma_0: {equiv_result['sigma_0_kernel']:.2f} barns")
    
    print()
    
    # Test full HTGR fuel shielding
    print("3. Complete HTGR Fuel Shielding:")
    fuel_comp = {
        'U235': 0.0005,  # atoms/b-cm
        'U238': 0.0020,
        'O16': 0.0050
    }
    
    result = shielding.htgr_fuel_shielding(fuel_comp, triso_geom, T)
    
    for nuc, xs in result.items():
        print(f"   {nuc}:")
        print(f"      Capture: {xs['capture']:.2f} b")
        if xs['fission'] > 0:
            print(f"      Fission: {xs['fission']:.2f} b")
