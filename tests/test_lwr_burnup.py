"""
Tests for smrforge.burnup.lwr_burnup module.
"""

import numpy as np
import pytest
from unittest.mock import Mock, MagicMock, patch

from smrforge.burnup.lwr_burnup import (
    GadoliniumPoison,
    AssemblyBurnup,
    RodBurnup,
    GadoliniumDepletion,
)
from smrforge.core.reactor_core import Nuclide, NuclearDataCache


class TestGadoliniumPoison:
    """Tests for GadoliniumPoison dataclass."""
    
    def test_gadolinium_poison_init(self):
        """Test GadoliniumPoison initialization."""
        nuclides = [
            Nuclide(Z=64, A=155),
            Nuclide(Z=64, A=157),
        ]
        initial_concentrations = np.array([1e20, 5e19])
        
        poison = GadoliniumPoison(
            nuclides=nuclides,
            initial_concentrations=initial_concentrations,
        )
        
        assert poison.nuclides == nuclides
        assert np.allclose(poison.initial_concentrations, initial_concentrations)
        assert poison.depletion_rates is None
    
    def test_gadolinium_poison_with_depletion_rates(self):
        """Test GadoliniumPoison with depletion rates."""
        nuclides = [Nuclide(Z=64, A=155)]
        initial_concentrations = np.array([1e20])
        depletion_rates = np.array([1e-5])
        
        poison = GadoliniumPoison(
            nuclides=nuclides,
            initial_concentrations=initial_concentrations,
            depletion_rates=depletion_rates,
        )
        
        assert np.allclose(poison.depletion_rates, depletion_rates)


class TestAssemblyBurnup:
    """Tests for AssemblyBurnup dataclass."""
    
    def test_assembly_burnup_init(self):
        """Test AssemblyBurnup initialization."""
        inventory = Mock()
        
        assembly = AssemblyBurnup(
            assembly_id="A1",
            position=(0, 0),
            burnup=10.5,
            average_enrichment=0.195,
            peak_power=150.0,
            nuclide_inventory=inventory,
        )
        
        assert assembly.assembly_id == "A1"
        assert assembly.position == (0, 0)
        assert assembly.burnup == 10.5
        assert assembly.average_enrichment == 0.195
        assert assembly.peak_power == 150.0
        assert assembly.nuclide_inventory == inventory
    
    def test_assembly_burnup_no_inventory(self):
        """Test AssemblyBurnup without inventory."""
        assembly = AssemblyBurnup(
            assembly_id="A2",
            position=(1, 0),
            burnup=20.0,
            average_enrichment=0.20,
            peak_power=200.0,
        )
        
        assert assembly.nuclide_inventory is None


class TestRodBurnup:
    """Tests for RodBurnup dataclass."""
    
    def test_rod_burnup_init(self):
        """Test RodBurnup initialization."""
        rod = RodBurnup(
            rod_id="R1",
            position=(5, 5),
            burnup=15.5,
            enrichment=0.19,  # Required parameter
        )
        
        assert rod.rod_id == "R1"
        assert rod.position == (5, 5)
        assert rod.burnup == 15.5
        assert rod.enrichment == 0.19
    
    def test_rod_burnup_with_all_params(self):
        """Test RodBurnup with all parameters."""
        rod = RodBurnup(
            rod_id="R2",
            position=(3, 4),
            burnup=12.0,
            enrichment=0.19,
            gadolinium_content=1e19,
            control_rod_proximity=5.0,
            shadowing_factor=0.8,
        )
        
        assert rod.rod_id == "R2"
        assert rod.position == (3, 4)
        assert rod.burnup == 12.0
        assert rod.enrichment == 0.19
        assert rod.gadolinium_content == 1e19
        assert rod.control_rod_proximity == 5.0
        assert rod.shadowing_factor == 0.8


class TestGadoliniumDepletion:
    """Tests for GadoliniumDepletion class."""
    
    def test_gadolinium_depletion_init_default(self):
        """Test GadoliniumDepletion initialization with default cache."""
        gd = GadoliniumDepletion()
        
        assert isinstance(gd.cache, NuclearDataCache)
        assert gd.gd155 == Nuclide(Z=64, A=155)
        assert gd.gd157 == Nuclide(Z=64, A=157)
    
    def test_gadolinium_depletion_init_with_cache(self):
        """Test GadoliniumDepletion initialization with provided cache."""
        cache = NuclearDataCache()
        gd = GadoliniumDepletion(cache=cache)
        
        assert gd.cache == cache
    
    @patch('smrforge.burnup.lwr_burnup.NuclearDataCache')
    def test_get_capture_cross_section_gd155(self, mock_cache_class):
        """Test get_capture_cross_section for Gd-155."""
        mock_cache = Mock()
        mock_cache.get_cross_section.return_value = (
            np.array([0.01, 0.025, 0.1]),
            np.array([50000, 61000, 55000])
        )
        gd = GadoliniumDepletion(cache=mock_cache)
        
        gd155 = Nuclide(Z=64, A=155)
        xs = gd.get_capture_cross_section(gd155, temperature=600.0)
        
        assert xs > 0
        assert isinstance(xs, (float, np.floating, int, np.integer))
    
    @patch('smrforge.burnup.lwr_burnup.NuclearDataCache')
    def test_get_capture_cross_section_gd157(self, mock_cache_class):
        """Test get_capture_cross_section for Gd-157."""
        mock_cache = Mock()
        mock_cache.get_cross_section.return_value = (
            np.array([0.01, 0.025, 0.1]),
            np.array([200000, 254000, 240000])
        )
        gd = GadoliniumDepletion(cache=mock_cache)
        
        gd157 = Nuclide(Z=64, A=157)
        xs = gd.get_capture_cross_section(gd157, temperature=600.0)
        
        assert xs > 0
        assert isinstance(xs, (float, np.floating, int, np.integer))
    
    @patch('smrforge.burnup.lwr_burnup.NuclearDataCache')
    def test_get_capture_cross_section_fallback(self, mock_cache_class):
        """Test get_capture_cross_section with exception (fallback values)."""
        mock_cache = Mock()
        mock_cache.get_cross_section.side_effect = Exception("Data not available")
        gd = GadoliniumDepletion(cache=mock_cache)
        
        gd155 = Nuclide(Z=64, A=155)
        xs = gd.get_capture_cross_section(gd155)
        
        # Should use fallback value
        assert xs == 61000.0
    
    def test_deplete(self):
        """Test deplete method."""
        gd = GadoliniumDepletion()
        
        gd155 = Nuclide(Z=64, A=155)
        initial_concentration = 1e20
        flux = 1e14  # n/cm²/s
        time = 365 * 24 * 3600  # 1 year
        
        final_concentration = gd.deplete(
            nuclide=gd155,
            initial_concentration=initial_concentration,
            flux=flux,
            time=time,
        )
        
        assert isinstance(final_concentration, (float, np.floating))
        assert 0 <= final_concentration <= initial_concentration
        # With very high cross-sections, depletion might be very fast
        # Just verify it's a valid concentration
        assert final_concentration >= 0
    
    def test_deplete_zero_time(self):
        """Test deplete with zero time (should return initial concentration)."""
        gd = GadoliniumDepletion()
        
        gd155 = Nuclide(Z=64, A=155)
        initial_concentration = 1e20
        
        final_concentration = gd.deplete(
            nuclide=gd155,
            initial_concentration=initial_concentration,
            flux=1e14,
            time=0.0,
        )
        
        assert np.isclose(final_concentration, initial_concentration)
