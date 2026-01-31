"""
Unit tests for advanced two-phase flow models.
"""

import numpy as np
import pytest

from smrforge.thermal.two_phase_advanced import (
    BoilingHeatTransfer,
    DriftFluxModel,
    InterfacialTransferModels,
    TwoFluidModel,
    TwoPhaseThermalHydraulics,
)


class TestDriftFluxModel:
    """Tests for DriftFluxModel class."""

    def test_zuber_findlay_model(self):
        """Test Zuber-Findlay drift-flux model."""
        model = DriftFluxModel(model_type="zuber_findlay")
        
        void_fraction = model.calculate_void_fraction(
            quality=0.5,
            mass_flux=1000.0,  # kg/(m²·s)
            pressure=7e6,  # Pa
            diameter=0.01,  # m
            flow_direction="vertical",
        )
        
        assert 0.0 <= void_fraction <= 1.0
        assert void_fraction > 0.5  # Void fraction > quality (vapor less dense)

    def test_chexal_lellouche_model(self):
        """Test Chexal-Lellouche drift-flux model."""
        model = DriftFluxModel(model_type="chexal_lellouche")
        
        void_fraction = model.calculate_void_fraction(
            quality=0.3,
            mass_flux=1500.0,
            pressure=7e6,
            diameter=0.01,
        )
        
        assert 0.0 <= void_fraction <= 1.0

    def test_ishii_mishima_model(self):
        """Test Ishii-Mishima drift-flux model."""
        model = DriftFluxModel(model_type="ishii_mishima")
        
        void_fraction = model.calculate_void_fraction(
            quality=0.4,
            mass_flux=1200.0,
            pressure=7e6,
            diameter=0.01,
        )
        
        assert 0.0 <= void_fraction <= 1.0

    def test_distribution_parameter(self):
        """Test distribution parameter calculation."""
        model = DriftFluxModel(model_type="chexal_lellouche")
        
        C0 = model._calculate_distribution_parameter(
            quality=0.5,
            mass_flux=1000.0,
            pressure=7e6,
            diameter=0.01,
            flow_direction="vertical",
        )
        
        assert C0 > 1.0  # Should be > 1.0 for vertical flow

    def test_drift_velocity(self):
        """Test drift velocity calculation."""
        model = DriftFluxModel(model_type="zuber_findlay")
        
        Vgj = model._calculate_drift_velocity(
            quality=0.5,
            mass_flux=1000.0,
            pressure=7e6,
            diameter=0.01,
            flow_direction="vertical",
        )
        
        assert Vgj > 0.0  # Should be positive

    def test_void_fraction_quality_bounds_and_zero_mass_flux(self, monkeypatch):
        model = DriftFluxModel(model_type="chexal_lellouche")

        assert model.calculate_void_fraction(quality=0.0, mass_flux=1000.0, pressure=7e6, diameter=0.01) == 0.0
        assert model.calculate_void_fraction(quality=1.0, mass_flux=1000.0, pressure=7e6, diameter=0.01) == 1.0

        # Force invalid saturation densities -> returns 0.
        monkeypatch.setattr(model, "_get_saturation_properties", lambda pressure: (0.0, 0.0, 1.0))
        assert model.calculate_void_fraction(quality=0.5, mass_flux=1000.0, pressure=7e6, diameter=0.01) == 0.0

        # j == 0 -> returns 0.
        monkeypatch.setattr(model, "_get_saturation_properties", lambda pressure: (740.0, 36.5, 1.5e6))
        assert model.calculate_void_fraction(quality=0.5, mass_flux=0.0, pressure=7e6, diameter=0.01) == 0.0

    def test_distribution_parameter_and_drift_velocity_overrides_and_unknown_model(self):
        # Explicit overrides should be returned.
        model = DriftFluxModel(model_type="zuber_findlay", distribution_parameter=2.0, drift_velocity=3.0)
        assert model._calculate_distribution_parameter(0.5, 1000.0, 7e6, 0.01, "vertical") == 2.0
        assert model._calculate_drift_velocity(0.5, 1000.0, 7e6, 0.01, "vertical") == 3.0

        # Horizontal flow -> no drift.
        model2 = DriftFluxModel(model_type="zuber_findlay")
        assert model2._calculate_drift_velocity(0.5, 1000.0, 7e6, 0.01, "horizontal") == 0.0

        # Unknown model_type -> defaults.
        model3 = DriftFluxModel(model_type="unknown")
        assert model3._calculate_distribution_parameter(0.5, 1000.0, 7e6, 0.01, "vertical") == 1.0
        assert model3._calculate_drift_velocity(0.5, 1000.0, 7e6, 0.01, "vertical") == 0.0

    def test_saturation_properties_scaling_paths(self):
        model = DriftFluxModel(model_type="chexal_lellouche")
        rho_l, rho_v, h_fg = model._get_saturation_properties(pressure=9e6)
        assert rho_l > 0 and rho_v > 0 and h_fg > 0


class TestTwoFluidModel:
    """Tests for TwoFluidModel class."""

    def test_solve_two_fluid(self):
        """Test two-fluid model solution."""
        model = TwoFluidModel(
            pressure=7e6,
            temperature=558.15,
            mass_flux=1000.0,
            quality=0.3,
            diameter=0.01,
            length=4.0,
        )
        
        result = model.solve_two_fluid(
            heat_flux=500000.0,  # W/m²
            inlet_quality=0.0,
        )
        
        assert "void_fraction" in result
        assert "pressure_drop" in result
        assert "liquid_velocity" in result
        assert "vapor_velocity" in result
        assert 0.0 <= result["void_fraction"] <= 1.0
        assert result["pressure_drop"] > 0.0

    def test_pressure_drop_calculation(self):
        """Test pressure drop calculation."""
        model = TwoFluidModel(
            pressure=7e6,
            temperature=558.15,
            mass_flux=1000.0,
            quality=0.3,
            diameter=0.01,
            length=4.0,
        )
        
        dp = model._calculate_pressure_drop(
            void_fraction=0.5,
            liquid_velocity=1.0,
            vapor_velocity=10.0,
            rho_l=740.0,
            rho_v=36.5,
        )
        
        assert dp > 0.0

    def test_two_fluid_saturation_property_scaling(self):
        model = TwoFluidModel(
            pressure=9e6,
            temperature=558.15,
            mass_flux=1000.0,
            quality=0.3,
            diameter=0.01,
            length=4.0,
        )
        rho_l, rho_v, h_fg = model._get_saturation_properties(pressure=9e6)
        assert rho_l > 0 and rho_v > 0 and h_fg > 0


class TestBoilingHeatTransfer:
    """Tests for BoilingHeatTransfer class."""

    def test_chen_correlation(self):
        """Test Chen correlation for boiling heat transfer."""
        boiling = BoilingHeatTransfer(
            pressure=7e6,
            mass_flux=1000.0,
            quality=0.3,
            diameter=0.01,
        )
        
        htc = boiling.calculate_heat_transfer_coefficient(
            heat_flux=500000.0,
            wall_temperature=568.15,  # 10K superheat
            bulk_temperature=558.15,
            correlation="chen",
        )
        
        assert htc > 0.0
        assert htc > 1000.0  # Boiling HTC should be high

    def test_forster_zuber_correlation(self):
        """Test Forster-Zuber correlation."""
        boiling = BoilingHeatTransfer(
            pressure=7e6,
            mass_flux=1000.0,
            quality=0.2,
            diameter=0.01,
        )
        
        htc = boiling.calculate_heat_transfer_coefficient(
            heat_flux=400000.0,
            wall_temperature=563.15,
            bulk_temperature=558.15,
            correlation="forster_zuber",
        )
        
        assert htc > 0.0

    def test_gorenflo_correlation_and_default_fallback(self):
        boiling = BoilingHeatTransfer(
            pressure=9e6,
            mass_flux=1000.0,
            quality=0.2,
            diameter=0.01,
        )

        htc = boiling.calculate_heat_transfer_coefficient(
            heat_flux=400000.0,
            wall_temperature=565.0,
            bulk_temperature=558.15,
            correlation="gorenflo",
        )
        assert htc > 0.0

        htc2 = boiling.calculate_heat_transfer_coefficient(
            heat_flux=400000.0,
            wall_temperature=565.0,
            bulk_temperature=558.15,
            correlation="unknown",
        )
        assert htc2 > 0.0

    def test_heat_transfer_coefficient_delta_t_nonpositive(self):
        boiling = BoilingHeatTransfer(pressure=7e6, mass_flux=1000.0, quality=0.2, diameter=0.01)
        htc = boiling.calculate_heat_transfer_coefficient(
            heat_flux=400000.0,
            wall_temperature=500.0,
            bulk_temperature=500.0,
        )
        assert htc == pytest.approx(1000.0)

    def test_critical_heat_flux(self):
        """Test critical heat flux calculation."""
        boiling = BoilingHeatTransfer(
            pressure=7e6,
            mass_flux=1000.0,
            quality=0.3,
            diameter=0.01,
        )
        
        chf = boiling.calculate_critical_heat_flux(correlation="bowring")
        
        assert chf > 0.0
        assert chf >= 1e6  # Should be >= 1 MW/m² (minimum enforced)

    def test_biasi_chf(self):
        """Test Biasi CHF correlation."""
        boiling = BoilingHeatTransfer(
            pressure=7e6,
            mass_flux=1500.0,
            quality=0.2,
            diameter=0.01,
        )
        
        chf = boiling.calculate_critical_heat_flux(correlation="biasi")
        
        assert chf > 0.0

    def test_chf_groeneveld_and_default(self):
        boiling = BoilingHeatTransfer(pressure=9e6, mass_flux=1000.0, quality=0.3, diameter=0.01)
        assert boiling.calculate_critical_heat_flux(correlation="groeneveld") > 0.0
        assert boiling.calculate_critical_heat_flux(correlation="unknown") > 0.0

    def test_boiling_saturation_property_scaling(self):
        boiling = BoilingHeatTransfer(pressure=9e6, mass_flux=1000.0, quality=0.3, diameter=0.01)
        rho_l, rho_v, h_fg = boiling._get_saturation_properties(pressure=9e6)
        assert rho_l > 0 and rho_v > 0 and h_fg > 0


class TestInterfacialTransferModels:
    def test_saturation_property_scaling(self):
        it = InterfacialTransferModels(
            pressure=9e6,
            temperature_liquid=550.0,
            temperature_vapor=560.0,
            void_fraction=0.2,
            liquid_velocity=1.0,
            vapor_velocity=5.0,
            diameter=0.01,
            model_type="ishii_hibiki",
        )
        rho_l, rho_v, h_fg = it._get_saturation_properties(pressure=9e6)
        assert rho_l > 0 and rho_v > 0 and h_fg > 0

    def test_mass_energy_and_momentum_transfer_branches(self):
        # Mass transfer: exercise interfacial_area branches and heat_flux_interface branch.
        it_bubbly = InterfacialTransferModels(
            pressure=7e6,
            temperature_liquid=600.0,
            temperature_vapor=550.0,
            void_fraction=0.2,
            liquid_velocity=1.0,
            vapor_velocity=5.0,
            diameter=0.01,
            model_type="ishii_hibiki",
        )
        mt1 = it_bubbly.calculate_mass_transfer_rate(heat_flux_interface=1e5)
        assert "interfacial_area" in mt1
        assert mt1["interfacial_area"] > 0.0

        it_slug = InterfacialTransferModels(
            pressure=7e6,
            temperature_liquid=600.0,
            temperature_vapor=550.0,
            void_fraction=0.5,
            liquid_velocity=1.0,
            vapor_velocity=5.0,
            diameter=0.01,
            model_type="ishii_hibiki",
        )
        mt2 = it_slug.calculate_mass_transfer_rate()
        assert mt2["interfacial_area"] > 0.0

        # Energy transfer: cover both total_heat_transfer paths.
        et1 = it_bubbly.calculate_energy_transfer(heat_flux_interface=None)
        assert "heat_transfer_rate" in et1
        et2 = it_bubbly.calculate_energy_transfer(heat_flux_interface=1e4)
        assert et2["heat_transfer_rate"] > 0.0

        # Area density branches
        assert it_bubbly._calculate_interfacial_area_density() > 0.0
        assert it_slug._calculate_interfacial_area_density() > 0.0
        it_annular = InterfacialTransferModels(
            pressure=7e6,
            temperature_liquid=600.0,
            temperature_vapor=550.0,
            void_fraction=0.8,
            liquid_velocity=1.0,
            vapor_velocity=5.0,
            diameter=0.01,
            model_type="ishii_hibiki",
        )
        assert it_annular._calculate_interfacial_area_density() > 0.0

        # Drag coefficient branches
        assert 0.0 < it_bubbly._calculate_interfacial_drag_coefficient(1.0) <= 1.0
        assert 0.0 < it_slug._calculate_interfacial_drag_coefficient(1.0) <= 1.0
        assert 0.0 < it_annular._calculate_interfacial_drag_coefficient(1.0) <= 1.0

        it_relap = InterfacialTransferModels(
            pressure=7e6,
            temperature_liquid=600.0,
            temperature_vapor=550.0,
            void_fraction=0.2,
            liquid_velocity=1.0,
            vapor_velocity=5.0,
            diameter=0.01,
            model_type="relap5",
        )
        assert 0.0 < it_relap._calculate_interfacial_drag_coefficient(1.0) <= 1.0

        it_trap = InterfacialTransferModels(
            pressure=7e6,
            temperature_liquid=600.0,
            temperature_vapor=550.0,
            void_fraction=0.2,
            liquid_velocity=1.0,
            vapor_velocity=5.0,
            diameter=0.01,
            model_type="trap",
        )
        assert 0.0 < it_trap._calculate_interfacial_drag_coefficient(1.0) <= 1.0

        # Heat transfer coefficient regime corrections
        assert it_annular._calculate_interfacial_heat_transfer_coefficient() > 0.0
        assert it_bubbly._calculate_interfacial_heat_transfer_coefficient() > 0.0


class TestTwoPhaseThermalHydraulics:
    """Tests for TwoPhaseThermalHydraulics class."""

    def test_solve_drift_flux(self):
        """Test two-phase thermal-hydraulics with drift-flux model."""
        solver = TwoPhaseThermalHydraulics(
            pressure=7e6,
            mass_flux=1000.0,
            diameter=0.01,
            length=4.0,
            heat_flux=500000.0,
        )
        
        result = solver.solve(
            inlet_temperature=558.15,
            inlet_quality=0.0,
            model_type="drift_flux",
        )
        
        assert "void_fraction" in result
        assert "outlet_quality" in result
        assert "pressure_drop" in result
        assert "heat_transfer_coefficient" in result
        assert "critical_heat_flux" in result
        assert "flow_regime" in result
        assert result["outlet_quality"] > 0.0

    def test_solve_two_fluid(self):
        """Test two-phase thermal-hydraulics with two-fluid model."""
        solver = TwoPhaseThermalHydraulics(
            pressure=7e6,
            mass_flux=1000.0,
            diameter=0.01,
            length=4.0,
            heat_flux=500000.0,
        )
        
        result = solver.solve(
            inlet_temperature=558.15,
            inlet_quality=0.0,
            model_type="two_fluid",
        )
        
        assert "void_fraction" in result
        assert "pressure_drop" in result
        assert result["pressure_drop"] > 0.0

    def test_chf_margin(self):
        """Test CHF margin calculation."""
        solver = TwoPhaseThermalHydraulics(
            pressure=7e6,
            mass_flux=1000.0,
            diameter=0.01,
            length=4.0,
            heat_flux=500000.0,  # Low heat flux
        )
        
        result = solver.solve(inlet_temperature=558.15, inlet_quality=0.0)
        
        assert "chf_margin" in result
        assert result["chf_margin"] > 0.0  # Should have positive margin

    def test_flow_regime_determination(self):
        """Test flow regime determination."""
        solver = TwoPhaseThermalHydraulics(
            pressure=7e6,
            mass_flux=1000.0,
            diameter=0.01,
            length=4.0,
            heat_flux=500000.0,
        )
        
        result = solver.solve(inlet_temperature=558.15, inlet_quality=0.0)
        
        assert "flow_regime" in result
        assert result["flow_regime"] in ["bubbly", "slug", "churn", "annular", "mist"]

    def test_flow_regime_boundaries_and_saturation_scaling(self):
        solver = TwoPhaseThermalHydraulics(
            pressure=9e6,
            mass_flux=1000.0,
            diameter=0.01,
            length=4.0,
            heat_flux=500000.0,
        )

        assert solver._determine_flow_regime(0.05, 0.1) == "bubbly"
        assert solver._determine_flow_regime(0.2, 0.1) == "slug"
        assert solver._determine_flow_regime(0.5, 0.1) == "churn"
        assert solver._determine_flow_regime(0.8, 0.1) == "annular"
        assert solver._determine_flow_regime(0.95, 0.1) == "mist"

        rho_l, rho_v, h_fg = solver._get_saturation_properties(pressure=9e6)
        assert rho_l > 0 and rho_v > 0 and h_fg > 0
