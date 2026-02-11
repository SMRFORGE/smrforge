import builtins
import importlib

import pytest


def _import_web_app_without_dash():
    orig_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        # Force the top-level Dash/Plotly stack to be unavailable.
        if name in {
            "dash",
            "dash_bootstrap_components",
            "plotly",
            "plotly.graph_objects",
            "plotly.express",
        }:
            raise ImportError("forced for coverage")
        return orig_import(name, globals, locals, fromlist, level)

    import smrforge.gui.web_app as web_app

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(builtins, "__import__", guarded_import)
        web_app = importlib.reload(web_app)
    return web_app


def test_web_app_no_dash_paths():
    web_app = _import_web_app_without_dash()
    assert web_app._DASH_AVAILABLE is False
    assert web_app.app is None

    # create_app logs and returns None
    with pytest.MonkeyPatch.context() as mp:
        calls = {"n": 0}

        def fake_error(*args, **kwargs):
            calls["n"] += 1

        mp.setattr(web_app.logger, "error", fake_error)
        assert web_app.create_app() is None
        assert calls["n"] >= 1

    # run_server raises ImportError when dash unavailable
    with pytest.raises(ImportError):
        web_app.run_server()


def test_web_app_create_app_and_register_callbacks_and_run_server_branches():
    import smrforge.gui.web_app as web_app

    web_app = importlib.reload(web_app)
    assert web_app._DASH_AVAILABLE is True

    # create_app: avoid wiring all callbacks here; cover layout + return path.
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(web_app, "_register_callbacks", lambda: None)
        app = web_app.create_app()
        assert app is web_app.app
        assert web_app.app.layout is not None

    # _register_callbacks: ensure each registrar gets called
    from unittest.mock import Mock

    nav = Mock()
    rb = Mock()
    gd = Mock()
    an = Mock()
    res = Mock()
    dm = Mock()
    proj = Mock()
    fl = Mock()
    theme = Mock()

    with (pytest.MonkeyPatch.context() as mp,):
        import smrforge.gui.callbacks as cb
        import smrforge.gui.callbacks.theme as cb_theme

        mp.setattr(cb, "register_navigation_callbacks", nav)
        mp.setattr(cb, "register_reactor_builder_callbacks", rb)
        mp.setattr(cb, "register_geometry_designer_callbacks", gd)
        mp.setattr(cb, "register_analysis_callbacks", an)
        mp.setattr(cb, "register_results_callbacks", res)
        mp.setattr(cb, "register_data_manager_callbacks", dm)
        mp.setattr(cb, "register_project_callbacks", proj)
        mp.setattr(cb, "register_feature_lab_callbacks", fl)
        mp.setattr(cb_theme, "register_theme_callbacks", theme)

        web_app._register_callbacks()

    nav.assert_called_once_with(web_app.app)
    rb.assert_called_once_with(web_app.app)
    gd.assert_called_once_with(web_app.app)
    an.assert_called_once_with(web_app.app)
    res.assert_called_once_with(web_app.app)
    dm.assert_called_once_with(web_app.app)
    proj.assert_called_once_with(web_app.app)
    fl.assert_called_once_with(web_app.app)
    theme.assert_called_once_with(web_app.app)

    # run_server: create_app returns None -> RuntimeError
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(web_app, "create_app", lambda: None)
        with pytest.raises(RuntimeError):
            web_app.run_server()

    # run_server: app_instance has run()
    class DummyDashNew:
        def __init__(self):
            self.called = False

        def run(self, **kwargs):
            self.called = True
            self.kwargs = kwargs

    dummy_new = DummyDashNew()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(web_app, "create_app", lambda: dummy_new)
        web_app.run_server(host="0.0.0.0", port=9999, debug=True)
        assert dummy_new.called is True

    # run_server: fallback to run_server() when run() absent
    class DummyDashOld:
        def __init__(self):
            self.called = False

        def run_server(self, **kwargs):
            self.called = True
            self.kwargs = kwargs

    dummy_old = DummyDashOld()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(web_app, "create_app", lambda: dummy_old)
        web_app.run_server(host="127.0.0.1", port=8051, debug=False)
        assert dummy_old.called is True
