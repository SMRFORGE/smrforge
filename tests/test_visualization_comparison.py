from types import SimpleNamespace

import numpy as np
import pytest


class DummyPlotlyFigure:
    def __init__(self):
        self.traces = []
        self.x_updates = []
        self.y_updates = []
        self.layout_updates = []

    def add_trace(self, trace, row=None, col=None):
        self.traces.append((trace, row, col))

    def update_xaxes(self, **kwargs):
        self.x_updates.append(kwargs)

    def update_yaxes(self, **kwargs):
        self.y_updates.append(kwargs)

    def update_layout(self, **kwargs):
        self.layout_updates.append(kwargs)


def test_compare_designs_matplotlib_and_plotly_and_overlay(monkeypatch):
    import smrforge.visualization.comparison as comp

    # Geometry types missing -> ImportError
    monkeypatch.setattr(comp, "_GEOMETRY_TYPES_AVAILABLE", False)
    with pytest.raises(ImportError):
        comp.compare_designs_matplotlib({"A": {"geometry": object()}})

    # Patch geometry availability + layout plotter
    monkeypatch.setattr(comp, "_GEOMETRY_TYPES_AVAILABLE", True)

    def fake_plot_core_layout(geometry, *, view, ax, show_labels=False, **kwargs):
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)

    monkeypatch.setattr(comp, "plot_core_layout", fake_plot_core_layout)
    monkeypatch.setattr(comp.plt, "colorbar", lambda *args, **kwargs: None)

    geom = object()
    data = np.arange(4, dtype=float).reshape(2, 2)

    # Missing geometry for a design -> ValueError
    with pytest.raises(ValueError):
        comp.compare_designs_matplotlib({"A": {"data": data}})

    fig, axes = comp.compare_designs_matplotlib(
        {
            "A": {"geometry": geom, "data": data},
            "B": {"geometry": geom, "data": data},
        },
        n_cols=2,
        colorbar_shared=True,
    )
    assert fig is not None
    assert len(axes) >= 2

    # Plotly path: ImportError when plotly unavailable
    monkeypatch.setattr(comp, "_PLOTLY_AVAILABLE", False)
    with pytest.raises(ImportError):
        comp.compare_designs_plotly({"A": {"geometry": geom, "data": data}})

    # Patch plotly backend with stubs
    monkeypatch.setattr(comp, "_PLOTLY_AVAILABLE", True)
    dummy_go = SimpleNamespace(Heatmap=lambda **kwargs: SimpleNamespace(kwargs=kwargs))
    monkeypatch.setattr(comp, "go", dummy_go, raising=False)
    monkeypatch.setattr(
        comp, "make_subplots", lambda **kwargs: DummyPlotlyFigure(), raising=False
    )

    figp = comp.compare_designs_plotly(
        {"A": {"geometry": geom, "data": data}, "B": {"geometry": geom, "data": data}},
        n_cols=2,
    )
    assert isinstance(figp, DummyPlotlyFigure)
    assert len(figp.traces) == 2

    # compare_metrics_matplotlib covers both 1D and (n,2) arrays
    mfig, max_ = comp.compare_metrics_matplotlib(
        {
            "A": {"keff": np.array([1.0, 1.01])},
            "B": {"rho": np.array([[0.0, 0.0], [1.0, 1.0]])},
        }
    )
    assert mfig is not None
    assert max_ is not None

    # overlay_comparison_matplotlib: input validation
    with pytest.raises(ValueError):
        comp.overlay_comparison_matplotlib([geom], labels=["a", "b"])

    # Patch PrismaticCore type and provide blocks to hit annotation branch
    class DummyPrismatic:
        def __init__(self):
            self.blocks = [SimpleNamespace(position=SimpleNamespace(x=0.0, y=0.0))]

    monkeypatch.setattr(comp, "PrismaticCore", DummyPrismatic, raising=False)
    g1 = DummyPrismatic()

    figo, axo = comp.overlay_comparison_matplotlib(
        geometries=[g1],
        labels=["Design A"],
        colors=["blue"],
    )
    assert figo is not None
    assert axo is not None
