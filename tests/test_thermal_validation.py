"""
Validation and error handling tests for thermal-hydraulics module.
"""

import numpy as np
import pytest


@pytest.fixture
def simple_geometry():
    """Create a simple channel geometry for testing."""
    from smrforge.thermal.hydraulics import ChannelGeometry

    return ChannelGeometry(
        length=400.0,  # cm
        diameter=1.0,  # cm
        flow_area=np.pi * (0.5) ** 2,  # cm²
        heated_perimeter=np.pi * 1.0,  # cm
    )


@pytest.fixture
def simple_inlet_conditions():
    """Create simple inlet conditions for testing."""
    return {
        "temperature": 823.15,  # K
        "pressure": 7.0e6,  # Pa
        "mass_flow_rate": 0.1,  # kg/s
    }


class TestChannelThermalHydraulicsValidation:
    """Test input validation for ChannelThermalHydraulics."""

    def test_invalid_geometry_type(self, simple_inlet_conditions):
        """Test that invalid geometry type raises ValueError."""
        from smrforge.thermal.hydraulics import ChannelThermalHydraulics

        with pytest.raises(ValueError, match="geometry must be ChannelGeometry"):
            ChannelThermalHydraulics(
                geometry="invalid", inlet_conditions=simple_inlet_conditions
            )

    def test_invalid_inlet_conditions_type(self, simple_geometry):
        """Test that invalid inlet_conditions type raises ValueError."""
        from smrforge.thermal.hydraulics import ChannelThermalHydraulics

        with pytest.raises(ValueError, match="inlet_conditions must be dict"):
            ChannelThermalHydraulics(
                geometry=simple_geometry, inlet_conditions="invalid"
            )

    def test_missing_inlet_key(self, simple_geometry):
        """Test that missing inlet condition key raises ValueError."""
        from smrforge.thermal.hydraulics import ChannelThermalHydraulics

        incomplete = {
            "temperature": 823.15,
            "pressure": 7.0e6,
        }  # Missing mass_flow_rate
        with pytest.raises(ValueError, match="missing required key"):
            ChannelThermalHydraulics(
                geometry=simple_geometry, inlet_conditions=incomplete
            )

    def test_invalid_temperature(self, simple_geometry):
        """Test that invalid temperature raises ValueError."""
        from smrforge.thermal.hydraulics import ChannelThermalHydraulics

        invalid = {
            "temperature": -100.0,  # Negative
            "pressure": 7.0e6,
            "mass_flow_rate": 0.1,
        }
        with pytest.raises(ValueError, match="temperature.*must be > 0"):
            ChannelThermalHydraulics(geometry=simple_geometry, inlet_conditions=invalid)

    def test_invalid_pressure(self, simple_geometry):
        """Test that invalid pressure raises ValueError."""
        from smrforge.thermal.hydraulics import ChannelThermalHydraulics

        invalid = {
            "temperature": 823.15,
            "pressure": -100.0,  # Negative
            "mass_flow_rate": 0.1,
        }
        with pytest.raises(ValueError, match="pressure.*must be > 0"):
            ChannelThermalHydraulics(geometry=simple_geometry, inlet_conditions=invalid)

    def test_invalid_mass_flow_rate(self, simple_geometry):
        """Test that invalid mass flow rate raises ValueError."""
        from smrforge.thermal.hydraulics import ChannelThermalHydraulics

        invalid = {
            "temperature": 823.15,
            "pressure": 7.0e6,
            "mass_flow_rate": -0.1,  # Negative
        }
        with pytest.raises(ValueError, match="mass_flow_rate.*must be > 0"):
            ChannelThermalHydraulics(geometry=simple_geometry, inlet_conditions=invalid)

    def test_invalid_geometry_length(self, simple_inlet_conditions):
        """Test that invalid geometry length raises ValueError."""
        from smrforge.thermal.hydraulics import (
            ChannelGeometry,
            ChannelThermalHydraulics,
        )

        invalid_geom = ChannelGeometry(
            length=-100.0,  # Negative
            diameter=1.0,
            flow_area=np.pi * 0.25,
            heated_perimeter=np.pi * 1.0,
        )
        with pytest.raises(ValueError, match="length.*must be > 0"):
            ChannelThermalHydraulics(
                geometry=invalid_geom, inlet_conditions=simple_inlet_conditions
            )

    def test_invalid_power_profile_length(
        self, simple_geometry, simple_inlet_conditions
    ):
        """Test that incorrect power profile length raises ValueError."""
        from smrforge.thermal.hydraulics import ChannelThermalHydraulics

        th = ChannelThermalHydraulics(
            geometry=simple_geometry, inlet_conditions=simple_inlet_conditions
        )

        wrong_length = np.ones(50)  # Wrong length
        with pytest.raises(ValueError, match="power_profile length.*!= z length"):
            th.set_power_profile(wrong_length)

    def test_negative_power_profile(self, simple_geometry, simple_inlet_conditions):
        """Test that negative power profile values are handled."""
        from smrforge.thermal.hydraulics import ChannelThermalHydraulics

        th = ChannelThermalHydraulics(
            geometry=simple_geometry, inlet_conditions=simple_inlet_conditions
        )

        # Negative values should be set to zero with warning
        power_profile = np.ones(len(th.z)) * 100.0
        power_profile[10:20] = -50.0  # Some negative values

        # Should not raise error, just warn
        th.set_power_profile(power_profile)
        assert np.all(th.q_linear >= 0)

    def test_invalid_t_fuel_length(self, simple_geometry, simple_inlet_conditions):
        """Test that incorrect T_fuel length raises ValueError."""
        from smrforge.thermal.hydraulics import ChannelThermalHydraulics

        th = ChannelThermalHydraulics(
            geometry=simple_geometry, inlet_conditions=simple_inlet_conditions
        )
        th.set_power_profile(np.ones(len(th.z)) * 100.0)

        wrong_length = np.ones(50) * 1200.0  # Wrong length
        with pytest.raises(ValueError, match="T_fuel length.*!= z length"):
            th.solve_steady_state(T_fuel=wrong_length)

    def test_invalid_t_fuel_negative(self, simple_geometry, simple_inlet_conditions):
        """Test that negative T_fuel raises ValueError."""
        from smrforge.thermal.hydraulics import ChannelThermalHydraulics

        th = ChannelThermalHydraulics(
            geometry=simple_geometry, inlet_conditions=simple_inlet_conditions
        )
        th.set_power_profile(np.ones(len(th.z)) * 100.0)

        invalid_t_fuel = np.ones(len(th.z)) * 1200.0
        invalid_t_fuel[10] = -100.0  # One negative value
        with pytest.raises(ValueError, match="T_fuel must be > 0"):
            th.solve_steady_state(T_fuel=invalid_t_fuel)


class TestFuelRodThermalValidation:
    """Test input validation for FuelRodThermal."""

    def test_invalid_radius(self):
        """Test that invalid radius raises ValueError."""
        from smrforge.thermal.hydraulics import FuelRodThermal

        with pytest.raises(ValueError, match="radius must be > 0"):
            FuelRodThermal(radius=-0.5)

    def test_invalid_n_nodes(self):
        """Test that invalid n_nodes raises ValueError."""
        from smrforge.thermal.hydraulics import FuelRodThermal

        with pytest.raises(ValueError, match="n_nodes must be > 0"):
            FuelRodThermal(radius=0.5, n_nodes=-10)

    def test_invalid_q_vol(self):
        """Test that negative q_vol raises ValueError."""
        from smrforge.thermal.hydraulics import FuelRodThermal

        rod = FuelRodThermal(radius=0.5)
        with pytest.raises(ValueError, match="q_vol must be >= 0"):
            rod.solve_steady_conduction(q_vol=-100.0, k_fuel=0.2, T_surface=1000.0)

    def test_invalid_k_fuel(self):
        """Test that invalid k_fuel raises ValueError."""
        from smrforge.thermal.hydraulics import FuelRodThermal

        rod = FuelRodThermal(radius=0.5)
        with pytest.raises(ValueError, match="k_fuel must be > 0"):
            rod.solve_steady_conduction(q_vol=100.0, k_fuel=-0.2, T_surface=1000.0)

    def test_invalid_t_surface(self):
        """Test that invalid T_surface raises ValueError."""
        from smrforge.thermal.hydraulics import FuelRodThermal

        rod = FuelRodThermal(radius=0.5)
        with pytest.raises(ValueError, match="T_surface must be > 0"):
            rod.solve_steady_conduction(q_vol=100.0, k_fuel=0.2, T_surface=-100.0)


class TestPorousMediaFlowValidation:
    """Test input validation for PorousMediaFlow."""

    def test_invalid_bed_height(self):
        """Test that invalid bed_height raises ValueError."""
        from smrforge.thermal.hydraulics import PorousMediaFlow

        with pytest.raises(ValueError, match="bed_height must be > 0"):
            PorousMediaFlow(
                bed_height=-100.0,
                bed_diameter=300.0,
                pebble_diameter=6.0,
                porosity=0.39,
            )

    def test_invalid_bed_diameter(self):
        """Test that invalid bed_diameter raises ValueError."""
        from smrforge.thermal.hydraulics import PorousMediaFlow

        with pytest.raises(ValueError, match="bed_diameter must be > 0"):
            PorousMediaFlow(
                bed_height=1100.0,
                bed_diameter=-300.0,
                pebble_diameter=6.0,
                porosity=0.39,
            )

    def test_invalid_pebble_diameter(self):
        """Test that invalid pebble_diameter raises ValueError."""
        from smrforge.thermal.hydraulics import PorousMediaFlow

        with pytest.raises(ValueError, match="pebble_diameter must be > 0"):
            PorousMediaFlow(
                bed_height=1100.0,
                bed_diameter=300.0,
                pebble_diameter=-6.0,
                porosity=0.39,
            )

    def test_invalid_porosity_too_low(self):
        """Test that porosity <= 0 raises ValueError."""
        from smrforge.thermal.hydraulics import PorousMediaFlow

        with pytest.raises(ValueError, match="porosity must be in \\(0, 1\\)"):
            PorousMediaFlow(
                bed_height=1100.0,
                bed_diameter=300.0,
                pebble_diameter=6.0,
                porosity=0.0,
            )

    def test_invalid_porosity_too_high(self):
        """Test that porosity >= 1 raises ValueError."""
        from smrforge.thermal.hydraulics import PorousMediaFlow

        with pytest.raises(ValueError, match="porosity must be in \\(0, 1\\)"):
            PorousMediaFlow(
                bed_height=1100.0,
                bed_diameter=300.0,
                pebble_diameter=6.0,
                porosity=1.0,
            )

    def test_invalid_mdot(self):
        """Test that invalid mdot raises ValueError."""
        from smrforge.thermal.hydraulics import PorousMediaFlow

        bed = PorousMediaFlow(
            bed_height=1100.0,
            bed_diameter=300.0,
            pebble_diameter=6.0,
            porosity=0.39,
        )

        with pytest.raises(ValueError, match="mdot must be > 0"):
            bed.solve_flow(
                mdot=-50.0,
                T_in=573.0,
                P_in=7.0e6,
                q_vol_profile=np.ones(bed.nz + 1) * 5.0,
            )

    def test_invalid_t_in(self):
        """Test that invalid T_in raises ValueError."""
        from smrforge.thermal.hydraulics import PorousMediaFlow

        bed = PorousMediaFlow(
            bed_height=1100.0,
            bed_diameter=300.0,
            pebble_diameter=6.0,
            porosity=0.39,
        )

        with pytest.raises(ValueError, match="T_in must be > 0"):
            bed.solve_flow(
                mdot=50.0,
                T_in=-573.0,
                P_in=7.0e6,
                q_vol_profile=np.ones(bed.nz + 1) * 5.0,
            )

    def test_invalid_p_in(self):
        """Test that invalid P_in raises ValueError."""
        from smrforge.thermal.hydraulics import PorousMediaFlow

        bed = PorousMediaFlow(
            bed_height=1100.0,
            bed_diameter=300.0,
            pebble_diameter=6.0,
            porosity=0.39,
        )

        with pytest.raises(ValueError, match="P_in must be > 0"):
            bed.solve_flow(
                mdot=50.0,
                T_in=573.0,
                P_in=-7.0e6,
                q_vol_profile=np.ones(bed.nz + 1) * 5.0,
            )

    def test_invalid_q_vol_profile_length(self):
        """Test that incorrect q_vol_profile length raises ValueError."""
        from smrforge.thermal.hydraulics import PorousMediaFlow

        bed = PorousMediaFlow(
            bed_height=1100.0,
            bed_diameter=300.0,
            pebble_diameter=6.0,
            porosity=0.39,
        )

        wrong_length = np.ones(30)  # Wrong length
        with pytest.raises(ValueError, match="q_vol_profile length.*!= z length"):
            bed.solve_flow(
                mdot=50.0, T_in=573.0, P_in=7.0e6, q_vol_profile=wrong_length
            )
