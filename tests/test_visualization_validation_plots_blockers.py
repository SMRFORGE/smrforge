import builtins
import importlib
import sys
from types import SimpleNamespace

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
        return self

    def update_layout(self, **kwargs):
        self.layout_updates.append(dict(kwargs))
        return self


class _DummyGo:
    Figure = _DummyFigure

    class Bar(_DummyTrace):
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
    """Reload an already-imported module while blocking an optional dependency import."""
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == blocked_prefix or name.startswith(blocked_prefix + "."):
            raise ImportError(f"blocked import: {blocked_prefix}")
        return real_import(name, globals, locals, fromlist, level)

    with monkeypatch.context() as mp:
        mp.setattr(builtins, "__import__", fake_import)
        return importlib.reload(module)


def test_validation_plots_import_fallbacks(monkeypatch):
    import smrforge.visualization.validation_plots as vp

    m1 = _reload_module_with_blocked_import(monkeypatch, vp, "matplotlib")
    assert m1._MATPLOTLIB_AVAILABLE is False

    m2 = _reload_module_with_blocked_import(monkeypatch, vp, "plotly")
    assert m2._PLOTLY_AVAILABLE is False

    # Restore normal module state
    importlib.reload(vp)


def test_summary_counts_supported_and_unsupported():
    import smrforge.visualization.validation_plots as vp

    # data_validation-like shape (summary() -> dict)
    r1 = SimpleNamespace(summary=lambda: {"critical": 1, "error": 2, "warning": 3, "info": 4})
    assert vp._summary_counts(r1) == {"critical": 1, "error": 2, "warning": 3, "info": 4}

    # constraints-like shape (violations/warnings)
    r2 = SimpleNamespace(violations=[1, 2], warnings=[3])
    assert vp._summary_counts(r2)["error"] == 2
    assert vp._summary_counts(r2)["warning"] == 1

    with pytest.raises(ValueError, match="Unsupported validation result type"):
        vp._summary_counts(object())


def test_plot_validation_summary_plotly_matplotlib_and_errors(monkeypatch):
    import smrforge.visualization.validation_plots as vp

    r = SimpleNamespace(summary=lambda: {"critical": 0, "error": 1, "warning": 2, "info": 3})

    monkeypatch.setattr(vp, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(vp, "ensure_plotly_available", lambda ok: None)
    monkeypatch.setattr(vp, "go", _DummyGo)
    fig = vp.plot_validation_summary(r, backend="plotly", title="t")
    assert isinstance(fig, _DummyFigure)
    assert len(fig.traces) == 1

    monkeypatch.setattr(vp, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(vp, "ensure_matplotlib_available", lambda ok: None)
    monkeypatch.setattr(vp, "plt", _DummyPlt())
    fig_ax = vp.plot_validation_summary(r, backend="matplotlib", title="t")
    assert isinstance(fig_ax, tuple)

    with pytest.raises(ValueError, match="Unknown backend"):
        vp.plot_validation_summary(r, backend="nope")


def test_plot_validation_issues_data_validation_branch(monkeypatch):
    import smrforge.visualization.validation_plots as vp

    issues = [
        SimpleNamespace(parameter="a"),
        SimpleNamespace(parameter="a"),
        SimpleNamespace(parameter="b"),
    ]
    r = SimpleNamespace(issues=issues)

    monkeypatch.setattr(vp, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(vp, "ensure_plotly_available", lambda ok: None)
    monkeypatch.setattr(vp, "go", _DummyGo)
    fig = vp.plot_validation_issues(r, backend="plotly", max_items=20)
    assert isinstance(fig, _DummyFigure)

    monkeypatch.setattr(vp, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(vp, "ensure_matplotlib_available", lambda ok: None)
    monkeypatch.setattr(vp, "plt", _DummyPlt())
    fig_ax = vp.plot_validation_issues(r, backend="matplotlib", max_items=20)
    assert isinstance(fig_ax, tuple)

    with pytest.raises(ValueError, match="Unknown backend"):
        vp.plot_validation_issues(r, backend="nope")


def test_plot_validation_issues_constraints_branch(monkeypatch):
    import smrforge.visualization.validation_plots as vp

    # No violations -> error
    empty = SimpleNamespace(violations=[], warnings=[])
    with pytest.raises(ValueError, match="No violations/warnings"):
        vp.plot_validation_issues(empty, backend="plotly")

    # A couple violations/warnings with varying severity and sign.
    v1 = SimpleNamespace(constraint_name="c1", value=1.0, limit=2.0, severity="warning")
    v2 = SimpleNamespace(constraint_name="c2", value=10.0, limit=3.0, severity="error")
    r = SimpleNamespace(violations=[v2], warnings=[v1])

    monkeypatch.setattr(vp, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(vp, "ensure_plotly_available", lambda ok: None)
    monkeypatch.setattr(vp, "go", _DummyGo)
    fig = vp.plot_validation_issues(r, backend="plotly")
    assert isinstance(fig, _DummyFigure)
    assert fig.traces

    monkeypatch.setattr(vp, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(vp, "ensure_matplotlib_available", lambda ok: None)
    monkeypatch.setattr(vp, "plt", _DummyPlt())
    fig_ax = vp.plot_validation_issues(r, backend="matplotlib")
    assert isinstance(fig_ax, tuple)

    with pytest.raises(ValueError, match="Unknown backend"):
        vp.plot_validation_issues(r, backend="nope")

