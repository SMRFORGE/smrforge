import builtins
import importlib

import pytest


def _import_without_dash(module_path: str):
    """
    Import a GUI component module while forcing dash/dbc imports to fail.
    Returns the imported module (reloaded under forced ImportError).
    """
    orig_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in {"dash", "dash_bootstrap_components"}:
            raise ImportError("forced for coverage")
        return orig_import(name, globals, locals, fromlist, level)

    mod = importlib.import_module(module_path)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(builtins, "__import__", guarded_import)
        mod = importlib.reload(mod)
    return mod


def test_gui_components_happy_and_no_dash_paths():
    # Happy path (Dash available in this test environment)
    from smrforge.gui.components import (
        analysis_panel,
        data_manager,
        feature_lab,
        geometry_designer,
        reactor_builder,
        results_viewer,
        sidebar,
    )

    assert analysis_panel.create_analysis_panel() is not None
    assert data_manager.create_data_manager() is not None
    assert feature_lab.create_feature_lab() is not None
    assert geometry_designer.create_geometry_designer() is not None
    assert reactor_builder.create_reactor_builder() is not None
    assert results_viewer.create_results_viewer() is not None
    assert sidebar.create_sidebar() is not None

    # No-dash import path (exercise ImportError branches and early returns)
    ap = _import_without_dash("smrforge.gui.components.analysis_panel")
    dm = _import_without_dash("smrforge.gui.components.data_manager")
    fl = _import_without_dash("smrforge.gui.components.feature_lab")
    gd = _import_without_dash("smrforge.gui.components.geometry_designer")
    rb = _import_without_dash("smrforge.gui.components.reactor_builder")
    rv = _import_without_dash("smrforge.gui.components.results_viewer")
    sb = _import_without_dash("smrforge.gui.components.sidebar")

    assert ap._DASH_AVAILABLE is False
    assert dm._DASH_AVAILABLE is False
    assert fl._DASH_AVAILABLE is False
    assert gd._DASH_AVAILABLE is False
    assert rb._DASH_AVAILABLE is False
    assert rv._DASH_AVAILABLE is False
    assert sb._DASH_AVAILABLE is False

    assert ap.create_analysis_panel() == "Dash not available"
    assert dm.create_data_manager() == "Dash not available"
    assert fl.create_feature_lab() == "Dash not available"
    assert gd.create_geometry_designer() == "Dash not available"
    assert rb.create_reactor_builder() == "Dash not available"
    assert rv.create_results_viewer() == "Dash not available"
    assert sb.create_sidebar() == "Dash not available"

