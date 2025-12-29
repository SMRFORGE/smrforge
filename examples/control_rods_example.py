"""
Control Rod Geometry Examples

This script demonstrates how to use the SMRForge control rod geometry module
for managing control rods, banks, and systems.
"""

from smrforge.geometry.control_rods import (
    ControlRod,
    ControlRodBank,
    ControlRodSystem,
    ControlRodType,
)
from smrforge.geometry.core_geometry import Point3D


def example_single_control_rod():
    """Example: Create and manipulate a single control rod."""
    print("=" * 60)
    print("Example 1: Single Control Rod")
    print("=" * 60)

    # Create a control rod
    rod = ControlRod(
        id=1,
        position=Point3D(0, 0, 400),
        length=400.0,  # cm
        diameter=5.0,  # cm
        material="B4C",
        rod_type=ControlRodType.SHUTDOWN,
    )

    print(f"Control Rod {rod.id}:")
    print(f"  Position: ({rod.position.x}, {rod.position.y}, {rod.position.z}) cm")
    print(f"  Length: {rod.length} cm")
    print(f"  Diameter: {rod.diameter} cm")
    print(f"  Material: {rod.material}")
    print(f"  Type: {rod.rod_type}")
    print(f"  Initial insertion: {rod.insertion:.1%} (fully withdrawn)")
    print(f"  Volume: {rod.volume():.2f} cm³")

    # Insert rod halfway
    rod.insertion = 0.5
    print(f"\nAfter 50% insertion:")
    print(f"  Insertion: {rod.insertion:.1%}")
    print(f"  Inserted length: {rod.inserted_length():.2f} cm")
    print(f"  Fully inserted: {rod.is_fully_inserted()}")
    print(f"  Fully withdrawn: {rod.is_fully_withdrawn()}")

    # Scram (fully insert)
    rod.insertion = 0.0
    print(f"\nAfter scram:")
    print(f"  Insertion: {rod.insertion:.1%}")
    print(f"  Fully inserted: {rod.is_fully_inserted()}")


def example_control_rod_bank():
    """Example: Create and manage a control rod bank."""
    print("\n" + "=" * 60)
    print("Example 2: Control Rod Bank")
    print("=" * 60)

    # Create a bank
    bank = ControlRodBank(id=1, name="Shutdown-A", max_worth=2000.0)  # 2000 pcm

    # Add rods to the bank
    for i in range(6):
        rod = ControlRod(
            id=i + 1,
            position=Point3D(i * 10, 0, 400),
            length=400.0,
            diameter=5.0,
            material="B4C",
        )
        bank.add_rod(rod)

    print(f"Bank '{bank.name}' created with {len(bank.rods)} rods")
    print(f"Maximum reactivity worth: {bank.max_worth} pcm")

    # Set insertion for all rods
    bank.set_insertion(0.5)
    print(f"\nBank insertion set to {bank.insertion:.1%}")
    print(f"Total reactivity worth: {bank.total_worth():.1f} pcm")

    # Withdraw all rods
    bank.withdraw()
    print(f"\nAfter withdrawal:")
    print(f"  Bank insertion: {bank.insertion:.1%}")
    print(f"  Total reactivity worth: {bank.total_worth():.1f} pcm")

    # Scram all rods
    bank.scram()
    print(f"\nAfter scram:")
    print(f"  Bank insertion: {bank.insertion:.1%}")
    print(f"  Total reactivity worth: {bank.total_worth():.1f} pcm")


def example_control_rod_system():
    """Example: Create and manage a complete control rod system."""
    print("\n" + "=" * 60)
    print("Example 3: Control Rod System")
    print("=" * 60)

    # Create system
    system = ControlRodSystem(name="Primary-Control-System")
    system.scram_threshold = 50e6  # 50 MW scram threshold

    # Create shutdown banks
    shutdown_bank1 = ControlRodBank(id=1, name="Shutdown-A", max_worth=2000.0)
    shutdown_bank2 = ControlRodBank(id=2, name="Shutdown-B", max_worth=2000.0)

    # Create regulation bank
    regulation_bank = ControlRodBank(id=3, name="Regulation", max_worth=500.0)

    # Add rods to banks
    for bank in [shutdown_bank1, shutdown_bank2, regulation_bank]:
        for i in range(3 if bank.name == "Regulation" else 6):
            rod = ControlRod(
                id=i + 1,
                position=Point3D(i * 10, 0, 400),
                length=400.0,
                diameter=5.0,
            )
            bank.add_rod(rod)

    # Add banks to system
    system.add_bank(shutdown_bank1)
    system.add_bank(shutdown_bank2)
    system.add_bank(regulation_bank)

    print(f"System '{system.name}' created with {len(system.banks)} banks")

    # Set different insertions for different banks
    shutdown_bank1.set_insertion(0.8)  # 80% withdrawn
    shutdown_bank2.set_insertion(0.8)
    regulation_bank.set_insertion(0.5)  # 50% withdrawn

    print("\nBank insertions:")
    for bank in system.banks:
        print(f"  {bank.name}: {bank.insertion:.1%} ({bank.total_worth():.1f} pcm)")

    total_worth = system.total_reactivity_worth()
    print(f"\nTotal system reactivity worth: {total_worth:.1f} pcm")

    # Calculate shutdown margin
    k_eff = 1.05  # Example: 5% excess reactivity
    margin = system.shutdown_margin(k_eff)
    print(f"\nShutdown margin (k_eff={k_eff:.3f}): {margin:.1f} pcm")
    if margin > 0:
        print("  ✓ Positive margin - reactor can be shutdown")
    else:
        print("  ✗ Negative margin - shutdown may be insufficient")

    # Scram all banks
    system.scram_all()
    print(f"\nAfter system scram:")
    margin = system.shutdown_margin(k_eff)
    print(f"  Shutdown margin: {margin:.1f} pcm")


if __name__ == "__main__":
    example_single_control_rod()
    example_control_rod_bank()
    example_control_rod_system()

    print("\n" + "=" * 60)
    print("Control rod examples completed!")
    print("=" * 60)

