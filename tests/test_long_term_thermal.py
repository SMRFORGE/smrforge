"""
Unit tests for long-term thermal-hydraulics coupling.
"""

import numpy as np
import pytest

from smrforge.fuel_cycle.long_term import LongTermThermalCoupling


class TestLongTermThermalCoupling:
    """Tests for LongTermThermalCoupling class."""

    def test_initialization(self):
        """Test initialization."""
        initial_temp = np.ones(100) * 900.0  # K
        coupling = LongTermThermalCoupling(
            initial_temperature=initial_temp,
            time_span=(0.0, 365.0),  # 1 year
        )
        
        assert len(coupling.temperature_history) == 1
        assert np.allclose(coupling.temperature_history[0], initial_temp)

    def test_update_temperature(self):
        """Test temperature update."""
        initial_temp = np.ones(100) * 900.0
        coupling = LongTermThermalCoupling(
            initial_temperature=initial_temp,
            time_span=(0.0, 365.0),
        )
        
        power_dist = np.ones(100) * 1e6  # W/cm³
        new_temp = coupling.update_temperature(
            power_distribution=power_dist,
            time=30.0,  # 30 days
            coolant_flow_rate=100.0,  # kg/s
            coolant_temperature=600.0,  # K
        )
        
        assert new_temp.shape == initial_temp.shape
        assert len(coupling.temperature_history) == 2

    def test_get_temperature_feedback(self):
        """Test temperature feedback calculation."""
        initial_temp = np.ones(100) * 900.0
        coupling = LongTermThermalCoupling(
            initial_temperature=initial_temp,
            time_span=(0.0, 365.0),
        )
        
        feedback = coupling.get_temperature_feedback(0.0)
        
        assert "temperature" in feedback
        assert "average_temperature" in feedback
        assert "reactivity_feedback" in feedback
        assert "doppler_coefficient" in feedback

    def test_solve_long_term_coupled(self):
        """Test long-term coupled solution."""
        initial_temp = np.ones(100) * 900.0
        coupling = LongTermThermalCoupling(
            initial_temperature=initial_temp,
            time_span=(0.0, 90.0),  # 3 months
            update_frequency=30.0,
        )
        
        # Mock solvers
        def neutronics_solver(temperature):
            return {
                "power_distribution": np.ones(100) * 1e6,
                "k_eff": 1.0,
            }
        
        def thermal_solver(power, time, temperature):
            return temperature + 10.0  # Simple increase
        
        result = coupling.solve_long_term_coupled(
            neutronics_solver, thermal_solver
        )
        
        assert "time" in result
        assert "power_history" in result
        assert "temperature_history" in result
        assert "k_eff_history" in result
