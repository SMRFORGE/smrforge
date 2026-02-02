"""
Tests for lumped-parameter thermal-hydraulics.
"""

import numpy as np
import pytest
from unittest.mock import patch


class TestThermalLump:
    """Test ThermalLump class."""

    def test_thermal_lump_creation(self):
        """Test creating thermal lump."""
        from smrforge.thermal.lumped import ThermalLump

        lump = ThermalLump(
            name="fuel",
            capacitance=1e8,  # J/K
            temperature=1200.0,  # K
            heat_source=lambda t: 1e6,  # W
        )

        assert lump.name == "fuel"
        assert lump.capacitance == 1e8
        assert lump.temperature == 1200.0
        assert lump.heat_source(0.0) == 1e6

    def test_thermal_lump_invalid_capacitance(self):
        """Test that invalid capacitance raises error."""
        from smrforge.thermal.lumped import ThermalLump

        with pytest.raises(ValueError):
            ThermalLump(
                name="fuel",
                capacitance=-1.0,  # Invalid
                temperature=1200.0,
                heat_source=lambda t: 1e6,
            )

    def test_thermal_lump_invalid_temperature(self):
        """Test that invalid temperature raises error."""
        from smrforge.thermal.lumped import ThermalLump

        with pytest.raises(ValueError):
            ThermalLump(
                name="fuel",
                capacitance=1e8,
                temperature=-100.0,  # Invalid
                heat_source=lambda t: 1e6,
            )


class TestThermalResistance:
    """Test ThermalResistance class."""

    def test_thermal_resistance_creation(self):
        """Test creating thermal resistance."""
        from smrforge.thermal.lumped import ThermalResistance

        resistance = ThermalResistance(
            name="fuel_to_moderator",
            resistance=1e-6,  # K/W
            lump1_name="fuel",
            lump2_name="moderator",
        )

        assert resistance.name == "fuel_to_moderator"
        assert resistance.resistance == 1e-6
        assert resistance.lump1_name == "fuel"
        assert resistance.lump2_name == "moderator"

    def test_thermal_resistance_invalid(self):
        """Test that invalid resistance raises error."""
        from smrforge.thermal.lumped import ThermalResistance

        with pytest.raises(ValueError):
            ThermalResistance(
                name="fuel_to_moderator",
                resistance=-1e-6,  # Invalid
                lump1_name="fuel",
                lump2_name="moderator",
            )


class TestLumpedThermalHydraulics:
    """Test LumpedThermalHydraulics solver."""

    def test_solver_creation(self):
        """Test creating solver."""
        from smrforge.thermal.lumped import (
            LumpedThermalHydraulics,
            ThermalLump,
            ThermalResistance,
        )

        fuel = ThermalLump(
            name="fuel",
            capacitance=1e8,
            temperature=1200.0,
            heat_source=lambda t: 1e6,
        )

        moderator = ThermalLump(
            name="moderator",
            capacitance=5e8,
            temperature=800.0,
            heat_source=lambda t: 0.0,
        )

        resistance = ThermalResistance(
            name="fuel_to_moderator",
            resistance=1e-6,
            lump1_name="fuel",
            lump2_name="moderator",
        )

        solver = LumpedThermalHydraulics(
            lumps={"fuel": fuel, "moderator": moderator},
            resistances=[resistance],
            ambient_temperature=300.0,
        )

        assert solver.n_lumps == 2
        assert len(solver.resistances) == 1

    def test_solver_invalid_lumps(self):
        """Test that empty lumps raises error."""
        from smrforge.thermal.lumped import LumpedThermalHydraulics

        with pytest.raises(ValueError):
            LumpedThermalHydraulics(
                lumps={},  # Empty
                resistances=[],
            )

    def test_solver_invalid_resistance_reference(self):
        """Test that invalid resistance reference raises error."""
        from smrforge.thermal.lumped import (
            LumpedThermalHydraulics,
            ThermalLump,
            ThermalResistance,
        )

        fuel = ThermalLump(
            name="fuel",
            capacitance=1e8,
            temperature=1200.0,
            heat_source=lambda t: 1e6,
        )

        resistance = ThermalResistance(
            name="fuel_to_moderator",
            resistance=1e-6,
            lump1_name="fuel",
            lump2_name="nonexistent",  # Invalid reference
        )

        with pytest.raises(ValueError):
            LumpedThermalHydraulics(
                lumps={"fuel": fuel},
                resistances=[resistance],
            )

    def test_solver_lumps_not_dict(self):
        """Cover line 186: lumps must be dict."""
        from smrforge.thermal.lumped import LumpedThermalHydraulics

        with pytest.raises(ValueError, match="lumps must be dict"):
            LumpedThermalHydraulics(lumps=[("a", 1)], resistances=[])

    def test_solver_resistance_lump1_unknown(self):
        """Cover lines 191-194: resistance references unknown lump1_name."""
        from smrforge.thermal.lumped import (
            LumpedThermalHydraulics,
            ThermalLump,
            ThermalResistance,
        )

        fuel = ThermalLump(
            name="fuel",
            capacitance=1e8,
            temperature=1200.0,
            heat_source=lambda t: 1e6,
        )
        resistance = ThermalResistance(
            name="r1",
            resistance=1e-6,
            lump1_name="nonexistent",
            lump2_name="fuel",
        )
        with pytest.raises(ValueError, match="unknown lump: nonexistent"):
            LumpedThermalHydraulics(
                lumps={"fuel": fuel},
                resistances=[resistance],
            )

    def test_solver_ambient_temperature_invalid(self):
        """Cover lines 200-203: ambient_temperature must be > 0."""
        from smrforge.thermal.lumped import (
            LumpedThermalHydraulics,
            ThermalLump,
            ThermalResistance,
        )

        fuel = ThermalLump(
            name="fuel",
            capacitance=1e8,
            temperature=1200.0,
            heat_source=lambda t: 1e6,
        )
        res = ThermalResistance(
            name="r1",
            resistance=1e-6,
            lump1_name="fuel",
            lump2_name="fuel",
        )
        with pytest.raises(ValueError, match="ambient_temperature must be > 0"):
            LumpedThermalHydraulics(
                lumps={"fuel": fuel},
                resistances=[res],
                ambient_temperature=0.0,
            )

    def test_solve_transient_t_span_invalid_length(self):
        """Cover line 261: t_span must be tuple of length 2."""
        from smrforge.thermal.lumped import (
            LumpedThermalHydraulics,
            ThermalLump,
            ThermalResistance,
        )

        fuel = ThermalLump(
            name="fuel",
            capacitance=1e8,
            temperature=1200.0,
            heat_source=lambda t: 1e6,
        )
        res = ThermalResistance(
            name="r1",
            resistance=1e-6,
            lump1_name="fuel",
            lump2_name="fuel",
        )
        solver = LumpedThermalHydraulics(
            lumps={"fuel": fuel},
            resistances=[res],
        )
        with pytest.raises(ValueError, match="t_span must be tuple of length 2"):
            solver.solve_transient(t_span=(0.0,), max_step=1.0, adaptive=False)

    def test_solve_transient_t_span_reversed(self):
        """Cover line 263: t_span[1] must be > t_span[0]."""
        from smrforge.thermal.lumped import (
            LumpedThermalHydraulics,
            ThermalLump,
            ThermalResistance,
        )

        fuel = ThermalLump(
            name="fuel",
            capacitance=1e8,
            temperature=1200.0,
            heat_source=lambda t: 1e6,
        )
        res = ThermalResistance(
            name="r1",
            resistance=1e-6,
            lump1_name="fuel",
            lump2_name="fuel",
        )
        solver = LumpedThermalHydraulics(
            lumps={"fuel": fuel},
            resistances=[res],
        )
        with pytest.raises(ValueError, match="t_span\\[1\\] must be >"):
            solver.solve_transient(
                t_span=(10.0, 5.0),
                max_step=1.0,
                adaptive=False,
            )

    def test_solve_transient_max_step_none(self):
        """Cover line 268: max_step defaults when None."""
        from smrforge.thermal.lumped import (
            LumpedThermalHydraulics,
            ThermalLump,
            ThermalResistance,
        )

        fuel = ThermalLump(
            name="fuel",
            capacitance=1e8,
            temperature=1200.0,
            heat_source=lambda t: 1e6,
        )
        res = ThermalResistance(
            name="r1",
            resistance=1e-6,
            lump1_name="fuel",
            lump2_name="fuel",
        )
        solver = LumpedThermalHydraulics(
            lumps={"fuel": fuel},
            resistances=[res],
        )
        result = solver.solve_transient(
            t_span=(0.0, 100.0),
            max_step=None,
            adaptive=False,
        )
        assert "time" in result
        assert len(result["time"]) > 0

    def test_solve_transient_ode_solver_fails_success_false(self):
        """Cover lines 346-348: RuntimeError when sol.success is False."""
        from smrforge.thermal.lumped import (
            LumpedThermalHydraulics,
            ThermalLump,
            ThermalResistance,
        )

        fuel = ThermalLump(
            name="fuel",
            capacitance=1e8,
            temperature=1200.0,
            heat_source=lambda t: 1e6,
        )
        res = ThermalResistance(
            name="r1",
            resistance=1e-6,
            lump1_name="fuel",
            lump2_name="fuel",
        )
        solver = LumpedThermalHydraulics(
            lumps={"fuel": fuel},
            resistances=[res],
        )
        mock_result = type("MockResult", (), {})()
        mock_result.success = False
        mock_result.message = "test failure"

        with patch(
            "smrforge.thermal.lumped.solve_ivp",
            return_value=mock_result,
        ):
            with pytest.raises(RuntimeError, match="ODE solver failed"):
                solver.solve_transient(
                    t_span=(0.0, 10.0),
                    max_step=1.0,
                    adaptive=True,
                )

    def test_solve_transient_ode_solver_raises(self):
        """Cover lines 350-351: RuntimeError when solve_ivp raises."""
        from smrforge.thermal.lumped import (
            LumpedThermalHydraulics,
            ThermalLump,
            ThermalResistance,
        )

        fuel = ThermalLump(
            name="fuel",
            capacitance=1e8,
            temperature=1200.0,
            heat_source=lambda t: 1e6,
        )
        res = ThermalResistance(
            name="r1",
            resistance=1e-6,
            lump1_name="fuel",
            lump2_name="fuel",
        )
        solver = LumpedThermalHydraulics(
            lumps={"fuel": fuel},
            resistances=[res],
        )
        with patch(
            "smrforge.thermal.lumped.solve_ivp",
            side_effect=ValueError("bad ode"),
        ):
            with pytest.raises(RuntimeError, match="ODE solver failed"):
                solver.solve_transient(
                    t_span=(0.0, 10.0),
                    max_step=1.0,
                    adaptive=True,
                )

    def test_solve_transient(self):
        """Test solving transient."""
        from smrforge.thermal.lumped import (
            LumpedThermalHydraulics,
            ThermalLump,
            ThermalResistance,
        )

        fuel = ThermalLump(
            name="fuel",
            capacitance=1e8,
            temperature=1200.0,
            heat_source=lambda t: 1e6 if t < 1.0 else 0.1e6,  # Decay heat
        )

        moderator = ThermalLump(
            name="moderator",
            capacitance=5e8,
            temperature=800.0,
            heat_source=lambda t: 0.0,
        )

        resistance = ThermalResistance(
            name="fuel_to_moderator",
            resistance=1e-6,
            lump1_name="fuel",
            lump2_name="moderator",
        )

        solver = LumpedThermalHydraulics(
            lumps={"fuel": fuel, "moderator": moderator},
            resistances=[resistance],
        )

        result = solver.solve_transient(
            t_span=(0.0, 10.0),
            max_step=1.0,
            adaptive=False,  # Fixed steps for testing
        )

        assert "time" in result
        assert "T_fuel" in result
        assert "T_moderator" in result
        assert "Q_fuel" in result
        assert "Q_moderator" in result

        assert len(result["time"]) > 0
        assert len(result["T_fuel"]) == len(result["time"])
        assert len(result["T_moderator"]) == len(result["time"])

        # Check that temperatures are physical
        assert np.all(result["T_fuel"] > 0)
        assert np.all(result["T_moderator"] > 0)

    def test_solve_transient_adaptive(self):
        """Test solving transient with adaptive stepping."""
        from smrforge.thermal.lumped import (
            LumpedThermalHydraulics,
            ThermalLump,
            ThermalResistance,
        )

        fuel = ThermalLump(
            name="fuel",
            capacitance=1e8,
            temperature=1200.0,
            heat_source=lambda t: 1e6,
        )

        moderator = ThermalLump(
            name="moderator",
            capacitance=5e8,
            temperature=800.0,
            heat_source=lambda t: 0.0,
        )

        resistance = ThermalResistance(
            name="fuel_to_moderator",
            resistance=1e-6,
            lump1_name="fuel",
            lump2_name="moderator",
        )

        solver = LumpedThermalHydraulics(
            lumps={"fuel": fuel, "moderator": moderator},
            resistances=[resistance],
        )

        result = solver.solve_transient(
            t_span=(0.0, 100.0),
            max_step=10.0,
            adaptive=True,
        )

        assert "time" in result
        assert len(result["time"]) > 0

    def test_solve_transient_long_term(self):
        """Test solving long-term transient."""
        from smrforge.thermal.lumped import (
            LumpedThermalHydraulics,
            ThermalLump,
            ThermalResistance,
        )

        fuel = ThermalLump(
            name="fuel",
            capacitance=1e8,
            temperature=1200.0,
            heat_source=lambda t: 1e6 * np.exp(-t / 3600.0),  # Exponential decay
        )

        moderator = ThermalLump(
            name="moderator",
            capacitance=5e8,
            temperature=800.0,
            heat_source=lambda t: 0.0,
        )

        resistance = ThermalResistance(
            name="fuel_to_moderator",
            resistance=1e-6,
            lump1_name="fuel",
            lump2_name="moderator",
        )

        solver = LumpedThermalHydraulics(
            lumps={"fuel": fuel, "moderator": moderator},
            resistances=[resistance],
        )

        # 72-hour transient
        result = solver.solve_transient(
            t_span=(0.0, 72 * 3600),
            max_step=3600.0,  # 1 hour steps
            adaptive=True,
        )

        assert len(result["time"]) > 0
        assert result["time"][-1] >= 72 * 3600 - 3600.0  # Should reach near end
