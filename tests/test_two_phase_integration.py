def test_integrate_two_phase_with_thermal_hydraulics_smoke():
    from smrforge.thermal.hydraulics import ChannelGeometry, ChannelThermalHydraulics
    from smrforge.thermal.two_phase_integration import integrate_two_phase_with_thermal_hydraulics

    geom = ChannelGeometry(length=100.0, diameter=2.0, flow_area=3.14159, heated_perimeter=6.28318)
    inlet = {"temperature": 600.0, "pressure": 7.0e6, "mass_flow_rate": 0.1}
    thermal = ChannelThermalHydraulics(geom, inlet)

    out = integrate_two_phase_with_thermal_hydraulics(
        thermal_solver=thermal,
        geometry=geom,
        pressure=7.0e6,
        mass_flux=1000.0,
        heat_flux=1.0e5,
        inlet_temperature=600.0,
        inlet_quality=0.0,
        model_type="drift_flux",
    )

    # Basic contract checks
    assert "two_phase" in out
    assert "void_fraction" in out
    assert "outlet_quality" in out
    assert "pressure_drop" in out
    assert "heat_transfer_coefficient" in out
    assert "critical_heat_flux" in out
    assert "chf_margin" in out
    assert "flow_regime" in out

