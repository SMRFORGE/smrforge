"""
Tests for SMR-specific fuel management.

Tests long-cycle fuel management, batch refueling patterns, and compact core shuffling.
"""

import numpy as np
import pytest

try:
    from smrforge.geometry.assembly import Assembly
    from smrforge.geometry.core_geometry import Point3D
    from smrforge.geometry.smr_fuel_management import (
        SMRFuelManager,
        SMRRefuelingPattern,
    )

    _SMR_FUEL_MANAGEMENT_AVAILABLE = True
except ImportError:
    _SMR_FUEL_MANAGEMENT_AVAILABLE = False


@pytest.mark.skipif(
    not _SMR_FUEL_MANAGEMENT_AVAILABLE,
    reason="SMR fuel management not available",
)
class TestSMRRefuelingPattern:
    """Tests for SMRRefuelingPattern class."""

    def test_pattern_creation(self):
        """Test creating SMR refueling pattern."""
        pattern = SMRRefuelingPattern(
            name="3-batch-long-cycle",
            cycle_length_years=4.0,
            n_batches=3,
        )

        assert pattern.name == "3-batch-long-cycle"
        assert pattern.cycle_length_years == 4.0
        assert pattern.n_batches == 3
        assert pattern.compact_core is True

    def test_pattern_validation(self):
        """Test pattern validation."""
        # Valid pattern
        pattern = SMRRefuelingPattern(
            name="valid",
            batch_fractions=[0.33, 0.33, 0.34],
        )
        assert pattern.n_batches == 3

        # Invalid: fractions don't sum to 1.0
        with pytest.raises(ValueError):
            SMRRefuelingPattern(
                name="invalid",
                batch_fractions=[0.5, 0.5, 0.5],
            )

        # Invalid: wrong number of fractions
        with pytest.raises(ValueError):
            SMRRefuelingPattern(
                name="invalid",
                n_batches=3,
                batch_fractions=[0.5, 0.5],
            )


@pytest.mark.skipif(
    not _SMR_FUEL_MANAGEMENT_AVAILABLE,
    reason="SMR fuel management not available",
)
class TestSMRFuelManager:
    """Tests for SMRFuelManager class."""

    def test_manager_creation(self):
        """Test creating SMR fuel manager."""
        manager = SMRFuelManager(name="Test-SMR-Manager")

        assert manager.name == "Test-SMR-Manager"
        assert manager.cycle_length_years == 3.0
        assert manager.total_operating_years == 0.0

    def test_refuel_smr(self):
        """Test SMR-specific refueling."""
        manager = SMRFuelManager()

        # Create assemblies
        for i in range(9):
            batch = (i % 3) + 1
            burnup = 70.0 if batch == 3 else 30.0
            assembly = Assembly(
                id=i,
                position=Point3D(i * 10, 0, 0),
                batch=batch,
                burnup=burnup,
                enrichment=0.045,
            )
            manager.add_assembly(assembly)

        pattern = SMRRefuelingPattern(
            name="3-batch",
            cycle_length_years=4.0,
            n_batches=3,
        )

        initial_cycle = manager.current_cycle
        manager.refuel_smr(pattern, target_burnup=60.0)

        assert manager.current_cycle == initial_cycle + 1
        assert manager.total_operating_years == 4.0
        assert manager.smr_pattern == pattern

    def test_shuffle_out_in(self):
        """Test out-in shuffling pattern."""
        manager = SMRFuelManager()

        # Create assemblies in a pattern
        positions = [
            (0, 0),
            (10, 0),
            (-10, 0),
            (0, 10),
            (0, -10),
            (7, 7),
            (-7, 7),
            (7, -7),
            (-7, -7),
        ]

        for i, (x, y) in enumerate(positions):
            assembly = Assembly(
                id=i,
                position=Point3D(x, y, 0),
                batch=(i % 3) + 1,
            )
            manager.add_assembly(assembly)

        pattern = SMRRefuelingPattern(
            name="out-in",
            shuffle_pattern="out-in",
            n_batches=3,
        )

        manager.shuffle_smr_compact(pattern)

        # Check that batches were updated
        batches = [a.batch for a in manager.assemblies]
        assert all(b == -1 or (b >= 1 and b <= 3) for b in batches)

    def test_shuffle_in_out(self):
        """Test in-out shuffling pattern."""
        manager = SMRFuelManager()

        # Create assemblies
        for i in range(9):
            assembly = Assembly(
                id=i,
                position=Point3D(i * 5, 0, 0),
                batch=(i % 3) + 1,
            )
            manager.add_assembly(assembly)

        pattern = SMRRefuelingPattern(
            name="in-out",
            shuffle_pattern="in-out",
            n_batches=3,
        )

        manager.shuffle_smr_compact(pattern)

        # Check that batches were updated
        batches = [a.batch for a in manager.assemblies]
        assert all(b == -1 or (b >= 1 and b <= 3) for b in batches)

    def test_get_long_cycle_burnup(self):
        """Test long cycle burnup calculation."""
        manager = SMRFuelManager()

        burnup = manager.get_long_cycle_burnup(cycle_years=4.0, power_density=40.0)

        assert burnup > 0
        assert burnup < 100.0  # Reasonable upper bound

    def test_simulate_long_cycle(self):
        """Test long cycle simulation."""
        manager = SMRFuelManager()

        # Create assemblies
        for i in range(9):
            batch = (i % 3) + 1
            assembly = Assembly(
                id=i,
                position=Point3D(i * 10, 0, 0),
                batch=batch,
                burnup=20.0,
                enrichment=0.045,
            )
            manager.add_assembly(assembly)

        pattern = SMRRefuelingPattern(
            name="3-batch",
            cycle_length_years=4.0,
            n_batches=3,
        )

        history = manager.simulate_long_cycle(pattern, n_cycles=3, target_burnup=60.0)

        assert "cycles" in history
        assert "burnup_avg" in history
        assert "burnup_max" in history
        assert "operating_years" in history

        assert len(history["cycles"]) == 3
        assert len(history["burnup_avg"]) == 3
        assert manager.total_operating_years == 12.0  # 3 cycles * 4 years
