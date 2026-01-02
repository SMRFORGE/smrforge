"""
Example demonstrating the SMRForge help system.

This script shows how to use the interactive help system to discover
functions, classes, and features in SMRForge.
"""

import smrforge as smr


def main():
    """Demonstrate the help system."""
    print("=" * 70)
    print("SMRForge Help System Demonstration")
    print("=" * 70)
    print()

    # 1. Show main help menu
    print("\n1. Main Help Menu:")
    print("-" * 70)
    smr.help()

    # 2. Get help on a specific function
    print("\n\n2. Help on create_simple_core:")
    print("-" * 70)
    smr.help("create_simple_core")

    # 3. Get help on a category
    print("\n\n3. Help on Geometry Category:")
    print("-" * 70)
    smr.help("geometry")

    # 4. Get help on convenience functions
    print("\n\n4. Help on Convenience Functions:")
    print("-" * 70)
    smr.help("convenience")

    # 5. Get help on getting started
    print("\n\n5. Getting Started Guide:")
    print("-" * 70)
    smr.help("getting_started")

    # 6. Get help on examples
    print("\n\n6. Examples Guide:")
    print("-" * 70)
    smr.help("examples")

    # 7. Get help on workflows
    print("\n\n7. Common Workflows:")
    print("-" * 70)
    smr.help("workflows")

    # 8. Get help on materials
    print("\n\n8. Materials Help:")
    print("-" * 70)
    smr.help("materials")

    # 9. Get help on nuclides
    print("\n\n9. Nuclides Help:")
    print("-" * 70)
    smr.help("nuclides")

    # 10. Get help on visualization
    print("\n\n10. Visualization Help:")
    print("-" * 70)
    smr.help("visualization")

    print("\n" + "=" * 70)
    print("Help System Demonstration Complete")
    print("=" * 70)
    print("\nTry these commands in your Python session:")
    print("  >>> import smrforge as smr")
    print("  >>> smr.help()                    # Show main menu")
    print("  >>> smr.help('create_reactor')    # Help on function")
    print("  >>> smr.help('geometry')          # Help on category")
    print("  >>> smr.help('getting_started')   # Getting started guide")


if __name__ == "__main__":
    main()
