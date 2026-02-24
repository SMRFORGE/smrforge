"""
SMRForge Pro — Multi-Objective Design Optimization Example

Optimize across neutronics (k_eff), safety margins, and economics.

Workflow:
  1. Define reactor_from_x(x) mapping params to reactor
  2. Call multi_objective_optimize()
  3. Inspect x_opt, objectives, pareto_front

Required: Pro license, smrforge, scipy
Output: Optimal design point, objective values
"""


def main():
    try:
        from smrforge.convenience import create_reactor
        from smrforge_pro.workflows.multi_objective_optimization import (
            multi_objective_optimize,
        )
    except ImportError as e:
        print("SMRForge Pro and smrforge required for multi-objective optimization.")
        print("Install: pip install smrforge smrforge-pro")
        print(f"Error: {e}")
        return 1

    print("=" * 60)
    print("SMRForge Pro — Multi-Objective Optimization Example")
    print("=" * 60)

    bounds = [(0.18, 0.22)]
    param_names = ["enrichment"]

    def reactor_from_x(x):
        return create_reactor(
            power_mw=10,
            enrichment=float(x[0]),
            core_height=200,
            core_diameter=100,
        )

    print("\n1. Optimizing k_eff vs enrichment (bounds [0.18, 0.22])...")
    result = multi_objective_optimize(
        reactor_from_x,
        bounds,
        param_names,
        max_evaluations=30,
        seed=42,
    )

    print(f"\n2. Optimal enrichment: {result.x_opt[0]:.4f}")
    print(f"   Objectives: {result.objectives}")
    print(f"   Evaluations: {result.n_evaluations}")

    print("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
