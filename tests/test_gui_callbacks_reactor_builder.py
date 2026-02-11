import builtins
import importlib
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


def test_register_reactor_builder_callbacks_no_dash_returns_early():
    mod = _import_module_without_dash("smrforge.gui.callbacks.reactor_builder")
    assert mod._DASH_AVAILABLE is False
    app = DummyApp()
    assert mod.register_reactor_builder_callbacks(app) is None
    assert app.callbacks == []


def test_reactor_builder_callbacks_cover_branches():
    import dash
    import dash_bootstrap_components as dbc

    from smrforge.gui.callbacks import reactor_builder as rb

    rb = importlib.reload(rb)
    assert rb._DASH_AVAILABLE is True

    app = DummyApp()
    rb.register_reactor_builder_callbacks(app)
    by_name = {fn.__name__: fn for fn in app.callbacks}

    load_presets = by_name["load_presets"]
    create_reactor = by_name["create_reactor"]
    display_reactor_spec = by_name["display_reactor_spec"]

    # load_presets: strategy1 success
    with patch("smrforge.list_presets", return_value=["p1", "p2"]):
        opts = load_presets({})
        assert opts and opts[0]["value"] == "p1"

    # load_presets: strategy1 raises -> strategy2 uses convenience.list_presets
    import smrforge.convenience as conv

    with (
        patch("smrforge.list_presets", side_effect=RuntimeError("nope")),
        patch.object(conv, "list_presets", return_value=["c1"]),
    ):
        opts = load_presets({})
        assert opts and opts[0]["value"] == "c1"

    # load_presets: exercise "conv_mod has no list_presets" branch (best-effort)
    import types

    import smrforge as smr_pkg

    real_conv = smr_pkg.convenience
    fake_conv = types.ModuleType("smrforge.convenience")
    with (
        patch("smrforge.list_presets", side_effect=RuntimeError("nope")),
        patch.dict(sys.modules, {"smrforge.convenience": fake_conv}),
        patch.object(smr_pkg, "convenience", fake_conv),
    ):
        _ = load_presets({})
    # restore attribute (patch.object handles restore automatically)
    assert smr_pkg.convenience is real_conv

    # load_presets: strategy3 DesignLibrary path
    class DummyLib:
        def list_designs(self):
            return ["d1"]

    with (
        patch("smrforge.list_presets", side_effect=RuntimeError("nope")),
        patch.object(conv, "list_presets", side_effect=RuntimeError("nope2")),
        patch("smrforge.presets.htgr.DesignLibrary", return_value=DummyLib()),
    ):
        opts = load_presets({})
        assert opts and opts[0]["value"] == "d1"

    # load_presets: strategy3 failure (covers exception logging path)
    with (
        patch("smrforge.list_presets", side_effect=RuntimeError("nope")),
        patch.object(conv, "list_presets", side_effect=RuntimeError("nope2")),
        patch(
            "smrforge.presets.htgr.DesignLibrary", side_effect=RuntimeError("no lib")
        ),
    ):
        opts = load_presets({})
        assert opts and opts[0].get("disabled") is True

    # load_presets: none found -> placeholder
    with (patch("smrforge.list_presets", return_value=[]),):
        opts = load_presets({})
        assert opts and opts[0].get("disabled") is True

    # load_presets: outer exception path (logger.info raises)
    with (
        patch("smrforge.list_presets", return_value=["p"]),
        patch.object(rb.logger, "info", side_effect=RuntimeError("boom")),
    ):
        opts = load_presets({})
        assert opts and opts[0]["label"].startswith("Error")

    # create_reactor: no ctx.triggered => PreventUpdate
    with patch.object(dash, "callback_context", SimpleNamespace(triggered=[])):
        with pytest.raises(dash.exceptions.PreventUpdate):
            create_reactor(
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            )

    # create_reactor: load preset button but preset missing => PreventUpdate
    with patch.object(
        dash,
        "callback_context",
        SimpleNamespace(triggered=[{"prop_id": "load-preset-button.n_clicks"}]),
    ):
        with pytest.raises(dash.exceptions.PreventUpdate):
            create_reactor(
                None,
                1,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            )

    # create_reactor: preset load success
    from smrforge.validation.models import ReactorSpecification

    spec = ReactorSpecification(
        name="Preset",
        reactor_type="prismatic",
        power_thermal=10e6,
        core_height=200.0,
        core_diameter=100.0,
        enrichment=0.195,
        inlet_temperature=823.15,
        outlet_temperature=1023.15,
        max_fuel_temperature=1523.15,
        primary_pressure=7.0e6,
        reflector_thickness=30.0,
        fuel_type="UCO",
        heavy_metal_loading=150.0,
        coolant_flow_rate=8.0,
        cycle_length=3650.0,
        capacity_factor=0.95,
        target_burnup=150.0,
        doppler_coefficient=-3.5e-5,
        shutdown_margin=0.05,
    )
    reactor = SimpleNamespace(spec=spec)
    with (
        patch.object(
            dash,
            "callback_context",
            SimpleNamespace(triggered=[{"prop_id": "load-preset-button.n_clicks"}]),
        ),
        patch("smrforge.create_reactor", return_value=reactor),
    ):
        data, feedback = create_reactor(
            None, 1, "p1", None, None, None, None, None, None, None, None, None, None
        )
        assert isinstance(feedback, dbc.Alert)
        assert data.get("name") == "Preset"

    # create_reactor: preset load validation fails
    with (
        patch.object(
            dash,
            "callback_context",
            SimpleNamespace(triggered=[{"prop_id": "load-preset-button.n_clicks"}]),
        ),
        patch("smrforge.create_reactor", return_value=reactor),
        patch(
            "smrforge.validation.models.ReactorSpecification",
            side_effect=RuntimeError("validation error"),
        ),
    ):
        data, feedback = create_reactor(
            None, 2, "p1", None, None, None, None, None, None, None, None, None, None
        )
        assert data == {}
        assert isinstance(feedback, dbc.Alert)

    # create_reactor: custom reactor success
    with patch.object(
        dash,
        "callback_context",
        SimpleNamespace(triggered=[{"prop_id": "create-reactor-button.n_clicks"}]),
    ):
        data, feedback = create_reactor(
            1,
            None,
            None,
            "Custom",
            "prismatic",
            10.0,
            200.0,
            100.0,
            0.195,
            800.0,
            900.0,
            7.0e6,
            150.0,
        )
        assert isinstance(feedback, dbc.Alert)
        assert data.get("name") == "Custom"

    # create_reactor: custom reactor validation error path
    class RaisingSpec:
        def __init__(self, **kwargs):
            raise RuntimeError("validation error: bad fields")

    with (
        patch.object(
            dash,
            "callback_context",
            SimpleNamespace(triggered=[{"prop_id": "create-reactor-button.n_clicks"}]),
        ),
        patch("smrforge.validation.models.ReactorSpecification", RaisingSpec),
    ):
        data, feedback = create_reactor(
            2, None, None, None, None, None, None, None, None, None, None, None, None
        )
        assert data == {}
        assert isinstance(feedback, dbc.Alert)

    # create_reactor: outer exception
    with (
        patch.object(
            dash,
            "callback_context",
            SimpleNamespace(triggered=[{"prop_id": "load-preset-button.n_clicks"}]),
        ),
        patch("smrforge.create_reactor", side_effect=RuntimeError("boom")),
    ):
        data, feedback = create_reactor(
            None, 3, "p1", None, None, None, None, None, None, None, None, None, None
        )
        assert data == {}
        assert isinstance(feedback, dbc.Alert)

    # display_reactor_spec: empty
    assert display_reactor_spec({}) == ""

    # display_reactor_spec: formatting branches
    spec_data = {
        "name": "X",
        "reactor_type": "prismatic",
        "power_thermal": 2.0e6,  # >= 1e6
        "core_height": 2000.0,  # >= 1e3
        "shutdown_margin": 0.005,  # < 0.01
        "capacity_factor": 0.95,  # normal float
        "primary_pressure": 7.0e6,
        "description": None,  # exercise N/A display
    }
    card = display_reactor_spec(spec_data)
    assert isinstance(card, dbc.Card)
