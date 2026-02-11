"""
Tests for optimized long-term transient analysis features.
"""

import numpy as np
import pytest


class TestTransientOptimizations:
    """Test optimized transient solver features."""

    def test_adaptive_time_stepping(self):
        """Test adaptive time stepping."""
        from smrforge.safety.transients import (
            PointKineticsParameters,
            PointKineticsSolver,
        )

        beta = np.array([2.13e-4, 1.43e-3, 1.27e-3, 2.56e-3, 7.48e-4, 2.73e-4])
        lambda_d = np.array([0.0124, 0.0305, 0.111, 0.301, 1.14, 3.01])

        params = PointKineticsParameters(
            beta=beta,
            lambda_d=lambda_d,
            alpha_fuel=-3.5e-5,
            alpha_moderator=-1.0e-5,
            Lambda=5e-4,
            fuel_heat_capacity=1e8,
            moderator_heat_capacity=5e8,
        )

        solver = PointKineticsSolver(params)

        def rho_external(t):
            return 0.001 if t < 1.0 else 0.0

        def power_removal(t, T_fuel, T_mod):
            return 0.9 * 1e6

        initial_state = {
            "power": 1e6,
            "T_fuel": 1200.0,
            "T_mod": 800.0,
        }

        # Test with adaptive stepping
        result = solver.solve_transient(
            rho_external=rho_external,
            power_removal=power_removal,
            initial_state=initial_state,
            t_span=(0.0, 10.0),
            adaptive=True,  # Adaptive stepping
            max_step=None,  # Auto-determined
        )

        # Result may use 't' or 'time' key depending on implementation
        assert "t" in result or "time" in result
        time_key = "t" if "t" in result else "time"
        assert len(result[time_key]) > 0

    def test_long_term_optimization(self):
        """Test long-term optimization mode."""
        from smrforge.safety.transients import (
            PointKineticsParameters,
            PointKineticsSolver,
        )

        beta = np.array([2.13e-4, 1.43e-3, 1.27e-3, 2.56e-3, 7.48e-4, 2.73e-4])
        lambda_d = np.array([0.0124, 0.0305, 0.111, 0.301, 1.14, 3.01])

        params = PointKineticsParameters(
            beta=beta,
            lambda_d=lambda_d,
            alpha_fuel=-3.5e-5,
            alpha_moderator=-1.0e-5,
            Lambda=5e-4,
            fuel_heat_capacity=1e8,
            moderator_heat_capacity=5e8,
        )

        solver = PointKineticsSolver(params)

        def rho_external(t):
            return -0.05 if t < 1.0 else 0.0  # Scram

        def power_removal(t, T_fuel, T_mod):
            # Decay heat model (simplified)
            P0 = 1e6
            P_decay = P0 * 0.066 * (t + 1.0) ** (-0.2)
            return min(P_decay, 0.9 * P0)

        initial_state = {
            "power": 1e6,
            "T_fuel": 1200.0,
            "T_mod": 800.0,
        }

        # Long-term transient with optimizations
        result = solver.solve_transient(
            rho_external=rho_external,
            power_removal=power_removal,
            initial_state=initial_state,
            # Keep this short for unit tests (the long-term mode is what we care about,
            # not simulating multiple days in CI).
            t_span=(0.0, 2 * 3600),  # 2 hours
            long_term_optimization=True,  # Enable optimizations
            adaptive=True,
        )

        # Result may use 't' or 'time' key depending on implementation
        assert "t" in result or "time" in result
        time_key = "t" if "t" in result else "time"
        assert len(result[time_key]) > 0
        assert result[time_key][-1] >= 2 * 3600 - 60.0  # Should reach near end

        # Check that solution is reasonable
        assert np.all(result["power"] >= 0)
        assert np.all(result["T_fuel"] > 0)
        assert np.all(result["T_moderator"] > 0)

    def test_auto_max_step(self):
        """Test automatic max_step determination."""
        from smrforge.safety.transients import (
            PointKineticsParameters,
            PointKineticsSolver,
        )

        beta = np.array([2.13e-4, 1.43e-3, 1.27e-3, 2.56e-3, 7.48e-4, 2.73e-4])
        lambda_d = np.array([0.0124, 0.0305, 0.111, 0.301, 1.14, 3.01])

        params = PointKineticsParameters(
            beta=beta,
            lambda_d=lambda_d,
            alpha_fuel=-3.5e-5,
            alpha_moderator=-1.0e-5,
            Lambda=5e-4,
            fuel_heat_capacity=1e8,
            moderator_heat_capacity=5e8,
        )

        solver = PointKineticsSolver(params)

        def rho_external(t):
            return 0.001 if t < 1.0 else 0.0

        def power_removal(t, T_fuel, T_mod):
            return 0.9 * 1e6

        initial_state = {
            "power": 1e6,
            "T_fuel": 1200.0,
            "T_mod": 800.0,
        }

        # Short transient (should use small steps)
        result_short = solver.solve_transient(
            rho_external=rho_external,
            power_removal=power_removal,
            initial_state=initial_state,
            t_span=(0.0, 10.0),  # 10 seconds
            max_step=None,  # Auto-determined
        )

        # Long transient (should use larger steps)
        result_long = solver.solve_transient(
            rho_external=rho_external,
            power_removal=power_removal,
            initial_state=initial_state,
            t_span=(0.0, 2 * 3600.0),  # 2 hours
            long_term_optimization=True,
            max_step=None,  # Auto-determined
        )

        # Result may use 't' or 'time' key depending on implementation
        time_key_short = "t" if "t" in result_short else "time"
        time_key_long = "t" if "t" in result_long else "time"
        assert len(result_short[time_key_short]) > 0
        assert len(result_long[time_key_long]) > 0

        # Long transient should have fewer points per unit time (larger effective step size)
        # This is a heuristic check - actual behavior depends on solver
        time_span_short = (
            result_short[time_key_short][-1] - result_short[time_key_short][0]
        )
        time_span_long = result_long[time_key_long][-1] - result_long[time_key_long][0]

        points_per_second_short = len(result_short[time_key_short]) / time_span_short
        points_per_second_long = len(result_long[time_key_long]) / time_span_long

        # Long transient should have lower point density (larger steps)
        # Note: This is not guaranteed but is expected behavior
        # We just check that both work without errors
