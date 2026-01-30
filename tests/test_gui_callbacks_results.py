import builtins
import importlib
import json
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest


class DummyApp:
    def __init__(self):
        self.callbacks = []

    def callback(self, *args, **kwargs):
        def decorator(fn):
            self.callbacks.append(fn)
            return fn

        return decorator


def _import_module_without_dash(module_name: str):
    import smrforge.gui.components  # noqa: F401

    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "dash" or name.startswith("dash."):
            raise ImportError("forced dash ImportError for coverage")
        if name == "dash_bootstrap_components":
            raise ImportError("forced dbc ImportError for coverage")
        return real_import(name, globals, locals, fromlist, level)

    sys.modules.pop(module_name, None)
    with patch("builtins.__import__", side_effect=guarded_import):
        return importlib.import_module(module_name)


def test_register_results_callbacks_no_dash_returns_early():
    mod = _import_module_without_dash("smrforge.gui.callbacks.results")
    assert mod._DASH_AVAILABLE is False
    app = DummyApp()
    assert mod.register_results_callbacks(app) is None
    assert app.callbacks == []


def test_results_callbacks_cover_branches(tmp_path, monkeypatch):
    import dash
    import dash_bootstrap_components as dbc

    monkeypatch.chdir(tmp_path)

    from smrforge.gui.callbacks import results as res

    res = importlib.reload(res)
    assert res._DASH_AVAILABLE is True

    app = DummyApp()
    res.register_results_callbacks(app)
    by_name = {fn.__name__: fn for fn in app.callbacks}

    update_results_summary = by_name["update_results_summary"]
    update_flux_plot = by_name["update_flux_plot"]
    update_power_plot = by_name["update_power_plot"]
    update_3d_plot = by_name["update_3d_plot"]
    update_transient_plot = by_name["update_transient_plot"]
    export_results = by_name["export_results"]

    # Summary: no results
    assert isinstance(update_results_summary({}), dbc.Alert)

    # Summary: k_eff bands + warning
    for k_eff in [0.90, 0.97, 1.00, 1.05]:
        out = update_results_summary(
            {
                "neutronics": {"k_eff": k_eff, "status": "success", "warning": "validation"},
                "burnup": {"message": "burn ok"},
                "safety": {"message": "safe ok"},
            }
        )
        assert out is not None
    # Summary: non-numeric k_eff branch
    out = update_results_summary({"neutronics": {"k_eff": "N/A", "status": "success"}})
    assert out is not None

    # Flux plot: no neutronics
    assert isinstance(update_flux_plot({}), dbc.Alert)
    # Flux plot: with sample
    g = update_flux_plot({"neutronics": {"flux": {"sample": [1, 2, 3], "max": 3.0, "mean": 2.0, "min": 1.0}}})
    assert g is not None
    # Flux plot: without sample but with stats
    g = update_flux_plot({"neutronics": {"flux": {"max": 3.0, "mean": 2.0, "min": 1.0}}})
    assert g is not None

    # Power plot: no neutronics
    assert isinstance(update_power_plot({}), dbc.Alert)
    # Power plot: with sample
    g = update_power_plot({"neutronics": {"power": {"sample": [1, 2, 3], "max": 3.0, "mean": 2.0, "min": 1.0}}})
    assert g is not None
    # Power plot: without sample but with stats
    g = update_power_plot({"neutronics": {"power": {"max": 3.0, "mean": 2.0, "min": 1.0}}})
    assert g is not None

    # 3D plot: no reactor spec
    assert isinstance(update_3d_plot({}, None), dbc.Alert)

    class DummySpec:
        def __init__(self, **kwargs):
            self.name = kwargs.get("name", "R")
            self.power_thermal = kwargs.get("power_thermal", 10e6)
            self.core_height = kwargs.get("core_height", 200.0)
            self.core_diameter = kwargs.get("core_diameter", 100.0)
            self.enrichment = kwargs.get("enrichment", 0.195)
            self.reactor_type = kwargs.get("reactor_type", "prismatic")
            self.fuel_type = kwargs.get("fuel_type", "UCO")
            self.inlet_temperature = kwargs.get("inlet_temperature", 800.0)
            self.outlet_temperature = kwargs.get("outlet_temperature", 900.0)

    dummy_reactor = SimpleNamespace(_get_core=lambda: object())

    with (
        patch("smrforge.validation.models.ReactorSpecification", DummySpec),
        patch("smrforge.create_reactor", return_value=dummy_reactor),
        patch("smrforge.visualization.advanced.plot_ray_traced_geometry", return_value=res.go.Figure()),
    ):
        g = update_3d_plot({}, {"name": "R"})
        assert g is not None

    with (
        patch("smrforge.validation.models.ReactorSpecification", DummySpec),
        patch("smrforge.create_reactor", return_value=dummy_reactor),
        patch("smrforge.visualization.advanced.plot_ray_traced_geometry", side_effect=RuntimeError("nope")),
    ):
        out = update_3d_plot({}, {"name": "R"})
        assert isinstance(out, dbc.Alert)

    # Transient plot: no results
    assert isinstance(update_transient_plot(None), dbc.Alert)
    # No transient series found
    assert isinstance(update_transient_plot({"neutronics": {"status": "success"}}), dbc.Alert)
    # Safety preferred
    out = update_transient_plot({"safety": {"status": "success", "time": [0, 1], "power": [1, 2], "T_fuel": [10, 11], "T_moderator": [9, 10], "reactivity": [0.0, 0.1]}})
    assert out is not None
    # Quick transient
    out = update_transient_plot({"quick_transient": {"status": "success", "time": [0, 1], "power": [1, 2], "T_fuel": [10, 11], "T_mod": [9, 10], "reactivity": [0.0, 0.1]}})
    assert out is not None
    # Lumped thermal
    out = update_transient_plot({"lumped_thermal": {"status": "success", "result": {"time": [0, 1], "T_fuel": [1, 2], "T_moderator": [3, 4]}}})
    assert out is not None

    # Export: no ctx.triggered
    with patch.object(dash, "callback_context", SimpleNamespace(triggered=[])):
        with pytest.raises(dash.exceptions.PreventUpdate):
            export_results(None, None, None, {}, {})

    # Export: no results
    with patch.object(dash, "callback_context", SimpleNamespace(triggered=[{"prop_id": "export-json-button.n_clicks"}])):
        out = export_results(1, None, None, {}, {})
        assert isinstance(out, dbc.Alert)

    # Export: JSON success
    with patch.object(dash, "callback_context", SimpleNamespace(triggered=[{"prop_id": "export-json-button.n_clicks"}])):
        out = export_results(1, None, None, {"neutronics": {"k_eff": 1.0}}, {"name": "R"})
        assert isinstance(out, dbc.Alert)
        # a JSON file should exist
        assert any(p.name.startswith("smrforge_results_") and p.suffix == ".json" for p in tmp_path.iterdir())

    # Export: JSON error
    with (
        patch.object(dash, "callback_context", SimpleNamespace(triggered=[{"prop_id": "export-json-button.n_clicks"}])),
        patch("builtins.open", side_effect=OSError("no write")),
    ):
        out = export_results(2, None, None, {"neutronics": {"k_eff": 1.0}}, {"name": "R"})
        assert isinstance(out, dbc.Alert)

    # Export: CSV success
    with patch.object(dash, "callback_context", SimpleNamespace(triggered=[{"prop_id": "export-csv-button.n_clicks"}])):
        out = export_results(None, 1, None, {"neutronics": {"k_eff": 1.0, "flux": {"max": 1, "mean": 0.5, "min": 0.1}}}, {"name": "R"})
        assert isinstance(out, dbc.Alert)
        assert any(p.name.startswith("smrforge_results_") and p.suffix == ".csv" for p in tmp_path.iterdir())

    # Export: CSV no rows
    with patch.object(dash, "callback_context", SimpleNamespace(triggered=[{"prop_id": "export-csv-button.n_clicks"}])):
        out = export_results(None, 2, None, {"x": 1}, None)
        assert isinstance(out, dbc.Alert)

    # Export: plots placeholder
    with patch.object(dash, "callback_context", SimpleNamespace(triggered=[{"prop_id": "export-plots-button.n_clicks"}])):
        out = export_results(None, None, 1, {"neutronics": {"k_eff": 1.0}}, None)
        assert isinstance(out, dbc.Alert)

    # Export: unknown => PreventUpdate
    with patch.object(dash, "callback_context", SimpleNamespace(triggered=[{"prop_id": "export-unknown.n_clicks"}])):
        # Note: PreventUpdate is caught by the function's broad exception handler,
        # which returns a danger Alert.
        out = export_results(1, 1, 1, {"neutronics": {"k_eff": 1.0}}, None)
        assert isinstance(out, dbc.Alert)

