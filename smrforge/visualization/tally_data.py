"""
Tally data visualization for energy spectra and spatial distributions.

Provides visualization for tally results, adapted from OpenMC's tally
visualization for use with diffusion solver results.
"""

from typing import Dict, List, Optional, Tuple, Union

import numpy as np

try:
    import matplotlib.pyplot as plt

    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False
    plt = None  # type: ignore

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False
    go = None  # type: ignore

from ..utils.logging import get_logger

logger = get_logger("smrforge.visualization.tally_data")


def plot_energy_spectrum(
    flux: np.ndarray,
    energy_groups: np.ndarray,
    position: Optional[Tuple[int, ...]] = None,
    backend: str = "plotly",
    show_uncertainty: bool = False,
    uncertainty: Optional[np.ndarray] = None,
    **kwargs,
):
    """
    Plot energy spectrum (flux vs. energy).

    Visualizes flux as a function of energy, similar to OpenMC's energy
    spectrum plots.

    Args:
        flux: Flux array [..., ng] or [ng] for single position
        energy_groups: Energy group boundaries [eV] (length ng+1)
        position: Optional position tuple for multi-dimensional flux
        backend: Visualization backend
        show_uncertainty: Whether to show uncertainty bands
        uncertainty: Optional uncertainty array (same shape as flux)
        **kwargs: Additional arguments

    Returns:
        Figure object

    Example:
        >>> from smrforge.visualization.tally_data import plot_energy_spectrum
        >>>
        >>> # Flux from solver [nz, nr, ng]
        >>> flux = solver.get_flux()
        >>> energy_groups = np.logspace(7, -5, 27)  # 26 groups
        >>>
        >>> # Plot spectrum at center of core
        >>> fig = plot_energy_spectrum(
        ...     flux[5, 10, :],  # Single position
        ...     energy_groups,
        ...     backend='plotly'
        ... )
    """
    # Extract flux at position if needed
    if position is not None and flux.ndim > 1:
        flux_at_pos = flux[position]
        if uncertainty is not None:
            uncertainty_at_pos = uncertainty[position]
        else:
            uncertainty_at_pos = None
    else:
        flux_at_pos = flux if flux.ndim == 1 else flux.flatten()
        uncertainty_at_pos = uncertainty.flatten() if uncertainty is not None else None

    # Calculate group centers (lethargy-weighted)
    group_centers = np.sqrt(energy_groups[:-1] * energy_groups[1:])

    if backend == "plotly":
        return _plot_spectrum_plotly(
            flux_at_pos, group_centers, show_uncertainty, uncertainty_at_pos, **kwargs
        )
    elif backend == "matplotlib":
        return _plot_spectrum_matplotlib(
            flux_at_pos, group_centers, show_uncertainty, uncertainty_at_pos, **kwargs
        )
    else:
        raise ValueError(f"Unknown backend: {backend}")


def _plot_spectrum_plotly(flux, group_centers, show_uncertainty, uncertainty, **kwargs):
    """Plot energy spectrum using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")

    fig = go.Figure()

    # Main spectrum line
    fig.add_trace(
        go.Scatter(
            x=group_centers,
            y=flux,
            mode="lines+markers",
            name="Flux",
            line=dict(width=2),
        )
    )

    # Uncertainty bands if requested
    if show_uncertainty and uncertainty is not None:
        upper = flux + uncertainty
        lower = flux - uncertainty

        fig.add_trace(
            go.Scatter(
                x=group_centers,
                y=upper,
                mode="lines",
                name="Upper Bound",
                line=dict(width=0),
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=group_centers,
                y=lower,
                mode="lines",
                name="Lower Bound",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(0,100,80,0.2)",
                showlegend=False,
            )
        )

    fig.update_layout(
        title="Energy Spectrum",
        xaxis_title="Energy (eV)",
        yaxis_title="Flux (n/cm²/s)",
        xaxis_type="log",
        yaxis_type="log",
    )

    return fig


def _plot_spectrum_matplotlib(
    flux, group_centers, show_uncertainty, uncertainty, **kwargs
):
    """Plot energy spectrum using matplotlib."""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib is required")

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(group_centers, flux, "o-", linewidth=2, markersize=4)

    if show_uncertainty and uncertainty is not None:
        upper = flux + uncertainty
        lower = flux - uncertainty
        ax.fill_between(group_centers, lower, upper, alpha=0.3, label="Uncertainty")

    ax.set_xlabel("Energy (eV)")
    ax.set_ylabel("Flux (n/cm²/s)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_title("Energy Spectrum")
    ax.grid(True, alpha=0.3)
    ax.legend()

    return fig, ax


def plot_flux_spectrum_comparison(
    fluxes: Dict[str, np.ndarray],
    energy_groups: np.ndarray,
    position: Optional[Tuple[int, ...]] = None,
    backend: str = "plotly",
    normalize: bool = True,
    **kwargs,
):
    """
    Compare multiple flux spectra on the same axes.

    Args:
        fluxes: Mapping label -> flux array [..., ng] or [ng]
        energy_groups: Energy group boundaries [eV] (length ng+1)
        position: Optional position tuple for multi-dimensional flux
        backend: Visualization backend
        normalize: If True, normalize each spectrum to its max
    """
    if not isinstance(fluxes, dict) or len(fluxes) == 0:
        raise ValueError("fluxes must be a non-empty dict")

    group_centers = np.sqrt(energy_groups[:-1] * energy_groups[1:])

    def extract(arr: np.ndarray) -> np.ndarray:
        a = np.asarray(arr)
        if position is not None and a.ndim > 1:
            a = a[position]
        if a.ndim > 1:
            a = np.sum(a, axis=tuple(range(a.ndim - 1)))
        a = np.asarray(a, dtype=float).reshape(-1)
        if normalize and np.max(a) > 0:
            a = a / np.max(a)
        return a

    spectra = {k: extract(v) for k, v in fluxes.items()}

    if backend == "plotly":
        if not _PLOTLY_AVAILABLE:
            raise ImportError("plotly is required")
        fig = go.Figure()
        for label, spec in spectra.items():
            fig.add_trace(
                go.Scatter(x=group_centers, y=spec, mode="lines+markers", name=label)
            )
        fig.update_layout(
            title=kwargs.get("title", "Flux spectrum comparison"),
            xaxis_title="Energy (eV)",
            yaxis_title=("Normalized flux" if normalize else "Flux"),
            xaxis_type="log",
            yaxis_type=("linear" if normalize else "log"),
        )
        return fig

    if backend == "matplotlib":
        if not _MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required")
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 6)))
        for label, spec in spectra.items():
            ax.plot(group_centers, spec, "o-", linewidth=2, markersize=4, label=label)
        ax.set_xscale("log")
        if not normalize:
            ax.set_yscale("log")
        ax.set_title(kwargs.get("title", "Flux spectrum comparison"))
        ax.set_xlabel("Energy (eV)")
        ax.set_ylabel("Normalized flux" if normalize else "Flux")
        ax.grid(True, alpha=0.3)
        ax.legend()
        return fig, ax

    raise ValueError(f"Unknown backend: {backend}")


def plot_neutronics_dashboard(
    flux: np.ndarray,
    energy_groups: np.ndarray,
    *,
    k_eff: Optional[float] = None,
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Lightweight neutronics dashboard:
    - total flux spectrum (summed over space)
    - optional 2D heatmap of total flux over indices (if flux is 3D: [nz, nr, ng])
    """
    arr = np.asarray(flux)
    if arr.ndim < 1:
        raise ValueError("flux must be at least 1D")

    group_centers = np.sqrt(energy_groups[:-1] * energy_groups[1:])

    if arr.ndim == 1:
        spectrum = arr.astype(float)
        spatial_map = None
    else:
        spectrum = (
            np.sum(arr, axis=tuple(range(arr.ndim - 1))).astype(float).reshape(-1)
        )
        spatial_map = np.sum(arr, axis=-1).astype(float) if arr.ndim == 3 else None

    plot_title = title or "Neutronics dashboard"
    if k_eff is not None:
        plot_title = f"{plot_title} (k_eff={k_eff:.6f})"

    if backend == "plotly":
        if not _PLOTLY_AVAILABLE:
            raise ImportError("plotly is required")
        if make_subplots is None:
            raise ImportError("plotly.subplots is required")

        has_map = spatial_map is not None
        fig = make_subplots(
            rows=2 if has_map else 1,
            cols=1,
            subplot_titles=(
                ["Energy spectrum"] + (["Total flux (indices)"] if has_map else [])
            ),
            vertical_spacing=0.12,
        )
        fig.add_trace(
            go.Scatter(
                x=group_centers, y=spectrum, mode="lines+markers", name="total spectrum"
            ),
            row=1,
            col=1,
        )
        fig.update_xaxes(type="log", title_text="Energy (eV)", row=1, col=1)
        fig.update_yaxes(type="log", title_text="Flux (a.u.)", row=1, col=1)

        if has_map:
            fig.add_trace(
                go.Heatmap(
                    z=spatial_map, colorscale=kwargs.get("colorscale", "Viridis")
                ),
                row=2,
                col=1,
            )
            fig.update_xaxes(title_text="r index", row=2, col=1)
            fig.update_yaxes(title_text="z index", row=2, col=1)

        fig.update_layout(title=plot_title, height=650 if has_map else 350)
        return fig

    if backend == "matplotlib":
        if not _MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required")
        has_map = spatial_map is not None
        fig = plt.figure(figsize=kwargs.get("figsize", (10, 8 if has_map else 5)))
        if has_map:
            gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.2])
            ax1 = fig.add_subplot(gs[0, 0])
            ax2 = fig.add_subplot(gs[1, 0])
        else:
            ax1 = fig.add_subplot(1, 1, 1)
            ax2 = None

        ax1.plot(group_centers, spectrum, "o-", linewidth=2, markersize=4)
        ax1.set_xscale("log")
        ax1.set_yscale("log")
        ax1.set_title(plot_title)
        ax1.set_xlabel("Energy (eV)")
        ax1.set_ylabel("Flux (a.u.)")
        ax1.grid(True, alpha=0.3)

        if ax2 is not None:
            im = ax2.imshow(
                spatial_map,
                aspect="auto",
                origin="lower",
                cmap=kwargs.get("cmap", "viridis"),
            )
            ax2.set_title("Total flux (indices)")
            ax2.set_xlabel("r index")
            ax2.set_ylabel("z index")
            fig.colorbar(im, ax=ax2, label="a.u.")

        fig.tight_layout()
        return fig, ax1 if ax2 is None else (ax1, ax2)

    raise ValueError(f"Unknown backend: {backend}")


def plot_spatial_distribution(
    tally_data: np.ndarray,
    positions: np.ndarray,
    field_name: str = "flux",
    backend: str = "plotly",
    **kwargs,
):
    """
    Plot spatial distribution of tally data.

    Visualizes how a tally value varies spatially across the reactor.

    Args:
        tally_data: Tally data array [n_positions] or [nx, ny, nz]
        positions: Position array [n_positions, 3] or coordinate arrays
        field_name: Name of the field (for labels)
        backend: Visualization backend
        **kwargs: Additional arguments

    Returns:
        Figure object

    Example:
        >>> from smrforge.visualization.tally_data import plot_spatial_distribution
        >>>
        >>> # Flux distribution
        >>> flux_total = np.sum(flux, axis=-1)  # Sum over energy groups
        >>> positions = mesh.get_centers()  # [n_positions, 3]
        >>>
        >>> fig = plot_spatial_distribution(flux_total, positions, field_name="Flux")
    """
    if backend == "plotly":
        return _plot_spatial_plotly(tally_data, positions, field_name, **kwargs)
    elif backend == "matplotlib":
        return _plot_spatial_matplotlib(tally_data, positions, field_name, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def _plot_spatial_plotly(tally_data, positions, field_name, **kwargs):
    """Plot spatial distribution using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")

    if positions.ndim == 2 and positions.shape[1] == 3:
        # 3D scatter plot
        x, y, z = positions[:, 0], positions[:, 1], positions[:, 2]

        fig = go.Figure(
            data=go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="markers",
                marker=dict(
                    size=5,
                    color=tally_data,
                    colorscale="Viridis",
                    colorbar=dict(title=field_name),
                ),
            )
        )

        fig.update_layout(
            title=f"{field_name} Spatial Distribution",
            scene=dict(
                xaxis_title="X (cm)",
                yaxis_title="Y (cm)",
                zaxis_title="Z (cm)",
            ),
        )
    else:
        # 2D heatmap
        fig = go.Figure(
            data=go.Heatmap(
                z=tally_data,
                colorscale="Viridis",
                colorbar=dict(title=field_name),
            )
        )

        fig.update_layout(
            title=f"{field_name} Spatial Distribution",
        )

    return fig


def _plot_spatial_matplotlib(tally_data, positions, field_name, **kwargs):
    """Plot spatial distribution using matplotlib."""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib is required")

    if positions.ndim == 2 and positions.shape[1] == 3:
        # 3D scatter
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection="3d")

        scatter = ax.scatter(
            positions[:, 0],
            positions[:, 1],
            positions[:, 2],
            c=tally_data,
            cmap="viridis",
            s=20,
        )

        ax.set_xlabel("X (cm)")
        ax.set_ylabel("Y (cm)")
        ax.set_zlabel("Z (cm)")
        ax.set_title(f"{field_name} Spatial Distribution")
        plt.colorbar(scatter, ax=ax, label=field_name)
    else:
        # 2D contour
        fig, ax = plt.subplots(figsize=(10, 8))

        if tally_data.ndim == 2:
            im = ax.contourf(tally_data, levels=20, cmap="viridis")
            plt.colorbar(im, ax=ax, label=field_name)
        else:
            ax.plot(positions, tally_data, "o-")
            ax.set_xlabel("Position")
            ax.set_ylabel(field_name)

        ax.set_title(f"{field_name} Spatial Distribution")

    return fig, ax


def plot_time_dependent_tally(
    tally_data: np.ndarray,
    times: np.ndarray,
    positions: Optional[np.ndarray] = None,
    field_name: str = "flux",
    backend: str = "plotly",
    **kwargs,
):
    """
    Plot time-dependent tally data.

    Visualizes how tally values evolve over time.

    Args:
        tally_data: Tally data array [n_times, n_positions] or [n_times, ...]
        times: Time array [n_times] [seconds]
        positions: Optional position array for multiple positions
        field_name: Name of the field
        backend: Visualization backend
        **kwargs: Additional arguments

    Returns:
        Figure object
    """
    if backend == "plotly":
        return _plot_time_dependent_plotly(
            tally_data, times, positions, field_name, **kwargs
        )
    elif backend == "matplotlib":
        return _plot_time_dependent_matplotlib(
            tally_data, times, positions, field_name, **kwargs
        )
    else:
        raise ValueError(f"Unknown backend: {backend}")


def _plot_time_dependent_plotly(tally_data, times, positions, field_name, **kwargs):
    """Plot time-dependent data using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")

    fig = go.Figure()

    if positions is not None and tally_data.ndim > 1:
        # Multiple positions
        for i, pos in enumerate(positions[:10]):  # Limit to 10 positions
            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=tally_data[:, i],
                    mode="lines",
                    name=f"Position {i}",
                )
            )
    else:
        # Single position or averaged
        if tally_data.ndim > 1:
            data = np.mean(tally_data, axis=tuple(range(1, tally_data.ndim)))
        else:
            data = tally_data

        fig.add_trace(
            go.Scatter(
                x=times,
                y=data,
                mode="lines",
                name=field_name,
            )
        )

    fig.update_layout(
        title=f"{field_name} vs. Time",
        xaxis_title="Time (s)",
        yaxis_title=field_name,
    )

    return fig


def _plot_time_dependent_matplotlib(tally_data, times, positions, field_name, **kwargs):
    """Plot time-dependent data using matplotlib."""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib is required")

    fig, ax = plt.subplots(figsize=(10, 6))

    if positions is not None and tally_data.ndim > 1:
        # Multiple positions
        for i, pos in enumerate(positions[:10]):  # Limit to 10
            ax.plot(times, tally_data[:, i], label=f"Position {i}")
        ax.legend()
    else:
        # Single position or averaged
        if tally_data.ndim > 1:
            data = np.mean(tally_data, axis=tuple(range(1, tally_data.ndim)))
        else:
            data = tally_data

        ax.plot(times, data, linewidth=2)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel(field_name)
    ax.set_title(f"{field_name} vs. Time")
    ax.grid(True, alpha=0.3)

    return fig, ax


def plot_uncertainty(
    mean: np.ndarray,
    uncertainty: np.ndarray,
    positions: Optional[np.ndarray] = None,
    backend: str = "plotly",
    **kwargs,
):
    """
    Plot statistical uncertainty visualization.

    Visualizes uncertainty in tally results, useful for Monte Carlo results
    or uncertainty quantification.

    Args:
        mean: Mean values [n_positions] or [nx, ny, nz]
        uncertainty: Uncertainty values (1-sigma) [same shape as mean]
        positions: Optional position array
        backend: Visualization backend
        **kwargs: Additional arguments

    Returns:
        Figure object
    """
    if backend == "plotly":
        return _plot_uncertainty_plotly(mean, uncertainty, positions, **kwargs)
    elif backend == "matplotlib":
        return _plot_uncertainty_matplotlib(mean, uncertainty, positions, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def _plot_uncertainty_plotly(mean, uncertainty, positions, **kwargs):
    """Plot uncertainty using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required")

    # Calculate relative error
    relative_error = uncertainty / mean if np.any(mean > 0) else uncertainty

    fig = go.Figure()

    if positions is not None and mean.ndim == 1:
        # 1D plot with error bars
        fig.add_trace(
            go.Scatter(
                x=positions,
                y=mean,
                error_y=dict(type="data", array=uncertainty, visible=True),
                mode="markers",
                name="Mean ± 1σ",
            )
        )
    else:
        # Heatmap of relative error
        fig.add_trace(
            go.Heatmap(
                z=relative_error,
                colorscale="Reds",
                colorbar=dict(title="Relative Error"),
            )
        )

    fig.update_layout(
        title="Statistical Uncertainty",
        xaxis_title="Position" if positions is not None else "X",
        yaxis_title="Value" if positions is not None else "Y",
    )

    return fig


def _plot_uncertainty_matplotlib(mean, uncertainty, positions, **kwargs):
    """Plot uncertainty using matplotlib."""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib is required")

    fig, ax = plt.subplots(figsize=(10, 6))

    if positions is not None and mean.ndim == 1:
        # Error bars
        ax.errorbar(positions, mean, yerr=uncertainty, fmt="o", capsize=5)
    else:
        # Heatmap of relative error
        relative_error = uncertainty / mean if np.any(mean > 0) else uncertainty
        im = ax.contourf(relative_error, levels=20, cmap="Reds")
        plt.colorbar(im, ax=ax, label="Relative Error")

    ax.set_xlabel("Position" if positions is not None else "X")
    ax.set_ylabel("Value" if positions is not None else "Y")
    ax.set_title("Statistical Uncertainty")
    ax.grid(True, alpha=0.3)

    return fig, ax


__all__ = [
    "plot_energy_spectrum",
    "plot_flux_spectrum_comparison",
    "plot_neutronics_dashboard",
    "plot_spatial_distribution",
    "plot_time_dependent_tally",
    "plot_uncertainty",
]
