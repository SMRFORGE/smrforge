"""
SMRForge Pro — Physics-Informed Surrogate Example

Build surrogate with uncertainty quantification and physics constraints
(e.g., k_eff > 0).

Workflow:
  1. Provide sweep results [{enrichment: x, k_eff: y}, ...]
  2. Call physics_informed_surrogate_from_sweep()
  3. Use predictor(x) -> PhysicsInformedPrediction with mean, std, violations

Required: Pro license
Output: Predictor function with UQ and physics checks
"""


def main():
    try:
        import numpy as np
        from smrforge_pro.ai.physics_informed import (
            PhysicsInformedSurrogateConfig,
            physics_informed_surrogate_from_sweep,
        )
    except ImportError:
        print("SMRForge Pro is required for physics-informed surrogates.")
        print("Install: pip install smrforge-pro")
        return 1

    print("=" * 60)
    print("SMRForge Pro — Physics-Informed Surrogate Example")
    print("=" * 60)

    results = [
        {"enrichment": 0.18, "k_eff": 0.98},
        {"enrichment": 0.19, "k_eff": 1.02},
        {"enrichment": 0.20, "k_eff": 1.05},
    ]

    config = PhysicsInformedSurrogateConfig(
        enforce_positive_keff=True,
        uncertainty_quantification=True,
    )

    print("\n1. Fitting surrogate from sweep results...")
    predictor = physics_informed_surrogate_from_sweep(
        results,
        ["enrichment"],
        output_metric="k_eff",
        config=config,
    )

    print("\n2. Predictions at enrichment=0.19:")
    pred = predictor(np.array([0.19]))
    print(f"   Mean k_eff: {pred.mean:.4f}")
    if pred.std is not None:
        print(f"   Std: {pred.std:.4f}")
    print(f"   Physics violations: {pred.physics_violations or 'none'}")

    print("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
