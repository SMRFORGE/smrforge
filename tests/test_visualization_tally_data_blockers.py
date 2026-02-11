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

    class Scatter(_DummyTrace):
        pass

    class Scatter3d(_DummyTrace):
        pass

    class Heatmap(_DummyTrace):
        pass


def _dummy_make_subplots(*args, **kwargs):
    return _DummyFigure()


class _DummyPlt:
    def __init__(self):
        self.colorbars = 0

    def subplots(self, *args, **kwargs):
        return object(), _DummyAx()

    def figure(self, *args, **kwargs):
        return _DummyFig()

    def colorbar(self, *args, **kwargs):
        self.colorbars += 1


class _DummyFig:
    class _DummyGridSpec:
        def __getitem__(self, key):
            return key

    def add_gridspec(self, *args, **kwargs):
        return self._DummyGridSpec()

    def add_subplot(self, *args, **kwargs):
        return _DummyAx()

    def tight_layout(self):
        return None

    def colorbar(self, *args, **kwargs):
        return None


class _DummyAx:
    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            return _DummyTrace()

        return _noop


def test_plot_energy_spectrum_plotly_and_matplotlib(monkeypatch):
    import smrforge.visualization.tally_data as td

    flux = np.arange(4, dtype=float)
    energy_groups = np.array([1e-3, 1e-2, 1e-1, 1.0, 10.0], dtype=float)
    unc = np.ones_like(flux) * 0.1

    monkeypatch.setattr(td, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(td, "go", _DummyGo)
    fig = td.plot_energy_spectrum(
        flux, energy_groups, backend="plotly", show_uncertainty=True, uncertainty=unc
    )
    assert isinstance(fig, _DummyFigure)
    assert len(fig.data) >= 3  # spectrum + upper + lower

    monkeypatch.setattr(td, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(td, "plt", _DummyPlt())
    fig_ax = td.plot_energy_spectrum(
        flux,
        energy_groups,
        backend="matplotlib",
        show_uncertainty=True,
        uncertainty=unc,
    )
    assert isinstance(fig_ax, tuple)

    with pytest.raises(ValueError, match="Unknown backend"):
        td.plot_energy_spectrum(flux, energy_groups, backend="nope")

    # Position extraction path with uncertainty=None
    flux3 = np.arange(2 * 3 * 4, dtype=float).reshape(2, 3, 4)
    fig_pos = td.plot_energy_spectrum(
        flux3,
        energy_groups,
        position=(1, 2),
        backend="plotly",
        show_uncertainty=True,
        uncertainty=None,
    )
    assert isinstance(fig_pos, _DummyFigure)

    unc3 = np.ones_like(flux3) * 0.1
    fig_pos_unc = td.plot_energy_spectrum(
        flux3,
        energy_groups,
        position=(1, 2),
        backend="plotly",
        show_uncertainty=True,
        uncertainty=unc3,
    )
    assert isinstance(fig_pos_unc, _DummyFigure)

    monkeypatch.setattr(td, "_PLOTLY_AVAILABLE", False)
    with pytest.raises(ImportError):
        td.plot_energy_spectrum(flux, energy_groups, backend="plotly")

    monkeypatch.setattr(td, "_MATPLOTLIB_AVAILABLE", False)
    with pytest.raises(ImportError):
        td.plot_energy_spectrum(flux, energy_groups, backend="matplotlib")


def test_plot_flux_spectrum_comparison_plotly_and_matplotlib(monkeypatch):
    import smrforge.visualization.tally_data as td

    energy_groups = np.array([1e-3, 1e-2, 1e-1, 1.0], dtype=float)
    fluxes = {"a": np.array([1.0, 2.0, 3.0]), "b": np.array([2.0, 1.0, 0.5])}

    with pytest.raises(ValueError, match="non-empty dict"):
        td.plot_flux_spectrum_comparison({}, energy_groups)

    monkeypatch.setattr(td, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(td, "go", _DummyGo)
    fig = td.plot_flux_spectrum_comparison(
        fluxes, energy_groups, backend="plotly", normalize=True
    )
    assert isinstance(fig, _DummyFigure)
    assert len(fig.data) >= 2

    monkeypatch.setattr(td, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(td, "plt", _DummyPlt())
    fig_ax = td.plot_flux_spectrum_comparison(
        fluxes, energy_groups, backend="matplotlib", normalize=False
    )
    assert isinstance(fig_ax, tuple)

    # Position + reduction path and unknown backend
    fluxes3d = {"a": np.arange(2 * 2 * 3, dtype=float).reshape(2, 2, 3)}
    fig3 = td.plot_flux_spectrum_comparison(
        fluxes3d, energy_groups, position=(1, 1), backend="plotly", normalize=False
    )
    assert isinstance(fig3, _DummyFigure)

    fluxes_sum = {"a": np.arange(2 * 2 * 3, dtype=float).reshape(2, 2, 3)}
    fig4 = td.plot_flux_spectrum_comparison(
        fluxes_sum, energy_groups, position=None, backend="plotly", normalize=False
    )
    assert isinstance(fig4, _DummyFigure)

    with pytest.raises(ValueError, match="Unknown backend"):
        td.plot_flux_spectrum_comparison(fluxes, energy_groups, backend="nope")

    monkeypatch.setattr(td, "_PLOTLY_AVAILABLE", False)
    with pytest.raises(ImportError):
        td.plot_flux_spectrum_comparison(fluxes, energy_groups, backend="plotly")

    monkeypatch.setattr(td, "_MATPLOTLIB_AVAILABLE", False)
    with pytest.raises(ImportError):
        td.plot_flux_spectrum_comparison(fluxes, energy_groups, backend="matplotlib")


def test_plot_neutronics_dashboard_plotly_and_matplotlib(monkeypatch):
    import smrforge.visualization.tally_data as td

    nz, nr, ng = 2, 3, 4
    flux = np.arange(nz * nr * ng, dtype=float).reshape(nz, nr, ng)
    energy_groups = np.logspace(-3, 1, ng + 1)

    monkeypatch.setattr(td, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(td, "go", _DummyGo)
    monkeypatch.setattr(td, "make_subplots", _dummy_make_subplots)
    fig = td.plot_neutronics_dashboard(
        flux, energy_groups, backend="plotly", k_eff=1.05
    )
    assert isinstance(fig, _DummyFigure)

    monkeypatch.setattr(td, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(td, "plt", _DummyPlt())
    fig_ax = td.plot_neutronics_dashboard(flux, energy_groups, backend="matplotlib")
    assert isinstance(fig_ax, tuple)

    with pytest.raises(ValueError, match="Unknown backend"):
        td.plot_neutronics_dashboard(flux, energy_groups, backend="nope")

    with pytest.raises(ValueError, match="at least 1D"):
        td.plot_neutronics_dashboard(np.array(1.0), energy_groups, backend="plotly")

    # 1D flux path (no spatial map)
    monkeypatch.setattr(td, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(td, "go", _DummyGo)
    flux1d = np.arange(ng, dtype=float)
    fig1d = td.plot_neutronics_dashboard(flux1d, energy_groups, backend="plotly")
    assert isinstance(fig1d, _DummyFigure)

    # plotly.subplots missing
    monkeypatch.setattr(td, "make_subplots", None)
    with pytest.raises(ImportError, match="subplots"):
        td.plot_neutronics_dashboard(flux, energy_groups, backend="plotly")

    monkeypatch.setattr(td, "_PLOTLY_AVAILABLE", False)
    with pytest.raises(ImportError):
        td.plot_neutronics_dashboard(flux, energy_groups, backend="plotly")

    monkeypatch.setattr(td, "_MATPLOTLIB_AVAILABLE", False)
    with pytest.raises(ImportError):
        td.plot_neutronics_dashboard(flux, energy_groups, backend="matplotlib")

    # matplotlib 1D flux path (has_map False)
    monkeypatch.setattr(td, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(td, "plt", _DummyPlt())
    fig_ax1d = td.plot_neutronics_dashboard(flux1d, energy_groups, backend="matplotlib")
    assert isinstance(fig_ax1d, tuple)


def test_plot_spatial_distribution_plotly_and_matplotlib(monkeypatch):
    import smrforge.visualization.tally_data as td

    data = np.arange(5, dtype=float)
    positions = np.arange(15, dtype=float).reshape(5, 3)

    monkeypatch.setattr(td, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(td, "go", _DummyGo)
    fig = td.plot_spatial_distribution(data, positions, backend="plotly")
    assert isinstance(fig, _DummyFigure)

    heat = np.arange(6, dtype=float).reshape(2, 3)
    fig2 = td.plot_spatial_distribution(
        heat, positions=np.zeros((2, 2)), backend="plotly"
    )
    assert isinstance(fig2, _DummyFigure)

    monkeypatch.setattr(td, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(td, "plt", _DummyPlt())
    fig_ax = td.plot_spatial_distribution(data, positions, backend="matplotlib")
    assert isinstance(fig_ax, tuple)

    fig_ax2 = td.plot_spatial_distribution(
        heat, positions=np.arange(3), backend="matplotlib"
    )
    assert isinstance(fig_ax2, tuple)

    # matplotlib 1D plot branch (not a 2D array)
    fig_ax3 = td.plot_spatial_distribution(
        np.arange(3, dtype=float), positions=np.arange(3), backend="matplotlib"
    )
    assert isinstance(fig_ax3, tuple)

    with pytest.raises(ValueError, match="Unknown backend"):
        td.plot_spatial_distribution(data, positions, backend="nope")

    monkeypatch.setattr(td, "_PLOTLY_AVAILABLE", False)
    with pytest.raises(ImportError):
        td.plot_spatial_distribution(data, positions, backend="plotly")

    monkeypatch.setattr(td, "_MATPLOTLIB_AVAILABLE", False)
    with pytest.raises(ImportError):
        td.plot_spatial_distribution(data, positions, backend="matplotlib")


def test_plot_time_dependent_tally_plotly_and_matplotlib(monkeypatch):
    import smrforge.visualization.tally_data as td

    times = np.linspace(0.0, 1.0, 5)
    tallies = np.arange(5 * 4, dtype=float).reshape(5, 4)
    positions = np.arange(4 * 3, dtype=float).reshape(4, 3)

    monkeypatch.setattr(td, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(td, "go", _DummyGo)
    fig_multi = td.plot_time_dependent_tally(
        tallies, times, positions=positions, backend="plotly"
    )
    assert isinstance(fig_multi, _DummyFigure)

    fig_single = td.plot_time_dependent_tally(
        tallies, times, positions=None, backend="plotly"
    )
    assert isinstance(fig_single, _DummyFigure)

    monkeypatch.setattr(td, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(td, "plt", _DummyPlt())
    fig_ax = td.plot_time_dependent_tally(
        tallies, times, positions=positions, backend="matplotlib"
    )
    assert isinstance(fig_ax, tuple)

    # matplotlib averaged path (positions None)
    monkeypatch.setattr(td, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(td, "plt", _DummyPlt())
    fig_ax_avg = td.plot_time_dependent_tally(
        tallies, times, positions=None, backend="matplotlib"
    )
    assert isinstance(fig_ax_avg, tuple)

    # matplotlib 1D path (no averaging)
    fig_ax_1d = td.plot_time_dependent_tally(
        np.arange(5, dtype=float), times, positions=None, backend="matplotlib"
    )
    assert isinstance(fig_ax_1d, tuple)

    # plotly 1D path (tally_data.ndim == 1)
    monkeypatch.setattr(td, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(td, "go", _DummyGo)
    fig_1d = td.plot_time_dependent_tally(
        np.arange(5, dtype=float), times, backend="plotly"
    )
    assert isinstance(fig_1d, _DummyFigure)

    with pytest.raises(ValueError, match="Unknown backend"):
        td.plot_time_dependent_tally(tallies, times, backend="nope")

    monkeypatch.setattr(td, "_PLOTLY_AVAILABLE", False)
    with pytest.raises(ImportError):
        td.plot_time_dependent_tally(tallies, times, backend="plotly")

    monkeypatch.setattr(td, "_MATPLOTLIB_AVAILABLE", False)
    with pytest.raises(ImportError):
        td.plot_time_dependent_tally(tallies, times, backend="matplotlib")


def test_plot_uncertainty_plotly_and_matplotlib(monkeypatch):
    import smrforge.visualization.tally_data as td

    mean = np.array([1.0, 2.0, 3.0])
    unc = np.array([0.1, 0.2, 0.3])
    pos = np.array([0.0, 1.0, 2.0])

    monkeypatch.setattr(td, "_PLOTLY_AVAILABLE", True)
    monkeypatch.setattr(td, "go", _DummyGo)
    fig = td.plot_uncertainty(mean, unc, positions=pos, backend="plotly")
    assert isinstance(fig, _DummyFigure)

    mean2 = np.arange(6, dtype=float).reshape(2, 3)
    unc2 = np.ones_like(mean2) * 0.1
    fig2 = td.plot_uncertainty(mean2, unc2, positions=None, backend="plotly")
    assert isinstance(fig2, _DummyFigure)

    monkeypatch.setattr(td, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(td, "plt", _DummyPlt())
    fig_ax = td.plot_uncertainty(mean, unc, positions=pos, backend="matplotlib")
    assert isinstance(fig_ax, tuple)

    # matplotlib heatmap path
    monkeypatch.setattr(td, "_MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(td, "plt", _DummyPlt())
    fig_ax2 = td.plot_uncertainty(mean2, unc2, positions=None, backend="matplotlib")
    assert isinstance(fig_ax2, tuple)

    with pytest.raises(ValueError, match="Unknown backend"):
        td.plot_uncertainty(mean, unc, backend="nope")

    monkeypatch.setattr(td, "_PLOTLY_AVAILABLE", False)
    with pytest.raises(ImportError):
        td.plot_uncertainty(mean, unc, positions=pos, backend="plotly")

    monkeypatch.setattr(td, "_MATPLOTLIB_AVAILABLE", False)
    with pytest.raises(ImportError):
        td.plot_uncertainty(mean, unc, positions=pos, backend="matplotlib")


def test_tally_data_import_fallbacks(monkeypatch):
    """Cover import-time fallbacks for optional plotting deps."""
    real_import = builtins.__import__

    def _reload_with_blocked(prefix: str):
        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == prefix or name.startswith(prefix + "."):
                raise ImportError(f"blocked import: {prefix}")
            return real_import(name, globals, locals, fromlist, level)

        with monkeypatch.context() as mp:
            mp.setattr(builtins, "__import__", fake_import)
            sys.modules.pop("smrforge.visualization.tally_data", None)
            sys.modules.pop(prefix, None)
            return importlib.import_module("smrforge.visualization.tally_data")

    mod = _reload_with_blocked("matplotlib")
    assert mod._MATPLOTLIB_AVAILABLE is False
    mod = _reload_with_blocked("plotly")
    assert mod._PLOTLY_AVAILABLE is False

    import smrforge.visualization.tally_data as td

    importlib.reload(td)
