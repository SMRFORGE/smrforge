import builtins
import sys
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest


class DummyMesh:
    def __init__(self):
        self.cell_data = {}

    def add_cell_data(self, name, data):
        self.cell_data[name] = np.asarray(data)


class DummyPlotlyFig:
    def __init__(self):
        self.calls = []

    def write_html(self, path):
        self.calls.append(("write_html", path))

    def write_image(self, path):
        self.calls.append(("write_image", path))


class DummyMplFig:
    def __init__(self):
        self.saved = []

    def savefig(self, path):
        self.saved.append(path)


def test_create_plot_and_plot_dispatch(monkeypatch):
    import smrforge.visualization.plot_api as api

    p = api.create_plot(plot_type="slice", basis="xy", backend="plotly")
    assert p.plot_type == "slice"
    assert p.basis == "xy"
    assert p.backend == "plotly"

    with pytest.raises(ValueError):
        api.Plot(plot_type="nope").plot(geometry=object())


def test_plot_slice_axis_position_and_output_save(monkeypatch):
    import smrforge.visualization.plot_api as api

    # Inject a tiny stub module for smrforge.visualization.advanced
    adv = ModuleType("smrforge.visualization.advanced")
    calls = {}

    def fake_plot_slice(data, geometry, *, axis, position, field_name, backend):
        calls["axis"] = axis
        calls["position"] = position
        calls["field_name"] = field_name
        calls["backend"] = backend
        return "slice-fig"

    adv.plot_slice = fake_plot_slice  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "smrforge.visualization.advanced", adv)

    p = api.Plot(
        plot_type="slice",
        origin=(0.0, 0.0, 0.0),
        width=(10.0, 20.0, 30.0),
        basis="xy",
        backend="plotly",
        output_file="out.html",
    )

    saved = {"n": 0}
    monkeypatch.setattr(
        p, "_save_figure", lambda fig, out: saved.__setitem__("n", saved["n"] + 1)
    )

    fig = p.plot(geometry=object(), data=None, field_name=None)
    assert fig == "slice-fig"
    assert calls["axis"] == "z"
    assert calls["position"] == pytest.approx(15.0)
    assert calls["field_name"] == "data"
    assert calls["backend"] == "plotly"
    assert saved["n"] == 1

    # Invalid basis for slice plot
    with pytest.raises(ValueError):
        api.Plot(plot_type="slice", basis="xyz").plot(geometry=object())


def test_plot_voxel_importerror_and_success(monkeypatch):
    import smrforge.visualization.plot_api as api

    # Force ImportError for voxel_plots module
    orig_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        pkg = (globals or {}).get("__package__")
        if (
            name.endswith("smrforge.visualization.voxel_plots")
            or name.endswith("visualization.voxel_plots")
            or (
                level == 1 and name == "voxel_plots" and pkg == "smrforge.visualization"
            )
        ):
            raise ImportError("forced")
        return orig_import(name, globals, locals, fromlist, level)

    with pytest.MonkeyPatch.context() as mp:
        sys.modules.pop("smrforge.visualization.voxel_plots", None)
        mp.setattr(builtins, "__import__", guarded_import)
        with pytest.raises(ImportError):
            api.Plot(plot_type="voxel").plot(geometry=object())

    # Inject stub voxel_plots module
    vox = ModuleType("smrforge.visualization.voxel_plots")
    vox.plot_voxel = lambda *args, **kwargs: "vox-fig"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "smrforge.visualization.voxel_plots", vox)

    fig = api.Plot(plot_type="voxel").plot(
        geometry=object(), data=np.array([1.0]), field_name="f"
    )
    assert fig == "vox-fig"


def test_plot_ray_trace(monkeypatch):
    import smrforge.visualization.plot_api as api

    adv = ModuleType("smrforge.visualization.advanced")
    adv.plot_ray_traced_geometry = lambda *args, **kwargs: "ray-fig"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "smrforge.visualization.advanced", adv)

    fig = api.Plot(plot_type="ray_trace").plot(geometry=object())
    assert fig == "ray-fig"


def test_plot_unstructured_paths_and_save_figure(monkeypatch):
    import smrforge.visualization.plot_api as api

    # Stub mesh_3d module
    m3d = ModuleType("smrforge.visualization.mesh_3d")
    m3d.plot_mesh3d_plotly = lambda mesh, **kwargs: ("plotly3d", mesh, kwargs)  # type: ignore[attr-defined]
    m3d.plot_mesh3d_pyvista = lambda mesh, **kwargs: ("pv3d", mesh, kwargs)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "smrforge.visualization.mesh_3d", m3d)

    # Stub mesh_extraction module
    mex = ModuleType("smrforge.geometry.mesh_extraction")
    mex.extract_core_volume_mesh = lambda geometry: DummyMesh()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "smrforge.geometry.mesh_extraction", mex)

    # Treat DummyMesh as Mesh3D for this test
    monkeypatch.setattr(api, "Mesh3D", DummyMesh)

    # Case 1: already a mesh, add data (named) and plotly backend
    mesh = DummyMesh()
    p = api.Plot(plot_type="unstructured", backend="plotly")
    fig = p.plot(mesh, data=np.array([1.0, 2.0]), field_name="phi")
    assert fig[0] == "plotly3d"
    assert "phi" in mesh.cell_data

    # Case 2: geometry not mesh -> extraction, unnamed data key
    p2 = api.Plot(plot_type="unstructured", backend="pyvista")
    fig2 = p2.plot(object(), data=np.array([3.0]), field_name=None)
    assert fig2[0] == "pv3d"
    extracted_mesh = fig2[1]
    assert extracted_mesh.cell_data["data"].shape == (1,)

    # Unsupported backend for unstructured
    with pytest.raises(ValueError):
        api.Plot(plot_type="unstructured", backend="matplotlib").plot(object())

    # Missing mesh_3d import
    orig_import = builtins.__import__

    def bad_import(name, globals=None, locals=None, fromlist=(), level=0):
        pkg = (globals or {}).get("__package__")
        if (
            name.endswith("smrforge.visualization.mesh_3d")
            or name.endswith("visualization.mesh_3d")
            or (level == 1 and name == "mesh_3d" and pkg == "smrforge.visualization")
        ):
            raise ImportError("forced")
        return orig_import(name, globals, locals, fromlist, level)

    sys.modules.pop("smrforge.visualization.mesh_3d", None)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(builtins, "__import__", bad_import)
        with pytest.raises(ImportError):
            api.Plot(plot_type="unstructured", backend="plotly").plot(object())

    # _save_figure branches
    p_save = api.Plot(backend="plotly")
    figp = DummyPlotlyFig()
    p_save._save_figure(figp, "out.html")
    p_save._save_figure(figp, "out.png")
    p_save._save_figure(figp, "out.pdf")
    p_save._save_figure(figp, "out.unknown")
    assert ("write_html", "out.html") in figp.calls
    assert ("write_image", "out.png") in figp.calls

    # matplotlib saving for tuple and fig object
    p_mpl = api.Plot(backend="matplotlib")
    f = DummyMplFig()
    p_mpl._save_figure((f, object()), "out.png")
    assert "out.png" in f.saved
    f2 = DummyMplFig()
    p_mpl._save_figure(f2, "out2.png")
    assert "out2.png" in f2.saved
