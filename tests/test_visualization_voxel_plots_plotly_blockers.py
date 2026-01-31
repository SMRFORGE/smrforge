import numpy as np


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

    def update_layout(self, **kwargs):
        self.layout_updates.append(dict(kwargs))
        return self


class _DummyGo:
    Figure = _DummyFigure

    class Volume(_DummyTrace):
        pass


def test_plot_voxel_plotly_constructs_flat_coords_and_uses_field(monkeypatch):
    import smrforge.visualization.voxel_plots as vp

    monkeypatch.setattr(vp, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(vp, "go", _DummyGo)

    voxel_grid = {
        "x": np.array([0.5, 1.5]),
        "y": np.array([10.5, 20.5, 30.5]),
        "z": np.array([100.5]),
        "material_ids": np.arange(6).reshape(2, 3, 1),
        "cell_ids": np.ones((2, 3, 1), dtype=int) * 7,
    }

    fig = vp._plot_voxel_plotly(
        voxel_grid,
        color_by="material",
        data=None,
        field_name=None,
        colors=None,
        background="white",
    )
    assert isinstance(fig, _DummyFigure)
    assert len(fig.data) == 1

    trace = fig.data[0]
    assert isinstance(trace, _DummyTrace)
    assert len(trace.kwargs["x"]) == 6
    assert len(trace.kwargs["y"]) == 6
    assert len(trace.kwargs["z"]) == 6
    assert len(trace.kwargs["value"]) == 6

    # Validate ordering matches meshgrid(..., indexing="ij").flatten()
    assert np.allclose(trace.kwargs["x"], [0.5] * 3 + [1.5] * 3)
    assert np.allclose(trace.kwargs["y"], [10.5, 20.5, 30.5] * 2)
    assert np.allclose(trace.kwargs["z"], [100.5] * 6)
    assert np.allclose(trace.kwargs["value"], np.arange(6))

    # data branch
    data = np.ones((2, 3, 1), dtype=float) * 42.0
    fig2 = vp._plot_voxel_plotly(
        voxel_grid,
        color_by="material",
        data=data,
        field_name="flux",
        colors=None,
        background="white",
    )
    trace2 = fig2.data[0]
    assert np.allclose(trace2.kwargs["value"], np.ones(6) * 42.0)
    assert trace2.kwargs["colorbar"]["title"] == "flux"

    # cell branch
    fig3 = vp._plot_voxel_plotly(
        voxel_grid,
        color_by="cell",
        data=None,
        field_name=None,
        colors=None,
        background="white",
    )
    trace3 = fig3.data[0]
    assert np.allclose(trace3.kwargs["value"], np.ones(6) * 7)
