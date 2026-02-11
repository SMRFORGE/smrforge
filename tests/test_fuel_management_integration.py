"""
Tests for smrforge.burnup.fuel_management_integration module.
"""

from dataclasses import replace
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from smrforge.burnup.fuel_management_integration import BurnupFuelManagerIntegration


@pytest.fixture
def mock_fuel_manager():
    """Create a mock fuel manager (AssemblyManager)."""
    manager = Mock()

    # Mock assemblies
    assembly1 = Mock()
    assembly1.id = 1
    assembly1.batch = 1
    assembly1.burnup = 10.0

    assembly2 = Mock()
    assembly2.id = 2
    assembly2.batch = 2
    assembly2.burnup = 20.0

    manager.assemblies = [assembly1, assembly2]

    # Mock methods
    manager.get_depleted_assemblies = Mock(return_value=[assembly2])

    return manager


@pytest.fixture
def mock_neutronics_solver():
    """Create a mock neutronics solver."""
    solver = Mock()
    return solver


@pytest.fixture
def mock_burnup_options():
    """Create a mock BurnupOptions."""
    from smrforge.burnup.solver import BurnupOptions

    # Create actual dataclass instance so replace() works
    # Use default values for all parameters except time_steps
    options = BurnupOptions(time_steps=[0.0, 100.0, 365.0])
    return options


@pytest.fixture
def mock_burnup_solver():
    """Create a mock BurnupSolver."""
    solver = Mock()

    # Mock solve method
    inventory = Mock()
    inventory.burnup = np.array([0.0, 5.0, 10.0])
    solver.solve = Mock(return_value=inventory)

    return solver


class TestBurnupFuelManagerIntegration:
    """Tests for BurnupFuelManagerIntegration class."""

    def test_integration_init(self, mock_fuel_manager):
        """Test BurnupFuelManagerIntegration initialization."""
        integration = BurnupFuelManagerIntegration(mock_fuel_manager)

        assert integration.fuel_manager == mock_fuel_manager
        assert len(integration._assembly_solvers) == 0
        assert len(integration._assembly_inventories) == 0

    def test_run_cycle_burnup(
        self,
        mock_fuel_manager,
        mock_neutronics_solver,
        mock_burnup_options,
        mock_burnup_solver,
    ):
        """Test run_cycle_burnup method."""
        integration = BurnupFuelManagerIntegration(mock_fuel_manager)

        # Mock BurnupSolver creation
        with patch(
            "smrforge.burnup.solver.BurnupSolver", return_value=mock_burnup_solver
        ):
            results = integration.run_cycle_burnup(
                neutronics_solver=mock_neutronics_solver,
                burnup_options=mock_burnup_options,
                cycle_days=365.0,
                update_assembly_burnup=True,
            )

        assert isinstance(results, dict)
        assert len(results) == 2  # Two assemblies
        assert 1 in results
        assert 2 in results
        # Assembly burnup should be updated
        assert mock_fuel_manager.assemblies[0].burnup > 10.0
        assert mock_fuel_manager.assemblies[1].burnup > 20.0

    def test_run_cycle_burnup_no_update(
        self,
        mock_fuel_manager,
        mock_neutronics_solver,
        mock_burnup_options,
        mock_burnup_solver,
    ):
        """Test run_cycle_burnup without updating assembly burnup."""
        integration = BurnupFuelManagerIntegration(mock_fuel_manager)
        initial_burnup = [a.burnup for a in mock_fuel_manager.assemblies]

        with patch(
            "smrforge.burnup.solver.BurnupSolver", return_value=mock_burnup_solver
        ):
            results = integration.run_cycle_burnup(
                neutronics_solver=mock_neutronics_solver,
                burnup_options=mock_burnup_options,
                cycle_days=365.0,
                update_assembly_burnup=False,
            )

        # Burnup should not change
        assert mock_fuel_manager.assemblies[0].burnup == initial_burnup[0]
        assert mock_fuel_manager.assemblies[1].burnup == initial_burnup[1]

    def test_update_assembly_burnup_values(self, mock_fuel_manager):
        """Test _update_assembly_burnup_values method."""
        integration = BurnupFuelManagerIntegration(mock_fuel_manager)

        # Create mock inventory
        inventory = Mock()
        inventory.burnup = np.array([0.0, 5.0, 10.0])

        initial_burnup = mock_fuel_manager.assemblies[0].burnup

        integration._update_assembly_burnup_values(inventory, cycle_days=365.0)

        # Burnup should be updated
        assert mock_fuel_manager.assemblies[0].burnup > initial_burnup

    def test_get_assembly_inventory(self, mock_fuel_manager):
        """Test get_assembly_inventory method."""
        integration = BurnupFuelManagerIntegration(mock_fuel_manager)

        # Initially no inventories
        assert integration.get_assembly_inventory(1) is None

        # Add inventory
        inventory = Mock()
        integration._assembly_inventories[1] = inventory

        assert integration.get_assembly_inventory(1) == inventory

    def test_get_batch_burnup_summary(self, mock_fuel_manager):
        """Test get_batch_burnup_summary method."""
        integration = BurnupFuelManagerIntegration(mock_fuel_manager)

        summary = integration.get_batch_burnup_summary()

        assert isinstance(summary, dict)
        assert 1 in summary
        assert 2 in summary
        assert summary[1] == 10.0  # Average of assembly 1
        assert summary[2] == 20.0  # Average of assembly 2

    def test_prepare_for_refueling(self, mock_fuel_manager):
        """Test prepare_for_refueling method."""
        integration = BurnupFuelManagerIntegration(mock_fuel_manager)

        depleted_ids = integration.prepare_for_refueling(target_burnup=15.0)

        assert isinstance(depleted_ids, list)
        # Assembly 2 has burnup 20.0 > 15.0, so should be depleted
        assert 2 in depleted_ids
        mock_fuel_manager.get_depleted_assemblies.assert_called_once_with(15.0)

    def test_apply_refueling_with_smr_manager(self, mock_fuel_manager):
        """Test apply_refueling with SMRFuelManager."""
        integration = BurnupFuelManagerIntegration(mock_fuel_manager)

        # Mock SMRFuelManager methods
        mock_fuel_manager.refuel_smr = Mock()
        pattern = Mock()

        integration.apply_refueling(
            pattern=pattern,
            target_burnup=15.0,
            fresh_enrichment=0.045,
        )

        # Should call refuel_smr if it exists
        if hasattr(mock_fuel_manager, "refuel_smr"):
            mock_fuel_manager.refuel_smr.assert_called_once_with(pattern, 15.0, 0.045)

        # Solvers should be cleared
        assert len(integration._assembly_solvers) == 0
        assert len(integration._assembly_inventories) == 0

    def test_apply_refueling_without_smr_manager(self, mock_fuel_manager):
        """Test apply_refueling without SMRFuelManager."""
        # Remove refuel_smr method
        if hasattr(mock_fuel_manager, "refuel_smr"):
            delattr(mock_fuel_manager, "refuel_smr")

        integration = BurnupFuelManagerIntegration(mock_fuel_manager)

        # Should still work (logs warning)
        integration.apply_refueling(
            pattern=None,
            target_burnup=15.0,
            fresh_enrichment=0.045,
        )

        # Solvers should be cleared
        assert len(integration._assembly_solvers) == 0

    def test_run_multi_cycle_burnup(
        self,
        mock_fuel_manager,
        mock_neutronics_solver,
        mock_burnup_options,
        mock_burnup_solver,
    ):
        """Test run_multi_cycle_burnup method."""
        integration = BurnupFuelManagerIntegration(mock_fuel_manager)

        pattern = Mock()
        pattern.cycle_length_years = 3.0

        # Mock refueling
        mock_fuel_manager.refuel_smr = Mock()

        with patch(
            "smrforge.burnup.solver.BurnupSolver", return_value=mock_burnup_solver
        ):
            results = integration.run_multi_cycle_burnup(
                neutronics_solver=mock_neutronics_solver,
                burnup_options=mock_burnup_options,
                pattern=pattern,
                n_cycles=3,
                target_burnup=60.0,
                fresh_enrichment=0.045,
            )

        assert isinstance(results, dict)
        # Should have results for each assembly
        assert 1 in results
        assert 2 in results
        # Each should have 3 inventories (one per cycle)
        assert len(results[1]) == 3
        assert len(results[2]) == 3

        # Refueling should be called (n_cycles - 1) times
        assert mock_fuel_manager.refuel_smr.call_count == 2

    def test_run_multi_cycle_burnup_no_pattern(
        self,
        mock_fuel_manager,
        mock_neutronics_solver,
        mock_burnup_options,
        mock_burnup_solver,
    ):
        """Test run_multi_cycle_burnup without pattern."""
        integration = BurnupFuelManagerIntegration(mock_fuel_manager)

        with patch(
            "smrforge.burnup.solver.BurnupSolver", return_value=mock_burnup_solver
        ):
            results = integration.run_multi_cycle_burnup(
                neutronics_solver=mock_neutronics_solver,
                burnup_options=mock_burnup_options,
                pattern=None,
                n_cycles=2,
            )

        assert isinstance(results, dict)
        # Should still run without refueling
        assert len(results[1]) == 2
