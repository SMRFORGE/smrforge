"""
SMRForge Stable API, ML Export, and AI Audit Example.

Demonstrates:
- smrforge.api: Stable facade for integration partners and AI
- export_ml_dataset: Export design points to Parquet/HDF5 for ML training
- record_ai_model: AI audit trail for regulatory traceability
- register_surrogate: Plugin custom surrogate models

Reference: NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md
"""

import numpy as np
from pathlib import Path


def main():
    # --- 1. Stable API: single import for integration ---
    from smrforge.api import fit_surrogate, export_ml_dataset, create_audit_trail

    # --- 2. Fit surrogate (built-in rbf or linear) ---
    X = np.array([[0, 0], [1, 0], [0, 1], [1, 1]])
    y = np.array([0.0, 1.0, 1.0, 2.0])
    sur = fit_surrogate(X, y, method="linear")
    print(f"Surrogate predict at (0.5, 0.5): {sur.predict([[0.5, 0.5]])[0]:.4f}")

    # --- 3. Register custom surrogate (Pro/third-party) ---
    from smrforge.workflows.plugin_registry import (
        register_surrogate,
        unregister_surrogate,
    )

    def mean_factory(X, y, **kwargs):
        m = float(np.mean(y))

        class DummySurrogate:
            def predict(self, x):
                arr = np.atleast_2d(x)
                return np.full(arr.shape[0], m)

        return DummySurrogate()

    register_surrogate("mean", mean_factory)
    sur2 = fit_surrogate(X, y, method="mean")
    print(f"Custom surrogate predict: {sur2.predict([[1, 1]])[0]:.4f}")
    unregister_surrogate("mean")

    # --- 4. Export ML dataset (Parquet) ---
    results = [
        {"parameters": {"x": 0.1, "y": 0.2}, "k_eff": 1.02, "power": 50.0},
        {"parameters": {"x": 0.2, "y": 0.3}, "k_eff": 1.05, "power": 55.0},
    ]
    out = Path("output") / "design_points.parquet"
    out.parent.mkdir(exist_ok=True)
    export_ml_dataset(results, out)
    print(f"Exported to {out}")

    # --- 5. AI audit trail ---
    trail = create_audit_trail(
        "keff",
        inputs={"reactor": "valar-10"},
        outputs={"k_eff": 1.002},
    )
    from smrforge.ai import record_ai_model

    record_ai_model(trail, "rbf", version="scipy-1.11", config_hash="abc123")
    print(f"AI models used: {trail.ai_models_used}")

    print("\nDone.")


if __name__ == "__main__":
    main()
