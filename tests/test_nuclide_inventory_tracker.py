"""
Tests for NuclideInventoryTracker class.

Tests general-purpose nuclide inventory tracking for burnup and material evolution.
"""

import numpy as np
import pytest

try:
    from smrforge.core.reactor_core import Nuclide, NuclideInventoryTracker

    _INVENTORY_TRACKER_AVAILABLE = True
except ImportError:
    _INVENTORY_TRACKER_AVAILABLE = False


@pytest.mark.skipif(
    not _INVENTORY_TRACKER_AVAILABLE, reason="NuclideInventoryTracker not available"
)
class TestNuclideInventoryTracker:
    """Tests for NuclideInventoryTracker class."""

    def test_tracker_creation(self):
        """Test creating an inventory tracker."""
        tracker = NuclideInventoryTracker()

        assert len(tracker.nuclides) == 0
        assert len(tracker.atom_densities) == 0
        assert tracker.burnup == 0.0
        assert tracker.time == 0.0
        assert tracker.units == "atoms/barn-cm"

    def test_add_nuclide(self):
        """Test adding nuclides to inventory."""
        tracker = NuclideInventoryTracker()

        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)

        tracker.add_nuclide(u235, atom_density=0.0005)
        tracker.add_nuclide(u238, atom_density=0.02)

        assert len(tracker.nuclides) == 2
        assert u235 in tracker.nuclides
        assert u238 in tracker.nuclides
        assert tracker.get_atom_density(u235) == 0.0005
        assert tracker.get_atom_density(u238) == 0.02

    def test_get_atom_density(self):
        """Test getting atom density."""
        tracker = NuclideInventoryTracker()

        u235 = Nuclide(Z=92, A=235)
        tracker.add_nuclide(u235, atom_density=0.0005)

        assert tracker.get_atom_density(u235) == 0.0005

        # Non-existent nuclide should return 0.0
        u236 = Nuclide(Z=92, A=236)
        assert tracker.get_atom_density(u236) == 0.0

    def test_update_nuclide(self):
        """Test updating nuclide atom density."""
        tracker = NuclideInventoryTracker()

        u235 = Nuclide(Z=92, A=235)
        tracker.add_nuclide(u235, atom_density=0.0005)

        tracker.update_nuclide(u235, atom_density=0.0004)
        assert tracker.get_atom_density(u235) == 0.0004

        # Updating non-existent nuclide should raise error
        u236 = Nuclide(Z=92, A=236)
        with pytest.raises(ValueError):
            tracker.update_nuclide(u236, atom_density=0.001)

    def test_remove_nuclide(self):
        """Test removing nuclides from inventory."""
        tracker = NuclideInventoryTracker()

        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)

        tracker.add_nuclide(u235, atom_density=0.0005)
        tracker.add_nuclide(u238, atom_density=0.02)

        tracker.remove_nuclide(u235)

        assert u235 not in tracker.nuclides
        assert u238 in tracker.nuclides
        assert tracker.get_atom_density(u235) == 0.0
        assert tracker.get_atom_density(u238) == 0.02

    def test_get_total_atom_density(self):
        """Test getting total atom density."""
        tracker = NuclideInventoryTracker()

        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)

        tracker.add_nuclide(u235, atom_density=0.0005)
        tracker.add_nuclide(u238, atom_density=0.02)

        total = tracker.get_total_atom_density()
        assert total == pytest.approx(0.0205)

    def test_get_mass_fraction(self):
        """Test getting mass fraction."""
        tracker = NuclideInventoryTracker()

        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)

        tracker.add_nuclide(u235, atom_density=0.0005)
        tracker.add_nuclide(u238, atom_density=0.02)

        # Mass fraction should be between 0 and 1
        u235_fraction = tracker.get_mass_fraction(u235)
        u238_fraction = tracker.get_mass_fraction(u238)

        assert 0.0 <= u235_fraction <= 1.0
        assert 0.0 <= u238_fraction <= 1.0
        # U-238 should have higher mass fraction (more atoms * higher A)
        assert u238_fraction > u235_fraction

    def test_get_heavy_metal_mass(self):
        """Test getting heavy metal mass."""
        tracker = NuclideInventoryTracker()

        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)
        cs137 = Nuclide(Z=55, A=137)  # Not a heavy metal

        tracker.add_nuclide(u235, atom_density=0.0005)
        tracker.add_nuclide(u238, atom_density=0.02)
        tracker.add_nuclide(cs137, atom_density=0.001)

        hm_mass = tracker.get_heavy_metal_mass()
        assert hm_mass > 0.0  # Should be positive

    def test_to_dict(self):
        """Test converting to dictionary."""
        tracker = NuclideInventoryTracker()

        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)

        tracker.add_nuclide(u235, atom_density=0.0005)
        tracker.add_nuclide(u238, atom_density=0.02)

        data = tracker.to_dict()

        assert isinstance(data, dict)
        assert "U235" in data
        assert "U238" in data
        assert data["U235"] == 0.0005
        assert data["U238"] == 0.02

    def test_from_dict(self):
        """Test loading from dictionary."""
        tracker = NuclideInventoryTracker()

        data = {
            "U235": 0.0005,
            "U238": 0.02,
        }

        tracker.from_dict(data)

        assert len(tracker.nuclides) == 2
        # Check that nuclides were parsed correctly
        u235_names = [
            nuc.name for nuc in tracker.nuclides if nuc.Z == 92 and nuc.A == 235
        ]
        assert len(u235_names) > 0

    def test_from_dict_extended_elements(self):
        """Test parsing nuclides with elements from full SYMBOL_TO_Z (Tc, Zr)."""
        tracker = NuclideInventoryTracker()
        data = {"Tc99": 1e-6, "Zr90": 2e-5}  # Not in old limited element map
        tracker.from_dict(data)
        assert len(tracker.nuclides) == 2
        tc99 = [n for n in tracker.nuclides if n.Z == 43 and n.A == 99]
        zr90 = [n for n in tracker.nuclides if n.Z == 40 and n.A == 90]
        assert len(tc99) == 1
        assert len(zr90) == 1

    def test_burnup_tracking(self):
        """Test burnup and time tracking."""
        tracker = NuclideInventoryTracker()

        tracker.burnup = 10.0  # MWd/kgU
        tracker.time = 86400.0  # 1 day in seconds

        assert tracker.burnup == 10.0
        assert tracker.time == 86400.0

    def test_units(self):
        """Test different unit systems."""
        tracker = NuclideInventoryTracker(units="atoms/cm³")

        assert tracker.units == "atoms/cm³"

        u235 = Nuclide(Z=92, A=235)
        tracker.add_nuclide(u235, atom_density=1e20)  # atoms/cm³

        assert tracker.get_atom_density(u235) == 1e20

    def test_multiple_updates(self):
        """Test multiple updates to same nuclide."""
        tracker = NuclideInventoryTracker()

        u235 = Nuclide(Z=92, A=235)
        tracker.add_nuclide(u235, atom_density=0.0005)

        # Simulate burnup evolution
        for burnup in [0.0, 10.0, 20.0, 30.0]:
            tracker.burnup = burnup
            # U-235 decreases with burnup (simplified)
            new_density = 0.0005 * (1.0 - burnup / 100.0)
            tracker.update_nuclide(u235, atom_density=new_density)

        # Final density should be less than initial
        assert tracker.get_atom_density(u235) < 0.0005
        assert tracker.burnup == 30.0
