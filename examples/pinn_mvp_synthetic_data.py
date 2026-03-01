"""
Generate synthetic training data for PINN MVP testing.

Usage:
    python examples/pinn_mvp_synthetic_data.py --output dataset.npz

Produces NPZ with 'x' (design params) and 'y' (k_eff, max_flux, avg_temp).
Requires: smrforge_pro with PyTorch (Pro tier) for full pipeline.
Standalone: This script only needs numpy — run from project root.
"""

import argparse
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np


def generate_synthetic_pinn_data(
    n_samples: int = 150,
    seed: int = 42,
    param_ranges: Optional[Dict[str, Tuple[float, float]]] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic (x, y) for PINN training.

    x: [enrichment, moderator_density, core_height, fuel_radius, cr_position]
    y: [k_eff, max_flux, avg_temp]
    """
    if param_ranges is None:
        param_ranges = {
            "enrichment": (5.0, 20.0),
            "moderator_density": (0.1, 0.9),
            "core_height": (1.0, 2.0),
            "fuel_radius": (0.4, 0.8),
            "cr_position": (0.0, 1.0),
        }
    rng = np.random.default_rng(seed)
    names = list(param_ranges.keys())
    lows = np.array([param_ranges[n][0] for n in names])
    highs = np.array([param_ranges[n][1] for n in names])
    x = rng.uniform(lows, highs, size=(n_samples, len(names)))

    # Simple physics-like relationship (placeholder for real simulator)
    enrichment_norm = (x[:, 0] - lows[0]) / (highs[0] - lows[0])
    mod_norm = x[:, 1]
    k_eff = (
        0.9
        + 0.1 * enrichment_norm
        - 0.05 * np.abs(mod_norm - 0.4)
        + 0.02 * rng.standard_normal(n_samples)
    )
    max_flux = 1e14 * (1.0 + 0.1 * rng.standard_normal(n_samples))
    avg_temp = 500 + 80 * enrichment_norm + 30 * rng.standard_normal(n_samples)

    y = np.column_stack([k_eff, max_flux, avg_temp])
    return x, y


def main():
    ap = argparse.ArgumentParser(description="Generate synthetic PINN training data")
    ap.add_argument(
        "--output", "-o", default="pinn_dataset.npz", help="Output NPZ path"
    )
    ap.add_argument("--samples", "-n", type=int, default=150, help="Number of samples")
    ap.add_argument("--seed", type=int, default=42, help="Random seed")
    args = ap.parse_args()

    x, y = generate_synthetic_pinn_data(n_samples=args.samples, seed=args.seed)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, x=x, y=y)
    print(f"Saved {args.samples} samples to {out}")
    print(f"  x shape: {x.shape}, y shape: {y.shape}")


if __name__ == "__main__":
    main()
