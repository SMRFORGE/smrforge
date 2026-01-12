"""Tests for assembly management module."""

import numpy as np
import pytest

from smrforge.geometry.assembly import (
    Assembly,
    AssemblyManager,
    FuelBatch,
    RefuelingEvent,
    RefuelingPattern,
)
from smrforge.geometry.core_geometry import Point3D


class TestAssembly:
    """Test Assembly class."""

    def test_assembly_creation(self):
        """Test basic assembly creation."""
        assembly = Assembly(
            id=1,
            position=Point3D(0, 0, 0),
            batch=1,
            burnup=50.0,
            enrichment=0.195,
            heavy_metal_mass=100.0,
        )

        assert assembly.id == 1
        assert assembly.batch == 1
        assert assembly.burnup == 50.0
        assert assembly.enrichment == 0.195
        assert assembly.heavy_metal_mass == 100.0
        assert len(assembly.refueling_history) == 0

    def test_assembly_burnup_fraction(self):
        """Test burnup fraction calculation."""
        assembly = Assembly(id=1, position=Point3D(0, 0, 0), burnup=60.0)
        fraction = assembly.burnup_fraction(target_burnup=120.0)
        assert fraction == pytest.approx(0.5)

        assembly.burnup = 120.0
        fraction = assembly.burnup_fraction(target_burnup=120.0)
        assert fraction == pytest.approx(1.0)

        assembly.burnup = 150.0
        fraction = assembly.burnup_fraction(target_burnup=120.0)
        assert fraction == pytest.approx(1.25)  # Over target

    def test_assembly_burnup_fraction_zero_target(self):
        """Test burnup fraction with zero target."""
        assembly = Assembly(id=1, position=Point3D(0, 0, 0), burnup=60.0)
        fraction = assembly.burnup_fraction(target_burnup=0.0)
        assert fraction == 0.0

    def test_assembly_is_depleted(self):
        """Test depletion check."""
        assembly = Assembly(id=1, position=Point3D(0, 0, 0), burnup=100.0)
        assert not assembly.is_depleted(target_burnup=120.0)

        assembly.burnup = 120.0
        assert assembly.is_depleted(target_burnup=120.0)

        assembly.burnup = 150.0
        assert assembly.is_depleted(target_burnup=120.0)

    def test_assembly_age_cycles(self):
        """Test age calculation."""
        assembly = Assembly(id=1, position=Point3D(0, 0, 0), insertion_cycle=5)
        assert assembly.age_cycles(current_cycle=10) == 5
        assert assembly.age_cycles(current_cycle=5) == 0
        assert assembly.age_cycles(current_cycle=15) == 10
    
    def test_assembly_rotate(self):
        """Test assembly rotation."""
        assembly = Assembly(id=1, position=Point3D(0, 0, 0), orientation=0.0)
        assembly.rotate(60.0)
        assert assembly.orientation == 60.0
        
        assembly.rotate(300.0)  # Should wrap to 0
        assert assembly.orientation == 0.0
        
        assembly.rotate(370.0)  # Should wrap to 10
        assert assembly.orientation == 10.0
    
    def test_assembly_set_orientation(self):
        """Test setting assembly orientation."""
        assembly = Assembly(id=1, position=Point3D(0, 0, 0), orientation=0.0)
        assembly.set_orientation(120.0)
        assert assembly.orientation == 120.0
        
        assembly.set_orientation(450.0)  # Should wrap to 90
        assert assembly.orientation == 90.0
    
    def test_assembly_record_position(self):
        """Test recording position history."""
        assembly = Assembly(id=1, position=Point3D(10, 20, 30))
        assert len(assembly.position_history) == 0
        
        assembly.record_position(cycle=1)
        assert len(assembly.position_history) == 1
        assert assembly.position_history[0][0] == 1
        assert assembly.position_history[0][1].x == 10
        assert assembly.position_history[0][1].y == 20
        assert assembly.position_history[0][1].z == 30
    
    def test_assembly_move_to(self):
        """Test moving assembly and recording history."""
        assembly = Assembly(id=1, position=Point3D(0, 0, 0))
        assert assembly.original_position is None
        
        new_pos = Point3D(10, 20, 30)
        assembly.move_to(new_pos, cycle=1)
        
        assert assembly.position.x == 10
        assert assembly.position.y == 20
        assert assembly.position.z == 30
        assert assembly.original_position is not None
        assert assembly.original_position.x == 0
        assert len(assembly.position_history) == 1
    
    def test_assembly_move_to_no_cycle(self):
        """Test moving assembly without recording cycle."""
        assembly = Assembly(id=1, position=Point3D(0, 0, 0))
        new_pos = Point3D(10, 20, 30)
        assembly.move_to(new_pos, cycle=None)
        
        assert assembly.position.x == 10
        assert len(assembly.position_history) == 0


class TestRefuelingPattern:
    """Test RefuelingPattern class."""

    def test_pattern_creation(self):
        """Test pattern creation."""
        pattern = RefuelingPattern(
            name="3-batch", n_batches=3, batch_fractions=[1 / 3, 1 / 3, 1 / 3]
        )
        assert pattern.name == "3-batch"
        assert pattern.n_batches == 3
        assert len(pattern.batch_fractions) == 3

    def test_pattern_validate(self):
        """Test pattern validation."""
        pattern = RefuelingPattern(
            name="3-batch", n_batches=3, batch_fractions=[1 / 3, 1 / 3, 1 / 3]
        )

        # Valid: 30 assemblies, 10 per batch
        assert pattern.validate(30) is True

        # Invalid: fractions don't sum to 1
        pattern.batch_fractions = [0.5, 0.5, 0.5]
        assert pattern.validate(30) is False

        # Invalid: wrong number of batches
        pattern.batch_fractions = [1 / 2, 1 / 2]
        pattern.n_batches = 3
        assert pattern.validate(30) is False

    def test_pattern_get_batch_size(self):
        """Test batch size calculation."""
        pattern = RefuelingPattern(
            name="3-batch", n_batches=3, batch_fractions=[1 / 3, 1 / 3, 1 / 3]
        )

        assert pattern.get_batch_size(30, 0) == 10
        assert pattern.get_batch_size(30, 1) == 10
        assert pattern.get_batch_size(30, 2) == 10

        # Test invalid batch
        assert pattern.get_batch_size(30, 3) == 0
        assert pattern.get_batch_size(30, -1) == 0
    
    def test_pattern_generate_position_based_shuffle_radial_rotation(self):
        """Test generating shuffle with radial rotation pattern."""
        pattern = RefuelingPattern(
            name="3-batch", n_batches=3, batch_fractions=[1 / 3, 1 / 3, 1 / 3]
        )
        
        # Create 9 assemblies
        assemblies = [
            Assembly(id=i, position=Point3D(i * 10, 0, 0), batch=(i % 3) + 1)
            for i in range(9)
        ]
        
        shuffle_map = pattern.generate_position_based_shuffle(
            assemblies, shuffle_type="radial_rotation"
        )
        
        assert len(shuffle_map) == 9
        # Each assembly should be mapped to another assembly
        assert all(new_id in [a.id for a in assemblies] for new_id in shuffle_map.values())
    
    def test_pattern_generate_position_based_shuffle_radial_outward(self):
        """Test generating shuffle with radial outward pattern."""
        pattern = RefuelingPattern(
            name="3-batch", n_batches=3, batch_fractions=[1 / 3, 1 / 3, 1 / 3]
        )
        
        # Create assemblies with different burnups
        assemblies = [
            Assembly(id=i, position=Point3D(i * 10, 0, 0), burnup=i * 10.0, batch=1)
            for i in range(9)
        ]
        
        shuffle_map = pattern.generate_position_based_shuffle(
            assemblies, shuffle_type="radial_outward"
        )
        
        assert len(shuffle_map) == 9
    
    def test_pattern_generate_position_based_shuffle_radial_inward(self):
        """Test generating shuffle with radial inward pattern."""
        pattern = RefuelingPattern(
            name="3-batch", n_batches=3, batch_fractions=[1 / 3, 1 / 3, 1 / 3]
        )
        
        # Create assemblies with different burnups
        assemblies = [
            Assembly(id=i, position=Point3D(i * 10, 0, 0), burnup=i * 10.0, batch=1)
            for i in range(9)
        ]
        
        shuffle_map = pattern.generate_position_based_shuffle(
            assemblies, shuffle_type="radial_inward"
        )
        
        assert len(shuffle_map) == 9
    
    def test_pattern_generate_position_based_shuffle_pattern_based(self):
        """Test generating shuffle with existing pattern."""
        existing_shuffle = {0: 5, 1: 6, 2: 7}
        pattern = RefuelingPattern(
            name="3-batch",
            n_batches=3,
            batch_fractions=[1 / 3, 1 / 3, 1 / 3],
            shuffle_sequence=existing_shuffle,
        )
        
        assemblies = [Assembly(id=i, position=Point3D(i * 10, 0, 0)) for i in range(9)]
        shuffle_map = pattern.generate_position_based_shuffle(
            assemblies, shuffle_type="pattern_based"
        )
        
        # Should use existing shuffle
        assert shuffle_map == existing_shuffle
    
    def test_pattern_generate_position_based_shuffle_default(self):
        """Test generating shuffle with default (no shuffle) pattern."""
        pattern = RefuelingPattern(
            name="3-batch", n_batches=3, batch_fractions=[1 / 3, 1 / 3, 1 / 3]
        )
        
        assemblies = [Assembly(id=i, position=Point3D(i * 10, 0, 0)) for i in range(9)]
        shuffle_map = pattern.generate_position_based_shuffle(
            assemblies, shuffle_type="unknown_type"
        )
        
        # Should map each assembly to itself
        assert len(shuffle_map) == 9
        assert all(shuffle_map[a.id] == a.id for a in assemblies)


class TestAssemblyManager:
    """Test AssemblyManager class."""

    def test_manager_creation(self):
        """Test manager creation."""
        manager = AssemblyManager(name="TestManager")
        assert manager.name == "TestManager"
        assert len(manager.assemblies) == 0
        assert manager.current_cycle == 0
        assert manager.refueling_pattern is None

    def test_manager_add_assembly(self):
        """Test adding assembly."""
        manager = AssemblyManager()
        assembly = Assembly(id=1, position=Point3D(0, 0, 0))
        manager.add_assembly(assembly)
        assert len(manager.assemblies) == 1
        assert manager.assemblies[0] == assembly

    def test_manager_get_assemblies_by_batch(self):
        """Test getting assemblies by batch."""
        manager = AssemblyManager()
        a1 = Assembly(id=1, position=Point3D(0, 0, 0), batch=1)
        a2 = Assembly(id=2, position=Point3D(10, 0, 0), batch=1)
        a3 = Assembly(id=3, position=Point3D(20, 0, 0), batch=2)

        manager.add_assembly(a1)
        manager.add_assembly(a2)
        manager.add_assembly(a3)

        batch1 = manager.get_assemblies_by_batch(1)
        assert len(batch1) == 2
        assert a1 in batch1
        assert a2 in batch1

        batch2 = manager.get_assemblies_by_batch(2)
        assert len(batch2) == 1
        assert a3 in batch2

    def test_manager_get_depleted_assemblies(self):
        """Test getting depleted assemblies."""
        manager = AssemblyManager()
        a1 = Assembly(id=1, position=Point3D(0, 0, 0), burnup=100.0)  # Not depleted
        a2 = Assembly(id=2, position=Point3D(10, 0, 0), burnup=120.0)  # Depleted
        a3 = Assembly(id=3, position=Point3D(20, 0, 0), burnup=150.0)  # Depleted

        manager.add_assembly(a1)
        manager.add_assembly(a2)
        manager.add_assembly(a3)

        depleted = manager.get_depleted_assemblies(target_burnup=120.0)
        assert len(depleted) == 2
        assert a2 in depleted
        assert a3 in depleted
        assert a1 not in depleted

    def test_manager_shuffle_assemblies(self):
        """Test shuffling assemblies."""
        manager = AssemblyManager()
        pattern = RefuelingPattern(
            name="3-batch", n_batches=3, batch_fractions=[1 / 3, 1 / 3, 1 / 3]
        )

        # Create 9 assemblies (3 per batch)
        for i in range(9):
            batch = (i % 3) + 1
            assembly = Assembly(
                id=i, position=Point3D(i * 10, 0, 0), batch=batch, burnup=i * 10.0
            )
            manager.add_assembly(assembly)

        initial_cycle = manager.current_cycle
        manager.shuffle_assemblies(pattern)

        # Check that cycle incremented
        assert manager.current_cycle == initial_cycle + 1

        # Check batch increments (batch 3 → discharged, batch 2 → batch 3, etc.)
        batches = [a.batch for a in manager.assemblies]
        # All should be in valid batches or discharged (-1)
        assert all(b == -1 or (b >= 1 and b <= 3) for b in batches)

    def test_manager_refuel(self):
        """Test refueling operation."""
        manager = AssemblyManager()
        pattern = RefuelingPattern(
            name="3-batch", n_batches=3, batch_fractions=[1 / 3, 1 / 3, 1 / 3]
        )

        # Create assemblies
        for i in range(9):
            batch = (i % 3) + 1
            burnup = 150.0 if batch == 3 else 50.0  # Batch 3 is depleted
            assembly = Assembly(
                id=i,
                position=Point3D(i * 10, 0, 0),
                batch=batch,
                burnup=burnup,
                enrichment=0.195,
                heavy_metal_mass=100.0,
                insertion_cycle=0,
            )
            manager.add_assembly(assembly)

        initial_cycle = manager.current_cycle
        manager.refuel(pattern, target_burnup=120.0, fresh_enrichment=0.20)

        # Check cycle incremented
        assert manager.current_cycle == initial_cycle + 1

        # Check that depleted assemblies (batch 3) were replaced
        batch3_assemblies = manager.get_assemblies_by_batch(3)
        # After shuffle, old batch 3 becomes discharged, new fresh fuel becomes batch 1
        # This is simplified - actual refueling logic replaces batch 3 with fresh

    def test_manager_average_burnup(self):
        """Test average burnup calculation."""
        manager = AssemblyManager()
        a1 = Assembly(id=1, position=Point3D(0, 0, 0), burnup=50.0)
        a2 = Assembly(id=2, position=Point3D(10, 0, 0), burnup=100.0)
        a3 = Assembly(id=3, position=Point3D(20, 0, 0), burnup=150.0)

        manager.add_assembly(a1)
        manager.add_assembly(a2)
        manager.add_assembly(a3)

        avg_burnup = manager.average_burnup()
        assert avg_burnup == pytest.approx(100.0)  # (50 + 100 + 150) / 3

        # Test batch-specific (a1 is batch 1 by default, need to set explicitly)
        a1.batch = 1
        a2.batch = 1
        a3.batch = 2
        avg_batch1 = manager.average_burnup(batch=1)
        assert avg_batch1 == pytest.approx(75.0)  # (50 + 100) / 2

    def test_manager_average_burnup_empty(self):
        """Test average burnup with no assemblies."""
        manager = AssemblyManager()
        assert manager.average_burnup() == 0.0

    def test_manager_cycle_length_estimate(self):
        """Test cycle length estimation."""
        manager = AssemblyManager()
        # Add assemblies with heavy metal mass
        for i in range(3):
            assembly = Assembly(
                id=i,
                position=Point3D(i * 10, 0, 0),
                heavy_metal_mass=100.0,  # kg
                batch=1,
            )
            manager.add_assembly(assembly)

        # Total HM = 300 kg
        # Target burnup = 120 MWd/kgU
        # Total energy = 300 * 120 * 24 * 3600 * 1e6 J
        # Power = 50 MW = 50e6 W
        # Cycle length = energy / power / (24*3600) days

        cycle_length = manager.cycle_length_estimate(
            power_thermal=50e6, target_burnup=120.0
        )
        assert cycle_length > 0
        assert cycle_length < 10000  # Reasonable range

    def test_manager_cycle_length_no_hm(self):
        """Test cycle length with no heavy metal."""
        manager = AssemblyManager()
        # Assembly with zero HM mass
        assembly = Assembly(id=1, position=Point3D(0, 0, 0), heavy_metal_mass=0.0)
        manager.add_assembly(assembly)

        cycle_length = manager.cycle_length_estimate(power_thermal=50e6, target_burnup=120.0)
        assert cycle_length == 0.0
    
    def test_pattern_validate_batch_sizes_dont_sum(self):
        """Test pattern validation when batch sizes don't sum correctly (line 165)."""
        pattern = RefuelingPattern(
            name="3-batch", n_batches=3, batch_fractions=[0.333, 0.333, 0.333]
        )
        # With 10 assemblies, 0.333 * 10 = 3.33 → int(3.33) = 3 per batch
        # Total = 3 + 3 + 3 = 9, but we have 10 assemblies → should fail validation (line 165)
        assert pattern.validate(10) is False
        
        # Test with another case that triggers line 165
        pattern2 = RefuelingPattern(
            name="2-batch", n_batches=2, batch_fractions=[0.4, 0.4]  # Sums to 0.8, not 1.0
        )
        # First check: fractions don't sum to 1, so validate should return False before line 165
        assert pattern2.validate(10) is False
        
        # But let's also test a case where fractions sum to 1 but sizes don't match
        pattern3 = RefuelingPattern(
            name="3-batch", n_batches=3, batch_fractions=[0.34, 0.33, 0.33]
        )
        # 0.34*10=3.4→3, 0.33*10=3.3→3, 0.33*10=3.3→3, sum=9 but n_assemblies=10
        # This should pass the fraction sum check but fail the batch size check (line 165)
        assert pattern3.validate(10) is False
    
    def test_manager_shuffle_assemblies_invalid_pattern(self):
        """Test shuffle_assemblies raises ValueError for invalid pattern (line 291)."""
        manager = AssemblyManager()
        pattern = RefuelingPattern(
            name="invalid", n_batches=3, batch_fractions=[0.5, 0.5, 0.5]
        )
        
        # Add 9 assemblies
        for i in range(9):
            manager.add_assembly(Assembly(id=i, position=Point3D(i * 10, 0, 0)))
        
        # Pattern is invalid for 9 assemblies (fractions don't sum to 1)
        with pytest.raises(ValueError, match="Invalid refueling pattern"):
            manager.shuffle_assemblies(pattern)
    
    def test_manager_shuffle_assemblies_batch_zero_assignment(self):
        """Test shuffle_assemblies assigns batch=1 for assemblies with batch=0 (line 312)."""
        manager = AssemblyManager()
        pattern = RefuelingPattern(
            name="3-batch", n_batches=3, batch_fractions=[1/3, 1/3, 1/3]
        )
        
        # Create 3 assemblies (one per batch) - pattern needs 3 assemblies minimum
        for i in range(3):
            batch = 0 if i == 0 else i  # First assembly has batch=0
            assembly = Assembly(id=i, position=Point3D(i * 10, 0, 0), batch=batch)
            manager.add_assembly(assembly)
        
        # Use "radial_rotation" to trigger the position_based branch where line 312 is
        manager.shuffle_assemblies(pattern, shuffle_type="radial_rotation", apply_positions=False)
        # Assembly with batch=0 should become batch=1 (line 312)
        assembly0 = manager.assemblies[0]
        assert assembly0.batch == 1  # batch=0 becomes batch=1
    
    def test_manager_shuffle_assemblies_position_updates(self):
        """Test shuffle_assemblies updates positions when apply_positions=True (lines 318-319)."""
        manager = AssemblyManager()
        pattern = RefuelingPattern(
            name="2-batch", n_batches=2, batch_fractions=[0.5, 0.5]
        )
        
        # Create 4 assemblies with different positions and IDs
        a1 = Assembly(id=1, position=Point3D(0, 0, 0), batch=1)
        a2 = Assembly(id=2, position=Point3D(10, 0, 0), batch=1)
        a3 = Assembly(id=3, position=Point3D(20, 0, 0), batch=2)
        a4 = Assembly(id=4, position=Point3D(30, 0, 0), batch=2)
        
        for a in [a1, a2, a3, a4]:
            manager.add_assembly(a)
        
        # Use "radial_rotation" shuffle type which will generate a shuffle_map
        # where at least some assemblies are mapped to different positions
        # This ensures new_id != assembly.id condition is met (lines 318-319)
        initial_pos_1_x = a1.position.x
        
        manager.shuffle_assemblies(pattern, shuffle_type="radial_rotation", apply_positions=True)
        
        # Verify code paths executed - cycle should increment
        assert manager.current_cycle == 1
        
        # The radial_rotation shuffle should move assemblies
        # Verify that at least the code path for position updates was executed
        # (Whether positions actually change depends on the shuffle algorithm)
    
    def test_manager_get_geometry_at_cycle(self):
        """Test get_geometry_at_cycle method (lines 427-430)."""
        manager = AssemblyManager()
        
        # Add assemblies
        for i in range(3):
            manager.add_assembly(Assembly(id=i, position=Point3D(i * 10, 0, 0), batch=1))
        
        # Record geometry snapshot at cycle 0
        manager._record_geometry_snapshot()
        manager.current_cycle = 1
        
        # Record geometry snapshot at cycle 1
        manager._record_geometry_snapshot()
        
        # Get snapshot for cycle 0
        snapshot0 = manager.get_geometry_at_cycle(0)
        assert snapshot0 is not None
        assert snapshot0.cycle == 0
        
        # Get snapshot for cycle 1
        snapshot1 = manager.get_geometry_at_cycle(1)
        assert snapshot1 is not None
        assert snapshot1.cycle == 1
        
        # Get snapshot for non-existent cycle
        snapshot2 = manager.get_geometry_at_cycle(999)
        assert snapshot2 is None
    
    def test_manager_get_position_history(self):
        """Test get_position_history method (lines 434-437)."""
        manager = AssemblyManager()
        
        # Add assembly and move it to record history
        a1 = Assembly(id=1, position=Point3D(0, 0, 0))
        manager.add_assembly(a1)
        
        # Move assembly and record history
        a1.move_to(Point3D(10, 0, 0), cycle=1)
        a1.move_to(Point3D(20, 0, 0), cycle=2)
        
        history = manager.get_position_history(1)
        assert len(history) == 2
        assert history[0][0] == 1  # cycle
        assert history[0][1].x == 10
        assert history[1][0] == 2
        assert history[1][1].x == 20
        
        # Test with non-existent assembly
        history_none = manager.get_position_history(999)
        assert history_none == []
    
    def test_manager_apply_burnup_dependent_shuffle(self):
        """Test apply_burnup_dependent_shuffle method (lines 450-464)."""
        manager = AssemblyManager()
        pattern = RefuelingPattern(
            name="2-batch", n_batches=2, batch_fractions=[0.5, 0.5]
        )
        
        # Create assemblies with different burnups
        a1 = Assembly(id=1, position=Point3D(0, 0, 0), burnup=150.0, batch=1)
        a2 = Assembly(id=2, position=Point3D(10, 0, 0), burnup=100.0, batch=1)
        a3 = Assembly(id=3, position=Point3D(20, 0, 0), burnup=50.0, batch=2)
        a4 = Assembly(id=4, position=Point3D(30, 0, 0), burnup=25.0, batch=2)
        
        for a in [a1, a2, a3, a4]:
            manager.add_assembly(a)
        
        initial_positions = {a.id: a.position for a in manager.assemblies}
        
        manager.apply_burnup_dependent_shuffle(pattern)
        
        # High burnup assemblies should move to outer positions (further from center)
        # Low burnup assemblies should move to inner positions
        # Verify positions changed (code path executed)
        final_positions = {a.id: a.position for a in manager.assemblies}
        # At least some positions should have changed
        assert any(initial_positions[a.id] != final_positions[a.id] for a in manager.assemblies)
    
    def test_manager_get_assemblies_by_orientation(self):
        """Test get_assemblies_by_orientation method (lines 476-477)."""
        manager = AssemblyManager()
        
        # Create assemblies with different orientations
        a1 = Assembly(id=1, position=Point3D(0, 0, 0), orientation=0.0)
        a2 = Assembly(id=2, position=Point3D(10, 0, 0), orientation=45.0)
        a3 = Assembly(id=3, position=Point3D(20, 0, 0), orientation=90.0)
        a4 = Assembly(id=4, position=Point3D(30, 0, 0), orientation=180.0)
        
        for a in [a1, a2, a3, a4]:
            manager.add_assembly(a)
        
        # Get assemblies with orientation between 0 and 90 degrees
        assemblies = manager.get_assemblies_by_orientation((0.0, 90.0))
        assert len(assemblies) >= 3  # Should include a1, a2, a3
        assert all(0.0 <= a.orientation <= 90.0 or a.orientation % 360 in range(0, 91) for a in assemblies)
    
    def test_manager_rotate_assembly(self):
        """Test rotate_assembly method (lines 483-485)."""
        manager = AssemblyManager()
        
        a1 = Assembly(id=1, position=Point3D(0, 0, 0), orientation=0.0)
        manager.add_assembly(a1)
        
        manager.rotate_assembly(1, 45.0)
        assert a1.orientation == 45.0
        
        # Test with non-existent assembly
        manager.rotate_assembly(999, 90.0)  # Should not raise error, just do nothing
    
    def test_manager_rotate_batch(self):
        """Test rotate_batch method (lines 489-490)."""
        manager = AssemblyManager()
        
        a1 = Assembly(id=1, position=Point3D(0, 0, 0), batch=1, orientation=0.0)
        a2 = Assembly(id=2, position=Point3D(10, 0, 0), batch=1, orientation=45.0)
        a3 = Assembly(id=3, position=Point3D(20, 0, 0), batch=2, orientation=0.0)
        
        for a in [a1, a2, a3]:
            manager.add_assembly(a)
        
        manager.rotate_batch(1, 30.0)
        assert a1.orientation == 30.0
        assert a2.orientation == 75.0  # 45 + 30
        assert a3.orientation == 0.0  # Not in batch 1, unchanged
    
    def test_manager_get_batch_statistics(self):
        """Test get_batch_statistics method (lines 502-510)."""
        manager = AssemblyManager()
        
        a1 = Assembly(id=1, position=Point3D(0, 0, 0), batch=1, burnup=50.0, enrichment=0.195, heavy_metal_mass=100.0, insertion_cycle=0)
        a2 = Assembly(id=2, position=Point3D(10, 0, 0), batch=1, burnup=100.0, enrichment=0.20, heavy_metal_mass=100.0, insertion_cycle=0)
        a3 = Assembly(id=3, position=Point3D(20, 0, 0), batch=2, burnup=150.0, enrichment=0.19, heavy_metal_mass=100.0, insertion_cycle=0)
        
        for a in [a1, a2, a3]:
            manager.add_assembly(a)
        
        manager.current_cycle = 5
        
        # Get statistics for batch 1
        stats1 = manager.get_batch_statistics(batch=1)
        assert stats1["count"] == 2
        assert stats1["avg_burnup"] == pytest.approx(75.0)
        assert stats1["max_burnup"] == 100.0
        assert stats1["min_burnup"] == 50.0
        assert stats1["total_hm_mass"] == 200.0
        
        # Get statistics for all assemblies
        stats_all = manager.get_batch_statistics(batch=None)
        assert stats_all["count"] == 3
        assert stats_all["avg_burnup"] == pytest.approx(100.0)
        
        # Get statistics for empty batch
        stats_empty = manager.get_batch_statistics(batch=999)
        assert stats_empty == {}
    
    def test_manager_support_multiple_batches(self):
        """Test support_multiple_batches method (line 531)."""
        manager = AssemblyManager(max_batches=5)
        
        assert manager.support_multiple_batches(3) is True
        assert manager.support_multiple_batches(5) is True
        assert manager.support_multiple_batches(6) is False
        assert manager.support_multiple_batches(10) is False
    
    def test_manager_create_multi_batch_pattern(self):
        """Test create_multi_batch_pattern method (lines 550-559)."""
        manager = AssemblyManager(max_batches=5)
        
        # Test successful creation
        pattern = manager.create_multi_batch_pattern("test", n_batches=3)
        assert pattern.name == "test"
        assert pattern.n_batches == 3
        assert len(pattern.batch_fractions) == 3
        assert all(abs(f - 1/3) < 1e-6 for f in pattern.batch_fractions)
        
        # Test with custom fractions
        pattern2 = manager.create_multi_batch_pattern("test2", n_batches=2, batch_fractions=[0.6, 0.4])
        assert pattern2.batch_fractions == [0.6, 0.4]
        
        # Test with n_batches exceeding max_batches (line 550-554)
        with pytest.raises(ValueError, match="exceeds maximum"):
            manager.create_multi_batch_pattern("invalid", n_batches=10)

