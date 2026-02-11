import builtins
import importlib
import sys

import numpy as np
import pytest


class _DummyTrace:
    def __init__(self, **kwargs):
        self.kwargs = dict(kwargs)


class _DummyFigure:
    def __init__(self, data=None):
        self.data = []
        self.layout_updates = []
        self.xaxes_updates = []
        self.yaxes_updates = []
        if data is None:
            return
        if isinstance(data, list):
            self.data.extend(data)
        else:
            self.data.append(data)

    def add_trace(self, trace, row=None, col=None):
        self.data.append((trace, row, col))
        return self

    def update_layout(self, **kwargs):
        self.layout_updates.append(dict(kwargs))
        return self

    def update_xaxes(self, **kwargs):
        self.xaxes_updates.append(dict(kwargs))
        return self

    def update_yaxes(self, **kwargs):
        self.yaxes_updates.append(dict(kwargs))
        return self


class _DummyGo:
    Figure = _DummyFigure

    class Heatmap(_DummyTrace):
        pass

    class Volume(_DummyTrace):
        pass


def _dummy_make_subplots(*args, **kwargs):
    return _DummyFigure()


class _DummyPv:
    class Plotter:
        def __init__(self):
            self.meshes = []
            self.show_axes_called = False

        def add_mesh(self, mesh, **kwargs):
            self.meshes.append((mesh, dict(kwargs)))

        def show_axes(self):
            self.show_axes_called = True

    class StructuredGrid(dict):
        def __init__(self, x, y, z):
            super().__init__()
            self.x = np.asarray(x)
            self.y = np.asarray(y)
            self.z = np.asarray(z)


class _DummyPlt:
    def __init__(self):
        self.colorbars = 0

    def subplots(self, *args, **kwargs):
        if args and args[0] == 1 and args[1] == 2:
            fig = object()
            return fig, (_DummyAx(), _DummyAx())
        fig = object()
        return fig, _DummyAx()

    def figure(self, *args, **kwargs):
        return _DummyFig()

    def colorbar(self, *args, **kwargs):
        self.colorbars += 1


class _DummyFig:
    def add_subplot(self, *args, **kwargs):
        return _DummyAx()


class _DummyAx:
    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            return _DummyTrace()

        return _noop


def test_extract_uncertainty_for_view_none_and_errors():
    import smrforge.visualization.mesh_tally as mt

    mesh = mt.MeshTally(
        name="t",
        tally_type="flux",
        data=np.zeros((2, 2, 2, 3)),
        mesh_coords=(np.arange(3), np.arange(3), np.arange(3)),
        uncertainty=None,
        geometry_type="cartesian",
    )
    assert mt._extract_uncertainty_for_view(mesh, energy_group=None) is None

    mesh_bad = mt.MeshTally(
        name="t",
        tally_type="flux",
        data=np.zeros((2, 2, 2, 3)),
        mesh_coords=(np.arange(3), np.arange(3), np.arange(3)),
        uncertainty=np.zeros((2, 2, 2, 4)),
        geometry_type="cartesian",
    )
    with pytest.raises(ValueError, match="must have the same shape"):
        mt._extract_uncertainty_for_view(mesh_bad, energy_group=None)

    mesh_ok = mt.MeshTally(
        name="t",
        tally_type="flux",
        data=np.ones((2, 2, 2, 3)),
        mesh_coords=(np.arange(3), np.arange(3), np.arange(3)),
        uncertainty=np.ones((2, 2, 2, 3)) * 0.1,
        geometry_type="cartesian",
    )
    rel = mt._extract_uncertainty_for_view(mesh_ok, energy_group=None, mode="percent")
    assert rel.shape == (2, 2, 2)
    assert np.all(rel >= 0.0)

    absu = mt._extract_uncertainty_for_view(mesh_ok, energy_group=0, mode="absolute")
    assert absu.shape == (2, 2, 2)

    with pytest.raises(ValueError, match="uncertainty_mode"):
        mt._extract_uncertainty_for_view(mesh_ok, energy_group=None, mode="nope")


def test_meshtally_get_total_and_group_branches():
    import smrforge.visualization.mesh_tally as mt

    m4 = mt.MeshTally(
        name="t",
        tally_type="flux",
        data=np.ones((2, 2, 2, 3)),
        mesh_coords=(np.arange(3), np.arange(3), np.arange(3)),
        geometry_type="cartesian",
    )
    assert m4.get_total().shape == (2, 2, 2)
    assert m4.get_group(1).shape == (2, 2, 2)

    m3 = mt.MeshTally(
        name="t",
        tally_type="flux",
        data=np.ones((2, 2, 3)),
        mesh_coords=(np.arange(3), np.arange(3)),
        geometry_type="cylindrical",
    )
    assert m3.get_total().shape == (2, 2)
    assert m3.get_group(0).shape == (2, 2)
    assert m3.get_group(1).shape == (2, 2)

    # Single-group data: group 0 returns data; group >0 raises.
    m_single = mt.MeshTally(
        name="t",
        tally_type="flux",
        data=np.ones((2, 2)),
        mesh_coords=(np.arange(3), np.arange(3)),
        geometry_type="cylindrical",
    )
    assert np.array_equal(m_single.get_group(0), m_single.data)
    with pytest.raises(IndexError):
        m_single.get_group(1)

    spec = m_single.get_energy_spectrum((0, 0))
    assert spec.shape == (1,)

    m_mg = mt.MeshTally(
        name="t",
        tally_type="flux",
        data=np.arange(2 * 2 * 3, dtype=float).reshape(2, 2, 3),
        mesh_coords=(np.arange(3), np.arange(3)),
        geometry_type="cylindrical",
    )
    spec2 = m_mg.get_energy_spectrum((0, 0))
    assert spec2.shape == (3,)


def test_plot_mesh_tally_backend_errors():
    import smrforge.visualization.mesh_tally as mt

    mesh = mt.MeshTally(
        name="t",
        tally_type="flux",
        data=np.ones((2, 2)),
        mesh_coords=(np.arange(3), np.arange(3)),
        geometry_type="cylindrical",
    )

    with pytest.raises(ValueError, match="Unknown backend"):
        mt.plot_mesh_tally(mesh, geometry=object(), backend="nope")

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(mt, "_PLOTLY_AVAILABLE", False)
    with pytest.raises(ImportError):
        mt.plot_mesh_tally(mesh, geometry=object(), backend="plotly")
    monkeypatch.undo()


def test_plot_mesh_tally_matplotlib_requires_matplotlib(monkeypatch):
    import smrforge.visualization.mesh_tally as mt

    mesh = mt.MeshTally(
        name="t",
        tally_type="flux",
        data=np.ones((2, 2)),
        mesh_coords=(np.arange(3), np.arange(3)),
        geometry_type="cylindrical",
    )
    monkeypatch.setattr(mt, "_MATPLOTLIB_AVAILABLE", False)
    with pytest.raises(ImportError):
        mt.plot_mesh_tally(mesh, geometry=object(), backend="matplotlib")


def test_plot_mesh_tally_pyvista_requires_pyvista(monkeypatch):
    import smrforge.visualization.mesh_tally as mt

    mesh = mt.MeshTally(
        name="t",
        tally_type="flux",
        data=np.ones((2, 2)),
        mesh_coords=(np.arange(3), np.arange(3)),
        geometry_type="cylindrical",
    )
    monkeypatch.setattr(mt, "_PYVISTA_AVAILABLE", False)
    with pytest.raises(ImportError):
        mt.plot_mesh_tally(mesh, geometry=object(), backend="pyvista")


def test_plot_mesh_tally_plotly_cylindrical_with_uncertainty(monkeypatch):
    import smrforge.visualization.mesh_tally as mt

    monkeypatch.setattr(mt, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(mt, "go", _DummyGo)
    monkeypatch.setattr(mt, "make_subplots", _dummy_make_subplots)

    r = np.array([0.0, 1.0, 2.0])
    z = np.array([0.0, 10.0, 20.0])
    data = np.arange(4, dtype=float).reshape(2, 2)
    unc = np.ones_like(data) * 0.1

    mesh = mt.MeshTally(
        name="flux",
        tally_type="flux",
        data=data,
        uncertainty=unc,
        mesh_coords=(r, z),
        geometry_type="cylindrical",
    )
    fig = mt.plot_mesh_tally(
        mesh, geometry=object(), backend="plotly", show_uncertainty=True
    )
    assert isinstance(fig, _DummyFigure)
    assert len(fig.data) >= 2


def test_plot_mesh_tally_plotly_cylindrical_no_uncertainty(monkeypatch):
    import smrforge.visualization.mesh_tally as mt

    monkeypatch.setattr(mt, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(mt, "go", _DummyGo)

    r = np.array([0.0, 1.0, 2.0])
    z = np.array([0.0, 10.0, 20.0])
    data = np.arange(4, dtype=float).reshape(2, 2)

    mesh = mt.MeshTally(
        name="flux",
        tally_type="flux",
        data=data,
        mesh_coords=(r, z),
        geometry_type="cylindrical",
    )
    fig = mt.plot_mesh_tally(
        mesh, geometry=object(), backend="plotly", show_uncertainty=False
    )
    assert isinstance(fig, _DummyFigure)


def test_plot_mesh_tally_plotly_cartesian_volume(monkeypatch):
    import smrforge.visualization.mesh_tally as mt

    monkeypatch.setattr(mt, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(mt, "go", _DummyGo)

    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.0, 1.0, 2.0])
    z = np.array([0.0, 1.0, 2.0])
    data = np.arange(8, dtype=float).reshape(2, 2, 2)

    mesh = mt.MeshTally(
        name="flux",
        tally_type="flux",
        data=data,
        mesh_coords=(x, y, z),
        geometry_type="cartesian",
    )
    fig = mt.plot_mesh_tally(mesh, geometry=object(), backend="plotly")
    assert isinstance(fig, _DummyFigure)
    assert len(fig.data) >= 1
    trace = fig.data[0]
    assert isinstance(trace, _DummyTrace)
    assert len(trace.kwargs["x"]) == 8
    assert len(trace.kwargs["y"]) == 8
    assert len(trace.kwargs["z"]) == 8
    assert len(trace.kwargs["value"]) == 8

    # Validate ordering matches meshgrid(..., indexing="ij").flatten()
    assert np.allclose(trace.kwargs["x"], [0.5] * 4 + [1.5] * 4)
    assert np.allclose(trace.kwargs["y"], [0.5, 0.5, 1.5, 1.5] * 2)
    assert np.allclose(trace.kwargs["z"], [0.5, 1.5] * 4)


def test_plot_mesh_tally_plotly_cartesian_group_title(monkeypatch):
    import smrforge.visualization.mesh_tally as mt

    monkeypatch.setattr(mt, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(mt, "go", _DummyGo)

    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.0, 1.0, 2.0])
    z = np.array([0.0, 1.0, 2.0])
    data = np.ones((2, 2, 2, 3))

    mesh = mt.MeshTally(
        name="flux",
        tally_type="flux",
        data=data,
        mesh_coords=(x, y, z),
        geometry_type="cartesian",
    )
    fig = mt.plot_mesh_tally(mesh, geometry=object(), backend="plotly", energy_group=1)
    assert isinstance(fig, _DummyFigure)


def test_plot_mesh_tally_matplotlib_cylindrical_no_uncertainty(monkeypatch):
    import smrforge.visualization.mesh_tally as mt

    monkeypatch.setattr(mt, "_MATPLOTLIB_AVAILABLE", True)
    plt = _DummyPlt()
    monkeypatch.setattr(mt, "plt", plt)

    r = np.array([0.0, 1.0, 2.0])
    z = np.array([0.0, 10.0, 20.0])
    data = np.arange(4, dtype=float).reshape(2, 2)

    mesh_c = mt.MeshTally(
        name="flux",
        tally_type="flux",
        data=data,
        mesh_coords=(r, z),
        geometry_type="cylindrical",
    )
    fig_ax = mt.plot_mesh_tally(
        mesh_c, geometry=object(), backend="matplotlib", show_uncertainty=False
    )
    assert isinstance(fig_ax, tuple)


def test_plot_mesh_tally_matplotlib_cartesian_with_uncertainty(monkeypatch):
    import smrforge.visualization.mesh_tally as mt

    monkeypatch.setattr(mt, "_MATPLOTLIB_AVAILABLE", True)
    plt = _DummyPlt()
    monkeypatch.setattr(mt, "plt", plt)

    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.0, 1.0, 2.0])
    z = np.array([0.0, 1.0, 2.0])
    data = np.ones((2, 2, 2))
    unc = np.ones_like(data) * 0.1

    mesh_xyz = mt.MeshTally(
        name="flux",
        tally_type="flux",
        data=data,
        uncertainty=unc,
        mesh_coords=(x, y, z),
        geometry_type="cartesian",
    )
    fig_axes = mt.plot_mesh_tally(
        mesh_xyz,
        geometry=object(),
        backend="matplotlib",
        show_uncertainty=True,
        uncertainty_mode="relative",
    )
    assert isinstance(fig_axes, tuple)


def test_plot_mesh_tally_matplotlib_cylindrical_and_cartesian(monkeypatch):
    import smrforge.visualization.mesh_tally as mt

    monkeypatch.setattr(mt, "_MATPLOTLIB_AVAILABLE", True)
    plt = _DummyPlt()
    monkeypatch.setattr(mt, "plt", plt)

    r = np.array([0.0, 1.0, 2.0])
    z = np.array([0.0, 10.0, 20.0])
    data = np.arange(4, dtype=float).reshape(2, 2)
    unc = np.ones_like(data) * 0.1

    mesh_c = mt.MeshTally(
        name="flux",
        tally_type="flux",
        data=data,
        uncertainty=unc,
        mesh_coords=(r, z),
        geometry_type="cylindrical",
    )
    fig_axes = mt.plot_mesh_tally(
        mesh_c, geometry=object(), backend="matplotlib", show_uncertainty=True
    )
    assert isinstance(fig_axes, tuple)

    # Cartesian 3D slice path
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.0, 1.0, 2.0])
    z2 = np.array([0.0, 1.0, 2.0])
    data3 = np.arange(8, dtype=float).reshape(2, 2, 2)
    mesh_xyz = mt.MeshTally(
        name="flux",
        tally_type="flux",
        data=data3,
        mesh_coords=(x, y, z2),
        geometry_type="cartesian",
    )
    fig_axes2 = mt.plot_mesh_tally(
        mesh_xyz, geometry=object(), backend="matplotlib", show_uncertainty=False
    )
    assert isinstance(fig_axes2, tuple)

    # energy_group path for 2D multi-group
    data_mg = np.arange(2 * 2 * 3, dtype=float).reshape(2, 2, 3)
    mesh_mg = mt.MeshTally(
        name="flux",
        tally_type="flux",
        data=data_mg,
        mesh_coords=(r, z),
        geometry_type="cylindrical",
    )
    fig_axes3 = mt.plot_mesh_tally(
        mesh_mg,
        geometry=object(),
        backend="matplotlib",
        energy_group=1,
        show_uncertainty=False,
    )
    assert isinstance(fig_axes3, tuple)


def test_plot_mesh_tally_pyvista(monkeypatch):
    import smrforge.visualization.mesh_tally as mt

    monkeypatch.setattr(mt, "_PYVISTA_AVAILABLE", True)
    monkeypatch.setattr(mt, "pv", _DummyPv)

    r = np.array([0.0, 1.0, 2.0])
    z = np.array([0.0, 10.0, 20.0])
    data = np.arange(4, dtype=float).reshape(2, 2)

    mesh_c = mt.MeshTally(
        name="flux",
        tally_type="flux",
        data=data,
        mesh_coords=(r, z),
        geometry_type="cylindrical",
    )
    plotter = mt.plot_mesh_tally(mesh_c, geometry=object(), backend="pyvista")
    assert isinstance(plotter, _DummyPv.Plotter)
    assert plotter.show_axes_called is True

    # Cartesian pyvista path
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.0, 1.0, 2.0])
    z2 = np.array([0.0, 1.0, 2.0])
    data3 = np.arange(8, dtype=float).reshape(2, 2, 2)
    mesh_xyz = mt.MeshTally(
        name="flux",
        tally_type="flux",
        data=data3,
        mesh_coords=(x, y, z2),
        geometry_type="cartesian",
    )
    plotter2 = mt.plot_mesh_tally(mesh_xyz, geometry=object(), backend="pyvista")
    assert isinstance(plotter2, _DummyPv.Plotter)

    # energy_group path (data.ndim == len(mesh_coords) + 1)
    data_mg = np.arange(2 * 2 * 3, dtype=float).reshape(2, 2, 3)
    mesh_mg = mt.MeshTally(
        name="flux",
        tally_type="flux",
        data=data_mg,
        mesh_coords=(r, z),
        geometry_type="cylindrical",
    )
    plotter3 = mt.plot_mesh_tally(
        mesh_mg, geometry=object(), backend="pyvista", energy_group=1
    )
    assert isinstance(plotter3, _DummyPv.Plotter)


def test_plot_multi_group_mesh_tally_paths(monkeypatch):
    import smrforge.visualization.mesh_tally as mt

    # ndim < 3 delegates
    mesh_single = mt.MeshTally(
        name="t",
        tally_type="flux",
        data=np.ones((2, 2)),
        mesh_coords=(np.arange(3), np.arange(3)),
        geometry_type="cylindrical",
    )
    monkeypatch.setattr(mt, "plot_mesh_tally", lambda *a, **k: "delegated")
    assert (
        mt.plot_multi_group_mesh_tally(mesh_single, geometry=object(), backend="plotly")
        == "delegated"
    )

    # plotly subplots path
    monkeypatch.setattr(mt, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(mt, "go", _DummyGo)
    monkeypatch.setattr(mt, "make_subplots", _dummy_make_subplots)

    r = np.array([0.0, 1.0, 2.0])
    z = np.array([0.0, 10.0, 20.0])
    data = np.arange(2 * 2 * 4, dtype=float).reshape(2, 2, 4)
    mesh_mg = mt.MeshTally(
        name="t",
        tally_type="flux",
        data=data,
        mesh_coords=(r, z),
        geometry_type="cylindrical",
    )
    fig = mt.plot_multi_group_mesh_tally(mesh_mg, geometry=object(), backend="plotly")
    assert isinstance(fig, _DummyFigure)

    # non-plotly returns list and calls plot_mesh_tally for each group
    calls = []

    def _pm(*args, **kwargs):
        calls.append(kwargs.get("energy_group"))
        return kwargs.get("energy_group")

    monkeypatch.setattr(mt, "plot_mesh_tally", _pm)
    out = mt.plot_multi_group_mesh_tally(
        mesh_mg, geometry=object(), backend="matplotlib"
    )
    assert out == [0, 1, 2, 3]
    assert calls == [0, 1, 2, 3]


def test_mesh_tally_import_fallbacks(monkeypatch):
    """Cover import-time fallbacks for optional plotting deps."""
    real_import = builtins.__import__

    def _reload_with_blocked(prefix: str):
        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == prefix or name.startswith(prefix + "."):
                raise ImportError(f"blocked import: {prefix}")
            return real_import(name, globals, locals, fromlist, level)

        with monkeypatch.context() as mp:
            mp.setattr(builtins, "__import__", fake_import)
            sys.modules.pop("smrforge.visualization.mesh_tally", None)
            sys.modules.pop(prefix, None)
            return importlib.import_module("smrforge.visualization.mesh_tally")

    mod = _reload_with_blocked("matplotlib")
    assert mod._MATPLOTLIB_AVAILABLE is False
    mod = _reload_with_blocked("plotly")
    assert mod._PLOTLY_AVAILABLE is False
    mod = _reload_with_blocked("pyvista")
    assert mod._PYVISTA_AVAILABLE is False

    import smrforge.visualization.mesh_tally as mt

    importlib.reload(mt)


def test_plot_multi_group_mesh_tally_plotly_requires_plotly(monkeypatch):
    import smrforge.visualization.mesh_tally as mt

    mesh_mg = mt.MeshTally(
        name="t",
        tally_type="flux",
        data=np.ones((2, 2, 4)),
        mesh_coords=(np.arange(3), np.arange(3)),
        geometry_type="cylindrical",
    )
    monkeypatch.setattr(mt, "_PLOTLY_AVAILABLE", False)
    with pytest.raises(ImportError):
        mt.plot_multi_group_mesh_tally(mesh_mg, geometry=object(), backend="plotly")
