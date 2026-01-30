import builtins
import importlib
import sys
from unittest.mock import Mock, patch


def _import_module_without_dash(module_name: str):
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


def test_register_theme_callbacks_no_dash_returns_early():
    mod = _import_module_without_dash("smrforge.gui.callbacks.theme")
    assert mod._DASH_AVAILABLE is False
    app = Mock()
    assert mod.register_theme_callbacks(app) is None


def test_register_theme_callbacks_registers_clientside_callbacks():
    from smrforge.gui.callbacks import theme

    theme = importlib.reload(theme)
    assert theme._DASH_AVAILABLE is True

    app = Mock()
    app.clientside_callback = Mock()

    with patch.object(theme, "clientside_callback", Mock()) as global_cb:
        theme.register_theme_callbacks(app)
        assert global_cb.call_count == 1
        assert app.clientside_callback.call_count == 2

