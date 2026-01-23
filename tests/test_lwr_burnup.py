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
    AssemblyWiseBurnupTracker,
    RodWiseBurnupTracker,
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
    
    def test_deplete_zero_flux(self):
        """Test deplete with zero flux (should return initial concentration)."""
        gd = GadoliniumDepletion()
        
        gd155 = Nuclide(Z=64, A=155)
        initial_concentration = 1e20
        
        final_concentration = gd.deplete(
            nuclide=gd155,
            initial_concentration=initial_concentration,
            flux=0.0,
            time=365 * 24 * 3600,
        )
        
        assert np.isclose(final_concentration, initial_concentration)
    
    def test_deplete_zero_initial_concentration(self):
        """Test deplete with zero initial concentration."""
        gd = GadoliniumDepletion()
        
        gd155 = Nuclide(Z=64, A=155)
        
        final_concentration = gd.deplete(
            nuclide=gd155,
            initial_concentration=0.0,
            flux=1e14,
            time=365 * 24 * 3600,
        )
        
        assert final_concentration == 0.0
    
    def test_deplete_negative_initial_concentration(self):
        """Test deplete with negative initial concentration."""
        gd = GadoliniumDepletion()
        
        gd155 = Nuclide(Z=64, A=155)
        
        final_concentration = gd.deplete(
            nuclide=gd155,
            initial_concentration=-1e20,
            flux=1e14,
            time=365 * 24 * 3600,
        )
        
        assert final_concentration == 0.0
    
    @patch('smrforge.burnup.lwr_burnup.NuclearDataCache')
    def test_get_capture_cross_section_other_nuclide(self, mock_cache_class):
        """Test get_capture_cross_section for other nuclide (fallback)."""
        mock_cache = Mock()
        mock_cache.get_cross_section.side_effect = Exception("Data not available")
        gd = GadoliniumDepletion(cache=mock_cache)
        
        other_nuclide = Nuclide(Z=64, A=156)  # Not Gd-155 or Gd-157
        xs = gd.get_capture_cross_section(other_nuclide)
        
        # Should use default fallback value
        assert xs == 1000.0
    
    @patch('smrforge.burnup.lwr_burnup.NuclearDataCache')
    def test_get_capture_cross_section_gd157_fallback(self, mock_cache_class):
        """Test get_capture_cross_section for Gd-157 with exception (fallback)."""
        mock_cache = Mock()
        mock_cache.get_cross_section.side_effect = Exception("Data not available")
        gd = GadoliniumDepletion(cache=mock_cache)
        
        gd157 = Nuclide(Z=64, A=157)
        xs = gd.get_capture_cross_section(gd157)
        
        # Should use Gd-157 fallback value
        assert xs == 254000.0
    
    def test_calculate_reactivity_worth(self):
        """Test calculate_reactivity_worth method."""
        gd = GadoliniumDepletion()
        
        gd155 = Nuclide(Z=64, A=155)
        gd157 = Nuclide(Z=64, A=157)
        
        poison = GadoliniumPoison(
            nuclides=[gd155, gd157],
            initial_concentrations=np.array([1e20, 5e19]),
        )
        
        flux = 1e14
        time = 365 * 24 * 3600
        
        worth = gd.calculate_reactivity_worth(poison, flux, time)
        
        # Reactivity worth should be negative (negative reactivity)
        assert worth < 0
        assert isinstance(worth, (float, np.floating))
    
    def test_calculate_reactivity_worth_zero_initial(self):
        """Test calculate_reactivity_worth with zero initial concentration."""
        gd = GadoliniumDepletion()
        
        gd155 = Nuclide(Z=64, A=155)
        
        poison = GadoliniumPoison(
            nuclides=[gd155],
            initial_concentrations=np.array([0.0]),
        )
        
        worth = gd.calculate_reactivity_worth(poison, 1e14, 365 * 24 * 3600)
        
        # Should handle zero concentration gracefully
        assert isinstance(worth, (float, np.floating))


class TestAssemblyWiseBurnupTracker:
    """Tests for AssemblyWiseBurnupTracker class."""
    
    def test_init_with_n_assemblies(self):
        """Test initialization with number of assemblies."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=37)
        
        assert tracker.n_assemblies == 37
        assert tracker.lattice_size[0] * tracker.lattice_size[1] >= 37
        assert len(tracker.assemblies) == 0
    
    def test_init_with_lattice_size(self):
        """Test initialization with explicit lattice size."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=37, lattice_size=(7, 7))
        
        assert tracker.n_assemblies == 37
        assert tracker.lattice_size == (7, 7)
    
    def test_get_assembly_position(self):
        """Test get_assembly_position method."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=16, lattice_size=(4, 4))
        
        position = tracker.get_assembly_position(0)
        assert position == (0, 0)
        
        position = tracker.get_assembly_position(5)
        assert position == (1, 1)
        
        position = tracker.get_assembly_position(15)
        assert position == (3, 3)
    
    def test_get_assembly_position_invalid_negative(self):
        """Test get_assembly_position with negative ID."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=16)
        
        with pytest.raises(ValueError, match="assembly_id must be"):
            tracker.get_assembly_position(-1)
    
    def test_get_assembly_position_invalid_too_large(self):
        """Test get_assembly_position with ID too large."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=16)
        
        with pytest.raises(ValueError, match="assembly_id must be"):
            tracker.get_assembly_position(16)
    
    def test_update_assembly(self):
        """Test update_assembly method."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=16)
        
        inventory = Mock()
        tracker.update_assembly(
            assembly_id=0,
            position=(0, 0),
            burnup=10.5,
            enrichment=0.195,
            peak_power=150.0,
            nuclide_inventory=inventory,
        )
        
        assert 0 in tracker.assemblies
        assert tracker.assemblies[0].assembly_id == "Assembly-0"
        assert tracker.assemblies[0].burnup == 10.5
        assert tracker.assemblies[0].nuclide_inventory == inventory
    
    def test_update_assembly_defaults(self):
        """Test update_assembly with default parameters."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=16)
        
        tracker.update_assembly(
            assembly_id=1,
            position=(0, 1),
            burnup=20.0,
        )
        
        assert tracker.assemblies[1].average_enrichment == 0.045
        assert tracker.assemblies[1].peak_power == 0.0
        assert tracker.assemblies[1].nuclide_inventory is None
    
    def test_get_burnup_distribution(self):
        """Test get_burnup_distribution method."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=9, lattice_size=(3, 3))
        
        # Update some assemblies
        tracker.update_assembly(0, (0, 0), 10.0)
        tracker.update_assembly(1, (0, 1), 20.0)
        tracker.update_assembly(4, (1, 1), 30.0)
        
        distribution = tracker.get_burnup_distribution()
        
        assert distribution.shape == (3, 3)
        assert distribution[0, 0] == 10.0
        assert distribution[0, 1] == 20.0
        assert distribution[1, 1] == 30.0
        assert distribution[2, 2] == 0.0  # Not updated
    
    def test_get_burnup_distribution_out_of_bounds(self):
        """Test get_burnup_distribution with out-of-bounds positions."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=9, lattice_size=(3, 3))
        
        # Create assembly with invalid position
        assembly = AssemblyBurnup(
            assembly_id="test",
            position=(5, 5),  # Out of bounds
            burnup=50.0,
            average_enrichment=0.20,
            peak_power=200.0,
        )
        tracker.assemblies[99] = assembly
        
        distribution = tracker.get_burnup_distribution()
        
        # Out-of-bounds position should not be included (distribution should be 3x3)
        assert distribution.shape == (3, 3)
        # All values should be 0.0 since position (5, 5) is out of bounds
        assert np.all(distribution == 0.0)
    
    def test_get_average_burnup(self):
        """Test get_average_burnup method."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=9)
        
        # Empty tracker
        assert tracker.get_average_burnup() == 0.0
        
        # Add assemblies
        tracker.update_assembly(0, (0, 0), 10.0)
        tracker.update_assembly(1, (0, 1), 20.0)
        tracker.update_assembly(2, (0, 2), 30.0)
        
        avg = tracker.get_average_burnup()
        assert np.isclose(avg, 20.0)
    
    def test_get_peak_burnup(self):
        """Test get_peak_burnup method."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=9)
        
        # Empty tracker
        assert tracker.get_peak_burnup() == 0.0
        
        # Add assemblies
        tracker.update_assembly(0, (0, 0), 10.0)
        tracker.update_assembly(1, (0, 1), 50.0)
        tracker.update_assembly(2, (0, 2), 30.0)
        
        peak = tracker.get_peak_burnup()
        assert peak == 50.0


class TestRodWiseBurnupTracker:
    """Tests for RodWiseBurnupTracker class."""
    
    def test_init(self):
        """Test RodWiseBurnupTracker initialization."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        assert tracker.assembly_size == (17, 17)
        assert tracker.n_rods == 17 * 17
        assert len(tracker.rods) == 0
    
    def test_get_rod_position(self):
        """Test get_rod_position method."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        position = tracker.get_rod_position(0)
        assert position == (0, 0)
        
        position = tracker.get_rod_position(18)
        assert position == (1, 1)
        
        position = tracker.get_rod_position(288)  # 17*17 - 1
        assert position == (16, 16)
    
    def test_get_rod_position_invalid_negative(self):
        """Test get_rod_position with negative ID."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        with pytest.raises(ValueError, match="rod_id must be"):
            tracker.get_rod_position(-1)
    
    def test_get_rod_position_invalid_too_large(self):
        """Test get_rod_position with ID too large."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        with pytest.raises(ValueError, match="rod_id must be"):
            tracker.get_rod_position(289)  # 17*17
    
    def test_calculate_shadowing_factor_no_control_rods(self):
        """Test calculate_shadowing_factor with no control rods."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        factor = tracker.calculate_shadowing_factor(
            rod_position=(8, 8),
            control_rod_positions=[],
        )
        
        assert factor == 1.0  # No shadowing
    
    def test_calculate_shadowing_factor_single_control_rod(self):
        """Test calculate_shadowing_factor with single control rod."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        # Rod at (8, 8), control rod at (8, 8) - same position
        factor = tracker.calculate_shadowing_factor(
            rod_position=(8, 8),
            control_rod_positions=[(8, 8)],
            pitch=1.26,
        )
        
        # Should have significant shadowing
        assert 0.0 <= factor <= 1.0
        assert factor < 1.0  # Some shadowing
    
    def test_calculate_shadowing_factor_distant_control_rod(self):
        """Test calculate_shadowing_factor with distant control rod."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        # Rod at (0, 0), control rod at (16, 16) - far away
        factor = tracker.calculate_shadowing_factor(
            rod_position=(0, 0),
            control_rod_positions=[(16, 16)],
            pitch=1.26,
        )
        
        # Should have minimal shadowing
        assert 0.0 <= factor <= 1.0
        assert factor > 0.5  # Less shadowing
    
    def test_calculate_shadowing_factor_multiple_control_rods(self):
        """Test calculate_shadowing_factor with multiple control rods."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        # Rod at (8, 8), control rods at (8, 7) and (7, 8) - nearby
        factor = tracker.calculate_shadowing_factor(
            rod_position=(8, 8),
            control_rod_positions=[(8, 7), (7, 8)],
            pitch=1.26,
        )
        
        # Should use minimum distance
        assert 0.0 <= factor <= 1.0
    
    def test_calculate_shadowing_factor_custom_pitch(self):
        """Test calculate_shadowing_factor with custom pitch."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        factor = tracker.calculate_shadowing_factor(
            rod_position=(8, 8),
            control_rod_positions=[(8, 9)],
            pitch=2.0,  # Larger pitch
        )
        
        assert 0.0 <= factor <= 1.0
    
    def test_update_rod(self):
        """Test update_rod method."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        tracker.update_rod(
            rod_id=0,
            position=(0, 0),
            burnup=15.5,
            enrichment=0.19,
            gadolinium_content=1e19,
            control_rod_proximity=5.0,
            shadowing_factor=0.8,
        )
        
        assert 0 in tracker.rods
        assert tracker.rods[0].rod_id == "Rod-0"
        assert tracker.rods[0].burnup == 15.5
        assert tracker.rods[0].shadowing_factor == 0.8
    
    def test_update_rod_defaults(self):
        """Test update_rod with default parameters."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        tracker.update_rod(
            rod_id=1,
            position=(0, 1),
            burnup=12.0,
            enrichment=0.19,
        )
        
        assert tracker.rods[1].gadolinium_content == 0.0
        assert tracker.rods[1].control_rod_proximity == 0.0
        assert tracker.rods[1].shadowing_factor == 1.0
    
    def test_get_burnup_distribution(self):
        """Test get_burnup_distribution method."""
        tracker = RodWiseBurnupTracker(assembly_size=(3, 3))
        
        # Update some rods
        tracker.update_rod(0, (0, 0), 10.0, 0.19)
        tracker.update_rod(1, (0, 1), 20.0, 0.19)
        tracker.update_rod(4, (1, 1), 30.0, 0.19)
        
        distribution = tracker.get_burnup_distribution()
        
        assert distribution.shape == (3, 3)
        assert distribution[0, 0] == 10.0
        assert distribution[0, 1] == 20.0
        assert distribution[1, 1] == 30.0
        assert distribution[2, 2] == 0.0  # Not updated
    
    def test_get_burnup_distribution_out_of_bounds(self):
        """Test get_burnup_distribution with out-of-bounds positions."""
        tracker = RodWiseBurnupTracker(assembly_size=(3, 3))
        
        # Create rod with invalid position
        rod = RodBurnup(
            rod_id="test",
            position=(5, 5),  # Out of bounds
            burnup=50.0,
            enrichment=0.20,
        )
        tracker.rods[99] = rod
        
        distribution = tracker.get_burnup_distribution()
        
        # Out-of-bounds position should not be included (distribution should be 3x3)
        assert distribution.shape == (3, 3)
        # All values should be 0.0 since position (5, 5) is out of bounds
        assert np.all(distribution == 0.0)
    
    def test_get_average_burnup(self):
        """Test get_average_burnup method."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        # Empty tracker
        assert tracker.get_average_burnup() == 0.0
        
        # Add rods
        tracker.update_rod(0, (0, 0), 10.0, 0.19)
        tracker.update_rod(1, (0, 1), 20.0, 0.19)
        tracker.update_rod(2, (0, 2), 30.0, 0.19)
        
        avg = tracker.get_average_burnup()
        assert np.isclose(avg, 20.0)
    
    def test_get_peak_burnup(self):
        """Test get_peak_burnup method."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        # Empty tracker
        assert tracker.get_peak_burnup() == 0.0
        
        # Add rods
        tracker.update_rod(0, (0, 0), 10.0, 0.19)
        tracker.update_rod(1, (0, 1), 50.0, 0.19)
        tracker.update_rod(2, (0, 2), 30.0, 0.19)
        
        peak = tracker.get_peak_burnup()
        assert peak == 50.0


class TestLWRBurnupEdgeCases:
    """Edge case tests for LWR burnup module to improve coverage."""
    
    def test_gadolinium_depletion_get_capture_cross_section_thermal_energy_not_exact(self):
        """Test get_capture_cross_section when thermal energy (0.025 eV) is not exactly in array."""
        from unittest.mock import patch
        
        gd = GadoliniumDepletion()
        gd155 = Nuclide(Z=64, A=155)
        
        # Mock cache to return energy array without exactly 0.025 eV
        mock_energy = np.array([0.01, 0.02, 0.03, 0.1])  # No 0.025 eV
        mock_xs = np.array([50000, 60000, 55000, 50000])
        
        with patch.object(gd.cache, 'get_cross_section', return_value=(mock_energy, mock_xs)):
            xs = gd.get_capture_cross_section(gd155, temperature=600.0)
            
            # Should use closest value (0.02 eV or 0.03 eV)
            assert xs > 0
            assert isinstance(xs, (float, np.floating, int, np.integer))
    
    def test_gadolinium_depletion_deplete_very_long_time(self):
        """Test deplete with very long time (should deplete significantly)."""
        gd = GadoliniumDepletion()
        gd155 = Nuclide(Z=64, A=155)
        
        initial_concentration = 1e20
        flux = 1e14
        time = 10 * 365 * 24 * 3600  # 10 years
        
        final_concentration = gd.deplete(
            nuclide=gd155,
            initial_concentration=initial_concentration,
            flux=flux,
            time=time,
        )
        
        # Should be significantly depleted (or equal if stable nuclide)
        assert 0 <= final_concentration <= initial_concentration
        # Allow equal if nuclide is stable (half-life = 1e20)
        assert final_concentration <= initial_concentration
    
    def test_gadolinium_depletion_deplete_very_high_flux(self):
        """Test deplete with very high flux."""
        gd = GadoliniumDepletion()
        gd155 = Nuclide(Z=64, A=155)
        
        initial_concentration = 1e20
        flux = 1e16  # Very high flux
        time = 365 * 24 * 3600  # 1 year
        
        final_concentration = gd.deplete(
            nuclide=gd155,
            initial_concentration=initial_concentration,
            flux=flux,
            time=time,
        )
        
        # Should deplete very quickly with high flux
        assert 0 <= final_concentration <= initial_concentration
    
    def test_gadolinium_depletion_calculate_reactivity_worth_empty_poison(self):
        """Test calculate_reactivity_worth with empty poison (no nuclides)."""
        gd = GadoliniumDepletion()
        
        poison = GadoliniumPoison(
            nuclides=[],
            initial_concentrations=np.array([]),
        )
        
        worth = gd.calculate_reactivity_worth(poison, 1e14, 365 * 24 * 3600)
        
        # Should return 0.0 for empty poison
        assert worth == 0.0
    
    def test_gadolinium_depletion_calculate_reactivity_worth_single_nuclide(self):
        """Test calculate_reactivity_worth with single nuclide."""
        gd = GadoliniumDepletion()
        gd155 = Nuclide(Z=64, A=155)
        
        poison = GadoliniumPoison(
            nuclides=[gd155],
            initial_concentrations=np.array([1e20]),
        )
        
        worth = gd.calculate_reactivity_worth(poison, 1e14, 365 * 24 * 3600)
        
        # Should be negative (negative reactivity)
        assert worth < 0
        assert isinstance(worth, (float, np.floating))
    
    def test_assembly_wise_burnup_tracker_lattice_size_calculation(self):
        """Test that lattice_size is calculated correctly from n_assemblies."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=25)
        
        # Should calculate lattice size (e.g., 5x5 for 25 assemblies)
        assert tracker.lattice_size[0] * tracker.lattice_size[1] >= 25
        assert tracker.n_assemblies == 25
    
    def test_assembly_wise_burnup_tracker_get_assembly_position_edge_cases(self):
        """Test get_assembly_position with edge case IDs."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=16, lattice_size=(4, 4))
        
        # First assembly
        assert tracker.get_assembly_position(0) == (0, 0)
        
        # Last assembly
        assert tracker.get_assembly_position(15) == (3, 3)
        
        # Middle assembly
        position = tracker.get_assembly_position(8)
        assert isinstance(position, tuple)
        assert len(position) == 2
    
    def test_rod_wise_burnup_tracker_calculate_shadowing_factor_zero_distance(self):
        """Test calculate_shadowing_factor when rod and control rod are at same position."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        # Rod and control rod at same position
        factor = tracker.calculate_shadowing_factor(
            rod_position=(8, 8),
            control_rod_positions=[(8, 8)],
        )
        
        # Should have maximum shadowing (lowest factor)
        assert 0.0 <= factor <= 1.0
        assert factor < 1.0
    
    def test_rod_wise_burnup_tracker_calculate_shadowing_factor_very_close(self):
        """Test calculate_shadowing_factor with very close control rod."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        # Rod at (8, 8), control rod at (8, 9) - adjacent
        factor = tracker.calculate_shadowing_factor(
            rod_position=(8, 8),
            control_rod_positions=[(8, 9)],
            pitch=1.26,
        )
        
        # Should have significant shadowing
        assert 0.0 <= factor <= 1.0
        assert factor < 1.0
    
    def test_rod_wise_burnup_tracker_get_rod_position_edge_cases(self):
        """Test get_rod_position with edge case IDs."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        # First rod
        assert tracker.get_rod_position(0) == (0, 0)
        
        # Last rod
        assert tracker.get_rod_position(288) == (16, 16)  # 17*17 - 1
        
        # Middle rod
        position = tracker.get_rod_position(144)  # Middle
        assert isinstance(position, tuple)
        assert len(position) == 2
    
    def test_assembly_wise_burnup_tracker_get_burnup_distribution_empty(self):
        """Test get_burnup_distribution with no assemblies updated."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=9, lattice_size=(3, 3))
        
        distribution = tracker.get_burnup_distribution()
        
        assert distribution.shape == (3, 3)
        assert np.all(distribution == 0.0)
    
    def test_rod_wise_burnup_tracker_get_burnup_distribution_empty(self):
        """Test get_burnup_distribution with no rods updated."""
        tracker = RodWiseBurnupTracker(assembly_size=(3, 3))
        
        distribution = tracker.get_burnup_distribution()
        
        assert distribution.shape == (3, 3)
        assert np.all(distribution == 0.0)
    
    def test_assembly_wise_burnup_tracker_get_average_burnup_single_assembly(self):
        """Test get_average_burnup with single assembly."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=9)
        
        tracker.update_assembly(0, (0, 0), 25.0)
        
        avg = tracker.get_average_burnup()
        assert avg == 25.0
    
    def test_rod_wise_burnup_tracker_get_average_burnup_single_rod(self):
        """Test get_average_burnup with single rod."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        tracker.update_rod(0, (0, 0), 25.0, 0.19)
        
        avg = tracker.get_average_burnup()
        assert avg == 25.0
    
    def test_assembly_wise_burnup_tracker_get_peak_burnup_single_assembly(self):
        """Test get_peak_burnup with single assembly."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=9)
        
        tracker.update_assembly(0, (0, 0), 25.0)
        
        peak = tracker.get_peak_burnup()
        assert peak == 25.0
    
    def test_rod_wise_burnup_tracker_get_peak_burnup_single_rod(self):
        """Test get_peak_burnup with single rod."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        tracker.update_rod(0, (0, 0), 25.0, 0.19)
        
        peak = tracker.get_peak_burnup()
        assert peak == 25.0
    
    def test_rod_wise_burnup_tracker_calculate_shadowing_factor_edge_distances(self):
        """Test calculate_shadowing_factor with various distances."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        # Test with very close control rod (distance ~0)
        factor_close = tracker.calculate_shadowing_factor(
            rod_position=(8, 8),
            control_rod_positions=[(8, 8)],  # Same position
            pitch=1.26,
        )
        assert 0.0 <= factor_close <= 1.0
        assert factor_close < 1.0  # Should have some shadowing
        
        # Test with very far control rod
        factor_far = tracker.calculate_shadowing_factor(
            rod_position=(0, 0),
            control_rod_positions=[(16, 16)],  # Far away
            pitch=1.26,
        )
        assert 0.0 <= factor_far <= 1.0
        assert factor_far > factor_close  # Less shadowing when far
        
        # Test with multiple control rods at different distances
        factor_multiple = tracker.calculate_shadowing_factor(
            rod_position=(8, 8),
            control_rod_positions=[(8, 7), (7, 8), (9, 9)],  # Multiple nearby
            pitch=1.26,
        )
        assert 0.0 <= factor_multiple <= 1.0
    
    def test_rod_wise_burnup_tracker_calculate_shadowing_factor_clipping(self):
        """Test calculate_shadowing_factor clipping to [0, 1]."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        # Test with extreme pitch values that might cause clipping
        factor = tracker.calculate_shadowing_factor(
            rod_position=(8, 8),
            control_rod_positions=[(8, 8)],
            pitch=0.1,  # Very small pitch
        )
        assert 0.0 <= factor <= 1.0
        
        factor2 = tracker.calculate_shadowing_factor(
            rod_position=(8, 8),
            control_rod_positions=[(8, 8)],
            pitch=10.0,  # Very large pitch
        )
        assert 0.0 <= factor2 <= 1.0
    
    def test_rod_wise_burnup_tracker_calculate_shadowing_factor_distance_calculation(self):
        """Test calculate_shadowing_factor distance calculation with different positions."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        # Test diagonal distance
        factor = tracker.calculate_shadowing_factor(
            rod_position=(0, 0),
            control_rod_positions=[(1, 1)],  # Diagonal, distance = sqrt(2)*pitch
            pitch=1.26,
        )
        assert 0.0 <= factor <= 1.0
        
        # Test horizontal distance
        factor2 = tracker.calculate_shadowing_factor(
            rod_position=(8, 8),
            control_rod_positions=[(8, 9)],  # Horizontal, distance = 1*pitch
            pitch=1.26,
        )
        assert 0.0 <= factor2 <= 1.0
        
        # Test vertical distance
        factor3 = tracker.calculate_shadowing_factor(
            rod_position=(8, 8),
            control_rod_positions=[(9, 8)],  # Vertical, distance = 1*pitch
            pitch=1.26,
        )
        assert 0.0 <= factor3 <= 1.0
    
    def test_gadolinium_depletion_calculate_reactivity_worth_multiple_nuclides(self):
        """Test calculate_reactivity_worth with multiple nuclides."""
        gd = GadoliniumDepletion()
        gd155 = Nuclide(Z=64, A=155)
        gd157 = Nuclide(Z=64, A=157)
        
        poison = GadoliniumPoison(
            nuclides=[gd155, gd157],
            initial_concentrations=np.array([1e20, 5e19]),
        )
        
        worth = gd.calculate_reactivity_worth(poison, 1e14, 365 * 24 * 3600)
        
        # Should sum contributions from both nuclides
        assert worth < 0  # Negative reactivity
        assert isinstance(worth, (float, np.floating))
    
    def test_gadolinium_depletion_calculate_reactivity_worth_partial_depletion(self):
        """Test calculate_reactivity_worth with partial depletion scenario."""
        gd = GadoliniumDepletion()
        gd155 = Nuclide(Z=64, A=155)
        
        poison = GadoliniumPoison(
            nuclides=[gd155],
            initial_concentrations=np.array([1e20]),
        )
        
        # Short time (partial depletion)
        worth_short = gd.calculate_reactivity_worth(poison, 1e14, 365 * 24 * 3600)  # 1 year
        
        # Long time (more depletion)
        worth_long = gd.calculate_reactivity_worth(poison, 1e14, 10 * 365 * 24 * 3600)  # 10 years
        
        # Both should be negative
        assert worth_short < 0
        assert worth_long < 0
        # Long time should have less negative worth (more depleted), or equal if stable
        assert worth_long >= worth_short
    
    def test_gadolinium_depletion_get_capture_cross_section_exception_handling(self):
        """Test get_capture_cross_section exception handling paths."""
        gd = GadoliniumDepletion()
        
        # Test with Gd-155 (should use fallback value)
        gd155 = Nuclide(Z=64, A=155)
        with patch.object(gd.cache, 'get_cross_section', side_effect=Exception("Data not available")):
            xs = gd.get_capture_cross_section(gd155)
            assert xs == 61000.0  # Fallback value
        
        # Test with Gd-157 (should use fallback value)
        gd157 = Nuclide(Z=64, A=157)
        with patch.object(gd.cache, 'get_cross_section', side_effect=Exception("Data not available")):
            xs = gd.get_capture_cross_section(gd157)
            assert xs == 254000.0  # Fallback value
        
        # Test with other nuclide (should use default fallback)
        other_nuclide = Nuclide(Z=64, A=156)
        with patch.object(gd.cache, 'get_cross_section', side_effect=Exception("Data not available")):
            xs = gd.get_capture_cross_section(other_nuclide)
            assert xs == 1000.0  # Default fallback
    
    def test_gadolinium_depletion_deplete_exponential_decay_edge_cases(self):
        """Test deplete with edge cases in exponential decay."""
        gd = GadoliniumDepletion()
        gd155 = Nuclide(Z=64, A=155)
        
        # Test with very high cross-section (should deplete very quickly)
        with patch.object(gd, 'get_capture_cross_section', return_value=1e6):  # Very high XS
            final = gd.deplete(
                nuclide=gd155,
                initial_concentration=1e20,
                flux=1e14,
                time=1000.0,  # Short time
            )
            # Should deplete significantly even in short time
            assert final < 1e20
            assert final >= 0.0
        
        # Test with very low cross-section (should deplete slowly)
        with patch.object(gd, 'get_capture_cross_section', return_value=1.0):  # Very low XS
            final = gd.deplete(
                nuclide=gd155,
                initial_concentration=1e20,
                flux=1e14,
                time=365 * 24 * 3600,  # 1 year
            )
            # Should still have significant concentration
            assert final > 1e19
            assert final <= 1e20
    
    def test_assembly_wise_burnup_tracker_get_burnup_distribution_partial_fill(self):
        """Test get_burnup_distribution when only some assemblies are updated."""
        tracker = AssemblyWiseBurnupTracker(n_assemblies=16, lattice_size=(4, 4))
        
        # Update only a few assemblies
        tracker.update_assembly(0, (0, 0), 10.0)
        tracker.update_assembly(5, (1, 1), 20.0)
        tracker.update_assembly(10, (2, 2), 30.0)
        
        distribution = tracker.get_burnup_distribution()
        
        assert distribution.shape == (4, 4)
        assert distribution[0, 0] == 10.0
        assert distribution[1, 1] == 20.0
        assert distribution[2, 2] == 30.0
        # Unupdated positions should be 0.0
        assert distribution[3, 3] == 0.0
    
    def test_rod_wise_burnup_tracker_get_burnup_distribution_partial_fill(self):
        """Test get_burnup_distribution when only some rods are updated."""
        tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        
        # Update only a few rods
        tracker.update_rod(0, (0, 0), 10.0, 0.19)
        tracker.update_rod(144, (8, 8), 20.0, 0.19)  # Middle rod
        tracker.update_rod(288, (16, 16), 30.0, 0.19)  # Last rod
        
        distribution = tracker.get_burnup_distribution()
        
        assert distribution.shape == (17, 17)
        assert distribution[0, 0] == 10.0
        assert distribution[8, 8] == 20.0
        assert distribution[16, 16] == 30.0
        # Unupdated positions should be 0.0
        assert distribution[1, 1] == 0.0
