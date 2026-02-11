import builtins
import importlib
import sys
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
    # Ensure any shared dependencies are already importable (and cached) so that
    # only the module's own dash imports are exercised under ImportError.
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


def test_register_data_manager_callbacks_no_dash_returns_early():
    mod = _import_module_without_dash("smrforge.gui.callbacks.data_manager")
    assert mod._DASH_AVAILABLE is False
    app = DummyApp()
    assert mod.register_data_manager_callbacks(app) is None
    assert app.callbacks == []


def test_data_manager_callbacks_cover_all_branches():
    import dash_bootstrap_components as dbc

    from smrforge.gui.callbacks import data_manager as dm

    dm = importlib.reload(dm)
    assert dm._DASH_AVAILABLE is True
    app = DummyApp()
    dm.register_data_manager_callbacks(app)

    by_name = {fn.__name__: fn for fn in app.callbacks}
    assert "update_endf_inputs" in by_name
    assert "download_endf_data" in by_name
    assert "save_configuration" in by_name

    update_endf_inputs = by_name["update_endf_inputs"]
    download_endf_data = by_name["download_endf_data"]
    save_configuration = by_name["save_configuration"]

    # update_endf_inputs branches
    iso = update_endf_inputs("isotopes")
    assert isinstance(iso, dbc.Input)
    assert iso.id == "endf-isotopes-input"
    ele = update_endf_inputs("elements")
    assert isinstance(ele, dbc.Input)
    assert ele.id == "endf-elements-input"
    assert update_endf_inputs("unknown") == ""

    # download_endf_data branches
    alert, progress = download_endf_data(
        1, "ENDF/B-VIII.1", "isotopes", None, None, None, 2
    )
    assert isinstance(alert, dbc.Alert)
    assert progress == ""

    with patch(
        "smrforge.data_downloader.download_endf_data",
        return_value={"downloaded": 1, "skipped": 2, "failed": 3},
    ):
        ok_alert, ok_progress = download_endf_data(
            1, "ENDF/B-VIII.1", "elements", None, "U, Pu", "C:\\tmp", 1
        )
        assert isinstance(ok_alert, dbc.Alert)
        assert ok_progress == ""

    with patch(
        "smrforge.data_downloader.download_endf_data",
        return_value={"downloaded": 1, "skipped": 0, "failed": 0},
    ):
        ok_alert, ok_progress = download_endf_data(
            1, "ENDF/B-VIII.1", "isotopes", "U235, U238", None, "C:\\tmp", 1
        )
        assert isinstance(ok_alert, dbc.Alert)
        assert ok_progress == ""

    with patch(
        "smrforge.data_downloader.download_endf_data", side_effect=RuntimeError("boom")
    ):
        err_alert, err_progress = download_endf_data(
            1, "ENDF/B-VIII.1", "common_smr", None, None, None, None
        )
        assert isinstance(err_alert, dbc.Alert)
        assert err_progress == ""

    # save_configuration branches
    assert save_configuration(0, None, None) == ""
    msg = save_configuration(1, "C:\\endf", "C:\\cache")
    assert isinstance(msg, dbc.Alert)
    msg2 = save_configuration(1, None, None)
    assert isinstance(msg2, dbc.Alert)

    # exception branch
    with patch.object(dm.html, "P", side_effect=RuntimeError("fail html.P")):
        out = save_configuration(1, "C:\\endf", None)
        assert isinstance(out, dbc.Alert)
