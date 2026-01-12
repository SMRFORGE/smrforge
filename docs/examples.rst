Examples
=========

This section contains example scripts demonstrating SMRForge usage.

Quick Start
-----------

For a comprehensive overview of key features, start with:

* :doc:`examples/comprehensive_examples` - Complete workflow examples covering geometry,
  neutronics, thermal-hydraulics, and integration
* :doc:`examples/advanced_features_examples` - **NEW (January 2026)**: Advanced features including
  visualization, decay chains, LWR SMRs, self-shielding, and more

Basic Examples
--------------

.. toctree::
   :maxdepth: 1

   examples/comprehensive_examples
   examples/basic_neutronics
   examples/preset_designs
   examples/custom_reactor
   examples/thermal_analysis

Advanced Features Examples
---------------------------

**NEW (January 2026)**: Comprehensive examples of new advanced features:

.. toctree::
   :maxdepth: 1

   examples/advanced_features_examples

These examples demonstrate:
- Advanced 3D visualization (ray-traced geometry, interactive viewers, dashboards)
- LWR SMR geometry (PWR, BWR, compact cores, integral designs)
- Resonance self-shielding for accurate cross-sections
- Fission yield and delayed neutron data
- Prompt/delayed chi for transient analysis
- Decay chain utilities and Bateman equation solving
- Thermal scattering laws (TSL)
- Nuclide inventory tracking
- Complete integrated SMR analysis workflows

Geometry Examples
-----------------

.. toctree::
   :maxdepth: 1

   examples/visualization_examples
   examples/visualization_3d_example
   examples/control_rods_example
   examples/assembly_refueling_example
   examples/geometry_import_example
   examples/lwr_smr_example

Advanced Examples
-----------------

.. toctree::
   :maxdepth: 1

   examples/complete_integration
   examples/integrated_safety_uq
   examples/burnup_example
   examples/decay_heat_example
   examples/thermal_scattering_example

All example scripts are available in the ``examples/`` directory of the source code.

Running Examples
----------------

All examples can be run directly from the command line:

.. code-block:: bash

   # Run a specific example
   python examples/comprehensive_examples.py
   python examples/basic_neutronics.py

   # Or run all examples
   cd examples
   python *.py

Output files (plots, JSON exports, etc.) are saved to the ``output/`` directory.

