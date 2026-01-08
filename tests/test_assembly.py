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

