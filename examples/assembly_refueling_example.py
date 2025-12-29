"""
Assembly Management and Refueling Examples

This script demonstrates how to use the SMRForge assembly management module
for tracking assemblies, managing refueling patterns, and estimating cycle lengths.
"""

from smrforge.geometry.assembly import (
    Assembly,
    AssemblyManager,
    RefuelingPattern,
)
from smrforge.geometry.core_geometry import Point3D


def example_single_assembly():
    """Example: Create and track a single assembly."""
    print("=" * 60)
    print("Example 1: Single Assembly")
    print("=" * 60)

    # Create an assembly
    assembly = Assembly(
        id=1,
        position=Point3D(0, 0, 0),
        batch=1,
        burnup=50.0,  # MWd/kgU
        enrichment=0.195,
        heavy_metal_mass=100.0,  # kg
        insertion_cycle=0,
    )

    print(f"Assembly {assembly.id}:")
    print(f"  Batch: {assembly.batch}")
    print(f"  Burnup: {assembly.burnup:.1f} MWd/kgU")
    print(f"  Enrichment: {assembly.enrichment:.1%}")
    print(f"  Heavy metal mass: {assembly.heavy_metal_mass:.1f} kg")

    # Check burnup status
    target_burnup = 120.0  # MWd/kgU
    fraction = assembly.burnup_fraction(target_burnup)
    print(f"\nBurnup status (target: {target_burnup} MWd/kgU):")
    print(f"  Burnup fraction: {fraction:.1%}")
    print(f"  Is depleted: {assembly.is_depleted(target_burnup)}")

    # Age calculation
    current_cycle = 5
    age = assembly.age_cycles(current_cycle)
    print(f"\nAge (current cycle: {current_cycle}):")
    print(f"  Cycles in core: {age}")

    # Update burnup
    assembly.burnup = 130.0
    print(f"\nAfter burnup update:")
    print(f"  New burnup: {assembly.burnup:.1f} MWd/kgU")
    print(f"  Is depleted: {assembly.is_depleted(target_burnup)}")


def example_refueling_pattern():
    """Example: Create and validate a refueling pattern."""
    print("\n" + "=" * 60)
    print("Example 2: Refueling Pattern")
    print("=" * 60)

    # Create a 3-batch pattern
    pattern = RefuelingPattern(
        name="3-batch",
        n_batches=3,
        batch_fractions=[1 / 3, 1 / 3, 1 / 3],
    )

    print(f"Pattern: {pattern.name}")
    print(f"  Number of batches: {pattern.n_batches}")
    print(f"  Batch fractions: {[f'{f:.3f}' for f in pattern.batch_fractions]}")

    # Validate pattern for different core sizes
    for n_assemblies in [30, 90, 99]:
        is_valid = pattern.validate(n_assemblies)
        print(f"\nValidation for {n_assemblies} assemblies: {is_valid}")

        if is_valid:
            for batch in range(pattern.n_batches):
                size = pattern.get_batch_size(n_assemblies, batch)
                print(f"  Batch {batch + 1} size: {size} assemblies")


def example_assembly_manager():
    """Example: Manage multiple assemblies and refueling."""
    print("\n" + "=" * 60)
    print("Example 3: Assembly Manager")
    print("=" * 60)

    # Create manager
    manager = AssemblyManager(name="Core-Manager")

    # Create pattern
    pattern = RefuelingPattern(
        name="3-batch",
        n_batches=3,
        batch_fractions=[1 / 3, 1 / 3, 1 / 3],
    )

    # Create 9 assemblies (3 per batch)
    for i in range(9):
        batch = (i % 3) + 1
        # Vary burnup by batch (batch 3 is oldest)
        burnup = batch * 40.0  # 40, 80, 120 MWd/kgU
        assembly = Assembly(
            id=i + 1,
            position=Point3D(i * 10, 0, 0),
            batch=batch,
            burnup=burnup,
            enrichment=0.195,
            heavy_metal_mass=100.0,
            insertion_cycle=0,
        )
        manager.add_assembly(assembly)

    print(f"Manager '{manager.name}' created with {len(manager.assemblies)} assemblies")
    print(f"Current cycle: {manager.current_cycle}")

    # Get assemblies by batch
    for batch in [1, 2, 3]:
        batch_assemblies = manager.get_assemblies_by_batch(batch)
        avg_burnup = manager.average_burnup(batch=batch)
        print(f"\nBatch {batch}:")
        print(f"  Number of assemblies: {len(batch_assemblies)}")
        print(f"  Average burnup: {avg_burnup:.1f} MWd/kgU")

    # Get depleted assemblies
    target_burnup = 120.0
    depleted = manager.get_depleted_assemblies(target_burnup)
    print(f"\nDepleted assemblies (target: {target_burnup} MWd/kgU):")
    print(f"  Count: {len(depleted)}")
    for assembly in depleted:
        print(f"    Assembly {assembly.id}: {assembly.burnup:.1f} MWd/kgU")

    # Average burnup for all assemblies
    avg_all = manager.average_burnup()
    print(f"\nOverall average burnup: {avg_all:.1f} MWd/kgU")

    # Cycle length estimate
    power_thermal = 50e6  # 50 MW
    cycle_length = manager.cycle_length_estimate(power_thermal, target_burnup)
    print(f"\nCycle length estimate:")
    print(f"  Thermal power: {power_thermal / 1e6:.0f} MW")
    print(f"  Target burnup: {target_burnup} MWd/kgU")
    print(f"  Estimated cycle length: {cycle_length:.1f} days ({cycle_length / 365:.2f} years)")

    # Shuffle assemblies
    print(f"\nShuffling assemblies (pattern: {pattern.name})...")
    initial_cycle = manager.current_cycle
    manager.shuffle_assemblies(pattern)
    print(f"  Cycle incremented: {initial_cycle} → {manager.current_cycle}")

    # Refuel
    print(f"\nRefueling...")
    initial_cycle = manager.current_cycle
    manager.refuel(pattern, target_burnup=target_burnup, fresh_enrichment=0.20)
    print(f"  Cycle incremented: {initial_cycle} → {manager.current_cycle}")

    # Check new burnup distribution
    print("\nNew burnup distribution after refueling:")
    for batch in [1, 2, 3]:
        avg_burnup = manager.average_burnup(batch=batch)
        print(f"  Batch {batch}: {avg_burnup:.1f} MWd/kgU")


if __name__ == "__main__":
    example_single_assembly()
    example_refueling_pattern()
    example_assembly_manager()

    print("\n" + "=" * 60)
    print("Assembly and refueling examples completed!")
    print("=" * 60)

