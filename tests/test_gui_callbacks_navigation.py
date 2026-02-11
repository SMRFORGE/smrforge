import builtins
import importlib
import sys
from types import SimpleNamespace
from unittest.mock import patch


class DummyApp:
    def __init__(self):
        self.callbacks = []

    def callback(self, *args, **kwargs):
        def decorator(fn):
            self.callbacks.append(fn)
            return fn

        return decorator


def _import_module_without_dash(module_name: str):
    # Pre-import components so that only dash-related imports in the target
    # module are exercised under ImportError.
    import smrforge.gui.components  # noqa: F401

    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "dash" or name.startswith("dash."):
            raise ImportError("forced dash ImportError for coverage")
        return real_import(name, globals, locals, fromlist, level)

    sys.modules.pop(module_name, None)
    with patch("builtins.__import__", side_effect=guarded_import):
        return importlib.import_module(module_name)


def test_register_navigation_callbacks_no_dash_returns_early():
    mod = _import_module_without_dash("smrforge.gui.callbacks.navigation")
    assert mod._DASH_AVAILABLE is False
    app = DummyApp()
    assert mod.register_navigation_callbacks(app) is None
    assert app.callbacks == []


def test_navigation_update_main_content_all_branches():
    import dash

    from smrforge.gui.callbacks import navigation as nav

    # Ensure we are not using a partially imported module from a prior ImportError-path test.
    nav = importlib.reload(nav)
    assert nav._DASH_AVAILABLE is True

    # Patch content factories
    with (
        patch.object(nav, "create_reactor_builder", return_value="reactor") as _rb,
        patch.object(nav, "create_geometry_designer", return_value="geom") as _gd,
        patch.object(nav, "create_analysis_panel", return_value="analysis") as _ap,
        patch.object(nav, "create_results_viewer", return_value="results") as _rv,
        patch.object(nav, "create_data_manager", return_value="data") as _dm,
        patch.object(nav, "create_feature_lab", return_value="feature") as _fl,
    ):
        app = DummyApp()
        nav.register_navigation_callbacks(app)
        (update_main_content,) = [
            fn for fn in app.callbacks if fn.__name__ == "update_main_content"
        ]

        # Initial load: ctx.triggered falsy
        with patch.object(dash, "callback_context", SimpleNamespace(triggered=[])):
            assert update_main_content(None, None, None, None, None, None) == "reactor"

        # Each navigation button branch
        cases = [
            ("nav-reactor-builder.n_clicks", "reactor"),
            ("nav-geometry-designer.n_clicks", "geom"),
            ("nav-analysis.n_clicks", "analysis"),
            ("nav-results.n_clicks", "results"),
            ("nav-data-manager.n_clicks", "data"),
            ("nav-feature-lab.n_clicks", "feature"),
            ("nav-unknown.n_clicks", "reactor"),
        ]
        for prop_id, expected in cases:
            with patch.object(
                dash,
                "callback_context",
                SimpleNamespace(triggered=[{"prop_id": prop_id}]),
            ):
                assert update_main_content(1, 1, 1, 1, 1, 1) == expected
