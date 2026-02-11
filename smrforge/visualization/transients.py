"""
Visualization for transient analysis and lumped thermal-hydraulics results.

Provides plotting capabilities for:
- Transient analysis (power, temperature, reactivity vs time)
- Lumped thermal-hydraulics (temperature of lumps vs time)
- Decay heat visualization
- Transient comparison plots
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

# Try importing matplotlib
try:
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker

    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False

# Try importing plotly
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False


def plot_transient(
    result: Dict,
    output: Optional[Union[str, Path]] = None,
    backend: str = "plotly",
    show_plot: bool = True,
    events: Optional[List[Tuple[float, str, str]]] = None,
    annotate_peaks: bool = False,
    **kwargs,
):
    """
    Plot transient analysis results.

    Creates a comprehensive multi-panel plot showing power, temperature,
    reactivity, and optional precursor concentrations over time.

    Args:
        result: Transient result dictionary with keys:
            - "time" or "t": Time array [s]
            - "power": Power array [W]
            - "T_fuel": Fuel temperature array [K]
            - "T_moderator" or "T_mod": Moderator temperature array [K]
            - "reactivity" or "rho_external": Reactivity array [dk/k] (optional)
            - "precursors": Precursor concentrations array (optional)
        output: Output file path for saving plot (optional).
            If None, plot is displayed but not saved.
        backend: Visualization backend ("plotly" or "matplotlib", default: "plotly").
        show_plot: Whether to display plot (default: True).
        **kwargs: Additional plot customization arguments.

    Returns:
        Figure object (plotly Figure or matplotlib Figure).

    Example:
        >>> from smrforge.convenience.transients import quick_transient
        >>> result = quick_transient(
        ...     power=1e6,
        ...     temperature=1200.0,
        ...     reactivity_insertion=0.001,
        ...     duration=100.0
        ... )
        >>> from smrforge.visualization.transients import plot_transient
        >>> fig = plot_transient(result, output="transient_plot.png")
    """
    # Get time array
    time = result.get("time", result.get("t", None))
    if time is None:
        raise ValueError("Result must contain 'time' or 't' array")

    time = np.array(time)

    # Get power array
    power = result.get("power", None)
    if power is None:
        raise ValueError("Result must contain 'power' array")

    power = np.array(power)

    # Get temperature arrays
    T_fuel = result.get("T_fuel", result.get("T_fuel", None))
    T_mod = result.get("T_moderator", result.get("T_mod", None))

    # Get reactivity array (optional)
    reactivity = result.get("reactivity", result.get("rho_external", None))
    if reactivity is not None:
        reactivity = np.array(reactivity)

    # Get precursors (optional)
    precursors = result.get("precursors", None)
    if precursors is not None:
        precursors = np.array(precursors)

    # Optional auto-event generation
    if events is None:
        events = []
    if annotate_peaks:
        try:
            if power.size:
                t_peak = float(time[int(np.argmax(power))])
                events.append((t_peak, "Peak power", "info"))
        except Exception:
            pass
        try:
            if reactivity is not None and reactivity.size:
                t_rho = float(time[int(np.argmax(reactivity))])
                events.append((t_rho, "Max reactivity", "warning"))
        except Exception:
            pass
        scram_t = result.get("scram_time", result.get("t_scram", None))
        if scram_t is not None:
            try:
                events.append((float(scram_t), "SCRAM", "danger"))
            except Exception:
                pass

    if backend == "plotly":
        if not _PLOTLY_AVAILABLE:
            raise ImportError("Plotly not available. Install with: pip install plotly")
        return _plot_transient_plotly(
            time,
            power,
            T_fuel,
            T_mod,
            reactivity,
            precursors,
            output=output,
            show_plot=show_plot,
            events=events,
            **kwargs,
        )
    elif backend == "matplotlib":
        if not _MATPLOTLIB_AVAILABLE:
            raise ImportError(
                "Matplotlib not available. Install with: pip install matplotlib"
            )
        return _plot_transient_matplotlib(
            time,
            power,
            T_fuel,
            T_mod,
            reactivity,
            precursors,
            output=output,
            show_plot=show_plot,
            events=events,
            **kwargs,
        )
    else:
        raise ValueError(
            f"Unknown backend: {backend}. Must be 'plotly' or 'matplotlib'"
        )


def _plot_transient_plotly(
    time: np.ndarray,
    power: np.ndarray,
    T_fuel: Optional[np.ndarray],
    T_mod: Optional[np.ndarray],
    reactivity: Optional[np.ndarray],
    precursors: Optional[np.ndarray],
    output: Optional[Union[str, Path]] = None,
    show_plot: bool = True,
    events: Optional[List[Tuple[float, str, str]]] = None,
    **kwargs,
):
    """Plot transient results using Plotly."""
    # Determine number of subplots
    n_plots = 2  # Power and temperature always
    if reactivity is not None:
        n_plots += 1
    if precursors is not None:
        n_plots += 1

    # Create subplots
    fig = make_subplots(
        rows=n_plots,
        cols=1,
        subplot_titles=(
            ["Power", "Temperature"]
            + (["Reactivity"] if reactivity is not None else [])
            + (["Delayed Neutron Precursors"] if precursors is not None else [])
        ),
        vertical_spacing=0.08,
        shared_xaxes=True,
    )

    # Plot power
    fig.add_trace(
        go.Scatter(
            x=time,
            y=power / 1e6,  # Convert to MW
            mode="lines",
            name="Power",
            line=dict(color="blue", width=2),
        ),
        row=1,
        col=1,
    )
    fig.update_yaxes(title_text="Power [MWth]", row=1, col=1)

    # Plot temperature
    row = 2
    if T_fuel is not None:
        fig.add_trace(
            go.Scatter(
                x=time,
                y=T_fuel - 273.15,  # Convert to Celsius
                mode="lines",
                name="Fuel Temperature",
                line=dict(color="red", width=2),
            ),
            row=row,
            col=1,
        )
    if T_mod is not None:
        fig.add_trace(
            go.Scatter(
                x=time,
                y=T_mod - 273.15,  # Convert to Celsius
                mode="lines",
                name="Moderator Temperature",
                line=dict(color="orange", width=2, dash="dash"),
            ),
            row=row,
            col=1,
        )
    fig.update_yaxes(title_text="Temperature [°C]", row=row, col=1)

    # Plot reactivity
    if reactivity is not None:
        row += 1
        fig.add_trace(
            go.Scatter(
                x=time,
                y=reactivity * 1000,  # Convert to m$
                mode="lines",
                name="Reactivity",
                line=dict(color="green", width=2),
            ),
            row=row,
            col=1,
        )
        fig.update_yaxes(title_text="Reactivity [m$]", row=row, col=1)

    # Plot precursors (first group)
    if precursors is not None:
        row += 1
        if len(precursors.shape) > 1:
            prec_data = precursors[0, :]  # First group
        else:
            prec_data = precursors

        fig.add_trace(
            go.Scatter(
                x=time,
                y=prec_data,
                mode="lines",
                name="Precursors (Group 1)",
                line=dict(color="purple", width=2),
            ),
            row=row,
            col=1,
        )
        fig.update_yaxes(title_text="Precursor Concentration", row=row, col=1)

    # Update x-axis (only on bottom plot)
    fig.update_xaxes(title_text="Time [s]", row=n_plots, col=1)

    # Update layout
    fig.update_layout(
        height=300 * n_plots,
        title_text="Transient Analysis Results",
        title_x=0.5,
        showlegend=True,
        hovermode="x unified",
        **kwargs.get("layout", {}),
    )

    # Optional event annotations
    if events:
        for t_evt, label, kind in events:
            color = {"info": "blue", "warning": "orange", "danger": "red"}.get(
                kind, "gray"
            )
            try:
                fig.add_vline(
                    x=float(t_evt), line_width=1, line_dash="dash", line_color=color
                )
                fig.add_annotation(
                    x=float(t_evt),
                    y=1.02,
                    xref="x",
                    yref="paper",
                    text=label,
                    showarrow=False,
                    font=dict(color=color),
                )
            except Exception:
                # Best-effort annotations only
                pass

    # Save or show
    if output:
        output_path = Path(output)
        if output_path.suffix == ".html":
            fig.write_html(str(output_path))
        else:
            fig.write_image(str(output_path))

    if show_plot:
        fig.show()

    return fig


def _plot_transient_matplotlib(
    time: np.ndarray,
    power: np.ndarray,
    T_fuel: Optional[np.ndarray],
    T_mod: Optional[np.ndarray],
    reactivity: Optional[np.ndarray],
    precursors: Optional[np.ndarray],
    output: Optional[Union[str, Path]] = None,
    show_plot: bool = True,
    events: Optional[List[Tuple[float, str, str]]] = None,
    **kwargs,
):
    """Plot transient results using Matplotlib."""
    # Determine number of subplots
    n_plots = 2  # Power and temperature always
    if reactivity is not None:
        n_plots += 1
    if precursors is not None:
        n_plots += 1

    fig, axes = plt.subplots(
        n_plots, 1, figsize=kwargs.get("figsize", (12, 3 * n_plots)), sharex=True
    )

    if n_plots == 1:
        axes = [axes]

    # Plot power
    axes[0].plot(time, power / 1e6, "b-", linewidth=2, label="Power")
    axes[0].set_ylabel("Power [MWth]")
    axes[0].set_title("Transient Analysis Results")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    # Plot temperature
    idx = 1
    if T_fuel is not None:
        axes[idx].plot(
            time, T_fuel - 273.15, "r-", linewidth=2, label="Fuel Temperature"
        )
    if T_mod is not None:
        axes[idx].plot(
            time,
            T_mod - 273.15,
            "orange",
            linestyle="--",
            linewidth=2,
            label="Moderator Temperature",
        )
    axes[idx].set_ylabel("Temperature [°C]")
    axes[idx].grid(True, alpha=0.3)
    axes[idx].legend()

    # Plot reactivity
    if reactivity is not None:
        idx += 1
        axes[idx].plot(time, reactivity * 1000, "g-", linewidth=2, label="Reactivity")
        axes[idx].set_ylabel("Reactivity [m$]")
        axes[idx].grid(True, alpha=0.3)
        axes[idx].legend()

    # Plot precursors
    if precursors is not None:
        idx += 1
        if len(precursors.shape) > 1:
            prec_data = precursors[0, :]  # First group
        else:
            prec_data = precursors
        axes[idx].plot(
            time, prec_data, "purple", linewidth=2, label="Precursors (Group 1)"
        )
        axes[idx].set_ylabel("Precursor Concentration")
        axes[idx].grid(True, alpha=0.3)
        axes[idx].legend()

    # X-axis label on bottom plot
    axes[-1].set_xlabel("Time [s]")

    # Optional event annotations (apply to all subplots)
    if events:
        for t_evt, label, kind in events:
            color = {"info": "blue", "warning": "orange", "danger": "red"}.get(
                kind, "gray"
            )
            for ax in axes:
                try:
                    ax.axvline(
                        float(t_evt),
                        linestyle="--",
                        color=color,
                        linewidth=1,
                        alpha=0.8,
                    )
                except Exception:
                    pass
            try:
                axes[0].text(
                    float(t_evt),
                    1.02,
                    label,
                    transform=axes[0].get_xaxis_transform(),
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    color=color,
                )
            except Exception:
                pass

    plt.tight_layout()

    # Save or show
    if output:
        plt.savefig(output, dpi=kwargs.get("dpi", 300), bbox_inches="tight")

    if show_plot:
        plt.show()
    else:
        plt.close(fig)

    return fig


def plot_lumped_thermal(
    result: Dict,
    output: Optional[Union[str, Path]] = None,
    backend: str = "plotly",
    show_plot: bool = True,
    **kwargs,
):
    """
    Plot lumped-parameter thermal-hydraulics results.

    Creates a plot showing temperature evolution of thermal lumps over time.

    Args:
        result: Lumped TH result dictionary with keys:
            - "time": Time array [s]
            - "T_{lump_name}": Temperature array for each lump [K]
            - "Q_{lump_name}": Heat source array for each lump [W] (optional)
        output: Output file path for saving plot (optional).
        backend: Visualization backend ("plotly" or "matplotlib", default: "plotly").
        show_plot: Whether to display plot (default: True).
        **kwargs: Additional plot customization arguments.

    Returns:
        Figure object (plotly Figure or matplotlib Figure).

    Example:
        >>> from smrforge.thermal.lumped import LumpedThermalHydraulics, ThermalLump
        >>> solver = LumpedThermalHydraulics(...)
        >>> result = solver.solve_transient(t_span=(0.0, 3600.0))
        >>> from smrforge.visualization.transients import plot_lumped_thermal
        >>> fig = plot_lumped_thermal(result, output="thermal_plot.png")
    """
    # Get time array
    time = result.get("time", None)
    if time is None:
        raise ValueError("Result must contain 'time' array")

    time = np.array(time)

    # Extract temperature data for all lumps
    T_data = {}
    Q_data = {}
    for key, value in result.items():
        if key.startswith("T_"):
            lump_name = key[2:]  # Remove "T_" prefix
            T_data[lump_name] = np.array(value)
        elif key.startswith("Q_"):
            lump_name = key[2:]  # Remove "Q_" prefix
            Q_data[lump_name] = np.array(value)

    if not T_data:
        raise ValueError("Result must contain at least one 'T_{lump_name}' key")

    if backend == "plotly":
        if not _PLOTLY_AVAILABLE:
            raise ImportError("Plotly not available. Install with: pip install plotly")
        return _plot_lumped_thermal_plotly(
            time, T_data, Q_data, output=output, show_plot=show_plot, **kwargs
        )
    elif backend == "matplotlib":
        if not _MATPLOTLIB_AVAILABLE:
            raise ImportError(
                "Matplotlib not available. Install with: pip install matplotlib"
            )
        return _plot_lumped_thermal_matplotlib(
            time, T_data, Q_data, output=output, show_plot=show_plot, **kwargs
        )
    else:
        raise ValueError(
            f"Unknown backend: {backend}. Must be 'plotly' or 'matplotlib'"
        )


def _plot_lumped_thermal_plotly(
    time: np.ndarray,
    T_data: Dict[str, np.ndarray],
    Q_data: Dict[str, np.ndarray],
    output: Optional[Union[str, Path]] = None,
    show_plot: bool = True,
    **kwargs,
):
    """Plot lumped thermal results using Plotly."""
    # Create subplots (temperature and optional heat source)
    n_plots = 2 if Q_data else 1

    fig = make_subplots(
        rows=n_plots,
        cols=1,
        subplot_titles=(["Temperature"] + (["Heat Source"] if Q_data else [])),
        vertical_spacing=0.1,
        shared_xaxes=True,
    )

    # Plot temperatures
    colors = ["red", "orange", "green", "blue", "purple", "brown", "pink", "gray"]
    for i, (lump_name, T_values) in enumerate(T_data.items()):
        color = colors[i % len(colors)]
        fig.add_trace(
            go.Scatter(
                x=time,
                y=T_values - 273.15,  # Convert to Celsius
                mode="lines",
                name=f"{lump_name.capitalize()} Temperature",
                line=dict(color=color, width=2),
            ),
            row=1,
            col=1,
        )
    fig.update_yaxes(title_text="Temperature [°C]", row=1, col=1)

    # Plot heat sources
    if Q_data:
        for i, (lump_name, Q_values) in enumerate(Q_data.items()):
            color = colors[i % len(colors)]
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=Q_values / 1e6,  # Convert to MW
                    mode="lines",
                    name=f"{lump_name.capitalize()} Heat Source",
                    line=dict(color=color, width=2, dash="dash"),
                ),
                row=2,
                col=1,
            )
        fig.update_yaxes(title_text="Heat Source [MW]", row=2, col=1)

    # Update x-axis
    fig.update_xaxes(title_text="Time [s]", row=n_plots, col=1)

    # Update layout
    fig.update_layout(
        height=300 * n_plots,
        title_text="Lumped-Parameter Thermal-Hydraulics Results",
        title_x=0.5,
        showlegend=True,
        hovermode="x unified",
        **kwargs.get("layout", {}),
    )

    # Save or show
    if output:
        output_path = Path(output)
        if output_path.suffix == ".html":
            fig.write_html(str(output_path))
        else:
            fig.write_image(str(output_path))

    if show_plot:
        fig.show()

    return fig


def _plot_lumped_thermal_matplotlib(
    time: np.ndarray,
    T_data: Dict[str, np.ndarray],
    Q_data: Dict[str, np.ndarray],
    output: Optional[Union[str, Path]] = None,
    show_plot: bool = True,
    **kwargs,
):
    """Plot lumped thermal results using Matplotlib."""
    # Create subplots
    n_plots = 2 if Q_data else 1
    fig, axes = plt.subplots(
        n_plots, 1, figsize=kwargs.get("figsize", (12, 4 * n_plots)), sharex=True
    )

    if n_plots == 1:
        axes = [axes]

    colors = ["red", "orange", "green", "blue", "purple", "brown", "pink", "gray"]

    # Plot temperatures
    for i, (lump_name, T_values) in enumerate(T_data.items()):
        color = colors[i % len(colors)]
        axes[0].plot(
            time,
            T_values - 273.15,
            color=color,
            linewidth=2,
            label=f"{lump_name.capitalize()}",
        )
    axes[0].set_ylabel("Temperature [°C]")
    axes[0].set_title("Lumped-Parameter Thermal-Hydraulics Results")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    # Plot heat sources
    if Q_data:
        for i, (lump_name, Q_values) in enumerate(Q_data.items()):
            color = colors[i % len(colors)]
            axes[1].plot(
                time,
                Q_values / 1e6,
                color=color,
                linestyle="--",
                linewidth=2,
                label=f"{lump_name.capitalize()}",
            )
        axes[1].set_ylabel("Heat Source [MW]")
        axes[1].grid(True, alpha=0.3)
        axes[1].legend()

    # X-axis label on bottom plot
    axes[-1].set_xlabel("Time [s]")

    plt.tight_layout()

    # Save or show
    if output:
        plt.savefig(output, dpi=kwargs.get("dpi", 300), bbox_inches="tight")

    if show_plot:
        plt.show()
    else:
        plt.close(fig)

    return fig


__all__ = [
    "plot_transient",
    "plot_lumped_thermal",
]
