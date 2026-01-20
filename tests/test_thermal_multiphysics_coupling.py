"""
Tests for thermal/multiphysics_coupling.py module.
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch

from smrforge.thermal.multiphysics_coupling import (
    MultiPhysicsOptions,
    MultiPhysicsCoupling,
)


class TestMultiPhysicsOptions:
    """Tests for MultiPhysicsOptions dataclass."""
    
    def test_default_options(self):
        """Test MultiPhysicsOptions with default values."""
        options = MultiPhysicsOptions()
        
        assert options.max_iterations == 50
        assert options.tolerance == 1e-4
        assert options.under_relaxation == 0.5
        assert options.include_structural is True
        assert options.include_control is True
        assert options.include_burnup is False
        assert options.structural_update_frequency == 5
        assert options.control_update_frequency == 1
        assert options.burnup_update_frequency == 10
    
    def test_custom_options(self):
        """Test MultiPhysicsOptions with custom values."""
        options = MultiPhysicsOptions(
            max_iterations=100,
            tolerance=1e-5,
            under_relaxation=0.7,
            include_structural=False,
            include_control=False,
            include_burnup=True,
            structural_update_frequency=10,
            control_update_frequency=2,
            burnup_update_frequency=5,
        )
        
        assert options.max_iterations == 100
        assert options.tolerance == 1e-5
        assert options.under_relaxation == 0.7
        assert options.include_structural is False
        assert options.include_control is False
        assert options.include_burnup is True
        assert options.structural_update_frequency == 10
        assert options.control_update_frequency == 2
        assert options.burnup_update_frequency == 5


class TestMultiPhysicsCoupling:
    """Tests for MultiPhysicsCoupling class."""
    
    def test_initialization(self):
        """Test MultiPhysicsCoupling initialization."""
        mock_neutronics = Mock()
        mock_thermal = Mock()
        options = MultiPhysicsOptions()
        
        coupling = MultiPhysicsCoupling(
            neutronics_solver=mock_neutronics,
            thermal_solver=mock_thermal,
            options=options,
        )
        
        assert coupling.neutronics_solver == mock_neutronics
        assert coupling.thermal_solver == mock_thermal
        assert coupling.structural_mechanics is None
        assert coupling.control_system is None
        assert coupling.burnup_solver is None
        assert coupling.options == options
        assert coupling.converged is False
        assert coupling.iteration_history == []
    
    def test_initialization_with_all_solvers(self):
        """Test MultiPhysicsCoupling initialization with all optional solvers."""
        mock_neutronics = Mock()
        mock_thermal = Mock()
        mock_structural = Mock()
        mock_control = Mock()
        mock_burnup = Mock()
        
        coupling = MultiPhysicsCoupling(
            neutronics_solver=mock_neutronics,
            thermal_solver=mock_thermal,
            structural_mechanics=mock_structural,
            control_system=mock_control,
            burnup_solver=mock_burnup,
        )
        
        assert coupling.structural_mechanics == mock_structural
        assert coupling.control_system == mock_control
        assert coupling.burnup_solver == mock_burnup
    
    def test_solve_steady_state_converges(self):
        """Test solve_steady_state with convergence."""
        # Mock neutronics solver
        mock_neutronics = Mock()
        mock_neutronics.flux = np.ones((10, 10))  # Add flux attribute for shape detection
        mock_neutronics.solve_steady_state.return_value = (1.05, np.ones(100))
        mock_neutronics.compute_power_distribution.return_value = np.ones(100) * 1e6
        
        # Mock thermal solver - solve_with_power returns temperature array directly
        mock_thermal = Mock()
        # Return temperature that will converge quickly
        initial_temp = np.ones((10, 10)) * 1200.0
        target_temp = np.ones((10, 10)) * 900.0
        mock_thermal.solve_with_power.return_value = target_temp
        
        coupling = MultiPhysicsCoupling(
            neutronics_solver=mock_neutronics,
            thermal_solver=mock_thermal,
            options=MultiPhysicsOptions(max_iterations=10, tolerance=1e-1),  # Loose tolerance for quick convergence
        )
        
        result = coupling.solve_steady_state(initial_temperature=initial_temp)
        
        assert 'k_eff' in result
        assert 'temperature' in result
        assert 'power_distribution' in result
        assert result['iterations'] <= 10
    
    def test_solve_steady_state_with_initial_conditions(self):
        """Test solve_steady_state with initial conditions."""
        mock_neutronics = Mock()
        mock_neutronics.flux = np.ones((10, 10))
        mock_neutronics.solve_steady_state.return_value = (1.05, np.ones(100))
        mock_neutronics.compute_power_distribution.return_value = np.ones(100) * 1e6
        
        mock_thermal = Mock()
        mock_thermal.solve_with_power.return_value = np.ones((10, 10)) * 900.0
        
        coupling = MultiPhysicsCoupling(
            neutronics_solver=mock_neutronics,
            thermal_solver=mock_thermal,
        )
        
        initial_temp = np.ones((10, 10)) * 850.0
        initial_power = 9e6
        
        result = coupling.solve_steady_state(
            initial_temperature=initial_temp,
            initial_power=initial_power,
        )
        
        assert 'k_eff' in result
        assert 'temperature' in result
    
    def test_solve_steady_state_with_structural_mechanics(self):
        """Test solve_steady_state with structural mechanics enabled."""
        mock_neutronics = Mock()
        mock_neutronics.flux = np.ones((10, 10))
        mock_neutronics.solve_steady_state.return_value = (1.05, np.ones(100))
        mock_neutronics.compute_power_distribution.return_value = np.ones(100) * 1e6
        
        mock_thermal = Mock()
        mock_thermal.solve_with_power.return_value = np.ones((10, 10)) * 900.0
        
        mock_structural = Mock()
        mock_structural.analyze.return_value = {
            'stress': np.ones(100) * 1e6,
            'strain': np.ones(100) * 0.001,
            'fuel_radius': 0.5,
            'gap': 0.001,
        }
        
        options = MultiPhysicsOptions(
            include_structural=True,
            structural_update_frequency=1,
            max_iterations=5,
        )
        
        coupling = MultiPhysicsCoupling(
            neutronics_solver=mock_neutronics,
            thermal_solver=mock_thermal,
            structural_mechanics=mock_structural,
            options=options,
        )
        
        result = coupling.solve_steady_state()
        
        assert 'structural_results' in result
        assert mock_structural.analyze.called
    
    def test_solve_steady_state_with_control_system(self):
        """Test solve_steady_state with control system enabled."""
        mock_neutronics = Mock()
        mock_neutronics.flux = np.ones((10, 10))
        mock_neutronics.solve_steady_state.return_value = (1.05, np.ones(100))
        mock_neutronics.compute_power_distribution.return_value = np.ones(100) * 1e6
        
        mock_thermal = Mock()
        mock_thermal.solve_with_power.return_value = np.ones((10, 10)) * 900.0
        
        mock_control = Mock()
        mock_control.compute_reactivity_adjustment.return_value = -0.001
        
        options = MultiPhysicsOptions(
            include_control=True,
            control_update_frequency=1,
            max_iterations=5,
        )
        
        coupling = MultiPhysicsCoupling(
            neutronics_solver=mock_neutronics,
            thermal_solver=mock_thermal,
            control_system=mock_control,
            options=options,
        )
        
        result = coupling.solve_steady_state()
        
        assert 'control_adjustments' in result
        assert mock_control.compute_reactivity_adjustment.called
    
    def test_solve_steady_state_with_burnup(self):
        """Test solve_steady_state with burnup enabled."""
        mock_neutronics = Mock()
        mock_neutronics.flux = np.ones((10, 10))
        mock_neutronics.solve_steady_state.return_value = (1.05, np.ones(100))
        mock_neutronics.compute_power_distribution.return_value = np.ones(100) * 1e6
        
        mock_thermal = Mock()
        mock_thermal.solve_with_power.return_value = np.ones((10, 10)) * 900.0
        
        mock_burnup = Mock()
        mock_burnup.update_composition.return_value = {'updated': True}
        
        options = MultiPhysicsOptions(
            include_burnup=True,
            burnup_update_frequency=1,
            max_iterations=5,
        )
        
        coupling = MultiPhysicsCoupling(
            neutronics_solver=mock_neutronics,
            thermal_solver=mock_thermal,
            burnup_solver=mock_burnup,
            options=options,
        )
        
        result = coupling.solve_steady_state()
        
        assert 'burnup_state' in result
        assert mock_burnup.update_composition.called
    
    def test_solve_steady_state_max_iterations(self):
        """Test solve_steady_state stops at max_iterations if not converged."""
        mock_neutronics = Mock()
        mock_neutronics.flux = np.ones((10, 10))
        # Return different temperature values each time to prevent convergence
        temp_values = [900.0, 920.0, 940.0, 960.0, 980.0]
        temp_counter = [0]
        
        def mock_solve():
            return (1.05, np.ones(100))
        
        def mock_thermal_solve(power_dist):
            temp = temp_values[temp_counter[0] % len(temp_values)]
            temp_counter[0] += 1
            return np.ones((10, 10)) * temp
        
        mock_neutronics.solve_steady_state.side_effect = mock_solve
        mock_neutronics.compute_power_distribution.return_value = np.ones(100) * 1e6
        
        mock_thermal = Mock()
        mock_thermal.solve_with_power.side_effect = mock_thermal_solve
        
        options = MultiPhysicsOptions(max_iterations=3, tolerance=1e-6)
        
        coupling = MultiPhysicsCoupling(
            neutronics_solver=mock_neutronics,
            thermal_solver=mock_thermal,
            options=options,
        )
        
        result = coupling.solve_steady_state()
        
        assert result['iterations'] == 3
        assert coupling.converged is False
    
    def test_solve_steady_state_under_relaxation(self):
        """Test that under_relaxation is applied."""
        mock_neutronics = Mock()
        mock_neutronics.flux = np.ones((10, 10))
        mock_neutronics.solve_steady_state.return_value = (1.05, np.ones(100))
        mock_neutronics.compute_power_distribution.return_value = np.ones(100) * 1e6
        
        mock_thermal = Mock()
        # Return different temperatures to test under-relaxation
        temp_values = [900.0, 920.0, 910.0]
        temp_counter = [0]
        
        def mock_solve_with_power(*args, **kwargs):
            temp = temp_values[temp_counter[0] % len(temp_values)]
            temp_counter[0] += 1
            return np.ones((10, 10)) * temp
        
        mock_thermal.solve_with_power.side_effect = mock_solve_with_power
        
        options = MultiPhysicsOptions(
            max_iterations=3,
            tolerance=1e-2,
            under_relaxation=0.5,
        )
        
        coupling = MultiPhysicsCoupling(
            neutronics_solver=mock_neutronics,
            thermal_solver=mock_thermal,
            options=options,
        )
        
        result = coupling.solve_steady_state()
        
        # Should complete iterations
        assert 'iterations' in result
    
    def test_iteration_history_tracking(self):
        """Test that iteration history is tracked."""
        mock_neutronics = Mock()
        mock_neutronics.flux = np.ones((10, 10))
        mock_neutronics.solve_steady_state.return_value = (1.05, np.ones(100))
        mock_neutronics.compute_power_distribution.return_value = np.ones(100) * 1e6
        
        mock_thermal = Mock()
        mock_thermal.solve_with_power.return_value = np.ones((10, 10)) * 900.0
        
        options = MultiPhysicsOptions(max_iterations=5)
        
        coupling = MultiPhysicsCoupling(
            neutronics_solver=mock_neutronics,
            thermal_solver=mock_thermal,
            options=options,
        )
        
        coupling.solve_steady_state()
        
        # Should have iteration history
        assert len(coupling.iteration_history) > 0
        assert all('iteration' in entry for entry in coupling.iteration_history)
        assert all('k_eff' in entry for entry in coupling.iteration_history)
        assert all('temperature' in entry for entry in coupling.iteration_history)
    
    def test_solve_transient(self):
        """Test solve_transient method."""
        mock_neutronics = Mock()
        mock_neutronics.flux = np.ones((10, 10))
        mock_neutronics.solve_steady_state.return_value = (1.05, np.ones(100))
        mock_neutronics.compute_power_distribution.return_value = np.ones(100) * 1e6
        
        mock_thermal = Mock()
        mock_thermal.solve_with_power.return_value = np.ones((10, 10)) * 900.0
        
        coupling = MultiPhysicsCoupling(
            neutronics_solver=mock_neutronics,
            thermal_solver=mock_thermal,
            options=MultiPhysicsOptions(max_iterations=2, tolerance=1e-1),
        )
        
        result = coupling.solve_transient(
            t_span=(0.0, 10.0),
            time_step=2.0,
        )
        
        assert 'time' in result
        assert 'k_eff_history' in result
        assert 'power_history' in result
        assert 'temperature_history' in result
        assert len(result['time']) > 0
        assert len(result['k_eff_history']) > 0
    
    def test_solve_transient_with_initial_conditions(self):
        """Test solve_transient with initial conditions."""
        mock_neutronics = Mock()
        mock_neutronics.flux = np.ones((10, 10))
        mock_neutronics.solve_steady_state.return_value = (1.05, np.ones(100))
        mock_neutronics.compute_power_distribution.return_value = np.ones(100) * 1e6
        
        mock_thermal = Mock()
        mock_thermal.solve_with_power.return_value = np.ones((10, 10)) * 900.0
        
        coupling = MultiPhysicsCoupling(
            neutronics_solver=mock_neutronics,
            thermal_solver=mock_thermal,
            options=MultiPhysicsOptions(max_iterations=2, tolerance=1e-1),
        )
        
        initial_temp = np.ones((10, 10)) * 850.0
        initial_power = 9e6
        
        result = coupling.solve_transient(
            t_span=(0.0, 5.0),
            initial_temperature=initial_temp,
            initial_power=initial_power,
            time_step=1.0,
        )
        
        assert 'time' in result
        assert len(result['time']) > 0
    
    def test_solve_transient_default_time_step(self):
        """Test solve_transient with default (adaptive) time step."""
        mock_neutronics = Mock()
        mock_neutronics.flux = np.ones((10, 10))
        mock_neutronics.solve_steady_state.return_value = (1.05, np.ones(100))
        mock_neutronics.compute_power_distribution.return_value = np.ones(100) * 1e6
        
        mock_thermal = Mock()
        mock_thermal.solve_with_power.return_value = np.ones((10, 10)) * 900.0
        
        coupling = MultiPhysicsCoupling(
            neutronics_solver=mock_neutronics,
            thermal_solver=mock_thermal,
            options=MultiPhysicsOptions(max_iterations=2, tolerance=1e-1),
        )
        
        result = coupling.solve_transient(t_span=(0.0, 10.0))
        
        assert 'time' in result
        assert len(result['time']) > 0
    
    def test_get_coupling_matrix_no_optional(self):
        """Test get_coupling_matrix without optional solvers."""
        mock_neutronics = Mock()
        mock_thermal = Mock()
        
        options = MultiPhysicsOptions(
            include_structural=False,
            include_control=False,
            include_burnup=False,
        )
        
        coupling = MultiPhysicsCoupling(
            neutronics_solver=mock_neutronics,
            thermal_solver=mock_thermal,
            options=options,
        )
        
        matrix = coupling.get_coupling_matrix()
        
        assert matrix.shape == (5, 5)
        # Should have neutronics-thermal coupling
        assert matrix[0, 1] == 1.0  # Neutronics -> Thermal
        assert matrix[1, 0] == 1.0  # Thermal -> Neutronics
        # Should not have structural/control/burnup coupling
        assert matrix[2, 0] == 0.0  # No structural -> neutronics
        assert matrix[3, 0] == 0.0  # No control -> neutronics
        assert matrix[4, 0] == 0.0  # No burnup -> neutronics
    
    def test_get_coupling_matrix_with_all_options(self):
        """Test get_coupling_matrix with all options enabled."""
        mock_neutronics = Mock()
        mock_thermal = Mock()
        
        options = MultiPhysicsOptions(
            include_structural=True,
            include_control=True,
            include_burnup=True,
        )
        
        coupling = MultiPhysicsCoupling(
            neutronics_solver=mock_neutronics,
            thermal_solver=mock_thermal,
            options=options,
        )
        
        matrix = coupling.get_coupling_matrix()
        
        assert matrix.shape == (5, 5)
        # Should have all couplings
        assert matrix[0, 1] == 1.0  # Neutronics -> Thermal
        assert matrix[1, 0] == 1.0  # Thermal -> Neutronics
        assert matrix[2, 0] == 0.5  # Structural -> Neutronics
        assert matrix[2, 1] == 0.5  # Structural -> Thermal
        assert matrix[1, 2] == 1.0  # Thermal -> Structural
        assert matrix[0, 2] == 0.5  # Neutronics -> Structural
        assert matrix[3, 0] == 1.0  # Control -> Neutronics
        assert matrix[0, 3] == 0.5  # Neutronics -> Control
        assert matrix[4, 0] == 0.8  # Burnup -> Neutronics
        assert matrix[0, 4] == 1.0  # Neutronics -> Burnup
