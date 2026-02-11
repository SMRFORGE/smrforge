import numpy as np
import pytest


def test_voxel_grid_prismatic_core_is_nonempty():
    from smrforge.geometry.core_geometry import PrismaticCore
    from smrforge.visualization.voxel_plots import _create_voxel_grid

    core = PrismaticCore(name="VoxelTestCore")
    core.build_hexagonal_lattice(
        n_rings=1, pitch=40.0, block_height=80.0, n_axial=1, flat_to_flat=36.0
    )

    grid = _create_voxel_grid(
        core,
        origin=(-120.0, -120.0, 0.0),
        width=(240.0, 240.0, 80.0),
        resolution=(30, 30, 10),
    )

    mats = grid["material_ids"]
    cells = grid["cell_ids"]
    assert mats.shape == (30, 30, 10)
    assert cells.shape == (30, 30, 10)

    # Should mark at least some voxels as belonging to a block/material.
    assert int(np.max(mats)) > 0
    assert int(np.max(cells)) > 0


def test_plot_voxel_unknown_backend_raises():
    from smrforge.visualization.voxel_plots import plot_voxel

    with pytest.raises(ValueError, match="Unknown backend"):
        plot_voxel(
            geometry=object(),
            origin=(0.0, 0.0, 0.0),
            width=(10.0, 10.0, 10.0),
            backend="nope",
            resolution=(2, 2, 1),
        )


def test_create_voxel_grid_skips_invalid_blocks_and_out_of_bounds():
    from types import SimpleNamespace

    from smrforge.visualization.voxel_plots import _create_voxel_grid

    class _Pos:
        def __init__(self, x, y, z):
            self.x = x
            self.y = y
            self.z = z

    # Missing required attrs -> skipped
    bad_block_missing = SimpleNamespace()

    # Invalid dimensions -> skipped
    bad_block_dims = SimpleNamespace(
        position=_Pos(0.0, 0.0, 0.0),
        flat_to_flat=0.0,
        height=10.0,
        block_type="fuel",
        id=1,
    )

    # Outside voxel bounds -> skipped
    far_block = SimpleNamespace(
        position=_Pos(1e9, 1e9, 1e9),
        flat_to_flat=10.0,
        height=10.0,
        block_type="fuel",
        id=2,
    )

    geometry = SimpleNamespace(blocks=[bad_block_missing, bad_block_dims, far_block])

    grid = _create_voxel_grid(
        geometry,
        origin=(0.0, 0.0, 0.0),
        width=(10.0, 10.0, 10.0),
        resolution=(2, 2, 1),
    )
    assert grid["material_ids"].shape == (2, 2, 1)
    assert grid["cell_ids"].shape == (2, 2, 1)


def test_plot_voxel_plotly_importerror_when_plotly_unavailable(monkeypatch):
    import smrforge.visualization.voxel_plots as vp

    monkeypatch.setattr(vp, "_PLOTLY_AVAILABLE", False)
    with pytest.raises(ImportError, match="plotly is required"):
        vp._plot_voxel_plotly(
            voxel_grid={
                "x": np.array([0.5]),
                "y": np.array([0.5]),
                "z": np.array([0.5]),
                "material_ids": np.zeros((1, 1, 1), dtype=int),
                "cell_ids": np.zeros((1, 1, 1), dtype=int),
                "origin": (0.0, 0.0, 0.0),
                "width": (1.0, 1.0, 1.0),
                "resolution": (1, 1, 1),
            },
            color_by="material",
            data=None,
            field_name=None,
            colors=None,
            background="white",
        )


def test_plot_voxel_pyvista_importerror_when_pyvista_unavailable(monkeypatch):
    import smrforge.visualization.voxel_plots as vp

    monkeypatch.setattr(vp, "_PYVISTA_AVAILABLE", False)
    with pytest.raises(ImportError, match="pyvista is required"):
        vp._plot_voxel_pyvista(
            voxel_grid={
                "x": np.array([0.5]),
                "y": np.array([0.5]),
                "z": np.array([0.5]),
                "material_ids": np.zeros((1, 1, 1), dtype=int),
                "cell_ids": np.zeros((1, 1, 1), dtype=int),
                "origin": (0.0, 0.0, 0.0),
                "width": (1.0, 1.0, 1.0),
                "resolution": (1, 1, 1),
            },
            color_by="material",
            data=None,
            field_name=None,
            colors=None,
            background="white",
        )


def test_export_voxel_to_hdf5_and_convert_to_vtk(tmp_path):
    from smrforge.visualization.voxel_plots import (
        convert_voxel_hdf5_to_vtk,
        export_voxel_to_hdf5,
    )

    voxel_grid = {
        "x": np.array([0.5, 1.5]),
        "y": np.array([0.5, 1.5]),
        "z": np.array([0.5]),
        "material_ids": np.array([[[1], [2]], [[3], [4]]], dtype=int),
        "cell_ids": np.array([[[10], [20]], [[30], [40]]], dtype=int),
        "origin": (0.0, 0.0, 0.0),
        "width": (2.0, 2.0, 1.0),
        "resolution": (2, 2, 1),
    }

    h5_path = tmp_path / "vox.h5"
    vtk_path = tmp_path / "vox.vtk"

    export_voxel_to_hdf5(voxel_grid, h5_path, note="hello")
    assert h5_path.exists()

    convert_voxel_hdf5_to_vtk(h5_path, vtk_path)
    assert vtk_path.exists()


def test_hdf5_and_vtk_exports_require_optional_dependencies(monkeypatch, tmp_path):
    import smrforge.visualization.voxel_plots as vp

    voxel_grid = {
        "x": np.array([0.5]),
        "y": np.array([0.5]),
        "z": np.array([0.5]),
        "material_ids": np.zeros((1, 1, 1), dtype=int),
        "cell_ids": np.zeros((1, 1, 1), dtype=int),
        "origin": (0.0, 0.0, 0.0),
        "width": (1.0, 1.0, 1.0),
        "resolution": (1, 1, 1),
    }

    monkeypatch.setattr(vp, "_H5PY_AVAILABLE", False)
    with pytest.raises(ImportError, match="h5py is required"):
        vp.export_voxel_to_hdf5(voxel_grid, tmp_path / "x.h5")
    with pytest.raises(ImportError, match="h5py is required"):
        vp.convert_voxel_hdf5_to_vtk(tmp_path / "x.h5", tmp_path / "x.vtk")

    monkeypatch.setattr(vp, "_H5PY_AVAILABLE", True)
    monkeypatch.setattr(vp, "_PYVISTA_AVAILABLE", False)
    with pytest.raises(ImportError, match="pyvista is required"):
        vp.convert_voxel_hdf5_to_vtk(tmp_path / "x.h5", tmp_path / "x.vtk")


def test_voxel_plots_module_import_fallbacks(monkeypatch):
    """Cover import-time fallbacks for optional deps (h5py/plotly/pyvista)."""
    import builtins
    import importlib
    import sys

    real_import = builtins.__import__

    def _reload_with_blocked(prefix: str):
        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == prefix or name.startswith(prefix + "."):
                raise ImportError(f"blocked import: {prefix}")
            return real_import(name, globals, locals, fromlist, level)

        with monkeypatch.context() as mp:
            mp.setattr(builtins, "__import__", fake_import)
            sys.modules.pop("smrforge.visualization.voxel_plots", None)
            sys.modules.pop(prefix, None)
            return importlib.import_module("smrforge.visualization.voxel_plots")

    mod = _reload_with_blocked("h5py")
    assert mod._H5PY_AVAILABLE is False

    mod = _reload_with_blocked("plotly")
    assert mod._PLOTLY_AVAILABLE is False

    mod = _reload_with_blocked("pyvista")
    assert mod._PYVISTA_AVAILABLE is False

    import smrforge.visualization.voxel_plots as vp

    importlib.reload(vp)


def test_plot_voxel_dispatches_to_plotly_and_pyvista(monkeypatch):
    import smrforge.visualization.voxel_plots as vp

    voxel_grid = {
        "x": np.array([0.5]),
        "y": np.array([0.5]),
        "z": np.array([0.5]),
        "material_ids": np.zeros((1, 1, 1), dtype=int),
        "cell_ids": np.zeros((1, 1, 1), dtype=int),
        "origin": (0.0, 0.0, 0.0),
        "width": (1.0, 1.0, 1.0),
        "resolution": (1, 1, 1),
    }
    monkeypatch.setattr(vp, "_create_voxel_grid", lambda *args, **kwargs: voxel_grid)

    plotly_sentinel = object()
    pyvista_sentinel = object()
    monkeypatch.setattr(
        vp, "_plot_voxel_plotly", lambda *args, **kwargs: plotly_sentinel
    )
    monkeypatch.setattr(
        vp, "_plot_voxel_pyvista", lambda *args, **kwargs: pyvista_sentinel
    )

    assert vp.plot_voxel(object(), backend="plotly") is plotly_sentinel
    assert vp.plot_voxel(object(), backend="pyvista") is pyvista_sentinel


def test_plot_voxel_pyvista_backend_path(monkeypatch):
    import smrforge.visualization.voxel_plots as vp

    class _DummyPv:
        class StructuredGrid(dict):
            def __init__(self, x, y, z):
                super().__init__()
                self.x = np.asarray(x)
                self.y = np.asarray(y)
                self.z = np.asarray(z)

        class Plotter:
            def __init__(self):
                self.meshes = []
                self.bg = None
                self.axes = 0

            def add_mesh(self, mesh, **kwargs):
                self.meshes.append((mesh, dict(kwargs)))

            def show_axes(self):
                self.axes += 1

            def set_background(self, background):
                self.bg = background

    monkeypatch.setattr(vp, "_PYVISTA_AVAILABLE", True)
    monkeypatch.setattr(vp, "pv", _DummyPv)

    voxel_grid = {
        "x": np.array([0.5, 1.5]),
        "y": np.array([0.5, 1.5]),
        "z": np.array([0.5]),
        "material_ids": np.array([[[1], [2]], [[3], [4]]], dtype=int),
        "cell_ids": np.array([[[10], [20]], [[30], [40]]], dtype=int),
        "origin": (0.0, 0.0, 0.0),
        "width": (2.0, 2.0, 1.0),
        "resolution": (2, 2, 1),
    }

    data = np.ones_like(voxel_grid["material_ids"], dtype=float)
    plotter = vp._plot_voxel_pyvista(
        voxel_grid,
        color_by="material",
        data=data,
        field_name="flux",
        colors=None,
        background="white",
    )
    assert isinstance(plotter, _DummyPv.Plotter)
    assert plotter.axes == 1
    assert plotter.bg == "white"
    assert len(plotter.meshes) == 1
    grid, _ = plotter.meshes[0]
    assert "flux" in grid
