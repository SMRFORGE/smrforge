import builtins
import importlib
import sys

import pytest


class _DummyTrace:
    def __init__(self, **kwargs):
        self.kwargs = dict(kwargs)


class _DummyFigure:
    def __init__(self, data=None):
        self.data = []
        self.layout_updates = []
        if data is None:
            return
        if isinstance(data, list):
            self.data.extend(data)
        else:
            self.data.append(data)

    def add_trace(self, trace):
        self.data.append(trace)
        return self

    def update_layout(self, **kwargs):
        self.layout_updates.append(dict(kwargs))
        return self


class _DummyGo:
    Figure = _DummyFigure

    class Bar(_DummyTrace):
        pass

    class Waterfall(_DummyTrace):
        pass


class _DummyAx:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            self.calls.append((name, args, dict(kwargs)))
            return None

        return _noop


class _DummyFig:
    def __init__(self):
        self.tight = 0

    def tight_layout(self):
        self.tight += 1


class _DummyPlt:
    def subplots(self, *args, **kwargs):
        return _DummyFig(), _DummyAx()


def _reload_module_with_blocked_import(monkeypatch, module, blocked_prefix: str):
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == blocked_prefix or name.startswith(blocked_prefix + "."):
            raise ImportError(f"blocked import: {blocked_prefix}")
        return real_import(name, globals, locals, fromlist, level)

    with monkeypatch.context() as mp:
        mp.setattr(builtins, "__import__", fake_import)
        return importlib.reload(module)


def test_economics_plots_import_fallbacks(monkeypatch):
    import smrforge.visualization.economics_plots as ep

    m1 = _reload_module_with_blocked_import(monkeypatch, ep, "matplotlib")
    assert m1._MATPLOTLIB_AVAILABLE is False
    m2 = _reload_module_with_blocked_import(monkeypatch, ep, "plotly")
    assert m2._PLOTLY_AVAILABLE is False
    importlib.reload(ep)


def test_plot_capex_breakdown_plotly_waterfall_and_bar(monkeypatch):
    import smrforge.visualization.economics_plots as ep

    monkeypatch.setattr(ep, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(ep, "ensure_plotly_available", lambda ok: None)
    monkeypatch.setattr(ep, "go", _DummyGo)

    breakdown = {"reactor": 10.0, "turbine": 5.0, "total_overnight_cost": 20.0, "zero": 0.0}

    fig = ep.plot_capex_breakdown(breakdown, backend="plotly", kind="waterfall", top_n=2)
    assert isinstance(fig, _DummyFigure)
    assert fig.data

    fig2 = ep.plot_capex_breakdown(breakdown, backend="plotly", kind="bar", top_n=2)
    assert isinstance(fig2, _DummyFigure)

    with pytest.raises(ValueError, match="kind must be"):
        ep.plot_capex_breakdown(breakdown, backend="plotly", kind="nope")


def test_plot_capex_breakdown_matplotlib_bar_and_waterfall(monkeypatch):
    import smrforge.visualization.economics_plots as ep

    monkeypatch.setattr(ep, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(ep, "ensure_matplotlib_available", lambda ok: None)
    monkeypatch.setattr(ep, "plt", _DummyPlt())

    breakdown = {"reactor": 10.0, "turbine": -5.0, "total_overnight_cost": 10.0}

    fig_ax = ep.plot_capex_breakdown(breakdown, backend="matplotlib", kind="bar")
    assert isinstance(fig_ax, tuple)

    fig_ax2 = ep.plot_capex_breakdown(breakdown, backend="matplotlib", kind="waterfall")
    assert isinstance(fig_ax2, tuple)

    with pytest.raises(ValueError, match="kind must be"):
        ep.plot_capex_breakdown(breakdown, backend="matplotlib", kind="nope")


def test_plot_capex_breakdown_input_errors_and_unknown_backend():
    import smrforge.visualization.economics_plots as ep

    with pytest.raises(ValueError, match="non-empty dict"):
        ep.plot_capex_breakdown({})
    with pytest.raises(ValueError, match="non-empty dict"):
        ep.plot_capex_breakdown(None)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Unknown backend"):
        ep.plot_capex_breakdown({"a": 1.0}, backend="nope")


def test_plot_lcoe_breakdown_plotly_and_matplotlib(monkeypatch):
    import smrforge.visualization.economics_plots as ep

    lcoe = {"capital_contribution": 0.1, "operating_contribution": 0.2, "decommissioning_contribution": 0.3}

    monkeypatch.setattr(ep, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(ep, "ensure_plotly_available", lambda ok: None)
    monkeypatch.setattr(ep, "go", _DummyGo)
    fig = ep.plot_lcoe_breakdown(lcoe, backend="plotly")
    assert isinstance(fig, _DummyFigure)
    assert len(fig.data) == 3

    monkeypatch.setattr(ep, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(ep, "ensure_matplotlib_available", lambda ok: None)
    monkeypatch.setattr(ep, "plt", _DummyPlt())
    fig_ax = ep.plot_lcoe_breakdown(lcoe, backend="matplotlib")
    assert isinstance(fig_ax, tuple)

    with pytest.raises(ValueError, match="Unknown backend"):
        ep.plot_lcoe_breakdown(lcoe, backend="nope")

    with pytest.raises(ValueError, match="non-empty dict"):
        ep.plot_lcoe_breakdown({})

