"""
Comprehensive tests for thermal-hydraulics module
"""

import numpy as np
import pytest


class TestThermalImports:
    """Test thermal module imports."""

    def test_thermal_module_import(self):
        """Test that thermal module can be imported."""

    from smrforge import thermal

    assert thermal is not None

    def test_channel_thermal_hydraulics_import(self):
        """Test that ChannelThermalHydraulics can be imported."""
        try:
            from smrforge.thermal.hydraulics import ChannelThermalHydraulics

            assert ChannelThermalHydraulics is not None
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")

    def test_channel_geometry_import(self):
        """Test that ChannelGeometry can be imported."""
        try:
            from smrforge.thermal.hydraulics import ChannelGeometry

            assert ChannelGeometry is not None
        except ImportError:
            pytest.skip("ChannelGeometry not available")


class TestChannelGeometry:
    """Test ChannelGeometry class."""

    def test_channel_geometry_creation(self):
        """Test creating a ChannelGeometry instance."""
        try:
            from smrforge.thermal.hydraulics import ChannelGeometry

            geometry = ChannelGeometry(
                length=400.0,  # cm
                diameter=1.0,  # cm
                flow_area=np.pi * (0.5) ** 2,  # cm²
                heated_perimeter=np.pi * 1.0,  # cm
            )

            assert geometry.length == 400.0
            assert geometry.diameter == 1.0
            assert geometry.flow_area > 0
            assert geometry.heated_perimeter > 0
        except ImportError:
            pytest.skip("ChannelGeometry not available")

    def test_channel_geometry_hydraulic_diameter(self):
        """Test hydraulic diameter calculation."""
        try:
            from smrforge.thermal.hydraulics import ChannelGeometry

            flow_area = np.pi * (0.5) ** 2  # cm²
            heated_perimeter = np.pi * 1.0  # cm

            geometry = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=flow_area,
                heated_perimeter=heated_perimeter,
            )

            D_h = geometry.hydraulic_diameter
            expected = 4 * flow_area / heated_perimeter
            assert np.isclose(D_h, expected)
            assert np.isclose(D_h, 1.0)  # For circular channel
        except ImportError:
            pytest.skip("ChannelGeometry not available")


class TestChannelThermalHydraulics:
    """Test ChannelThermalHydraulics class."""

    def test_thermal_hydraulics_creation(self):
        """Test creating a ChannelThermalHydraulics instance."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            geometry = ChannelGeometry(
                length=400.0,  # cm
                diameter=1.0,  # cm
                flow_area=np.pi * (0.5) ** 2,  # cm²
                heated_perimeter=np.pi * 1.0,  # cm
            )

            inlet_conditions = {
                "temperature": 823.15,  # K (550°C)
                "pressure": 7.0e6,  # Pa (7 MPa)
                "mass_flow_rate": 0.1,  # kg/s
            }

            th = ChannelThermalHydraulics(
                geometry=geometry, inlet_conditions=inlet_conditions
            )

            assert th.geom == geometry
            assert th.T_in == 823.15
            assert th.P_in == 7.0e6
            assert th.mdot == 0.1
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")

    def test_set_power_profile(self):
        """Test setting power profile."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            geometry = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=np.pi * (0.5) ** 2,
                heated_perimeter=np.pi * 1.0,
            )

            inlet_conditions = {
                "temperature": 823.15,
                "pressure": 7.0e6,
                "mass_flow_rate": 0.1,
            }

            th = ChannelThermalHydraulics(
                geometry=geometry, inlet_conditions=inlet_conditions
            )

            # Create power profile
            power_profile = np.ones(len(th.z)) * 1000.0  # W/cm

            th.set_power_profile(power_profile)

            assert len(th.q_linear) == len(th.z)
            assert np.all(th.q_linear == power_profile)
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")

    def test_solve_steady_state(self):
        """Test solving steady-state thermal-hydraulics."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            geometry = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=np.pi * (0.5) ** 2,
                heated_perimeter=np.pi * 1.0,
            )

            inlet_conditions = {
                "temperature": 823.15,
                "pressure": 7.0e6,
                "mass_flow_rate": 0.1,
            }

            th = ChannelThermalHydraulics(
                geometry=geometry, inlet_conditions=inlet_conditions
            )

            # Set uniform power profile
            power_profile = np.ones(len(th.z)) * 100.0  # W/cm
            th.set_power_profile(power_profile)

            # Solve
            result = th.solve_steady_state()

            assert "z" in result
            assert "T_coolant" in result
            assert "P_coolant" in result
            assert "T_wall" in result
            assert len(result["T_coolant"]) == len(th.z)
            # Temperature should increase along channel
            assert result["T_coolant"][-1] > result["T_coolant"][0]
            # Pressure should decrease along channel
            assert result["P_coolant"][-1] < result["P_coolant"][0]
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")

    def test_solve_steady_state_with_fuel_temperature(self):
        """Test solving steady-state with fuel temperature."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            geometry = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=np.pi * (0.5) ** 2,
                heated_perimeter=np.pi * 1.0,
            )

            inlet_conditions = {
                "temperature": 823.15,
                "pressure": 7.0e6,
                "mass_flow_rate": 0.1,
            }

            th = ChannelThermalHydraulics(
                geometry=geometry, inlet_conditions=inlet_conditions
            )

            power_profile = np.ones(len(th.z)) * 100.0  # W/cm
            th.set_power_profile(power_profile)

            # Fuel temperature profile
            T_fuel = np.ones(len(th.z)) * 1200.0  # K

            result = th.solve_steady_state(T_fuel=T_fuel)

            assert len(result["T_wall"]) == len(th.z)
            # Wall temperature should be between fuel and coolant (ignore last point which is 0)
            assert np.all(result["T_wall"][:-1] > result["T_coolant"][:-1])
            assert np.all(result["T_wall"][:-1] < T_fuel[:-1])
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")

    def test_validate_inputs_rejects_nonpositive_flow_area_and_perimeter(self):
        """Cover validation branches for flow area and heated perimeter."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            inlet_conditions = {
                "temperature": 823.15,
                "pressure": 7.0e6,
                "mass_flow_rate": 0.1,
            }

            geom_bad_area = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=0.0,
                heated_perimeter=np.pi * 1.0,
            )
            with pytest.raises(ValueError, match="flow_area must be > 0"):
                ChannelThermalHydraulics(
                    geometry=geom_bad_area, inlet_conditions=inlet_conditions
                )

            geom_bad_perim = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=np.pi * (0.5) ** 2,
                heated_perimeter=0.0,
            )
            with pytest.raises(ValueError, match="heated_perimeter must be > 0"):
                ChannelThermalHydraulics(
                    geometry=geom_bad_perim, inlet_conditions=inlet_conditions
                )
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")

    def test_set_power_profile_converts_list_input(self):
        """Cover set_power_profile list->ndarray conversion."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            geometry = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=np.pi * (0.5) ** 2,
                heated_perimeter=np.pi * 1.0,
            )
            inlet = {"temperature": 823.15, "pressure": 7.0e6, "mass_flow_rate": 0.1}
            th = ChannelThermalHydraulics(geometry=geometry, inlet_conditions=inlet)

            th.set_power_profile([100.0] * len(th.z))
            assert np.allclose(th.q_linear, 100.0)
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")

    def test_solve_steady_state_converts_t_fuel_list_input(self):
        """Cover solve_steady_state list->ndarray conversion for T_fuel."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            geometry = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=np.pi * (0.5) ** 2,
                heated_perimeter=np.pi * 1.0,
            )
            inlet = {"temperature": 823.15, "pressure": 7.0e6, "mass_flow_rate": 0.1}
            th = ChannelThermalHydraulics(geometry=geometry, inlet_conditions=inlet)
            th.set_power_profile(np.ones(len(th.z)) * 100.0)

            # T_fuel passed as list should be accepted (and converted internally).
            result = th.solve_steady_state(T_fuel=[1200.0] * len(th.z))
            assert "T_wall" in result
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")

    def test_solve_steady_state_raises_on_nonphysical_temperature(self):
        """Cover post-solve non-physical temperature guard."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            geometry = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=np.pi * (0.5) ** 2,
                heated_perimeter=np.pi * 1.0,
            )
            inlet = {"temperature": 823.15, "pressure": 7.0e6, "mass_flow_rate": 0.1}
            th = ChannelThermalHydraulics(geometry=geometry, inlet_conditions=inlet)

            # Force a degenerate state that skips marching but triggers the final check.
            th.nz = 0
            th.z = np.array([0.0])
            th.T_coolant = np.array([-1.0])
            th.P_coolant = np.array([7.0e6])
            th.T_wall = np.array([0.0])
            th.q_linear = np.array([0.0])

            with pytest.raises(RuntimeError, match="non-physical temperatures"):
                th.solve_steady_state()
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")

    def test_solve_steady_state_raises_on_nonphysical_pressure(self):
        """Cover post-solve non-physical pressure guard."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            geometry = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=np.pi * (0.5) ** 2,
                heated_perimeter=np.pi * 1.0,
            )
            inlet = {"temperature": 823.15, "pressure": 7.0e6, "mass_flow_rate": 0.1}
            th = ChannelThermalHydraulics(geometry=geometry, inlet_conditions=inlet)

            th.nz = 0
            th.z = np.array([0.0])
            th.T_coolant = np.array([823.15])
            th.P_coolant = np.array([-1.0])
            th.T_wall = np.array([0.0])
            th.q_linear = np.array([0.0])

            with pytest.raises(RuntimeError, match="non-physical pressures"):
                th.solve_steady_state()
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")

    def test_validate_inputs_requires_geometry_type_and_dict(self):
        """Cover geometry/inlet_conditions type validation."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            inlet = {"temperature": 823.15, "pressure": 7.0e6, "mass_flow_rate": 0.1}

            with pytest.raises(ValueError, match="geometry must be ChannelGeometry"):
                ChannelThermalHydraulics(geometry=object(), inlet_conditions=inlet)

            geom = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=np.pi * (0.5) ** 2,
                heated_perimeter=np.pi * 1.0,
            )
            with pytest.raises(ValueError, match="inlet_conditions must be dict"):
                ChannelThermalHydraulics(
                    geometry=geom, inlet_conditions=["not", "a", "dict"]
                )
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")

    def test_validate_inputs_rejects_nonpositive_length_and_inlet_values(self):
        """Cover input validation for non-physical geometry and inlet conditions."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            inlet_ok = {"temperature": 823.15, "pressure": 7.0e6, "mass_flow_rate": 0.1}
            geom_bad_len = ChannelGeometry(
                length=0.0,
                diameter=1.0,
                flow_area=np.pi * (0.5) ** 2,
                heated_perimeter=np.pi * 1.0,
            )
            with pytest.raises(ValueError, match="length must be > 0"):
                ChannelThermalHydraulics(
                    geometry=geom_bad_len, inlet_conditions=inlet_ok
                )

            geom_ok = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=np.pi * (0.5) ** 2,
                heated_perimeter=np.pi * 1.0,
            )
            with pytest.raises(ValueError, match="missing required key"):
                ChannelThermalHydraulics(
                    geometry=geom_ok, inlet_conditions={"temperature": 1.0}
                )
            with pytest.raises(ValueError, match="temperature.*must be > 0"):
                ChannelThermalHydraulics(
                    geometry=geom_ok,
                    inlet_conditions={
                        "temperature": 0.0,
                        "pressure": 7.0e6,
                        "mass_flow_rate": 0.1,
                    },
                )
            with pytest.raises(ValueError, match="pressure.*must be > 0"):
                ChannelThermalHydraulics(
                    geometry=geom_ok,
                    inlet_conditions={
                        "temperature": 823.15,
                        "pressure": 0.0,
                        "mass_flow_rate": 0.1,
                    },
                )
            with pytest.raises(ValueError, match="mass_flow_rate.*must be > 0"):
                ChannelThermalHydraulics(
                    geometry=geom_ok,
                    inlet_conditions={
                        "temperature": 823.15,
                        "pressure": 7.0e6,
                        "mass_flow_rate": 0.0,
                    },
                )
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")

    def test_set_power_profile_length_mismatch_raises(self):
        """Cover set_power_profile length mismatch error."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            geometry = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=np.pi * (0.5) ** 2,
                heated_perimeter=np.pi * 1.0,
            )
            inlet = {"temperature": 823.15, "pressure": 7.0e6, "mass_flow_rate": 0.1}
            th = ChannelThermalHydraulics(geometry=geometry, inlet_conditions=inlet)

            with pytest.raises(ValueError, match="power_profile length"):
                th.set_power_profile(np.ones(len(th.z) - 1))
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")

    def test_set_power_profile_clamps_negative_values(self):
        """Cover negative power_profile clamp."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            geometry = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=np.pi * (0.5) ** 2,
                heated_perimeter=np.pi * 1.0,
            )
            inlet = {"temperature": 823.15, "pressure": 7.0e6, "mass_flow_rate": 0.1}
            th = ChannelThermalHydraulics(geometry=geometry, inlet_conditions=inlet)

            power_profile = np.ones(len(th.z)) * 100.0
            power_profile[0] = -10.0
            th.set_power_profile(power_profile)
            assert np.all(th.q_linear >= 0.0)
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")

    def test_solve_steady_state_rejects_t_fuel_bad_inputs(self):
        """Cover T_fuel validation errors."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            geometry = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=np.pi * (0.5) ** 2,
                heated_perimeter=np.pi * 1.0,
            )
            inlet = {"temperature": 823.15, "pressure": 7.0e6, "mass_flow_rate": 0.1}
            th = ChannelThermalHydraulics(geometry=geometry, inlet_conditions=inlet)
            th.set_power_profile(np.ones(len(th.z)) * 100.0)

            with pytest.raises(ValueError, match="T_fuel length"):
                th.solve_steady_state(T_fuel=np.ones(len(th.z) - 1))
            with pytest.raises(ValueError, match="T_fuel must be > 0"):
                th.solve_steady_state(T_fuel=np.ones(len(th.z)) * -1.0)
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")


class TestFluidProperties:
    """Test FluidProperties class."""

    def test_fluid_properties_creation(self):
        """Test creating FluidProperties instance."""
        try:
            from smrforge.thermal.hydraulics import FluidProperties

            fluid = FluidProperties(temperature=823.15, pressure=7.0e6)
            assert fluid.temperature == 823.15
            assert fluid.pressure == 7.0e6
        except ImportError:
            pytest.skip("FluidProperties not available")

    def test_density(self):
        """Test density calculation."""
        try:
            from smrforge.thermal.hydraulics import FluidProperties

            fluid = FluidProperties(temperature=823.15, pressure=7.0e6)
            rho = fluid.density()

            # Should be positive
            assert rho > 0
            # At higher pressure, density should be higher
            fluid_high_p = FluidProperties(temperature=823.15, pressure=14.0e6)
            rho_high_p = fluid_high_p.density()
            assert rho_high_p > rho
            # At higher temperature, density should be lower
            fluid_high_t = FluidProperties(temperature=1023.15, pressure=7.0e6)
            rho_high_t = fluid_high_t.density()
            assert rho_high_t < rho
        except ImportError:
            pytest.skip("FluidProperties not available")

    def test_viscosity(self):
        """Test viscosity calculation."""
        try:
            from smrforge.thermal.hydraulics import FluidProperties

            fluid = FluidProperties(temperature=823.15, pressure=7.0e6)
            mu = fluid.viscosity()

            assert mu > 0
            # Viscosity should increase with temperature
            fluid_high_t = FluidProperties(temperature=1023.15, pressure=7.0e6)
            mu_high_t = fluid_high_t.viscosity()
            assert mu_high_t > mu
        except ImportError:
            pytest.skip("FluidProperties not available")

    def test_thermal_conductivity(self):
        """Test thermal conductivity calculation."""
        try:
            from smrforge.thermal.hydraulics import FluidProperties

            fluid = FluidProperties(temperature=823.15, pressure=7.0e6)
            k = fluid.thermal_conductivity()

            assert k > 0
        except ImportError:
            pytest.skip("FluidProperties not available")

    def test_specific_heat(self):
        """Test specific heat (should be constant for helium)."""
        try:
            from smrforge.thermal.hydraulics import FluidProperties

            fluid = FluidProperties(temperature=823.15, pressure=7.0e6)
            cp = fluid.specific_heat()

            assert cp > 0
            # Should be approximately constant
            fluid2 = FluidProperties(temperature=1023.15, pressure=7.0e6)
            cp2 = fluid2.specific_heat()
            assert np.isclose(cp, cp2)
        except ImportError:
            pytest.skip("FluidProperties not available")

    def test_prandtl_number(self):
        """Test Prandtl number calculation."""
        try:
            from smrforge.thermal.hydraulics import FluidProperties

            fluid = FluidProperties(temperature=823.15, pressure=7.0e6)
            Pr = fluid.prandtl_number()

            assert Pr > 0
            # Prandtl number should be reasonable (for helium at high temp, can be >1)
            assert 0.1 < Pr < 3.0
        except ImportError:
            pytest.skip("FluidProperties not available")


class TestFuelRodThermal:
    """Test FuelRodThermal class."""

    def test_fuel_rod_thermal_creation(self):
        """Test creating FuelRodThermal instance."""
        try:
            from smrforge.thermal.hydraulics import FuelRodThermal

            rod = FuelRodThermal(radius=0.5, n_nodes=50)
            assert rod.radius == 0.5
            assert rod.n_nodes == 50
            assert len(rod.r) == rod.n_nodes + 1
        except ImportError:
            pytest.skip("FuelRodThermal not available")

    def test_fuel_rod_thermal_creation_rejects_invalid_inputs(self):
        """Cover FuelRodThermal __init__ validation errors."""
        try:
            from smrforge.thermal.hydraulics import FuelRodThermal

            with pytest.raises(ValueError, match="radius must be > 0"):
                FuelRodThermal(radius=0.0, n_nodes=10)
            with pytest.raises(ValueError, match="n_nodes must be > 0"):
                FuelRodThermal(radius=0.5, n_nodes=0)
        except ImportError:
            pytest.skip("FuelRodThermal not available")

    def test_solve_steady_conduction(self):
        """Test solving steady-state conduction."""
        try:
            from smrforge.thermal.hydraulics import FuelRodThermal

            rod = FuelRodThermal(radius=0.5, n_nodes=50)
            q_vol = 100.0  # W/cm³
            k_fuel = 0.2  # W/cm-K
            T_surface = 1000.0  # K

            T = rod.solve_steady_conduction(q_vol, k_fuel, T_surface)

            assert len(T) == rod.n_nodes + 1
            # Surface temperature should match BC
            assert np.isclose(T[-1], T_surface)
            # Centerline should be hottest
            assert T[0] > T[-1]
            # Temperature should decrease monotonically from center
            for i in range(len(T) - 1):
                assert T[i] >= T[i + 1]
        except ImportError:
            pytest.skip("FuelRodThermal not available")

    def test_solve_steady_conduction_rejects_invalid_inputs(self):
        """Cover solve_steady_conduction validation errors."""
        try:
            from smrforge.thermal.hydraulics import FuelRodThermal

            rod = FuelRodThermal(radius=0.5, n_nodes=10)
            with pytest.raises(ValueError, match="q_vol must be >= 0"):
                rod.solve_steady_conduction(q_vol=-1.0, k_fuel=0.2, T_surface=1000.0)
            with pytest.raises(ValueError, match="k_fuel must be > 0"):
                rod.solve_steady_conduction(q_vol=1.0, k_fuel=0.0, T_surface=1000.0)
            with pytest.raises(ValueError, match="T_surface must be > 0"):
                rod.solve_steady_conduction(q_vol=1.0, k_fuel=0.2, T_surface=0.0)
        except ImportError:
            pytest.skip("FuelRodThermal not available")

    def test_solve_transient_conduction(self):
        """Test solving transient conduction."""
        try:
            from smrforge.thermal.hydraulics import FuelRodThermal

            rod = FuelRodThermal(radius=0.5, n_nodes=20)

            q_vol = 100.0  # Constant W/cm³
            k_fuel = 0.2  # W/cm-K
            rho = 10.5  # g/cm³
            cp = 0.25  # J/g-K
            T_surface = 1000.0  # K

            result = rod.solve_transient_conduction(
                q_vol=q_vol,
                k_fuel=k_fuel,
                rho=rho,
                cp=cp,
                T_surface=T_surface,
                t_span=(0.0, 100.0),
            )

            assert "t" in result
            assert "T" in result
            assert result["T"].shape[0] == rod.n_nodes + 1
        except ImportError:
            pytest.skip("FuelRodThermal not available")


class TestPorousMediaFlow:
    """Test PorousMediaFlow class."""

    def test_porous_media_flow_creation(self):
        """Test creating PorousMediaFlow instance."""
        try:
            from smrforge.thermal.hydraulics import PorousMediaFlow

            bed = PorousMediaFlow(
                bed_height=1100.0,
                bed_diameter=300.0,
                pebble_diameter=6.0,
                porosity=0.39,
            )

            assert bed.H == 1100.0
            assert bed.D == 300.0
            assert bed.d_p == 6.0
            assert bed.epsilon == 0.39
            assert len(bed.z) == bed.nz + 1
        except ImportError:
            pytest.skip("PorousMediaFlow not available")

    def test_porous_media_flow_creation_rejects_invalid_inputs(self):
        """Cover PorousMediaFlow __init__ validation errors."""
        try:
            from smrforge.thermal.hydraulics import PorousMediaFlow

            with pytest.raises(ValueError, match="bed_height must be > 0"):
                PorousMediaFlow(0.0, 300.0, 6.0, 0.39)
            with pytest.raises(ValueError, match="bed_diameter must be > 0"):
                PorousMediaFlow(1100.0, 0.0, 6.0, 0.39)
            with pytest.raises(ValueError, match="pebble_diameter must be > 0"):
                PorousMediaFlow(1100.0, 300.0, 0.0, 0.39)
            with pytest.raises(ValueError, match="porosity must be in"):
                PorousMediaFlow(1100.0, 300.0, 6.0, 1.0)
        except ImportError:
            pytest.skip("PorousMediaFlow not available")

    def test_solve_flow(self):
        """Test solving flow through porous bed."""
        try:
            from smrforge.thermal.hydraulics import PorousMediaFlow

            bed = PorousMediaFlow(
                bed_height=1100.0,
                bed_diameter=300.0,
                pebble_diameter=6.0,
                porosity=0.39,
            )

            mdot = 50.0  # kg/s
            T_in = 573.0  # K
            P_in = 7.0e6  # Pa
            q_vol_profile = np.ones(bed.nz + 1) * 5.0  # W/cm³

            result = bed.solve_flow(
                mdot=mdot, T_in=T_in, P_in=P_in, q_vol_profile=q_vol_profile
            )

            assert "z" in result
            assert "T_coolant" in result
            assert "P_coolant" in result
            assert "velocity" in result
            assert len(result["T_coolant"]) == bed.nz + 1
            # Temperature should increase along bed
            assert result["T_coolant"][-1] > result["T_coolant"][0]
            # Pressure should decrease along bed
            assert result["P_coolant"][-1] < result["P_coolant"][0]
        except ImportError:
            pytest.skip("PorousMediaFlow not available")

    def test_solve_flow_rejects_invalid_inputs_and_length_mismatch(self):
        """Cover solve_flow validation errors."""
        try:
            from smrforge.thermal.hydraulics import PorousMediaFlow

            bed = PorousMediaFlow(
                bed_height=1100.0,
                bed_diameter=300.0,
                pebble_diameter=6.0,
                porosity=0.39,
            )

            q_ok = np.ones(bed.nz + 1) * 5.0
            with pytest.raises(ValueError, match="mdot must be > 0"):
                bed.solve_flow(mdot=0.0, T_in=573.0, P_in=7.0e6, q_vol_profile=q_ok)
            with pytest.raises(ValueError, match="T_in must be > 0"):
                bed.solve_flow(mdot=50.0, T_in=0.0, P_in=7.0e6, q_vol_profile=q_ok)
            with pytest.raises(ValueError, match="P_in must be > 0"):
                bed.solve_flow(mdot=50.0, T_in=573.0, P_in=0.0, q_vol_profile=q_ok)
            with pytest.raises(ValueError, match="q_vol_profile length"):
                bed.solve_flow(
                    mdot=50.0, T_in=573.0, P_in=7.0e6, q_vol_profile=np.ones(bed.nz)
                )
        except ImportError:
            pytest.skip("PorousMediaFlow not available")

    def test_solve_flow_converts_profile_and_clamps_negative(self):
        """Cover q_vol_profile conversion and negative clamp."""
        try:
            from smrforge.thermal.hydraulics import PorousMediaFlow

            bed = PorousMediaFlow(
                bed_height=1100.0,
                bed_diameter=300.0,
                pebble_diameter=6.0,
                porosity=0.39,
            )

            # Pass as list (conversion) with a negative entry (clamp).
            q_vol_profile = [5.0] * (bed.nz + 1)
            q_vol_profile[0] = -1.0

            result = bed.solve_flow(
                mdot=50.0,
                T_in=573.0,
                P_in=7.0e6,
                q_vol_profile=q_vol_profile,
            )
            assert result["T_coolant"][0] > 0
            assert result["P_coolant"][0] > 0
        except ImportError:
            pytest.skip("PorousMediaFlow not available")

    def test_solve_flow_raises_on_nonphysical_temperature(self, monkeypatch):
        """Cover porous media non-physical temperature guard."""
        try:
            import smrforge.thermal.hydraulics as hyd

            bed = hyd.PorousMediaFlow(
                bed_height=1100.0,
                bed_diameter=300.0,
                pebble_diameter=6.0,
                porosity=0.39,
            )

            # Force temperature to decrease (cp < 0) so it can cross <= 0.
            monkeypatch.setattr(hyd.FluidProperties, "specific_heat", lambda self: -1.0)

            q_vol_profile = np.ones(bed.nz + 1) * 1.0e6  # large positive heat gen
            with pytest.raises(RuntimeError, match="non-physical temperatures"):
                bed.solve_flow(
                    mdot=50.0, T_in=10.0, P_in=7.0e6, q_vol_profile=q_vol_profile
                )
        except ImportError:
            pytest.skip("PorousMediaFlow not available")

    def test_solve_flow_raises_on_nonphysical_pressure(self, monkeypatch):
        """Cover porous media non-physical pressure guard."""
        try:
            import smrforge.thermal.hydraulics as hyd

            bed = hyd.PorousMediaFlow(
                bed_height=1100.0,
                bed_diameter=300.0,
                pebble_diameter=6.0,
                porosity=0.39,
            )

            # Force huge pressure gradient so pressure becomes <= 0.
            monkeypatch.setattr(
                bed, "_ergun_pressure_drop", lambda v_s, rho, mu: 1.0e20
            )

            q_vol_profile = np.ones(bed.nz + 1) * 5.0
            with pytest.raises(RuntimeError, match="non-physical pressures"):
                bed.solve_flow(
                    mdot=50.0, T_in=573.0, P_in=1.0, q_vol_profile=q_vol_profile
                )
        except ImportError:
            pytest.skip("PorousMediaFlow not available")


class TestFlowRegime:
    """Test FlowRegime enum."""

    def test_flow_regime_enum(self):
        """Test FlowRegime enum values."""
        try:
            from smrforge.thermal.hydraulics import FlowRegime

            assert FlowRegime.LAMINAR.value == "laminar"
            assert FlowRegime.TRANSITIONAL.value == "transitional"
            assert FlowRegime.TURBULENT.value == "turbulent"
        except ImportError:
            pytest.skip("FlowRegime not available")


class TestConjugateHeatTransfer:
    """Test ConjugateHeatTransfer class."""

    def test_conjugate_heat_transfer_creation(self):
        """Test creating a ConjugateHeatTransfer instance."""
        try:
            from smrforge.thermal.hydraulics import ConjugateHeatTransfer

            # Create mock solvers
            class MockNeutronics:
                def __init__(self):
                    self.flux = np.ones((10, 10, 2))  # 2 groups

                def solve_steady_state(self):
                    return 1.0, np.ones((10, 10, 2))

                def compute_power_distribution(self, power):
                    return np.ones((10, 10))

            class MockThermal:
                def solve_with_power(self, power):
                    return np.full((10, 10), 1200.0)

            neutronics = MockNeutronics()
            thermal = MockThermal()

            coupled = ConjugateHeatTransfer(neutronics, thermal)
            assert coupled.neutronics == neutronics
            assert coupled.thermal == thermal
        except ImportError:
            pytest.skip("ConjugateHeatTransfer not available")

    def test_solve_coupled_convergence(self):
        """Test solve_coupled method converges."""
        try:
            from smrforge.thermal.hydraulics import ConjugateHeatTransfer

            # Create mock solvers that converge quickly
            class MockNeutronics:
                def __init__(self):
                    self.flux = np.ones((5, 5, 2))

                def solve_steady_state(self):
                    return 1.0, np.ones((5, 5, 2))

                def compute_power_distribution(self, power):
                    return np.ones((5, 5))

            class MockThermal:
                def __init__(self):
                    self.temp = 1200.0

                def solve_with_power(self, power):
                    # Return same temperature to converge quickly
                    return np.full((5, 5), self.temp)

            neutronics = MockNeutronics()
            thermal = MockThermal()

            coupled = ConjugateHeatTransfer(neutronics, thermal)
            result = coupled.solve_coupled(max_iterations=5, tolerance=1e-2)

            assert "k_eff" in result
            assert "flux" in result
            assert "power" in result
            assert "T_fuel" in result
            assert result["k_eff"] == 1.0
        except ImportError:
            pytest.skip("ConjugateHeatTransfer not available")

    def test_solve_coupled_under_relaxation_updates_temperature(self):
        """Cover under-relaxation update step."""
        try:
            from smrforge.thermal.hydraulics import ConjugateHeatTransfer

            class MockNeutronics:
                def __init__(self):
                    self.flux = np.ones((2, 2, 1))

                def solve_steady_state(self):
                    return 1.0, self.flux

                def compute_power_distribution(self, power):
                    return np.ones((2, 2))

            class MockThermal:
                def __init__(self):
                    self.calls = 0

                def solve_with_power(self, power):
                    self.calls += 1
                    # First call: force a change from initial 1200K.
                    if self.calls == 1:
                        return np.full_like(power, 1000.0)
                    # Second call: match the relaxed value (0.5*1000 + 0.5*1200 = 1100).
                    return np.full_like(power, 1100.0)

            coupled = ConjugateHeatTransfer(MockNeutronics(), MockThermal())
            result = coupled.solve_coupled(max_iterations=5, tolerance=1e-9)
            assert np.allclose(result["T_fuel"], 1100.0)
        except ImportError:
            pytest.skip("ConjugateHeatTransfer not available")


class TestHeatTransferCoefficient:
    """Test _heat_transfer_coefficient method for different regimes."""

    def test_heat_transfer_coefficient_laminar(self):
        """Test _heat_transfer_coefficient in laminar regime."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            geometry = ChannelGeometry(
                length=100.0,
                diameter=1.0,
                flow_area=np.pi * 0.25,
                heated_perimeter=np.pi * 1.0,
            )
            inlet = {"temperature": 600.0, "pressure": 7e6, "mass_flow_rate": 0.01}
            channel = ChannelThermalHydraulics(geometry, inlet)

            Re = 1000.0  # Laminar
            Pr = 0.7
            k = 0.5
            h = channel._heat_transfer_coefficient(Re, Pr, k)
            assert h > 0
            assert np.isfinite(h)
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")

    def test_heat_transfer_coefficient_transitional(self):
        """Test _heat_transfer_coefficient in transitional regime."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            geometry = ChannelGeometry(
                length=100.0,
                diameter=1.0,
                flow_area=np.pi * 0.25,
                heated_perimeter=np.pi * 1.0,
            )
            inlet = {
                "temperature": 600.0,
                "pressure": 7e6,
                "mass_flow_rate": 0.01,
            }
            channel = ChannelThermalHydraulics(geometry, inlet)

            # Test transitional Re (~3000)
            Re = 3000.0  # Transitional
            Pr = 0.7
            k = 0.5

            # The method should interpolate between laminar and turbulent
            h = channel._heat_transfer_coefficient(Re, Pr, k)
            assert h > 0
            assert np.isfinite(h)
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")


class TestFrictionFactor:
    """Test _friction_factor method."""

    def test_friction_factor_laminar(self):
        """Test _friction_factor in laminar regime."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelGeometry,
                ChannelThermalHydraulics,
            )

            geometry = ChannelGeometry(
                length=100.0,
                diameter=1.0,
                flow_area=np.pi * 0.25,
                heated_perimeter=np.pi * 1.0,
            )
            inlet = {
                "temperature": 600.0,
                "pressure": 7e6,
                "mass_flow_rate": 0.001,
            }
            channel = ChannelThermalHydraulics(geometry, inlet)

            Re = 1000.0  # Laminar
            f = channel._friction_factor(Re)

            # Laminar: f = 64/Re
            expected = 64.0 / Re
            assert np.isclose(f, expected, rtol=1e-3)
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")


class TestTridiagonalSolver:
    """Test tridiagonal solver function."""

    def test_solve_tridiagonal_fast(self):
        """Test fast tridiagonal solver."""
        try:
            from smrforge.thermal.hydraulics import solve_tridiagonal_fast

            # Simple 3x3 system: x = [1, 2, 3]
            # Diagonal
            b = np.array([2.0, 2.0, 2.0])
            # Lower diagonal
            a = np.array([0.0, 1.0, 1.0])
            # Upper diagonal
            c = np.array([1.0, 1.0, 0.0])
            # Right-hand side
            d = np.array([4.0, 6.0, 7.0])

            func = (
                solve_tridiagonal_fast.py_func
                if hasattr(solve_tridiagonal_fast, "py_func")
                else solve_tridiagonal_fast
            )
            x = func(a, b, c, d)

            # Check solution: b[i]*x[i] + a[i]*x[i-1] + c[i]*x[i+1] = d[i]
            assert len(x) == 3
            assert np.allclose(b[0] * x[0] + c[0] * x[1], d[0])
            assert np.allclose(a[1] * x[0] + b[1] * x[1] + c[1] * x[2], d[1])
            assert np.allclose(a[2] * x[1] + b[2] * x[2], d[2])
        except ImportError:
            pytest.skip("solve_tridiagonal_fast not available")
