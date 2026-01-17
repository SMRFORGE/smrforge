"""
Unit tests for advanced two-phase flow models.
"""

import numpy as np
import pytest

from smrforge.thermal.two_phase_advanced import (
    BoilingHeatTransfer,
    DriftFluxModel,
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
