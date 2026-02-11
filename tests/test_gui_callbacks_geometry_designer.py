import builtins
import importlib
import sys
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
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
        if name == "plotly" or name.startswith("plotly."):
            raise ImportError("forced plotly ImportError for coverage")
        return real_import(name, globals, locals, fromlist, level)

    sys.modules.pop(module_name, None)
    with patch("builtins.__import__", side_effect=guarded_import):
        return importlib.import_module(module_name)


def test_register_geometry_designer_callbacks_no_dash_returns_early():
    mod = _import_module_without_dash("smrforge.gui.callbacks.geometry_designer")
    assert mod._DASH_AVAILABLE is False
    app = DummyApp()
    assert mod.register_geometry_designer_callbacks(app) is None
    assert app.callbacks == []


def test_geometry_designer_callbacks_cover_branches():
    from smrforge.gui.callbacks import geometry_designer as gd

    gd = importlib.reload(gd)
    assert gd._DASH_AVAILABLE is True

    app = DummyApp()
    gd.register_geometry_designer_callbacks(app)
    by_name = {fn.__name__: fn for fn in app.callbacks}

    update_core_layout = by_name["update_core_layout"]
    update_preview_and_stats = by_name["update_preview_and_stats"]
    update_tool = by_name["update_tool"]
    update_click_info = by_name["update_click_info"]

    # Initialize with no trigger
    with patch.object(gd, "callback_context", SimpleNamespace(triggered=[])):
        fig, data, palette = update_core_layout(
            "prismatic",
            2,
            2,
            36.0,
            None,
            "fuel",
            {"tool": "paint"},
            None,
            None,
            None,
            19.5,
            "UCO",
        )
        assert isinstance(data["layout"], np.ndarray)
        assert data["layout"].shape == (2, 2)

    # Clear button
    with patch.object(
        gd,
        "callback_context",
        SimpleNamespace(triggered=[{"prop_id": "geometry-clear-btn.n_clicks"}]),
    ):
        fig, data, palette = update_core_layout(
            "prismatic",
            2,
            2,
            36.0,
            None,
            "fuel",
            {"tool": "paint"},
            1,
            None,
            data,
            19.5,
            "UCO",
        )
        assert int(data["layout"].sum()) == 0

    # Reset button
    with patch.object(
        gd,
        "callback_context",
        SimpleNamespace(triggered=[{"prop_id": "geometry-reset-btn.n_clicks"}]),
    ):
        fig, data, palette = update_core_layout(
            "prismatic",
            3,
            3,
            36.0,
            None,
            "fuel",
            {"tool": "paint"},
            None,
            1,
            data,
            19.5,
            "UCO",
        )
        assert data["layout"].shape == (3, 3)

    # Paint click
    click_data = {"points": [{"x": 1, "y": 2}]}
    with patch.object(
        gd,
        "callback_context",
        SimpleNamespace(triggered=[{"prop_id": "geometry-core-layout.clickData"}]),
    ):
        fig, data, palette = update_core_layout(
            "prismatic",
            3,
            3,
            36.0,
            click_data,
            "fuel",
            {"tool": "paint"},
            None,
            None,
            data,
            10.0,
            "UO2",
        )
        assert int(data["layout"][2, 1]) == 1
        assert data["materials"]["2,1"] == "fuel"

    # Erase click
    with patch.object(
        gd,
        "callback_context",
        SimpleNamespace(triggered=[{"prop_id": "geometry-core-layout.clickData"}]),
    ):
        fig, data, palette = update_core_layout(
            "prismatic",
            3,
            3,
            36.0,
            click_data,
            None,
            {"tool": "erase"},
            None,
            None,
            data,
            19.5,
            "UCO",
        )
        assert int(data["layout"][2, 1]) == 0

    # update_preview_and_stats: no data
    fig3d, stats, props = update_preview_and_stats(None, None)
    assert fig3d is not None

    # update_preview_and_stats: with hover (no props)
    fig3d, stats, props = update_preview_and_stats(
        {"layout": np.zeros((2, 2), dtype=int), "materials": {}, "properties": {}}, None
    )
    assert fig3d is not None

    # update_preview_and_stats: with hover and props
    geometry_data = {
        "layout": np.zeros((2, 2), dtype=int),
        "materials": {"0,0": "fuel"},
        "properties": {"0,0": {"enrichment": 19.5, "fuel_type": "UCO"}},
    }
    hover = {"points": [{"x": 0, "y": 0}]}
    fig3d, stats, props = update_preview_and_stats(geometry_data, hover)
    assert fig3d is not None

    # update_tool: no ctx.triggered
    with patch.object(gd, "callback_context", SimpleNamespace(triggered=[])):
        with pytest.raises(gd.PreventUpdate):
            update_tool(None, None, None, None)

    # update_tool: each tool id
    for btn, expected in [
        ("geometry-tool-select.n_clicks", "select"),
        ("geometry-tool-paint.n_clicks", "paint"),
        ("geometry-tool-fill.n_clicks", "fill"),
        ("geometry-tool-erase.n_clicks", "erase"),
        ("geometry-tool-unknown.n_clicks", "paint"),
    ]:
        with patch.object(
            gd, "callback_context", SimpleNamespace(triggered=[{"prop_id": btn}])
        ):
            out = update_tool(1, 1, 1, 1)
            assert out["tool"] == expected

    # update_click_info branches
    assert "Click on the core layout" in update_click_info({}).children
    assert "Clicked" in update_click_info({"points": [{"x": 1, "y": 1}]}).children

    # Direct helper coverage
    fig = gd._create_core_layout_figure(np.array([[0, 1], [2, 3]]), 36.0)
    assert fig is not None
    fig3d = gd._create_3d_preview(np.array([[0, 1], [2, 3]]))
    assert fig3d is not None
    div = gd._calculate_core_statistics({"layout": np.array([[0, 1], [2, 3]])})
    assert div is not None
    div2 = gd._calculate_core_statistics(None)
    assert div2 is not None
