import builtins
import importlib
import sys

import numpy as np
import pytest


class _DummyTrace:
    def __init__(self, **kwargs):
        self.kwargs = dict(kwargs)


class _DummyFigure:
    def __init__(self):
        self.traces = []
        self.layout_updates = []

    def add_trace(self, trace):
        self.traces.append(trace)

    def update_layout(self, **kwargs):
        self.layout_updates.append(dict(kwargs))
        return self


class _DummyGo:
    Figure = _DummyFigure

    class Scatter3d(_DummyTrace):
        pass


class _DummyPatch:
    def __init__(self, vertices, **kwargs):
        self.vertices = vertices
        self.kwargs = dict(kwargs)


class _DummyAx:
    def __init__(self):
        self.patches = []
        self.text_calls = []
        self.aspect = None
        self.labels = {}
        self.title = None
        self.grid_calls = []
        self.transAxes = object()

    def add_patch(self, patch):
        self.patches.append(patch)

    def set_aspect(self, aspect):
        self.aspect = aspect

    def set_xlabel(self, s):
        self.labels["x"] = s

    def set_ylabel(self, s):
        self.labels["y"] = s

    def set_title(self, s):
        self.title = s

    def grid(self, *args, **kwargs):
        self.grid_calls.append((args, dict(kwargs)))

    def text(self, *args, **kwargs):
        self.text_calls.append((args, dict(kwargs)))


class _DummyPlt:
    def subplots(self, *args, **kwargs):
        return object(), _DummyAx()


def test_geometry_verification_import_fallbacks(monkeypatch):
    real_import = builtins.__import__

    def _reload_with_blocked(prefix: str):
        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == prefix or name.startswith(prefix + "."):
                raise ImportError(f"blocked import: {prefix}")
            return real_import(name, globals, locals, fromlist, level)

        with monkeypatch.context() as mp:
            mp.setattr(builtins, "__import__", fake_import)
            sys.modules.pop("smrforge.visualization.geometry_verification", None)
            sys.modules.pop(prefix, None)
            return importlib.import_module("smrforge.visualization.geometry_verification")

    mod = _reload_with_blocked("matplotlib")
    assert mod._MATPLOTLIB_AVAILABLE is False

    mod = _reload_with_blocked("plotly")
    assert mod._PLOTLY_AVAILABLE is False

    sys.modules.pop("smrforge.visualization.geometry_verification", None)
    importlib.import_module("smrforge.visualization.geometry_verification")


def test_plot_overlap_detection_plotly_and_matplotlib(monkeypatch):
    import smrforge.visualization.geometry_verification as gv

    class _Region:
        def __init__(self, verts):
            self._verts = verts

        def vertices(self):
            return list(self._verts)

    overlaps_3d = [("A", "B", _Region([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0)]))]
    overlaps_2d = [("A", "B", _Region([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]))]

    # plotly path
    monkeypatch.setattr(gv, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(gv, "go", _DummyGo)
    fig = gv.plot_overlap_detection(geometry=object(), overlaps=overlaps_3d, backend="plotly")
    assert isinstance(fig, _DummyFigure)
    assert len(fig.traces) == 1
    assert fig.traces[0].kwargs["mode"] == "lines"

    # Exercise the (currently no-op) geometry.blocks loop
    geom_blocks = type("G", (), {"blocks": [object()]})()
    fig_blocks = gv.plot_overlap_detection(geometry=geom_blocks, overlaps=overlaps_3d, backend="plotly")
    assert isinstance(fig_blocks, _DummyFigure)

    fig2 = gv.plot_overlap_detection(geometry=object(), overlaps=overlaps_2d, backend="plotly")
    assert isinstance(fig2, _DummyFigure)

    # matplotlib path
    monkeypatch.setattr(gv, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(gv, "plt", _DummyPlt())
    monkeypatch.setattr(gv, "Polygon", _DummyPatch)

    class _Block:
        def vertices(self):
            return [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]

    geom = type("G", (), {"blocks": [_Block()]})()
    fig_ax = gv.plot_overlap_detection(geometry=geom, overlaps=overlaps_2d, backend="matplotlib")
    assert isinstance(fig_ax, tuple)

    with pytest.raises(ValueError, match="Unknown backend"):
        gv.plot_overlap_detection(geometry=object(), overlaps=overlaps_2d, backend="nope")

    monkeypatch.setattr(gv, "_PLOTLY_AVAILABLE", False)
    with pytest.raises(ImportError):
        gv.plot_overlap_detection(geometry=object(), overlaps=overlaps_2d, backend="plotly")

    monkeypatch.setattr(gv, "_MATPLOTLIB_AVAILABLE", False)
    with pytest.raises(ImportError):
        gv.plot_overlap_detection(geometry=object(), overlaps=overlaps_2d, backend="matplotlib")


def test_plot_geometry_consistency_plotly_and_matplotlib(monkeypatch):
    import smrforge.visualization.geometry_verification as gv

    # plotly path uses advanced.plot_ray_traced_geometry
    adv_stub = type(sys)("smrforge.visualization.advanced")
    adv_stub.plot_ray_traced_geometry = lambda *a, **k: _DummyFigure()
    monkeypatch.setitem(sys.modules, "smrforge.visualization.advanced", adv_stub)

    monkeypatch.setattr(gv, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(gv, "go", _DummyGo)

    checks = {"a": True, "b": False}
    issues = ["Error: overlap", "warning: oddity"]
    fig = gv.plot_geometry_consistency(object(), checks, issues, backend="plotly")
    assert isinstance(fig, _DummyFigure)
    assert fig.layout_updates

    # matplotlib path imports visualization.geometry.plot_core_layout
    geom_stub = type(sys)("smrforge.visualization.geometry")
    geom_stub.plot_core_layout = lambda *a, **k: (object(), _DummyAx())
    monkeypatch.setitem(sys.modules, "smrforge.visualization.geometry", geom_stub)

    monkeypatch.setattr(gv, "_MATPLOTLIB_AVAILABLE", True)
    fig_ax = gv.plot_geometry_consistency(object(), {"ok": True}, ["note"], backend="matplotlib")
    assert isinstance(fig_ax, tuple)

    with pytest.raises(ValueError, match="Unknown backend"):
        gv.plot_geometry_consistency(object(), {"ok": True}, [], backend="nope")

    monkeypatch.setattr(gv, "_PLOTLY_AVAILABLE", False)
    with pytest.raises(ImportError):
        gv.plot_geometry_consistency(object(), {"ok": True}, [], backend="plotly")

    monkeypatch.setattr(gv, "_MATPLOTLIB_AVAILABLE", False)
    with pytest.raises(ImportError):
        gv.plot_geometry_consistency(object(), {"ok": True}, [], backend="matplotlib")


def test_plot_material_assignment_delegates_to_advanced(monkeypatch):
    import smrforge.visualization.geometry_verification as gv

    called = {}

    adv_stub = type(sys)("smrforge.visualization.advanced")

    def plot_material_boundaries(geometry, materials, backend="plotly", **kwargs):
        called["materials"] = list(materials)
        called["backend"] = backend
        return "ok"

    adv_stub.plot_material_boundaries = plot_material_boundaries
    monkeypatch.setitem(sys.modules, "smrforge.visualization.advanced", adv_stub)

    out = gv.plot_material_assignment(object(), {"a": "m1", "b": "m2"}, backend="matplotlib")
    assert out == "ok"
    assert called["materials"] == ["m1", "m2"]
    assert called["backend"] == "matplotlib"

