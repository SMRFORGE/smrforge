Comprehensive Examples
======================

This module provides comprehensive examples demonstrating key SMRForge features and workflows.

.. automodule:: examples.comprehensive_examples
   :members:
   :undoc-members:
   :show-inheritance:

The comprehensive examples script demonstrates:

1. **Geometry Creation**: Creating and configuring prismatic core geometries
2. **Neutronics Solver**: Solving multi-group diffusion equations
3. **Thermal-Hydraulics**: 1D channel thermal-hydraulics analysis
4. **Geometry Import/Export**: Working with geometry file formats
5. **Integrated Workflow**: Combining multiple modules for complete analysis

Usage
-----

Run the comprehensive examples:

.. code-block:: bash

   python examples/comprehensive_examples.py

This will execute all example functions and demonstrate the complete workflow.

Example Output
--------------

The script prints detailed information about each step:

.. code-block:: text

   ============================================================
   Example 1: Geometry Creation
   ============================================================
   Created core: Example-Core
     Core height: 793.0 cm
     Core diameter: 300.0 cm
     Number of blocks: 127
     Mesh: 30 radial × 20 axial cells

   ============================================================
   Example 2: Neutronics Solver
   ============================================================
   k-eff: 1.123456
   Flux shape: (10, 20, 2)
   Total flux: 1.23e+05
   ...

See the source file for complete output and more details.

