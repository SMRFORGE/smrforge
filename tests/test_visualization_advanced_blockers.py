import numpy as np
import pytest


class _DummyTrace:
    def __init__(self, **kwargs):
        self.kwargs = dict(kwargs)


class _DummyFigure:
    def __init__(self, data=None):
        self.data = []
        self.frames = []
        self.layout_updates = []
        self.xaxes_updates = []
        self.yaxes_updates = []
        self.shapes = []
        if data is None:
            return
        if isinstance(data, list):
            self.data.extend(data)
        else:
            self.data.append(data)

    def add_trace(self, trace, row=None, col=None):
        self.data.append((trace, row, col))
        return self

    def add_shape(self, **kwargs):
        self.shapes.append(dict(kwargs))
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

    class Scatter3d(_DummyTrace):
        pass

    class Heatmap(_DummyTrace):
        pass

    class Volume(_DummyTrace):
        pass

    class Isosurface(_DummyTrace):
        pass

    class Cone(_DummyTrace):
        pass

    class Scatter(_DummyTrace):
        pass

    class Frame(_DummyTrace):
        pass

    class Layout(_DummyTrace):
        pass


def _dummy_make_subplots(*args, **kwargs):
    return _DummyFigure()


class _DummyPv:
    class Plotter:
        def __init__(self):
            self.meshes = []
            self.saved = []
            self.show_called = False
            self.show_axes_called = False

        def add_mesh(self, mesh, **kwargs):
            self.meshes.append((mesh, dict(kwargs)))

        def show_axes(self):
            self.show_axes_called = True

        def show(self):
            self.show_called = True

        def save(self, path):
            self.saved.append(path)

    class ImageData(dict):
        def __init__(self, dimensions, spacing, origin):
            super().__init__()
            self.dimensions = dimensions
            self.spacing = spacing
            self.origin = origin

        def contour(self, values, scalars=None):
            return {"values": list(values), "scalars": scalars}

    class PolyData(dict):
        def __init__(self, points):
            super().__init__()
            self.points = np.asarray(points)

        def glyph(self, orient, scale, factor):
            return {"glyph": True, "orient": orient, "scale": scale, "factor": factor}


class _Pos:
    def __init__(self, z):
        self.z = z


class _Block:
    def __init__(self, block_id=1, z=0.0, material="fuel", vertices=None):
        self.id = block_id
        self.position = _Pos(z)
        self.material = material
        self._vertices = vertices or [(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)]

    def vertices(self):
        return list(self._vertices)


class _CylGeom:
    def __init__(self, radial_mesh, axial_mesh):
        self.radial_mesh = np.asarray(radial_mesh, dtype=float)
        self.axial_mesh = np.asarray(axial_mesh, dtype=float)


def test_plot_ray_traced_geometry_plotly_blocks(monkeypatch):
    import smrforge.visualization.advanced as adv

    monkeypatch.setattr(adv, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(adv, "go", _DummyGo)

    geom = type("G", (), {"blocks": [_Block(1, z=10.0), _Block(2, z=20.0)]})()
    fig = adv.plot_ray_traced_geometry(geom, backend="plotly")

    assert isinstance(fig, _DummyFigure)
    assert len(fig.data) >= 2


def test_plot_ray_traced_geometry_invalid_backend_raises():
    import smrforge.visualization.advanced as adv

    with pytest.raises(ValueError, match="Unknown backend"):
        adv.plot_ray_traced_geometry(object(), backend="nope")


def test_plot_slice_plotly_cylindrical_total_and_group(monkeypatch):
    import smrforge.visualization.advanced as adv

    monkeypatch.setattr(adv, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(adv, "go", _DummyGo)

    geom = _CylGeom(radial_mesh=[0.0, 1.0, 2.0], axial_mesh=[0.0, 5.0, 10.0])
    nz, nr, ng = 2, 2, 3
    data = np.arange(nz * nr * ng, dtype=float).reshape(nz, nr, ng)

    fig_total = adv.plot_slice(data, geom, axis="z", position=5.0, backend="plotly")
    assert isinstance(fig_total, _DummyFigure)

    fig_g1 = adv.plot_slice(data, geom, axis="r", position=1.0, backend="plotly", energy_group=1)
    assert isinstance(fig_g1, _DummyFigure)

    with pytest.raises(IndexError):
        adv.plot_slice(data, geom, axis="z", position=0.0, backend="plotly", energy_group=99)


def test_plot_slice_plotly_cylindrical_2d_transpose(monkeypatch):
    import smrforge.visualization.advanced as adv

    monkeypatch.setattr(adv, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(adv, "go", _DummyGo)

    geom = _CylGeom(radial_mesh=[0.0, 1.0, 2.0, 3.0], axial_mesh=[0.0, 10.0, 20.0])
    # Provide (nr, nz) to exercise transpose path.
    data = np.arange(3 * 2, dtype=float).reshape(3, 2)
    fig = adv.plot_slice(data, geom, axis="z", position=10.0, backend="plotly")
    assert isinstance(fig, _DummyFigure)


def test_plot_slice_plotly_cartesian_interactive(monkeypatch):
    import smrforge.visualization.advanced as adv

    monkeypatch.setattr(adv, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(adv, "go", _DummyGo)

    data = np.arange(3 * 4 * 5, dtype=float).reshape(3, 4, 5)
    fig = adv.plot_slice(
        data,
        geometry=object(),
        axis="x",
        position=1.0,
        field_name="flux",
        backend="plotly",
        interactive=True,
        max_frames=10,
        frame_ms=1,
    )
    assert isinstance(fig, _DummyFigure)
    assert len(fig.frames) > 0


def test_plot_slice_plotly_cartesian_coord_validation(monkeypatch):
    import smrforge.visualization.advanced as adv

    monkeypatch.setattr(adv, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(adv, "go", _DummyGo)

    data = np.zeros((2, 3, 4), dtype=float)
    with pytest.raises(ValueError, match="x_coords must be a 1D array of length"):
        adv.plot_slice(data, geometry=object(), axis="z", position=0.0, backend="plotly", x_coords=[0.0, 1.0, 2.0])


def test_plot_isosurface_plotly(monkeypatch):
    import smrforge.visualization.advanced as adv

    monkeypatch.setattr(adv, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(adv, "go", _DummyGo)

    data = np.arange(8, dtype=float).reshape(2, 2, 2)

    fig = adv.plot_isosurface(data, geometry=object(), isovalue=3.0, backend="plotly")
    assert isinstance(fig, _DummyFigure)

    x = np.array([0.0, 1.0])
    y = np.array([0.0, 1.0])
    z = np.array([0.0, 1.0])
    fig2 = adv.plot_isosurface(data, geometry=object(), isovalue=3.0, backend="plotly", x=x, y=y, z=z)
    assert isinstance(fig2, _DummyFigure)

    with pytest.raises(ValueError, match="isovalue must be finite"):
        adv.plot_isosurface(data, geometry=object(), isovalue=float("nan"), backend="plotly")


def test_plot_isosurface_pyvista(monkeypatch):
    import smrforge.visualization.advanced as adv

    monkeypatch.setattr(adv, "_PYVISTA_AVAILABLE", True)
    monkeypatch.setattr(adv, "pv", _DummyPv)

    data = np.arange(8, dtype=float).reshape(2, 2, 2)
    plotter = adv.plot_isosurface(data, geometry=object(), isovalue=3.0, backend="pyvista")
    assert isinstance(plotter, _DummyPv.Plotter)
    assert plotter.show_axes_called is True


def test_plot_vector_field_plotly_and_pyvista(monkeypatch):
    import smrforge.visualization.advanced as adv

    vectors = np.ones((3, 3), dtype=float)
    positions = np.arange(9, dtype=float).reshape(3, 3)

    monkeypatch.setattr(adv, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(adv, "go", _DummyGo)
    fig = adv.plot_vector_field(vectors, positions, geometry=object(), backend="plotly")
    assert isinstance(fig, _DummyFigure)

    monkeypatch.setattr(adv, "_PYVISTA_AVAILABLE", True)
    monkeypatch.setattr(adv, "pv", _DummyPv)
    plotter = adv.plot_vector_field(vectors, positions, geometry=object(), backend="pyvista")
    assert isinstance(plotter, _DummyPv.Plotter)


def test_plot_material_boundaries_plotly(monkeypatch):
    import smrforge.visualization.advanced as adv

    monkeypatch.setattr(adv, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(adv, "go", _DummyGo)

    geom = type("G", (), {"blocks": [_Block(1, material="fuel"), _Block(2, material="moderator")]})()
    fig = adv.plot_material_boundaries(geom, backend="plotly")
    assert isinstance(fig, _DummyFigure)


def test_create_dashboard_plotly_and_matplotlib(monkeypatch):
    import smrforge.visualization.advanced as adv

    plots = [{"type": "slice", "title": "A"}, {"type": "3d", "title": "B"}]

    monkeypatch.setattr(adv, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(adv, "go", _DummyGo)
    monkeypatch.setattr(adv, "make_subplots", _dummy_make_subplots)
    fig = adv.create_dashboard(plots, backend="plotly")
    assert isinstance(fig, _DummyFigure)

    class _DummyAxesArr(list):
        def flatten(self):
            return self

    class _DummyPlt:
        def subplots(self, nrows, ncols, figsize):
            axes = _DummyAxesArr([object() for _ in range(nrows * ncols)])
            return object(), axes

    monkeypatch.setattr(adv, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(adv, "plt", _DummyPlt())
    fig2 = adv.create_dashboard([{"type": "slice"}], backend="matplotlib")
    assert fig2 is not None


def test_export_visualization_all_supported_routes(tmp_path):
    import smrforge.visualization.advanced as adv

    calls = {"html": 0, "img": 0, "savefig": 0, "save": 0}

    class _FigHtml:
        def write_html(self, path, **kwargs):
            calls["html"] += 1

    class _FigImg:
        def write_image(self, path, format, **kwargs):
            calls["img"] += 1

    class _FigMpl:
        def savefig(self, path, format, **kwargs):
            calls["savefig"] += 1

    class _Plotter:
        def save(self, path):
            calls["save"] += 1

    adv.export_visualization(_FigHtml(), tmp_path / "a.html", format="html")
    adv.export_visualization(_FigImg(), tmp_path / "a.png", format="png")
    adv.export_visualization(_FigMpl(), tmp_path / "a.pdf", format="pdf")
    adv.export_visualization(_Plotter(), tmp_path / "a.vtk", format="vtk")

    with pytest.raises(ValueError, match="Unknown format"):
        adv.export_visualization(_FigHtml(), tmp_path / "a.unknown", format="unknown")

    assert calls["html"] == 1
    assert calls["img"] == 1
    assert calls["savefig"] == 1
    assert calls["save"] == 1


def test_create_interactive_viewer_plotly_and_pyvista(monkeypatch):
    import smrforge.visualization.advanced as adv

    monkeypatch.setattr(adv, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(adv, "go", _DummyGo)
    fig = adv.create_interactive_viewer(type("G", (), {"blocks": [_Block(1)]})(), backend="plotly")
    assert isinstance(fig, _DummyFigure)

    monkeypatch.setattr(adv, "_PYVISTA_AVAILABLE", True)
    monkeypatch.setattr(adv, "pv", _DummyPv)
    viewer = adv.create_interactive_viewer(object(), backend="pyvista")
    assert isinstance(viewer, _DummyPv.Plotter)

