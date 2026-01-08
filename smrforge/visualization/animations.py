"""
Animation utilities for transient visualization.

Provides functions to create animations of time-dependent reactor data including
flux distributions, power distributions, temperature profiles, and control rod movements.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np

try:
    import matplotlib
    import matplotlib.animation as animation
    import matplotlib.pyplot as plt

    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False
    matplotlib = None  # type: ignore
    animation = None  # type: ignore
    plt = None  # type: ignore

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False
    go = None  # type: ignore
    make_subplots = None  # type: ignore
    _PLOTLY_AVAILABLE = False
    go = None  # type: ignore

try:
    from PIL import Image

    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False
    Image = None  # type: ignore

try:
    import imageio

    _IMAGEIO_AVAILABLE = True
except ImportError:
    _IMAGEIO_AVAILABLE = False
    imageio = None  # type: ignore

from ..geometry.mesh_3d import Mesh3D
from .geometry import plot_core_layout

if matplotlib is not None:
    Writer = animation.writers["ffmpeg"] if "ffmpeg" in animation.writers.list() else None
else:
    Writer = None


def animate_transient_matplotlib(
    times: np.ndarray,
    data_func: Callable[[float], np.ndarray],
    geometry_func: Optional[Callable[[float], "PrismaticCore"]] = None,
    field_name: str = "flux",
    view: str = "xy",
    interval: int = 100,
    figsize: tuple = (10, 8),
    save_path: Optional[Union[str, Path]] = None,
    fps: int = 10,
    **kwargs,
) -> animation.FuncAnimation:
    """
    Create matplotlib animation of transient reactor data.

    Args:
        times: Array of time points
        data_func: Function that takes time and returns 2D data array (n_radial x n_axial)
        geometry_func: Optional function that takes time and returns geometry
        field_name: Name of the field being animated (for labels)
        view: View direction ('xy', 'xz', 'yz')
        interval: Frame interval in milliseconds
        figsize: Figure size
        save_path: Optional path to save animation (MP4 or GIF)
        fps: Frames per second for saved animation
        **kwargs: Additional matplotlib arguments

    Returns:
        matplotlib.animation.FuncAnimation instance

    Examples:
        Animate flux distribution over time::

            def get_flux(t):
                # Return flux at time t
                return solver.get_flux_at_time(t)

            anim = animate_transient_matplotlib(
                times=np.linspace(0, 100, 50),
                data_func=get_flux,
                field_name="flux",
                save_path="flux_animation.gif"
            )
            plt.show()
    """
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "matplotlib is required for animations. Install with: pip install matplotlib"
        )

    fig, ax = plt.subplots(figsize=figsize)

    # Initialize plot
    time_idx = 0
    data = data_func(times[0])
    if geometry_func is not None:
        geometry = geometry_func(times[0])
        plot_core_layout(geometry, view=view, ax=ax, **kwargs)
        im = ax.imshow(
            data,
            extent=ax.get_xlim() + ax.get_ylim(),
            origin="lower",
            interpolation="bilinear",
            cmap=kwargs.get("cmap", "viridis"),
        )
    else:
        im = ax.imshow(data, origin="lower", interpolation="bilinear", cmap=kwargs.get("cmap", "viridis"))
        ax.set_xlabel("X (cm)" if view in ["xy", "xz"] else "Y (cm)")
        ax.set_ylabel("Y (cm)" if view == "xy" else "Z (cm)")

    ax.set_title(f"{field_name.title()} Distribution - t = {times[0]:.2f} s")
    plt.colorbar(im, ax=ax, label=field_name)

    def update(frame):
        """Update function for animation."""
        time_idx = frame % len(times)
        t = times[time_idx]
        data = data_func(t)

        # Update image data
        im.set_array(data)

        # Update geometry if provided
        if geometry_func is not None:
            ax.clear()
            geometry = geometry_func(t)
            plot_core_layout(geometry, view=view, ax=ax, **kwargs)
            im = ax.imshow(
                data,
                extent=ax.get_xlim() + ax.get_ylim(),
                origin="lower",
                interpolation="bilinear",
                cmap=kwargs.get("cmap", "viridis"),
            )

        # Update title
        ax.set_title(f"{field_name.title()} Distribution - t = {times[time_idx]:.2f} s")

        return [im]

    anim = animation.FuncAnimation(fig, update, frames=len(times), interval=interval, blit=True)

    # Save if path provided
    if save_path:
        save_path = Path(save_path)
        if save_path.suffix.lower() == ".gif":
            _save_gif_matplotlib(anim, save_path, fps=fps)
        elif save_path.suffix.lower() in [".mp4", ".mov"]:
            if Writer is None:
                raise ValueError(
                    "FFmpeg writer not available. Install ffmpeg to save MP4 files: "
                    "https://ffmpeg.org/download.html"
                )
            writer = Writer(fps=fps, bitrate=1800)
            anim.save(save_path, writer=writer)
        else:
            raise ValueError(f"Unsupported format: {save_path.suffix}")

    return anim


def animate_3d_transient_plotly(
    times: np.ndarray,
    mesh_func: Callable[[float], Mesh3D],
    field_name: str = "flux",
    interval: int = 100,
    title: str = "3D Transient",
    **kwargs,
) -> Any:  # type: ignore
    """
    Create plotly animation of 3D transient data.

    Args:
        times: Array of time points
        mesh_func: Function that takes time and returns Mesh3D instance
        field_name: Name of the field being animated
        interval: Frame interval in milliseconds
        title: Plot title
        **kwargs: Additional plotly arguments

    Returns:
        plotly.graph_objects.Figure with animation frames

    Examples:
        Animate 3D mesh over time::

            def get_mesh(t):
                return extract_mesh_at_time(t)

            fig = animate_3d_transient_plotly(
                times=np.linspace(0, 100, 20),
                mesh_func=get_mesh,
                field_name="flux"
            )
            fig.show()
    """
    if not _PLOTLY_AVAILABLE:
        raise ImportError(
            "plotly is required for 3D animations. Install with: pip install plotly"
        )

    from .mesh_3d import plot_mesh3d_plotly

    # Create initial frame
    initial_mesh = mesh_func(times[0])
    fig = plot_mesh3d_plotly(initial_mesh, color_by=field_name, title=title, **kwargs)

    # Create frames for animation
    frames = []
    for t in times:
        mesh = mesh_func(t)
        frame_fig = plot_mesh3d_plotly(mesh, color_by=field_name, title=f"{title} - t = {t:.2f} s", **kwargs)

        # Extract trace data
        frame_data = frame_fig.data[0]

        # Create frame
        frame = go.Frame(
            data=[frame_data],
            name=str(t),
            layout=go.Layout(title_text=f"{title} - t = {t:.2f} s"),
        )
        frames.append(frame)

    # Add frames to figure
    fig.frames = frames

    # Add animation controls
    fig.update_layout(
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "buttons": [
                    {
                        "label": "Play",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": interval, "redraw": True},
                                "fromcurrent": True,
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                    {
                        "label": "Pause",
                        "method": "animate",
                        "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}],
                    },
                ],
            }
        ],
        sliders=[
            {
                "active": 0,
                "yanchor": "top",
                "xanchor": "left",
                "currentvalue": {
                    "font": {"size": 20},
                    "prefix": "Time: ",
                    "visible": True,
                    "xanchor": "right",
                },
                "transition": {"duration": 0},
                "pad": {"b": 10, "t": 50},
                "len": 0.9,
                "x": 0.1,
                "y": 0,
                "steps": [
                    {
                        "args": [
                            [str(t)],
                            {
                                "frame": {"duration": interval, "redraw": True},
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                        "label": f"{t:.2f}",
                        "method": "animate",
                    }
                    for t in times
                ],
            }
        ],
    )

    return fig


def _save_gif_matplotlib(anim: "animation.FuncAnimation", save_path: Path, fps: int = 10) -> None:
    """Save matplotlib animation as GIF."""
    if not _IMAGEIO_AVAILABLE:
        raise ImportError(
            "imageio is required for GIF export. Install with: pip install imageio[ffmpeg]"
        )

    # Extract frames
    frames = []
    for frame_num in range(len(anim._frames)):  # type: ignore
        anim._draw_frame(frame_num)  # type: ignore
        fig = anim._fig
        fig.canvas.draw()
        buf = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        buf = buf.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        frames.append(buf)

    # Save as GIF
    imageio.mimsave(str(save_path), frames, fps=fps, loop=0)


def create_comparison_animation(
    data_dict: Dict[str, Dict[float, np.ndarray]],
    times: np.ndarray,
    field_name: str = "flux",
    n_cols: int = 2,
    figsize: tuple = (16, 8),
    interval: int = 100,
    save_path: Optional[Union[str, Path]] = None,
    fps: int = 10,
    **kwargs,
) -> animation.FuncAnimation:
    """
    Create side-by-side comparison animation of multiple reactor designs.

    Args:
        data_dict: Dictionary mapping design name -> {time: data_array}
        times: Array of time points
        field_name: Name of the field being compared
        n_cols: Number of columns in comparison grid
        figsize: Figure size
        interval: Frame interval in milliseconds
        save_path: Optional path to save animation
        fps: Frames per second for saved animation
        **kwargs: Additional matplotlib arguments

    Returns:
        matplotlib.animation.FuncAnimation instance

    Examples:
        Compare two reactor designs::

            data = {
                "Design A": {t: get_flux_a(t) for t in times},
                "Design B": {t: get_flux_b(t) for t in times}
            }

            anim = create_comparison_animation(
                data_dict=data,
                times=times,
                field_name="flux",
                save_path="comparison.gif"
            )
            plt.show()
    """
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "matplotlib is required for animations. Install with: pip install matplotlib"
        )

    design_names = list(data_dict.keys())
    n_designs = len(design_names)
    n_rows = int(np.ceil(n_designs / n_cols))

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    if n_designs == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    # Initialize plots
    images = []
    for i, name in enumerate(design_names):
        ax = axes[i]
        data = data_dict[name][times[0]]
        im = ax.imshow(data, origin="lower", interpolation="bilinear", cmap=kwargs.get("cmap", "viridis"))
        ax.set_title(f"{name} - t = {times[0]:.2f} s")
        ax.set_xlabel("X (cm)")
        ax.set_ylabel("Y (cm)")
        plt.colorbar(im, ax=ax, label=field_name)
        images.append(im)

    # Hide unused axes
    for i in range(n_designs, len(axes)):
        axes[i].axis("off")

    def update(frame):
        """Update function for animation."""
        time_idx = frame % len(times)
        t = times[time_idx]

        for i, name in enumerate(design_names):
            data = data_dict[name][t]
            images[i].set_array(data)
            axes[i].set_title(f"{name} - t = {t:.2f} s")

        return images

    anim = animation.FuncAnimation(fig, update, frames=len(times), interval=interval, blit=True)

    # Save if path provided
    if save_path:
        save_path = Path(save_path)
        if save_path.suffix.lower() == ".gif":
            _save_gif_matplotlib(anim, save_path, fps=fps)
        elif save_path.suffix.lower() in [".mp4", ".mov"]:
            if Writer is None:
                raise ValueError(
                    "FFmpeg writer not available. Install ffmpeg to save MP4 files: "
                    "https://ffmpeg.org/download.html"
                )
            writer = Writer(fps=fps, bitrate=1800)
            anim.save(save_path, writer=writer)

    return anim

