import numpy as np


def test_plot_slice_cylindrical_plane_plotly():
    # Skip if plotly isn't available in the environment.
    try:
        import plotly.graph_objects as go  # noqa: F401
    except Exception:  # pragma: no cover
        return

    from smrforge.geometry.core_geometry import PrismaticCore
    from smrforge.visualization.advanced import plot_slice

    core = PrismaticCore(name="SliceTestCore")
    core.core_height = 200.0
    core.core_diameter = 100.0
    core.generate_mesh(n_radial=6, n_axial=4)

    nz = len(core.axial_mesh) - 1
    nr = len(core.radial_mesh) - 1
    data = np.arange(nz * nr, dtype=float).reshape(nz, nr)

    fig = plot_slice(
        data, core, axis="z", position=100.0, field_name="flux", backend="plotly"
    )
    assert fig is not None


def test_plot_slice_cartesian_interactive_plotly():
    try:
        import plotly.graph_objects as go  # noqa: F401
    except Exception:  # pragma: no cover
        return

    from smrforge.visualization.advanced import plot_slice

    data = np.random.default_rng(0).random((8, 6, 5))
    fig = plot_slice(
        data,
        geometry=None,
        axis="z",
        position=2,
        field_name="T",
        backend="plotly",
        interactive=True,
        max_frames=10,
    )
    # If interactive, we should have frames.
    assert hasattr(fig, "frames")
    assert len(fig.frames) > 0
