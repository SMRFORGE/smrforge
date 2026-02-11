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
    # Pre-import components so package imports don't fail under dash ImportError.
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


def test_register_project_callbacks_no_dash_returns_early():
    mod = _import_module_without_dash("smrforge.gui.callbacks.projects")
    assert mod._DASH_AVAILABLE is False
    app = DummyApp()
    assert mod.register_project_callbacks(app) is None
    assert app.callbacks == []


def test_project_callbacks_save_and_open_paths(tmp_path, monkeypatch):
    import dash
    import dash_bootstrap_components as dbc

    # Work in an isolated directory (module uses output/smrforge_project.json)
    monkeypatch.chdir(tmp_path)
    proj_path = tmp_path / "output" / "smrforge_project.json"

    from smrforge.gui.callbacks import projects as proj

    proj = importlib.reload(proj)
    assert proj._DASH_AVAILABLE is True

    app = DummyApp()
    proj.register_project_callbacks(app)
    (handle_project,) = [fn for fn in app.callbacks if fn.__name__ == "handle_project"]

    # No ctx.triggered => PreventUpdate
    with patch.object(dash, "callback_context", SimpleNamespace(triggered=[])):
        with pytest.raises(dash.exceptions.PreventUpdate):
            handle_project(None, None, {}, {})

    # Save with empty reactor spec => warning
    with patch.object(
        dash,
        "callback_context",
        SimpleNamespace(triggered=[{"prop_id": "nav-save-project.n_clicks"}]),
    ):
        project_store, feedback, rs, ars = handle_project(1, None, {}, {})
        assert project_store["status"] == "error"
        assert isinstance(feedback, dbc.Alert)
        assert rs == {}
        assert ars == {}

    # Save success
    reactor_spec = {"name": "R1", "reactor_type": "prismatic", "power_thermal": 1.0e6}
    with patch.object(
        dash,
        "callback_context",
        SimpleNamespace(triggered=[{"prop_id": "nav-save-project.n_clicks"}]),
    ):
        project_store, feedback, rs, ars = handle_project(
            2, None, reactor_spec, {"k_eff": 1.05}
        )
        assert project_store["status"] == "success"
        assert isinstance(feedback, dbc.Alert)
        assert rs == {}
        assert ars == {}
        assert proj_path.exists()

    # Open when file missing
    proj_path.unlink(missing_ok=True)
    with patch.object(
        dash,
        "callback_context",
        SimpleNamespace(triggered=[{"prop_id": "nav-open-project.n_clicks"}]),
    ):
        project_store, feedback, rs, ars = handle_project(None, 1, reactor_spec, {})
        assert project_store["status"] == "error"
        assert isinstance(feedback, dbc.Alert)
        assert rs == {}
        assert ars == {}

    # Open with invalid JSON
    proj_path.parent.mkdir(parents=True, exist_ok=True)
    proj_path.write_text("{not json", encoding="utf-8")
    with patch.object(
        dash,
        "callback_context",
        SimpleNamespace(triggered=[{"prop_id": "nav-open-project.n_clicks"}]),
    ):
        project_store, feedback, rs, ars = handle_project(None, 2, reactor_spec, {})
        assert project_store["status"] == "error"
        assert isinstance(feedback, dbc.Alert)
        assert rs == {}
        assert ars == {}

    # Open with empty reactor_spec in file
    proj_path.write_text(
        json.dumps({"reactor_spec": {}, "results": {}}), encoding="utf-8"
    )
    with patch.object(
        dash,
        "callback_context",
        SimpleNamespace(triggered=[{"prop_id": "nav-open-project.n_clicks"}]),
    ):
        project_store, feedback, rs, ars = handle_project(None, 3, reactor_spec, {})
        assert project_store["status"] == "error"
        assert isinstance(feedback, dbc.Alert)
        assert rs == {}
        assert ars == {}

    # Open success
    file_data = {"reactor_spec": reactor_spec, "results": {"k_eff": 1.01}}
    proj_path.write_text(json.dumps(file_data), encoding="utf-8")
    with patch.object(
        dash,
        "callback_context",
        SimpleNamespace(triggered=[{"prop_id": "nav-open-project.n_clicks"}]),
    ):
        project_store, feedback, rs, ars = handle_project(None, 4, reactor_spec, {})
        assert project_store["status"] == "success"
        assert isinstance(feedback, dbc.Alert)
        assert rs == reactor_spec
        assert ars == {"k_eff": 1.01}

    # Open generic exception branch (open() fails)
    with (
        patch.object(
            dash,
            "callback_context",
            SimpleNamespace(triggered=[{"prop_id": "nav-open-project.n_clicks"}]),
        ),
        patch("builtins.open", side_effect=OSError("cannot read")),
    ):
        project_store, feedback, rs, ars = handle_project(None, 5, reactor_spec, {})
        assert project_store["status"] == "error"
        assert isinstance(feedback, dbc.Alert)
        assert rs == {}
        assert ars == {}

    # Unknown button id => PreventUpdate
    with patch.object(
        dash,
        "callback_context",
        SimpleNamespace(triggered=[{"prop_id": "nav-unknown.n_clicks"}]),
    ):
        with pytest.raises(dash.exceptions.PreventUpdate):
            handle_project(1, 1, reactor_spec, {})

    # Save exception branch: make open() fail
    with (
        patch.object(
            dash,
            "callback_context",
            SimpleNamespace(triggered=[{"prop_id": "nav-save-project.n_clicks"}]),
        ),
        patch("builtins.open", side_effect=OSError("nope")),
    ):
        project_store, feedback, rs, ars = handle_project(99, None, reactor_spec, {})
        assert project_store["status"] == "error"
        assert isinstance(feedback, dbc.Alert)
        assert rs == {}
        assert ars == {}
