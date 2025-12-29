"""Tests for control rod geometry module."""

import numpy as np
import pytest

from smrforge.geometry.control_rods import (
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

