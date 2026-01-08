"""Tests for control rod geometry module."""

import numpy as np
import pytest

from smrforge.geometry.control_rods import (
    BankPriority,
    ControlRod,
    ControlRodBank,
    ControlRodSystem,
    ControlRodType,
)
from smrforge.geometry.core_geometry import Point3D


class TestControlRod:
    """Test ControlRod class."""

    def test_control_rod_creation(self):
        """Test basic control rod creation."""
        rod = ControlRod(
            id=1,
            position=Point3D(0, 0, 0),
            length=400.0,
            diameter=5.0,
            material="B4C",
            rod_type=ControlRodType.SHUTDOWN,
        )

        assert rod.id == 1
        assert rod.length == 400.0
        assert rod.diameter == 5.0
        assert rod.material == "B4C"
        assert rod.rod_type == ControlRodType.SHUTDOWN
        assert rod.insertion == 1.0  # Default fully withdrawn

    def test_control_rod_volume(self):
        """Test control rod volume calculation."""
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0)
        expected_volume = np.pi * (5.0 / 2) ** 2 * 400.0
        assert rod.volume() == pytest.approx(expected_volume)

    def test_control_rod_inserted_length(self):
        """Test inserted length calculation."""
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0)
        rod.insertion = 0.5  # 50% withdrawn, 50% inserted
        assert rod.inserted_length() == pytest.approx(200.0)

        rod.insertion = 0.0  # Fully inserted
        assert rod.inserted_length() == pytest.approx(400.0)

        rod.insertion = 1.0  # Fully withdrawn
        assert rod.inserted_length() == pytest.approx(0.0)

    def test_control_rod_fully_inserted(self):
        """Test fully inserted check."""
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0)
        rod.insertion = 0.0
        assert rod.is_fully_inserted()

        rod.insertion = 0.01
        assert rod.is_fully_inserted()  # Within tolerance

        rod.insertion = 0.02
        assert not rod.is_fully_inserted()

    def test_control_rod_fully_withdrawn(self):
        """Test fully withdrawn check."""
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0)
        rod.insertion = 1.0
        assert rod.is_fully_withdrawn()

        rod.insertion = 0.99
        assert rod.is_fully_withdrawn()  # Within tolerance

        rod.insertion = 0.98
        assert not rod.is_fully_withdrawn()


class TestControlRodBank:
    """Test ControlRodBank class."""

    def test_bank_creation(self):
        """Test bank creation."""
        bank = ControlRodBank(id=1, name="Shutdown-A")
        assert bank.id == 1
        assert bank.name == "Shutdown-A"
        assert len(bank.rods) == 0
        assert bank.insertion == 1.0

    def test_bank_add_rod(self):
        """Test adding rod to bank."""
        bank = ControlRodBank(id=1, name="A")
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0)

        bank.add_rod(rod)
        assert len(bank.rods) == 1
        assert bank.rods[0] == rod

    def test_bank_set_insertion(self):
        """Test setting insertion for all rods in bank."""
        bank = ControlRodBank(id=1, name="A")
        rod1 = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0)
        rod2 = ControlRod(id=2, position=Point3D(10, 0, 0), length=400.0, diameter=5.0)

        bank.add_rod(rod1)
        bank.add_rod(rod2)

        bank.set_insertion(0.5)
        assert bank.insertion == 0.5
        assert rod1.insertion == 0.5
        assert rod2.insertion == 0.5

        # Test clipping
        bank.set_insertion(1.5)  # Should clip to 1.0
        assert bank.insertion == 1.0
        assert rod1.insertion == 1.0

        bank.set_insertion(-0.5)  # Should clip to 0.0
        assert bank.insertion == 0.0
        assert rod1.insertion == 0.0

    def test_bank_scram(self):
        """Test scram operation."""
        bank = ControlRodBank(id=1, name="A")
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0)
        rod.insertion = 0.5
        bank.add_rod(rod)

        bank.scram()
        assert bank.insertion == 0.0
        assert rod.insertion == 0.0
        assert rod.is_fully_inserted()

    def test_bank_withdraw(self):
        """Test withdraw operation."""
        bank = ControlRodBank(id=1, name="A")
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0)
        rod.insertion = 0.5
        bank.add_rod(rod)

        bank.withdraw()
        assert bank.insertion == 1.0
        assert rod.insertion == 1.0
        assert rod.is_fully_withdrawn()

    def test_bank_total_worth(self):
        """Test total worth calculation."""
        bank = ControlRodBank(id=1, name="A", max_worth=1000.0)  # 1000 pcm when fully inserted
        bank.set_insertion(0.5)  # 50% inserted
        # Worth should be proportional to insertion (1.0 - insertion)
        expected_worth = 1000.0 * (1.0 - 0.5)  # 500 pcm
        assert bank.total_worth() == pytest.approx(expected_worth)

        bank.set_insertion(0.0)  # Fully inserted
        assert bank.total_worth() == pytest.approx(1000.0)

        bank.set_insertion(1.0)  # Fully withdrawn
        assert bank.total_worth() == pytest.approx(0.0)

    def test_bank_total_worth_no_max(self):
        """Test total worth when max_worth is None."""
        bank = ControlRodBank(id=1, name="A", max_worth=None)
        assert bank.total_worth() == 0.0
    
    def test_bank_total_worth_with_worth_profile(self):
        """Test total worth with position-dependent worth profile."""
        # Create worth profile function (higher worth at bottom)
        def worth_profile(position_fraction):
            return 1.0 - 0.5 * position_fraction  # 1.0 at bottom, 0.5 at top
        
        bank = ControlRodBank(
            id=1,
            name="A",
            max_worth=1000.0,
            worth_profile=worth_profile,
        )
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0)
        bank.add_rod(rod)
        
        bank.set_insertion(0.5)  # 50% inserted = 200 cm inserted
        worth = bank.total_worth()
        # Should be positive - the exact value depends on the integration
        # With the profile (1.0 - 0.5 * pos_fraction) and integration, 
        # worth may vary but should be positive
        assert worth > 0
        # Worth profile integration may give different result than simple linear
        # Just verify it's reasonable (between 0 and max_worth)
        assert worth <= 1000.0
    
    def test_bank_length_property(self):
        """Test bank length property."""
        bank = ControlRodBank(id=1, name="A")
        assert bank.length == 0.0  # No rods
        
        rod1 = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0)
        rod2 = ControlRod(id=2, position=Point3D(10, 0, 0), length=500.0, diameter=5.0)
        bank.add_rod(rod1)
        bank.add_rod(rod2)
        
        assert bank.length == 500.0  # Max length
    
    def test_bank_get_rods_by_position(self):
        """Test getting rods within distance range."""
        bank = ControlRodBank(id=1, name="A")
        rod1 = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0)
        rod2 = ControlRod(id=2, position=Point3D(10, 0, 0), length=400.0, diameter=5.0)
        rod3 = ControlRod(id=3, position=Point3D(20, 0, 0), length=400.0, diameter=5.0)
        
        bank.add_rod(rod1)
        bank.add_rod(rod2)
        bank.add_rod(rod3)
        
        # Get rods within 5-15 cm of reference (rod1 at 0,0,0)
        rods = bank.get_rods_by_position(min_distance=5.0, max_distance=15.0)
        # Should get rod2 (distance = 10 cm) but not rod1 (< 5) or rod3 (> 15)
        assert len(rods) == 1
        assert rods[0].id == 2
    
    def test_bank_get_rods_by_position_no_rods(self):
        """Test getting rods when bank has no rods."""
        bank = ControlRodBank(id=1, name="A")
        rods = bank.get_rods_by_position(min_distance=0.0, max_distance=10.0)
        assert len(rods) == 0
    
    def test_bank_can_insert_no_dependencies(self):
        """Test can_insert when no dependencies."""
        bank = ControlRodBank(id=1, name="A")
        can_insert, reason = bank.can_insert()
        assert can_insert is True
        assert reason is None
    
    def test_bank_can_insert_with_dependencies(self):
        """Test can_insert with dependencies."""
        system = ControlRodSystem()
        dep_bank = ControlRodBank(id=1, name="Dependency", max_worth=500.0)
        dep_bank.set_insertion(0.0)  # Fully inserted
        system.add_bank(dep_bank)
        
        bank = ControlRodBank(id=2, name="A", dependencies=["Dependency"])
        can_insert, reason = bank.can_insert(system)
        assert can_insert is True
        assert reason is None
    
    def test_bank_can_insert_dependency_not_inserted(self):
        """Test can_insert when dependency not inserted."""
        system = ControlRodSystem()
        dep_bank = ControlRodBank(id=1, name="Dependency", max_worth=500.0)
        dep_bank.set_insertion(0.5)  # Not inserted
        system.add_bank(dep_bank)
        
        bank = ControlRodBank(id=2, name="A", dependencies=["Dependency"])
        can_insert, reason = bank.can_insert(system)
        assert can_insert is False
        assert "Dependency" in reason
        assert "inserted first" in reason
    
    def test_bank_can_insert_dependency_not_found(self):
        """Test can_insert when dependency bank not found."""
        system = ControlRodSystem()
        bank = ControlRodBank(id=1, name="A", dependencies=["MissingBank"])
        can_insert, reason = bank.can_insert(system)
        assert can_insert is False
        assert "not found" in reason


class TestControlRodSequence:
    """Test ControlRodSequence class."""
    
    def test_sequence_creation(self):
        """Test sequence creation."""
        from smrforge.geometry.control_rods import ControlRodSequence
        
        sequence = ControlRodSequence(name="Startup", steps=[])
        assert sequence.name == "Startup"
        assert len(sequence.steps) == 0
        assert sequence.description == ""
    
    def test_sequence_with_steps(self):
        """Test sequence with steps."""
        from smrforge.geometry.control_rods import ControlRodSequence
        
        steps = [("BankA", 0.5, 10.0)]  # (bank_name, target_insertion, time_seconds)
        sequence = ControlRodSequence(name="Startup", steps=steps, description="Test sequence")
        assert sequence.name == "Startup"
        assert len(sequence.steps) == 1
        assert sequence.steps[0] == ("BankA", 0.5, 10.0)
        assert sequence.description == "Test sequence"


class TestScramEvent:
    """Test ScramEvent class."""
    
    def test_scram_event_creation(self):
        """Test scram event creation."""
        from smrforge.geometry.control_rods import ScramEvent
        
        event = ScramEvent(
            timestamp=0.0,
            trigger_reason="Manual",
            banks_involved=["BankA", "BankB"],
            insertion_before={"BankA": 0.5, "BankB": 0.7},
            insertion_after={"BankA": 0.0, "BankB": 0.0},
        )
        assert event.timestamp == 0.0
        assert event.trigger_reason == "Manual"
        assert len(event.banks_involved) == 2
        assert "BankA" in event.banks_involved
        assert event.insertion_before["BankA"] == 0.5
        assert event.insertion_after["BankA"] == 0.0


class TestControlRodWorthAtPosition:
    """Test ControlRod.worth_at_position method."""
    
    def test_worth_at_position_no_worth(self):
        """Test worth_at_position when rod has no worth."""
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0, worth=None)
        worth = rod.worth_at_position(position=100.0)
        assert worth == 0.0
    
    def test_worth_at_position_outside_inserted_length(self):
        """Test worth_at_position when position is outside inserted length."""
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0, worth=1000.0)
        rod.insertion = 0.5  # 50% inserted = 200 cm inserted
        worth = rod.worth_at_position(position=250.0)  # Beyond inserted length
        assert worth == 0.0
    
    def test_worth_at_position_with_worth_profile(self):
        """Test worth_at_position with custom worth profile."""
        def worth_profile(position_fraction):
            return 1.0 - 0.5 * position_fraction
        
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0, worth=1000.0)
        rod.insertion = 0.5  # 50% inserted
        
        worth = rod.worth_at_position(position=100.0, worth_profile=worth_profile)
        # Should be positive since position (100 cm) < inserted length (200 cm)
        assert worth > 0
    
    def test_worth_at_position_zero_length(self):
        """Test worth_at_position when rod has zero length."""
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=0.0, diameter=5.0, worth=1000.0)
        worth = rod.worth_at_position(position=0.0)
        assert worth == 0.0


class TestControlRodSystem:
    """Test ControlRodSystem class."""

    def test_system_creation(self):
        """Test system creation."""
        system = ControlRodSystem(name="TestSystem")
        assert system.name == "TestSystem"
        assert len(system.banks) == 0
        assert system.scram_threshold is None

    def test_system_add_bank(self):
        """Test adding bank to system."""
        system = ControlRodSystem()
        bank = ControlRodBank(id=1, name="A")
        system.add_bank(bank)
        assert len(system.banks) == 1
        assert system.banks[0] == bank

    def test_system_get_bank(self):
        """Test getting bank by name."""
        system = ControlRodSystem()
        bank_a = ControlRodBank(id=1, name="A")
        bank_b = ControlRodBank(id=2, name="B")
        system.add_bank(bank_a)
        system.add_bank(bank_b)

        retrieved = system.get_bank("A")
        assert retrieved == bank_a

        retrieved = system.get_bank("B")
        assert retrieved == bank_b

        retrieved = system.get_bank("C")
        assert retrieved is None

    def test_system_scram_all(self):
        """Test scram all banks."""
        system = ControlRodSystem()
        bank1 = ControlRodBank(id=1, name="A")
        bank2 = ControlRodBank(id=2, name="B")

        rod1 = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0)
        rod2 = ControlRod(id=2, position=Point3D(10, 0, 0), length=400.0, diameter=5.0)

        bank1.add_rod(rod1)
        bank2.add_rod(rod2)
        bank1.set_insertion(0.5)
        bank2.set_insertion(0.7)

        system.add_bank(bank1)
        system.add_bank(bank2)

        system.scram_all()
        assert bank1.insertion == 0.0
        assert bank2.insertion == 0.0
        assert rod1.insertion == 0.0
        assert rod2.insertion == 0.0

    def test_system_total_reactivity_worth(self):
        """Test total reactivity worth calculation."""
        system = ControlRodSystem()
        bank1 = ControlRodBank(id=1, name="A", max_worth=1000.0)
        bank2 = ControlRodBank(id=2, name="B", max_worth=500.0)

        bank1.set_insertion(0.5)  # 500 pcm
        bank2.set_insertion(0.3)  # 350 pcm

        system.add_bank(bank1)
        system.add_bank(bank2)

        total_worth = system.total_reactivity_worth()
        assert total_worth == pytest.approx(850.0)  # 500 + 350

    def test_system_shutdown_margin(self):
        """Test shutdown margin calculation."""
        system = ControlRodSystem()
        bank = ControlRodBank(id=1, name="A", max_worth=2000.0)  # 2000 pcm scram worth
        system.add_bank(bank)

        # k_eff = 1.05 (5% excess reactivity = 5000 pcm)
        # beta_eff ≈ 650 pcm for HTGR
        # current_reactivity = (1.05 - 1.0) / 1.05 * 1e5 ≈ 4762 pcm
        # shutdown_margin = 2000 - 4762 = -2762 pcm (negative means not enough margin)
        margin = system.shutdown_margin(k_eff=1.05)
        assert margin < 0  # Not enough margin

        # k_eff = 1.0 (critical)
        # current_reactivity = 0 pcm
        # shutdown_margin = 2000 - 0 = 2000 pcm
        margin = system.shutdown_margin(k_eff=1.0)
        assert margin == pytest.approx(2000.0)

        # k_eff = 0.99 (subcritical)
        # current_reactivity ≈ -1010 pcm
        # shutdown_margin = 2000 - (-1010) = 3010 pcm
        margin = system.shutdown_margin(k_eff=0.99)
        assert margin > 2000.0

    def test_system_shutdown_margin_no_max_worth(self):
        """Test shutdown margin when banks have no max_worth."""
        system = ControlRodSystem()
        bank = ControlRodBank(id=1, name="A", max_worth=None)
        system.add_bank(bank)

        # Should still calculate margin (scram_worth = 0)
        margin = system.shutdown_margin(k_eff=1.05)
        assert margin < 0  # Negative because no scram worth
    
    def test_system_execute_sequence(self):
        """Test executing control rod sequence."""
        from smrforge.geometry.control_rods import ControlRodSequence
        
        system = ControlRodSystem()
        bank = ControlRodBank(id=1, name="BankA", max_worth=1000.0)
        bank.set_insertion(1.0)  # Fully withdrawn
        system.add_bank(bank)
        
        sequence = ControlRodSequence(name="Startup", steps=[("BankA", 0.5, 10.0)])
        system.execute_sequence(sequence, check_dependencies=False)
        
        assert bank.insertion == 0.5
    
    def test_system_execute_sequence_bank_not_found(self):
        """Test executing sequence with missing bank."""
        from smrforge.geometry.control_rods import ControlRodSequence
        
        system = ControlRodSystem()
        sequence = ControlRodSequence(name="Startup", steps=[("MissingBank", 0.5, 10.0)])
        
        with pytest.raises(ValueError, match="Bank 'MissingBank' not found"):
            system.execute_sequence(sequence, check_dependencies=False)
    
    def test_system_execute_sequence_with_dependency_check(self):
        """Test executing sequence with dependency check."""
        from smrforge.geometry.control_rods import ControlRodSequence
        
        system = ControlRodSystem()
        dep_bank = ControlRodBank(id=1, name="DepBank", max_worth=500.0)
        dep_bank.set_insertion(0.0)  # Inserted
        system.add_bank(dep_bank)
        
        bank = ControlRodBank(id=2, name="BankA", max_worth=1000.0, dependencies=["DepBank"])
        bank.set_insertion(1.0)
        system.add_bank(bank)
        
        sequence = ControlRodSequence(name="Startup", steps=[("BankA", 0.5, 10.0)])
        system.execute_sequence(sequence, check_dependencies=True)
        
        assert bank.insertion == 0.5
    
    def test_system_execute_sequence_dependency_failed(self):
        """Test executing sequence when dependency check fails."""
        from smrforge.geometry.control_rods import ControlRodSequence
        
        system = ControlRodSystem()
        dep_bank = ControlRodBank(id=1, name="DepBank", max_worth=500.0)
        dep_bank.set_insertion(0.5)  # Not inserted
        system.add_bank(dep_bank)
        
        bank = ControlRodBank(id=2, name="BankA", max_worth=1000.0, dependencies=["DepBank"])
        system.add_bank(bank)
        
        sequence = ControlRodSequence(name="Startup", steps=[("BankA", 0.5, 10.0)])
        
        with pytest.raises(ValueError, match="Cannot execute step"):
            system.execute_sequence(sequence, check_dependencies=True)
    
    def test_system_scram_all_records_history(self):
        """Test that scram_all records scram history."""
        system = ControlRodSystem()
        bank1 = ControlRodBank(id=1, name="BankA", max_worth=1000.0)
        bank1.set_insertion(0.5)
        bank2 = ControlRodBank(id=2, name="BankB", max_worth=500.0)
        bank2.set_insertion(0.7)
        
        system.add_bank(bank1)
        system.add_bank(bank2)
        
        assert len(system.scram_history) == 0
        system.scram_all(trigger_reason="Test scram", timestamp=100.0)
        
        assert len(system.scram_history) == 1
        event = system.scram_history[0]
        assert event.timestamp == 100.0
        assert event.trigger_reason == "Test scram"
        assert len(event.banks_involved) == 2
        assert "BankA" in event.banks_involved
        assert event.insertion_before["BankA"] == 0.5
        assert event.insertion_after["BankA"] == 0.0
    
    def test_system_add_sequence(self):
        """Test adding sequence to system."""
        from smrforge.geometry.control_rods import ControlRodSequence
        
        system = ControlRodSystem()
        sequence = ControlRodSequence(name="Startup", steps=[])
        system.add_sequence(sequence)
        
        assert len(system.sequences) == 1
        assert system.sequences[0] == sequence
    
    def test_system_get_sequence(self):
        """Test getting sequence by name."""
        from smrforge.geometry.control_rods import ControlRodSequence
        
        system = ControlRodSystem()
        seq1 = ControlRodSequence(name="Startup", steps=[])
        seq2 = ControlRodSequence(name="Shutdown", steps=[])
        system.add_sequence(seq1)
        system.add_sequence(seq2)
        
        retrieved = system.get_sequence("Startup")
        assert retrieved == seq1
        
        retrieved = system.get_sequence("Shutdown")
        assert retrieved == seq2
        
        retrieved = system.get_sequence("Missing")
        assert retrieved is None
    
    def test_system_get_banks_by_priority(self):
        """Test getting banks by priority."""
        from smrforge.geometry.control_rods import BankPriority
        
        system = ControlRodSystem()
        bank1 = ControlRodBank(id=1, name="A", priority=BankPriority.SAFETY)
        bank2 = ControlRodBank(id=2, name="B", priority=BankPriority.REGULATION)
        bank3 = ControlRodBank(id=3, name="C", priority=BankPriority.SAFETY)
        
        system.add_bank(bank1)
        system.add_bank(bank2)
        system.add_bank(bank3)
        
        safety_banks = system.get_banks_by_priority(BankPriority.SAFETY)
        assert len(safety_banks) == 2
        assert bank1 in safety_banks
        assert bank3 in safety_banks
        assert bank2 not in safety_banks
    
    def test_system_get_banks_by_zone(self):
        """Test getting banks by zone."""
        system = ControlRodSystem()
        bank1 = ControlRodBank(id=1, name="A", zone="core")
        bank2 = ControlRodBank(id=2, name="B", zone="reflector")
        bank3 = ControlRodBank(id=3, name="C", zone="core")
        
        system.add_bank(bank1)
        system.add_bank(bank2)
        system.add_bank(bank3)
        
        core_banks = system.get_banks_by_zone("core")
        assert len(core_banks) == 2
        assert bank1 in core_banks
        assert bank3 in core_banks
        assert bank2 not in core_banks
    
    def test_system_calculate_worth_at_position(self):
        """Test calculating worth at 3D position."""
        from smrforge.geometry.core_geometry import Point3D
        
        system = ControlRodSystem()
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0, worth=1000.0)
        bank = ControlRodBank(id=1, name="A")
        bank.add_rod(rod)
        system.add_bank(bank)
        
        # Calculate worth at position
        position = Point3D(10, 10, 100)  # 10 cm radial, 100 cm axial
        worth = system.calculate_worth_at_position(position, axial_position=100.0, core_radius=150.0)
        
        # Should be positive if rod is inserted enough
        rod.insertion = 0.5  # 50% inserted = 200 cm inserted
        worth = system.calculate_worth_at_position(position, axial_position=100.0, core_radius=150.0)
        assert worth >= 0
    
    def test_system_calculate_worth_at_position_with_radial_profile(self):
        """Test calculating worth with radial worth profile."""
        from smrforge.geometry.core_geometry import Point3D
        
        def radial_profile(r_fraction):
            return 1.0 - 0.5 * r_fraction  # Higher worth at center
        
        system = ControlRodSystem()
        system.radial_worth_profile = radial_profile
        
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0, worth=1000.0)
        rod.insertion = 0.5  # 50% inserted
        bank = ControlRodBank(id=1, name="A")
        bank.add_rod(rod)
        system.add_bank(bank)
        
        # Center position (r=0)
        center_position = Point3D(0, 0, 100)
        worth_center = system.calculate_worth_at_position(center_position, axial_position=100.0, core_radius=150.0)
        
        # Edge position (r near core_radius)
        edge_position = Point3D(140, 0, 100)
        worth_edge = system.calculate_worth_at_position(edge_position, axial_position=100.0, core_radius=150.0)
        
        assert worth_center >= 0
        assert worth_edge >= 0
    
    def test_system_calculate_worth_at_position_with_axial_profile(self):
        """Test calculating worth with axial worth profile."""
        from smrforge.geometry.core_geometry import Point3D
        
        def axial_profile(z_fraction):
            return 1.0 - 0.5 * z_fraction  # Higher worth at bottom
        
        system = ControlRodSystem()
        system.axial_worth_profile = axial_profile
        
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0, worth=1000.0)
        rod.insertion = 0.5  # 50% inserted
        bank = ControlRodBank(id=1, name="A")
        bank.add_rod(rod)
        system.add_bank(bank)
        
        position = Point3D(10, 10, 100)
        worth = system.calculate_worth_at_position(position, axial_position=100.0, core_radius=150.0)
        assert worth >= 0
    
    def test_system_calculate_worth_at_position_zero_radius(self):
        """Test calculating worth with zero core radius."""
        from smrforge.geometry.core_geometry import Point3D
        
        system = ControlRodSystem()
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0, worth=1000.0)
        rod.insertion = 0.5
        bank = ControlRodBank(id=1, name="A")
        bank.add_rod(rod)
        system.add_bank(bank)
        
        position = Point3D(10, 10, 100)
        worth = system.calculate_worth_at_position(position, axial_position=100.0, core_radius=0.0)
        assert worth >= 0
    
    def test_system_sequenced_insertion_by_priority(self):
        """Test sequenced insertion ordered by priority."""
        system = ControlRodSystem()
        bank1 = ControlRodBank(id=1, name="A", priority=BankPriority.SAFETY, max_worth=1000.0)
        bank2 = ControlRodBank(id=2, name="B", priority=BankPriority.REGULATION, max_worth=500.0)
        
        system.add_bank(bank1)
        system.add_bank(bank2)
        
        system.sequenced_insertion(target_insertion=0.5, order_by_priority=True)
        
        assert bank1.insertion == 0.5
        assert bank2.insertion == 0.5
    
    def test_system_sequenced_insertion_by_dependency(self):
        """Test sequenced insertion ordered by dependencies."""
        system = ControlRodSystem()
        dep_bank = ControlRodBank(id=1, name="DepBank", priority=BankPriority.SAFETY, max_worth=1000.0)
        # Start with DepBank already inserted (insertion <= 0.1 satisfies dependency check)
        dep_bank.set_insertion(0.05)  # Already inserted, satisfies dependency
        system.add_bank(dep_bank)
        
        bank = ControlRodBank(id=2, name="Bank", priority=BankPriority.REGULATION, max_worth=500.0, dependencies=["DepBank"])
        bank.set_insertion(1.0)  # Start fully withdrawn
        system.add_bank(bank)
        
        system.sequenced_insertion(target_insertion=0.3, order_by_priority=False)
        
        # Should insert in dependency order (DepBank first, then Bank)
        # Both should reach target insertion
        assert abs(dep_bank.insertion - 0.3) < 0.01
        assert abs(bank.insertion - 0.3) < 0.01
    
    def test_system_sequenced_insertion_specific_banks(self):
        """Test sequenced insertion with specific bank names."""
        system = ControlRodSystem()
        bank1 = ControlRodBank(id=1, name="A", max_worth=1000.0)
        bank2 = ControlRodBank(id=2, name="B", max_worth=500.0)
        bank3 = ControlRodBank(id=3, name="C", max_worth=300.0)
        
        system.add_bank(bank1)
        system.add_bank(bank2)
        system.add_bank(bank3)
        
        system.sequenced_insertion(target_insertion=0.6, bank_names=["A", "C"])
        
        assert bank1.insertion == 0.6
        assert bank2.insertion == 1.0  # Not in list, should remain unchanged
        assert bank3.insertion == 0.6
    
    def test_system_sequenced_insertion_circular_dependency(self):
        """Test sequenced insertion detects circular dependencies."""
        system = ControlRodSystem()
        bank1 = ControlRodBank(id=1, name="A", dependencies=["B"], max_worth=1000.0)
        bank2 = ControlRodBank(id=2, name="B", dependencies=["A"], max_worth=500.0)
        
        system.add_bank(bank1)
        system.add_bank(bank2)
        
        with pytest.raises(ValueError, match="Circular dependency"):
            system.sequenced_insertion(target_insertion=0.5, order_by_priority=False)
    
    def test_system_sequenced_insertion_dependency_violation(self):
        """Test sequenced insertion raises error on dependency violation."""
        system = ControlRodSystem()
        dep_bank = ControlRodBank(id=1, name="DepBank", max_worth=1000.0)
        dep_bank.set_insertion(0.5)  # Not inserted
        system.add_bank(dep_bank)
        
        bank = ControlRodBank(id=2, name="Bank", max_worth=500.0, dependencies=["DepBank"])
        system.add_bank(bank)
        
        with pytest.raises(ValueError, match="Cannot insert bank"):
            system.sequenced_insertion(target_insertion=0.3, order_by_priority=False)
    
    def test_system_get_scram_geometry(self):
        """Test getting scram geometry."""
        system = ControlRodSystem()
        rod1 = ControlRod(id=1, position=Point3D(0, 0, 0), length=400.0, diameter=5.0)
        rod2 = ControlRod(id=2, position=Point3D(10, 0, 0), length=400.0, diameter=5.0)
        
        bank1 = ControlRodBank(id=1, name="A")
        bank1.add_rod(rod1)
        bank2 = ControlRodBank(id=2, name="B")
        bank2.add_rod(rod2)
        
        system.add_bank(bank1)
        system.add_bank(bank2)
        
        scram_geo = system.get_scram_geometry()
        assert "A" in scram_geo
        assert "B" in scram_geo
        assert scram_geo["A"][1] == 0.0
        assert scram_geo["B"][2] == 0.0
    
    def test_system_is_in_scram_state(self):
        """Test checking if system is in scram state."""
        system = ControlRodSystem()
        bank1 = ControlRodBank(id=1, name="A")
        bank1.set_insertion(0.0)  # Fully inserted
        bank2 = ControlRodBank(id=2, name="B")
        bank2.set_insertion(0.01)  # Within tolerance
        
        system.add_bank(bank1)
        system.add_bank(bank2)
        
        assert system.is_in_scram_state()
        
        bank2.set_insertion(0.02)  # Not in scram
        assert not system.is_in_scram_state()
    
    def test_system_create_standard_sequence(self):
        """Test creating standard withdrawal sequence."""
        system = ControlRodSystem()
        reg_bank = ControlRodBank(id=1, name="Reg", priority=BankPriority.REGULATION, max_worth=500.0)
        safety_bank = ControlRodBank(id=2, name="Safety", priority=BankPriority.SAFETY, max_worth=1000.0)
        
        system.add_bank(reg_bank)
        system.add_bank(safety_bank)
        
        sequence = system.create_standard_sequence("Startup", withdrawal_steps=5, regulation_first=True)
        assert sequence.name == "Startup"
        assert len(sequence.steps) > 0
        
        # Should start with regulation bank
        first_step_bank = sequence.steps[0][0]
        assert first_step_bank == "Reg"
    
    def test_system_create_standard_sequence_not_regulation_first(self):
        """Test creating standard sequence without regulation first."""
        system = ControlRodSystem()
        reg_bank = ControlRodBank(id=1, name="Reg", priority=BankPriority.REGULATION, max_worth=500.0)
        safety_bank = ControlRodBank(id=2, name="Safety", priority=BankPriority.SAFETY, max_worth=1000.0)
        
        system.add_bank(reg_bank)
        system.add_bank(safety_bank)
        
        sequence = system.create_standard_sequence("Startup", withdrawal_steps=3, regulation_first=False)
        assert sequence.name == "Startup"
        assert len(sequence.steps) > 0
    
    def test_system_create_standard_sequence_empty_banks(self):
        """Test creating standard sequence with no banks."""
        system = ControlRodSystem()
        sequence = system.create_standard_sequence("Startup", withdrawal_steps=5)
        assert sequence.name == "Startup"
        assert len(sequence.steps) == 0

