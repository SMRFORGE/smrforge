Examples
=========

This section contains example scripts demonstrating SMRForge usage.

Quick Start
-----------

For a comprehensive overview of key features, start with:

* :doc:`examples/comprehensive_examples` - Complete workflow examples covering geometry,
  neutronics, thermal-hydraulics, and integration

Basic Examples
--------------

.. toctree::
   :maxdepth: 1

   examples/comprehensive_examples
   examples/basic_neutronics
   examples/preset_designs
   examples/custom_reactor
   examples/thermal_analysis

Geometry Examples
-----------------

.. toctree::
   :maxdepth: 1

   examples/visualization_examples
   examples/control_rods_example
   examples/assembly_refueling_example
   examples/geometry_import_example

Advanced Examples
-----------------

.. toctree::
   :maxdepth: 1

   examples/complete_integration
   examples/integrated_safety_uq

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

