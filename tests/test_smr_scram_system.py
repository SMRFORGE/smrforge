"""
Tests for SMR-specific scram system.

Tests advanced scram features for Small Modular Reactors.
"""

import pytest
import numpy as np

try:
    from smrforge.geometry.smr_scram_system import (
        SMRScramSequence,
        SMRScramSystem,
        ScramType,
        create_nuscale_scram_system,
    )
    from smrforge.geometry.control_rods import ControlRod, ControlRodBank, BankPriority
    from smrforge.geometry.core_geometry import Point3D

    _SMR_SCRAM_AVAILABLE = True
except ImportError:
    _SMR_SCRAM_AVAILABLE = False


@pytest.mark.skipif(
    not _SMR_SCRAM_AVAILABLE,
    reason="SMR scram system not available",
)
class TestSMRScramSequence:
    """Tests for SMRScramSequence class."""

    def test_sequence_creation(self):
        """Test creating scram sequence."""
        sequence = SMRScramSequence(
            name="test-sequence",
            scram_type=ScramType.FULL,
            insertion_velocity=75.0,
        )

        assert sequence.name == "test-sequence"
        assert sequence.scram_type == ScramType.FULL
        assert sequence.insertion_velocity == 75.0

    def test_calculate_scram_time_full(self):
        """Test scram time calculation for full scram."""
        sequence = SMRScramSequence(
            name="full-scram",
            scram_type=ScramType.FULL,
            insertion_velocity=75.0,  # cm/s
        )

        rod_length = 365.76  # cm
        n_banks = 3
        scram_time = sequence.calculate_scram_time(rod_length, n_banks)

        expected = rod_length / 75.0
        assert scram_time == pytest.approx(expected)

    def test_calculate_scram_time_emergency(self):
        """Test scram time calculation for emergency scram."""
        sequence = SMRScramSequence(
            name="emergency-scram",
            scram_type=ScramType.EMERGENCY,
            insertion_velocity=100.0,  # cm/s
        )

        rod_length = 365.76  # cm
        n_banks = 3
        scram_time = sequence.calculate_scram_time(rod_length, n_banks)

        expected = rod_length / 100.0
        assert scram_time == pytest.approx(expected)

    def test_calculate_scram_time_staged(self):
        """Test scram time calculation for staged scram."""
        sequence = SMRScramSequence(
            name="staged-scram",
            scram_type=ScramType.STAGED,
            insertion_velocity=75.0,  # cm/s
            delay_between_banks=0.1,  # s
        )

        rod_length = 365.76  # cm
        n_banks = 3
        scram_time = sequence.calculate_scram_time(rod_length, n_banks)

        insertion_time = rod_length / 75.0
        expected = insertion_time + (n_banks - 1) * 0.1
        assert scram_time == pytest.approx(expected)


@pytest.mark.skipif(
    not _SMR_SCRAM_AVAILABLE,
    reason="SMR scram system not available",
)
class TestSMRScramSystem:
    """Tests for SMRScramSystem class."""

    def test_system_creation(self):
        """Test creating SMR scram system."""
        system = SMRScramSystem(name="Test-Scram")

        assert system.name == "Test-Scram"
        assert system.compact_core is True
        assert system.scram_velocity == 75.0

    def test_add_scram_sequence(self):
        """Test adding scram sequence."""
        system = SMRScramSystem()
        sequence = SMRScramSequence(
            name="test-seq",
            scram_type=ScramType.FULL,
        )

        system.add_scram_sequence(sequence)

        assert len(system.scram_sequences) == 1
        assert system.scram_sequences[0] == sequence

    def test_scram_smr_full(self):
        """Test performing full scram."""
        system = SMRScramSystem()

        # Add a bank
        rod = ControlRod(
            id=1,
            position=Point3D(0, 0, 0),
            length=365.76,
            diameter=1.0,
        )
        bank = ControlRodBank(
            id=1,
            name="TestBank",
            rods=[rod],
            max_worth=1000.0,
        )
        system.add_bank(bank)

        # Perform scram
        sequence = SMRScramSequence(
            name="full-scram",
            scram_type=ScramType.FULL,
        )
        scram_event = system.scram_smr(sequence, trigger_reason="Test")

        assert scram_event.trigger_reason == "Test"
        assert "TestBank" in scram_event.banks_involved
        assert bank.insertion == 0.0  # Fully inserted

    def test_scram_smr_emergency(self):
        """Test performing emergency scram."""
        system = SMRScramSystem()

        # Add banks
        for i in range(3):
            rod = ControlRod(
                id=i,
                position=Point3D(i * 10, 0, 0),
                length=365.76,
                diameter=1.0,
            )
            bank = ControlRodBank(
                id=i,
                name=f"Bank{i}",
                rods=[rod],
            )
            system.add_bank(bank)

        # Perform emergency scram
        sequence = SMRScramSequence(
            name="emergency",
            scram_type=ScramType.EMERGENCY,
        )
        scram_event = system.scram_smr(sequence)

        assert len(scram_event.banks_involved) == 3
        assert all(bank.insertion == 0.0 for bank in system.banks)

    def test_calculate_scram_time(self):
        """Test calculating scram time."""
        system = SMRScramSystem()
        system.scram_velocity = 75.0

        # Add a bank with rods
        rod = ControlRod(
            id=1,
            position=Point3D(0, 0, 0),
            length=365.76,  # cm
            diameter=1.0,
        )
        bank = ControlRodBank(id=1, name="TestBank", rods=[rod])
        system.add_bank(bank)

        scram_time = system.calculate_scram_time()

        expected = 365.76 / 75.0
        assert scram_time == pytest.approx(expected, rel=0.1)

    def test_calculate_scram_worth(self):
        """Test calculating scram worth."""
        system = SMRScramSystem()

        # Add banks with worth
        for i in range(2):
            rod = ControlRod(id=i, position=Point3D(0, 0, 0), length=365.76, diameter=1.0)
            bank = ControlRodBank(
                id=i,
                name=f"Bank{i}",
                rods=[rod],
                max_worth=500.0,  # pcm
            )
            system.add_bank(bank)

        metrics = system.calculate_scram_worth(k_eff=1.0)

        assert "total_worth" in metrics
        assert "shutdown_margin" in metrics
        assert "scram_effectiveness" in metrics
        assert metrics["total_worth"] == pytest.approx(1000.0)

    def test_check_auto_scram(self):
        """Test auto-scram checking."""
        system = SMRScramSystem()
        system.auto_scram_enabled = True
        system.scram_threshold = 1.0e9  # W

        # Add a bank
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=365.76, diameter=1.0)
        bank = ControlRodBank(id=1, name="TestBank", rods=[rod])
        system.add_bank(bank)

        # Check with high power (should trigger)
        scram_event = system.check_auto_scram(power=1.5e9)

        assert scram_event is not None
        assert "High power" in scram_event.trigger_reason

        # Check with low power (should not trigger)
        scram_event = system.check_auto_scram(power=0.5e9)

        assert scram_event is None

    def test_get_scram_statistics(self):
        """Test getting scram statistics."""
        system = SMRScramSystem()

        # Perform a scram
        rod = ControlRod(id=1, position=Point3D(0, 0, 0), length=365.76, diameter=1.0)
        bank = ControlRodBank(id=1, name="TestBank", rods=[rod])
        system.add_bank(bank)

        system.scram_smr(trigger_reason="Test")

        stats = system.get_scram_statistics()

        assert "n_scrams" in stats
        assert "avg_scram_time" in stats
        assert "last_scram_time" in stats
        assert stats["n_scrams"] == 1


@pytest.mark.skipif(
    not _SMR_SCRAM_AVAILABLE,
    reason="SMR scram system not available",
)
class TestPresetScramSystems:
    """Tests for preset scram system functions."""

    def test_create_nuscale_scram_system(self):
        """Test creating NuScale-style scram system."""
        system = create_nuscale_scram_system()

        assert system.name == "NuScale-Scram"
        assert system.scram_velocity == 100.0
        assert system.auto_scram_enabled is True
        assert len(system.scram_sequences) > 0
