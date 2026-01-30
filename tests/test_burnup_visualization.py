import builtins
import importlib
from types import SimpleNamespace

import numpy as np
import pytest


class DummyInventory:
    def __init__(self, times_s, burnup):
        self.times = times_s
        self.burnup = burnup


class DummyTrace:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class DummyFigure:
    def __init__(self):
        self.data = []
        self.layout_updates = []

    def add_trace(self, trace, row=None, col=None):
        self.data.append((trace, row, col))

    def update_layout(self, **kwargs):
        self.layout_updates.append(kwargs)


class DummyAx:
    def __init__(self):
        self.plots = []

    def plot(self, *args, **kwargs):
        self.plots.append((args, kwargs))

    def set_title(self, *args, **kwargs):
        pass

    def set_xlabel(self, *args, **kwargs):
        pass

    def set_ylabel(self, *args, **kwargs):
        pass

    def legend(self, *args, **kwargs):
        pass

    def grid(self, *args, **kwargs):
        pass


class DummyMplFig:
    def tight_layout(self):
        pass


def _patch_plotly_backend(monkeypatch, viz):
    dummy_go = SimpleNamespace(
        Figure=DummyFigure,
        Scatter=lambda **kwargs: DummyTrace(**kwargs),
    )
    monkeypatch.setattr(viz, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(viz, "go", dummy_go, raising=False)

    # make_subplots is imported as a name
    monkeypatch.setattr(viz, "make_subplots", lambda **kwargs: DummyFigure(), raising=False)


def _patch_matplotlib_backend(monkeypatch, viz):
    monkeypatch.setattr(viz, "_MATPLOTLIB_AVAILABLE", True)

    def subplots(**kwargs):
        return DummyMplFig(), DummyAx()

    dummy_plt = SimpleNamespace(subplots=lambda **kwargs: subplots(**kwargs))
    monkeypatch.setattr(viz, "plt", dummy_plt, raising=False)


def test_plot_batch_comparison_plotly_and_matplotlib_and_errors(monkeypatch):
    import smrforge.burnup.visualization as viz

    inv = DummyInventory(times_s=[0.0, 86400.0], burnup=[0.0, 1.0])
    batches = {2: inv, 1: inv}

    with pytest.raises(ValueError):
        viz.plot_batch_comparison({})

    with pytest.raises(ValueError):
        viz.plot_batch_comparison(batches, backend="nope")

    monkeypatch.setattr(viz, "_PLOTLY_AVAILABLE", False)
    with pytest.raises(ImportError):
        viz.plot_batch_comparison(batches, backend="plotly")

    _patch_plotly_backend(monkeypatch, viz)
    fig = viz.plot_batch_comparison(batches, backend="plotly", title="t")
    assert isinstance(fig, DummyFigure)
    assert len(fig.data) == 2

    monkeypatch.setattr(viz, "_MATPLOTLIB_AVAILABLE", False)
    with pytest.raises(ImportError):
        viz.plot_batch_comparison(batches, backend="matplotlib")

    _patch_matplotlib_backend(monkeypatch, viz)
    fig2, ax2 = viz.plot_batch_comparison(batches, backend="matplotlib")
    assert isinstance(fig2, DummyMplFig)
    assert isinstance(ax2, DummyAx)


def test_plot_refueling_cycles_plotly_and_matplotlib_and_errors(monkeypatch):
    import smrforge.burnup.visualization as viz

    inv1 = DummyInventory(times_s=[0.0], burnup=[0.0])
    inv2 = DummyInventory(times_s=[0.0], burnup=[1.0])
    cycles = {10: [inv1, inv2]}

    with pytest.raises(ValueError):
        viz.plot_refueling_cycles({})

    monkeypatch.setattr(viz, "_PLOTLY_AVAILABLE", False)
    with pytest.raises(ImportError):
        viz.plot_refueling_cycles(cycles, backend="plotly")

    _patch_plotly_backend(monkeypatch, viz)
    fig = viz.plot_refueling_cycles(cycles, backend="plotly")
    assert isinstance(fig, DummyFigure)
    assert len(fig.data) == 1
    trace, _, _ = fig.data[0]
    # ensure time offset logic applied (second cycle adds ~1095 days)
    assert max(trace.kwargs["x"]) >= 1000

    monkeypatch.setattr(viz, "_MATPLOTLIB_AVAILABLE", False)
    with pytest.raises(ImportError):
        viz.plot_refueling_cycles(cycles, backend="matplotlib")

    _patch_matplotlib_backend(monkeypatch, viz)
    fig2, ax2 = viz.plot_refueling_cycles(cycles, backend="matplotlib")
    assert isinstance(fig2, DummyMplFig)
    assert isinstance(ax2, DummyAx)

    with pytest.raises(ValueError):
        viz.plot_refueling_cycles(cycles, backend="nope")


def test_plot_control_rod_effects_plotly_and_matplotlib(monkeypatch):
    import smrforge.burnup.visualization as viz

    inv_with = DummyInventory(times_s=[0.0, 86400.0], burnup=[0.0, 1.0])
    inv_without = DummyInventory(times_s=[0.0, 86400.0], burnup=[0.0, 0.9])

    # Backend missing branches
    monkeypatch.setattr(viz, "_PLOTLY_AVAILABLE", False)
    with pytest.raises(ImportError):
        viz.plot_control_rod_effects(inv_with, backend="plotly")

    monkeypatch.setattr(viz, "_MATPLOTLIB_AVAILABLE", False)
    with pytest.raises(ImportError):
        viz.plot_control_rod_effects(inv_with, backend="matplotlib")

    _patch_plotly_backend(monkeypatch, viz)
    fig = viz.plot_control_rod_effects(
        {"inventory": inv_with},
        {"inventory": inv_without},
        backend="plotly",
    )
    assert isinstance(fig, DummyFigure)
    assert len(fig.data) == 2

    # Cover hasattr(..., "times") branches for plotly too
    fig2 = viz.plot_control_rod_effects(inv_with, inv_without, backend="plotly")
    assert isinstance(fig2, DummyFigure)

    _patch_matplotlib_backend(monkeypatch, viz)
    fig3, ax3 = viz.plot_control_rod_effects(inv_with, inv_without, backend="matplotlib")
    assert isinstance(fig3, DummyMplFig)
    assert isinstance(ax3, DummyAx)

    # Cover dict-based path for matplotlib too
    fig4, ax4 = viz.plot_control_rod_effects({"inventory": inv_with}, {"inventory": inv_without}, backend="matplotlib")
    assert isinstance(fig4, DummyMplFig)
    assert isinstance(ax4, DummyAx)

    with pytest.raises(ValueError):
        viz.plot_control_rod_effects(inv_with, backend="nope")


def test_plot_burnup_dashboard_enhanced_returns_base_and_enhanced(monkeypatch):
    import smrforge.burnup.visualization as viz

    # Patch plotly backend (needed for isinstance(base_fig, go.Figure))
    _patch_plotly_backend(monkeypatch, viz)

    # Patch base dashboard function that burnup.visualization imports at runtime.
    import smrforge.visualization.material_composition as mc

    def fake_plot_burnup_dashboard(*args, **kwargs):
        base = DummyFigure()
        # mimic a burnup trace and two composition traces
        base.data = [DummyTrace(name="burnup"), DummyTrace(name="comp1"), DummyTrace(name="comp2")]
        return base

    monkeypatch.setattr(mc, "plot_burnup_dashboard", fake_plot_burnup_dashboard)

    inv = DummyInventory(times_s=[0.0], burnup=[0.0])

    # No batches -> should return base fig
    base = viz.plot_burnup_dashboard_enhanced(inv, batch_inventories=None, backend="plotly")
    assert isinstance(base, DummyFigure)
    assert len(base.data) == 3

    # With batches -> should create new subplot fig and return it
    batch_inv = DummyInventory(times_s=[0.0, 86400.0], burnup=[0.0, 1.0])
    enhanced = viz.plot_burnup_dashboard_enhanced(
        inv,
        batch_inventories={1: batch_inv},
        backend="plotly",
    )
    assert isinstance(enhanced, DummyFigure)
    # 1 burnup + 2 composition + 1 batch trace = 4 added traces
    assert len(enhanced.data) == 4


def test_module_import_flags_for_missing_plotly_and_matplotlib(monkeypatch):
    # Reload module while forcing backend imports to fail.
    orig_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("plotly") or name.startswith("matplotlib"):
            raise ImportError("forced")
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    viz = importlib.import_module("smrforge.burnup.visualization")
    viz2 = importlib.reload(viz)
    assert viz2._PLOTLY_AVAILABLE is False
    assert viz2._MATPLOTLIB_AVAILABLE is False

    monkeypatch.setattr(builtins, "__import__", orig_import)
    importlib.reload(viz2)

