"""
SMRForge Stable API Example (Community tier).

Demonstrates:
- smrforge.api: Stable facade for integration
- create_audit_trail: Audit trail for calculations
- Hooks: register_hook, run_hooks for extensibility

AI/surrogate features (fit_surrogate, export_ml_dataset, record_ai_model) require
SMRForge Pro. See docs/community_vs_pro.md.
"""

from pathlib import Path


def main():
    # --- 1. Stable API: single import ---
    from smrforge.api import create_audit_trail, register_hook, run_hooks

    # --- 2. Create audit trail (Community) ---
    trail = create_audit_trail(
        "keff",
        inputs={"reactor": "valar-10"},
        outputs={"k_eff": 1.002},
    )
    print(f"Audit trail: {trail.calculation_id}, k_eff={trail.outputs.get('k_eff')}")

    # --- 3. Hooks: register callback (Community) ---
    def log_after_keff(ctx):
        print(f"  [hook] after_keff: k_eff={ctx.get('k_eff')}")

    register_hook("after_keff", log_after_keff)
    run_hooks("after_keff", context={"k_eff": 1.05})
    print("Hooks work in Community.")

    # --- 4. Pro-only: fit_surrogate, export_ml_dataset, record_ai_model ---
    try:
        from smrforge.api import fit_surrogate
        import numpy as np
        X = np.array([[0, 0], [1, 1]])
        y = np.array([1.0, 2.0])
        fit_surrogate(X, y, method="linear")
    except ImportError as e:
        print(f"Pro feature (expected in Community): {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()
