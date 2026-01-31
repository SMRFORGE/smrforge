import builtins
import importlib
import sys
from pathlib import Path

import numpy as np
import pytest


class _DummyIm:
    def __init__(self):
        self.arrays = []

    def set_array(self, arr):
        self.arrays.append(np.asarray(arr))


class _DummyAx:
    def __init__(self):
        self.clears = 0
        self.titles = []
        self.xlabels = []
        self.ylabels = []
        self.imshow_calls = []
        self._xlim = (0.0, 2.0)
        self._ylim = (0.0, 3.0)

    def get_xlim(self):
        return self._xlim

    def get_ylim(self):
        return self._ylim

    def clear(self):
        self.clears += 1

    def imshow(self, *args, **kwargs):
        self.imshow_calls.append((args, dict(kwargs)))
        return _DummyIm()

    def set_title(self, title):
        self.titles.append(title)

    def set_xlabel(self, label):
        self.xlabels.append(label)

    def set_ylabel(self, label):
        self.ylabels.append(label)

    def axis(self, *args, **kwargs):
        return None


class _DummyFig:
    def __init__(self):
        self.canvas = _DummyCanvas()


class _DummyCanvas:
    def __init__(self):
        self.draws = 0

    def draw(self):
        self.draws += 1

    def tostring_rgb(self):
        # 2x3 image
        arr = np.arange(2 * 3 * 3, dtype=np.uint8).reshape(2, 3, 3)
        return arr.tobytes()

    def get_width_height(self):
        return (3, 2)


class _DummyPlt:
    def __init__(self):
        self.colorbars = 0

    def subplots(self, *args, **kwargs):
        return _DummyFig(), _DummyAx()

    def colorbar(self, *args, **kwargs):
        self.colorbars += 1


class _DummyAnim:
    def __init__(self, fig, update, frames, interval, blit):
        self._fig = fig
        self._update = update
        self._frames = list(range(frames))
        self._drawn = []
        self.saved = []

    def _draw_frame(self, frame_num):
        self._drawn.append(frame_num)
        self._update(frame_num)

    def save(self, save_path, writer=None):
        self.saved.append((str(save_path), writer))


class _DummyAnimationModule:
    FuncAnimation = _DummyAnim

    class _Writers:
        def __init__(self):
            self._has_ffmpeg = False

        def list(self):
            return ["ffmpeg"] if self._has_ffmpeg else []

        def __getitem__(self, key):
            assert key == "ffmpeg"

            class _Writer:
                def __init__(self, fps, bitrate):
                    self.fps = fps
                    self.bitrate = bitrate

            return _Writer

    writers = _Writers()


class _DummyGo:
    class Frame:
        def __init__(self, data=None, name=None, layout=None):
            self.data = data
            self.name = name
            self.layout = layout

    class Layout:
        def __init__(self, **kwargs):
            self.kwargs = dict(kwargs)


class _DummyPlotlyFig:
    def __init__(self):
        self.data = [object()]
        self.frames = []
        self.layout_updates = []

    def update_layout(self, **kwargs):
        self.layout_updates.append(dict(kwargs))
        return self


def test_animations_import_fallbacks(monkeypatch):
    real_import = builtins.__import__

    def _reload_with_blocked(prefix: str):
        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == prefix or name.startswith(prefix + "."):
                raise ImportError(f"blocked import: {prefix}")
            return real_import(name, globals, locals, fromlist, level)

        with monkeypatch.context() as mp:
            mp.setattr(builtins, "__import__", fake_import)
            sys.modules.pop("smrforge.visualization.animations", None)
            sys.modules.pop(prefix, None)

            # animations.py imports plot_core_layout at import time; the real
            # visualization.geometry module imports matplotlib unguarded.
            # Provide a tiny stub so we can test import fallbacks safely.
            geom_stub = type(sys)("smrforge.visualization.geometry")
            geom_stub.plot_core_layout = lambda *a, **k: None
            sys.modules["smrforge.visualization.geometry"] = geom_stub

            return importlib.import_module("smrforge.visualization.animations")

    mod = _reload_with_blocked("matplotlib")
    assert mod._MATPLOTLIB_AVAILABLE is False
    assert mod.Writer is None

    mod = _reload_with_blocked("plotly")
    assert mod._PLOTLY_AVAILABLE is False

    mod = _reload_with_blocked("PIL")
    assert mod._PIL_AVAILABLE is False

    mod = _reload_with_blocked("imageio")
    assert mod._IMAGEIO_AVAILABLE is False

    # Restore module for remaining tests
    sys.modules.pop("smrforge.visualization.animations", None)
    sys.modules.pop("smrforge.visualization.geometry", None)
    importlib.import_module("smrforge.visualization.animations")


def test_animate_transient_matplotlib_import_required(monkeypatch):
    import smrforge.visualization.animations as an

    monkeypatch.setattr(an, "_MATPLOTLIB_AVAILABLE", False)
    with pytest.raises(ImportError):
        an.animate_transient_matplotlib(np.array([0.0, 1.0]), lambda t: np.zeros((2, 2)))


def test_animate_transient_matplotlib_basic_and_saving(monkeypatch, tmp_path):
    import smrforge.visualization.animations as an

    monkeypatch.setattr(an, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(an, "plt", _DummyPlt())
    monkeypatch.setattr(an, "animation", _DummyAnimationModule)

    calls = {"layout": 0}
    monkeypatch.setattr(an, "plot_core_layout", lambda *a, **k: calls.__setitem__("layout", calls["layout"] + 1))

    times = np.array([0.0, 1.0])
    data_func = lambda t: np.full((2, 2), t, dtype=float)

    # No geometry_func path (labeling + set_array)
    anim = an.animate_transient_matplotlib(times, data_func, geometry_func=None, view="xy")
    assert isinstance(anim, _DummyAnim)
    out = anim._update(1)
    assert isinstance(out, list)

    # geometry_func path + gif save path should call _save_gif_matplotlib
    saved = {"gif": 0}

    def _save(anim_obj, path, fps):
        saved["gif"] += 1
        assert isinstance(path, Path)

    monkeypatch.setattr(an, "_save_gif_matplotlib", _save)
    anim2 = an.animate_transient_matplotlib(
        times,
        data_func,
        geometry_func=lambda t: object(),
        save_path=tmp_path / "out.gif",
        fps=12,
    )
    assert isinstance(anim2, _DummyAnim)
    anim2._update(1)
    assert saved["gif"] == 1
    assert calls["layout"] >= 1

    # MP4 save with missing Writer raises
    monkeypatch.setattr(an, "Writer", None)
    with pytest.raises(ValueError, match="FFmpeg writer not available"):
        an.animate_transient_matplotlib(times, data_func, save_path=tmp_path / "out.mp4")

    # Unsupported suffix raises
    with pytest.raises(ValueError, match="Unsupported format"):
        an.animate_transient_matplotlib(times, data_func, save_path=tmp_path / "out.xyz")

    # MP4 save with available Writer calls anim.save
    class _W:
        def __init__(self, fps, bitrate):
            self.fps = fps
            self.bitrate = bitrate

    monkeypatch.setattr(an, "Writer", _W)
    anim3 = an.animate_transient_matplotlib(times, data_func, save_path=tmp_path / "out.mp4", fps=7)
    assert anim3.saved and anim3.saved[0][0].endswith("out.mp4")
    assert isinstance(anim3.saved[0][1], _W)


def test_save_gif_matplotlib_requires_imageio(monkeypatch, tmp_path):
    import smrforge.visualization.animations as an

    monkeypatch.setattr(an, "_IMAGEIO_AVAILABLE", False)
    with pytest.raises(ImportError):
        an._save_gif_matplotlib(_DummyAnim(_DummyFig(), lambda f: [], frames=1, interval=1, blit=True), tmp_path / "a.gif")


def test_save_gif_matplotlib_writes_frames(monkeypatch, tmp_path):
    import smrforge.visualization.animations as an

    monkeypatch.setattr(an, "_IMAGEIO_AVAILABLE", True)

    written = {}

    class _DummyImageio:
        def mimsave(self, path, frames, fps, loop):
            written["path"] = path
            written["n"] = len(frames)
            written["fps"] = fps
            written["loop"] = loop

    monkeypatch.setattr(an, "imageio", _DummyImageio())

    fig = _DummyFig()
    ax = _DummyAx()

    # anim._frames is expected to exist; we simulate 2 frames
    anim = _DummyAnim(fig, lambda f: [ax], frames=2, interval=1, blit=True)
    an._save_gif_matplotlib(anim, tmp_path / "a.gif", fps=9)

    assert written["path"].endswith("a.gif")
    assert written["n"] == 2
    assert written["fps"] == 9
    assert written["loop"] == 0


def test_animate_3d_transient_plotly(monkeypatch):
    import smrforge.visualization.animations as an

    times = np.array([0.0, 1.0, 2.0])

    monkeypatch.setattr(an, "_PLOTLY_AVAILABLE", False)
    with pytest.raises(ImportError):
        an.animate_3d_transient_plotly(times, mesh_func=lambda t: object())

    monkeypatch.setattr(an, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(an, "go", _DummyGo)

    # Patch plot_mesh3d_plotly import target
    mesh3d_mod = importlib.import_module("smrforge.visualization.mesh_3d")
    monkeypatch.setattr(mesh3d_mod, "plot_mesh3d_plotly", lambda *a, **k: _DummyPlotlyFig())

    fig = an.animate_3d_transient_plotly(times, mesh_func=lambda t: object(), field_name="flux", interval=50, title="T")
    assert isinstance(fig, _DummyPlotlyFig)
    assert len(fig.frames) == len(times)


def test_create_comparison_animation_paths(monkeypatch, tmp_path):
    import smrforge.visualization.animations as an

    monkeypatch.setattr(an, "_MATPLOTLIB_AVAILABLE", True)

    # subplots should return axes that support flatten() for multi-design case
    class _AxesArr(list):
        def flatten(self):
            return self

    class _PltMulti(_DummyPlt):
        def subplots(self, n_rows, n_cols, figsize):
            axes = _AxesArr([_DummyAx() for _ in range(n_rows * n_cols)])
            return _DummyFig(), axes

    monkeypatch.setattr(an, "plt", _PltMulti())
    monkeypatch.setattr(an, "animation", _DummyAnimationModule)
    monkeypatch.setattr(an, "Writer", None)

    times = np.array([0.0, 1.0])
    data_dict = {
        "A": {0.0: np.zeros((2, 2)), 1.0: np.ones((2, 2))},
        "B": {0.0: np.zeros((2, 2)), 1.0: np.ones((2, 2)) * 2},
        "C": {0.0: np.zeros((2, 2)), 1.0: np.ones((2, 2)) * 3},
    }

    anim = an.create_comparison_animation(data_dict, times, n_cols=2)
    assert isinstance(anim, _DummyAnim)
    anim._update(1)

    # Save as GIF path hits _save_gif_matplotlib
    saved = {"gif": 0}
    monkeypatch.setattr(an, "_save_gif_matplotlib", lambda *a, **k: saved.__setitem__("gif", saved["gif"] + 1))
    an.create_comparison_animation(data_dict, times, n_cols=2, save_path=tmp_path / "x.gif")
    assert saved["gif"] == 1

    # MP4 with available Writer calls anim.save
    class _W:
        def __init__(self, fps, bitrate):
            self.fps = fps
            self.bitrate = bitrate

    monkeypatch.setattr(an, "Writer", _W)
    anim_mp4 = an.create_comparison_animation(data_dict, times, save_path=tmp_path / "x.mp4", fps=11)
    assert anim_mp4.saved and anim_mp4.saved[0][0].endswith("x.mp4")
    assert isinstance(anim_mp4.saved[0][1], _W)

    # MP4 with missing Writer raises
    monkeypatch.setattr(an, "Writer", None)
    with pytest.raises(ValueError, match="FFmpeg writer not available"):
        an.create_comparison_animation(data_dict, times, save_path=tmp_path / "x.mp4")

    # Single design path (axes list wrapped)
    class _PltSingle(_DummyPlt):
        def subplots(self, n_rows, n_cols, figsize):
            return _DummyFig(), _DummyAx()

    monkeypatch.setattr(an, "plt", _PltSingle())
    one = {"Only": {0.0: np.zeros((2, 2)), 1.0: np.ones((2, 2))}}
    anim2 = an.create_comparison_animation(one, times, n_cols=2)
    assert isinstance(anim2, _DummyAnim)

    monkeypatch.setattr(an, "_MATPLOTLIB_AVAILABLE", False)
    with pytest.raises(ImportError):
        an.create_comparison_animation(one, times)


def test_animations_imageio_available_true_via_reload(monkeypatch):
    # Cover the successful import branch setting _IMAGEIO_AVAILABLE = True.
    sys.modules.pop("smrforge.visualization.animations", None)

    geom_stub = type(sys)("smrforge.visualization.geometry")
    geom_stub.plot_core_layout = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "smrforge.visualization.geometry", geom_stub)

    imageio_stub = type(sys)("imageio")
    monkeypatch.setitem(sys.modules, "imageio", imageio_stub)

    mod = importlib.import_module("smrforge.visualization.animations")
    assert mod._IMAGEIO_AVAILABLE is True

