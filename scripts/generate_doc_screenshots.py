"""
Generate documentation screenshots for Sphinx.

Outputs images into:
  docs/_static/screenshots/

This script is intentionally lightweight and uses matplotlib's non-interactive
backend so it can run in CI/local environments.
"""

from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    import matplotlib

    matplotlib.use("Agg")  # Headless
    import matplotlib.pyplot as plt
    import numpy as np

    out_dir = _repo_root() / "docs" / "_static" / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Generating screenshots into: {out_dir}", flush=True)

    # 1) Core layout (2D) - real SMRForge plot
    try:
        from smrforge.geometry.core_geometry import PrismaticCore
        from smrforge.visualization.geometry import plot_core_layout

        core = PrismaticCore(name="example-core")
        core.build_hexagonal_lattice(
            n_rings=2,
            pitch=40.0,
            block_height=50.0,
            n_axial=1,
            flat_to_flat=36.0,
        )
        fig, ax = plot_core_layout(core, view="xy", show_labels=False)
        ax.set_title("Core layout (SMRForge example)")
        fig.tight_layout()
        fig.savefig(out_dir / "core_layout_xy.png", dpi=150)
        plt.close(fig)
        print("Wrote: core_layout_xy.png", flush=True)
    except Exception as e:
        print(f"[warn] core layout screenshot failed: {e}", flush=True)

    # 2) Neutronics outputs (flux + power samples)
    try:
        # Keep this screenshot fast and dependency-light: use smooth, representative
        # synthetic curves rather than running a full eigenvalue solve.
        k_eff = 1.0000
        x = np.linspace(0.0, 1.0, 500)
        flux_1d = np.exp(-4.0 * x) + 0.05 * np.sin(20 * x)
        power_1d = np.exp(-((x - 0.5) / 0.18) ** 2)

        fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=False)
        fig.suptitle(f"Neutronics outputs (k-eff = {k_eff:.6f})")

        axes[0].plot(flux_1d, color="navy")
        axes[0].set_ylabel("Flux (a.u.)")
        axes[0].set_title("Flux (representative shape)")

        axes[1].plot(power_1d, color="crimson")
        axes[1].set_ylabel("Power (a.u.)")
        axes[1].set_xlabel("Position index (a.u.)")
        axes[1].set_title("Power distribution (representative shape)")

        fig.tight_layout(rect=(0, 0, 1, 0.96))
        fig.savefig(out_dir / "neutronics_flux_power.png", dpi=150)
        plt.close(fig)
        print("Wrote: neutronics_flux_power.png", flush=True)
    except Exception as e:
        print(f"[warn] neutronics screenshot failed: {e}", flush=True)

    # 3) Quick transient (power + temperatures) - real SMRForge output
    try:
        from smrforge.convenience.transients import quick_transient

        res = quick_transient(
            power=1e6,
            temperature=1200.0,
            transient_type="reactivity_insertion",
            reactivity_insertion=0.001,
            duration=30.0,
            scram_available=True,
            scram_delay=1.0,
            plot=False,
        )

        # Note: the convenience API returns `t` (not `time`)
        t = np.asarray(res.get("t", []), dtype=float)
        p = np.asarray(res.get("power", []), dtype=float)
        tf = np.asarray(res.get("T_fuel", []), dtype=float)
        tm = np.asarray(res.get("T_moderator", []), dtype=float)

        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(t, p, label="Power (W)", color="navy")
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Power (W)", color="navy")
        ax1.tick_params(axis="y", labelcolor="navy")

        ax2 = ax1.twinx()
        if tf.size:
            ax2.plot(t, tf, label="T_fuel (K)", color="crimson", alpha=0.8)
        if tm.size:
            ax2.plot(t, tm, label="T_moderator (K)", color="orange", alpha=0.8)
        ax2.set_ylabel("Temperature (K)")

        ax1.set_title("Quick transient (SMRForge example): power + temperatures")
        # Legend (combine both axes)
        lines = ax1.get_lines() + ax2.get_lines()
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc="upper right")

        fig.tight_layout()
        fig.savefig(out_dir / "transient_power_temperatures.png", dpi=150)
        plt.close(fig)
        print("Wrote: transient_power_temperatures.png", flush=True)
    except Exception as e:
        print(f"[warn] transient screenshot failed: {e}", flush=True)

    print(f"Wrote screenshots to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

