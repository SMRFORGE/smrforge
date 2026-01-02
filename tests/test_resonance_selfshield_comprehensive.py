"""
Comprehensive tests for resonance_selfshield.py to improve coverage to 80%+.

Tests cover:
- BondarenkoMethod (f-factors, shielding, background XS)
- SubgroupMethod (effective XS, tabulation)
- EquivalenceTheory (Dancoff factors, escape probabilities)
- ResonanceSelfShielding (multi-group shielding, HTGR fuel)
"""

import numpy as np
import pytest

from smrforge.core.resonance_selfshield import (
    BondarenkoMethod,
    SubgroupMethod,
    EquivalenceTheory,
    ResonanceSelfShielding,
    ResonanceData,
)


class TestBondarenkoMethodComprehensive:
    """Comprehensive tests for BondarenkoMethod."""
    
    def test_get_f_factor(self):
        """Test getting f-factor."""
        method = BondarenkoMethod()
        
        # Test with known nuclide
        f = method.get_f_factor("U238", "capture", sigma_0=100.0, T=1200.0)
        assert 0 < f <= 1.0
        
        # Test with unknown nuclide (should return 1.0)
        f = method.get_f_factor("Unknown", "capture", sigma_0=100.0, T=1200.0)
        assert f == 1.0
    
    def test_get_f_factor_extreme_values(self):
        """Test f-factor with extreme sigma_0 and T values."""
        method = BondarenkoMethod()
        
        # Very small sigma_0
        f = method.get_f_factor("U238", "capture", sigma_0=0.1, T=1200.0)
        assert 0 < f <= 1.0
        
        # Very large sigma_0
        f = method.get_f_factor("U238", "capture", sigma_0=1e10, T=1200.0)
        assert 0 < f <= 1.0
        
        # Low temperature
        f = method.get_f_factor("U238", "capture", sigma_0=100.0, T=300.0)
        assert 0 < f <= 1.0
        
        # High temperature
        f = method.get_f_factor("U238", "capture", sigma_0=100.0, T=2100.0)
        assert 0 < f <= 1.0
    
    def test_shield_cross_section(self):
        """Test shielding cross-section."""
        method = BondarenkoMethod()
        
        xs_inf = 100.0  # barns
        xs_shielded = method.shield_cross_section(
            xs_inf, "U238", "capture", sigma_0=100.0, T=1200.0
        )
        
        assert xs_shielded > 0
        assert xs_shielded <= xs_inf  # Shielding reduces XS
    
    def test_compute_background_xs(self):
        """Test computing background cross-section."""
        method = BondarenkoMethod()
        
        composition = {
            "U235": 0.001,
            "U238": 0.002,
            "C": 0.08,  # Graphite
        }
        
        sigma_0 = method.compute_background_xs(composition)
        
        assert sigma_0 > 0
    
    def test_compute_background_xs_with_geometry(self):
        """Test background XS with geometry factor."""
        method = BondarenkoMethod()
        
        composition = {"U235": 0.001, "U238": 0.002}
        
        sigma_0 = method.compute_background_xs(
            composition, geometry_factor=0.5, include_moderator=False
        )
        
        assert sigma_0 > 0
    
    def test_get_potential_xs(self):
        """Test getting potential scattering cross-section."""
        # Test known nuclides
        assert BondarenkoMethod._get_potential_xs("U235") == 10.0
        assert BondarenkoMethod._get_potential_xs("U238") == 9.0
        assert BondarenkoMethod._get_potential_xs("C") == 4.8
        
        # Test unknown nuclide (should return default)
        assert BondarenkoMethod._get_potential_xs("Unknown") == 5.0


class TestSubgroupMethodComprehensive:
    """Comprehensive tests for SubgroupMethod."""
    
    def test_compute_effective_xs(self):
        """Test computing effective cross-section."""
        method = SubgroupMethod()
        
        # Test with known data
        xs_eff = method.compute_effective_xs(
            "U238", "capture", "thermal", sigma_0=100.0
        )
        
        assert xs_eff > 0
    
    def test_compute_effective_xs_unknown(self):
        """Test effective XS with unknown nuclide/reaction."""
        method = SubgroupMethod()
        
        # Should return sigma_0 if no subgroup data
        sigma_0 = 50.0
        xs_eff = method.compute_effective_xs(
            "Unknown", "capture", "thermal", sigma_0=sigma_0
        )
        
        assert xs_eff == sigma_0
    
    def test_tabulate_effective_xs(self):
        """Test tabulating effective XS vs sigma_0."""
        method = SubgroupMethod()
        
        sigma_0_range = np.array([1, 10, 100, 1000, 10000])
        xs_eff_table = method.tabulate_effective_xs(
            "U238", "capture", "thermal", sigma_0_range
        )
        
        assert len(xs_eff_table) == len(sigma_0_range)
        assert np.all(xs_eff_table > 0)


class TestEquivalenceTheoryComprehensive:
    """Comprehensive tests for EquivalenceTheory."""
    
    def test_dancoff_factor_hexagonal(self):
        """Test Dancoff factor calculation."""
        pitch = 1.0  # cm
        particle_radius = 0.05  # cm
        packing_fraction = 0.35
        
        C = EquivalenceTheory.dancoff_factor_hexagonal(
            pitch, particle_radius, packing_fraction
        )
        
        assert 0 <= C <= 1.0
    
    def test_dancoff_factor_extreme_values(self):
        """Test Dancoff factor with extreme values."""
        # Very small packing fraction
        C = EquivalenceTheory.dancoff_factor_hexagonal(1.0, 0.05, 0.01)
        assert 0 <= C <= 1.0
        
        # Very large packing fraction
        C = EquivalenceTheory.dancoff_factor_hexagonal(1.0, 0.05, 0.9)
        assert 0 <= C <= 1.0
    
    def test_escape_probability_sphere(self):
        """Test escape probability from sphere."""
        sigma_t = 1.0  # 1/cm
        radius = 0.1  # cm
        
        P_esc = EquivalenceTheory.escape_probability_sphere(sigma_t, radius)
        
        assert 0 < P_esc <= 1.0
    
    def test_escape_probability_extreme_values(self):
        """Test escape probability with extreme values."""
        # Small optical thickness
        P_esc = EquivalenceTheory.escape_probability_sphere(0.01, 0.1)
        assert 0 < P_esc <= 1.0
        
        # Large optical thickness
        P_esc = EquivalenceTheory.escape_probability_sphere(100.0, 0.1)
        assert 0 < P_esc <= 1.0
    
    def test_effective_background_xs(self):
        """Test effective background XS calculation."""
        dancoff = 0.3
        escape_prob = 0.7
        sigma_moderator = 0.385  # 1/cm
        N_fuel_to_mod = 0.1
        
        sigma_0_eff = EquivalenceTheory.effective_background_xs(
            dancoff, escape_prob, sigma_moderator, N_fuel_to_mod
        )
        
        assert sigma_0_eff > 0
    
    def test_compute_triso_shielding(self):
        """Test complete TRISO shielding calculation."""
        theory = EquivalenceTheory()
        
        result = theory.compute_triso_shielding(
            kernel_radius=212.5e-4,  # cm
            buffer_thickness=100e-4,  # cm
            packing_fraction=0.35,
            N_graphite=0.08,  # atoms/b-cm
        )
        
        assert "sigma_0_kernel" in result
        assert "dancoff_factor" in result
        assert "escape_probability" in result
        assert result["sigma_0_kernel"] > 0
        assert 0 <= result["dancoff_factor"] <= 1.0
        assert 0 < result["escape_probability"] <= 1.0


class TestResonanceSelfShieldingComprehensive:
    """Comprehensive tests for ResonanceSelfShielding."""
    
    def test_shield_multigroup_xs_bondarenko(self):
        """Test multi-group shielding with Bondarenko method."""
        shielding = ResonanceSelfShielding()
        
        n_groups = 3
        n_temps = 2
        xs_inf = np.ones((n_groups, n_temps)) * 100.0  # barns
        temperatures = np.array([600.0, 1200.0])
        sigma_0 = 100.0
        
        xs_shielded = shielding.shield_multigroup_xs(
            xs_inf, "U238", "capture", temperatures, sigma_0, method="bondarenko"
        )
        
        assert xs_shielded.shape == (n_groups, n_temps)
        assert np.all(xs_shielded > 0)
        assert np.all(xs_shielded <= xs_inf)  # Shielding reduces XS
    
    def test_shield_multigroup_xs_subgroup(self):
        """Test multi-group shielding with subgroup method."""
        shielding = ResonanceSelfShielding()
        
        n_groups = 3
        n_temps = 2
        xs_inf = np.ones((n_groups, n_temps)) * 100.0
        temperatures = np.array([600.0, 1200.0])
        sigma_0 = 100.0
        
        xs_shielded = shielding.shield_multigroup_xs(
            xs_inf, "U238", "capture", temperatures, sigma_0, method="subgroup"
        )
        
        assert xs_shielded.shape == (n_groups, n_temps)
        assert np.all(xs_shielded > 0)
    
    def test_shield_multigroup_xs_invalid_method(self):
        """Test shielding with invalid method."""
        shielding = ResonanceSelfShielding()
        
        xs_inf = np.ones((2, 1)) * 100.0
        temperatures = np.array([1200.0])
        sigma_0 = 100.0
        
        with pytest.raises(ValueError):
            shielding.shield_multigroup_xs(
                xs_inf, "U238", "capture", temperatures, sigma_0, method="invalid"
            )
    
    def test_htgr_fuel_shielding(self):
        """Test complete HTGR fuel shielding."""
        shielding = ResonanceSelfShielding()
        
        fuel_composition = {
            "U235": 0.0005,  # atoms/b-cm
            "U238": 0.0020,
            "O16": 0.0050,
        }
        
        triso_geometry = {
            "kernel_radius": 212.5e-4,  # cm
            "buffer_thickness": 100e-4,  # cm
            "packing_fraction": 0.35,
        }
        
        temperature = 1200.0  # K
        
        result = shielding.htgr_fuel_shielding(
            fuel_composition, triso_geometry, temperature
        )
        
        assert isinstance(result, dict)
        for nuclide, xs_dict in result.items():
            assert "capture" in xs_dict
            assert "fission" in xs_dict
            assert xs_dict["capture"] > 0
    
    def test_htgr_fuel_shielding_fissile(self):
        """Test HTGR fuel shielding with fissile nuclide."""
        shielding = ResonanceSelfShielding()
        
        fuel_composition = {
            "U235": 0.0005,  # Fissile
            "U238": 0.0020,
        }
        
        triso_geometry = {
            "kernel_radius": 212.5e-4,
            "buffer_thickness": 100e-4,
            "packing_fraction": 0.35,
        }
        
        result = shielding.htgr_fuel_shielding(
            fuel_composition, triso_geometry, 1200.0
        )
        
        # U235 should have fission XS
        if "U235" in result:
            assert result["U235"]["fission"] > 0


class TestResonanceData:
    """Tests for ResonanceData dataclass."""
    
    def test_resonance_data_creation(self):
        """Test creating ResonanceData."""
        energy = np.array([1.0, 10.0, 100.0])  # eV
        gamma_n = np.array([0.1, 0.2, 0.3])  # eV
        gamma_gamma = np.array([0.05, 0.1, 0.15])  # eV
        gamma_f = np.array([0.0, 0.0, 0.0])  # eV
        l = np.array([0, 0, 0])
        J = np.array([0.5, 0.5, 0.5])
        statistical_weight = np.array([1.0, 1.0, 1.0])
        
        data = ResonanceData(
            nuclide="U238",
            energy=energy,
            gamma_n=gamma_n,
            gamma_gamma=gamma_gamma,
            gamma_f=gamma_f,
            l=l,
            J=J,
            statistical_weight=statistical_weight,
        )
        
        assert data.nuclide == "U238"
        assert len(data.energy) == 3
        assert len(data.gamma_n) == 3

