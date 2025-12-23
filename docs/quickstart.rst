Quick Start Guide
==================

This guide will get you started with SMRForge in just a few minutes.

Installation
------------

Install SMRForge using pip:

.. code-block:: bash

   pip install smrforge

Or install from source:

.. code-block:: bash

   git clone https://github.com/cmwhalen/smrforge.git
   cd smrforge
   pip install -e .

Basic Usage
-----------

Import SMRForge:

.. code-block:: python

   import smrforge as smr

Create a Simple Reactor
-----------------------

Using preset designs:

.. code-block:: python

   from smrforge.presets.htgr import ValarAtomicsReactor
   
   # Create a preset reactor
   reactor = ValarAtomicsReactor()
   
   print(f"Reactor: {reactor.spec.name}")
   print(f"Power: {reactor.spec.power_thermal / 1e6} MW")

Run Neutronics Analysis
------------------------

.. code-block:: python

   from smrforge.neutronics.solver import MultiGroupDiffusion
   from smrforge.validation.models import CrossSectionData, SolverOptions
   from tests.test_utilities import SimpleGeometry
   
   # Create geometry
   geometry = SimpleGeometry()
   
   # Create cross-section data
   xs_data = CrossSectionData(...)  # See examples for details
   
   # Create solver options
   options = SolverOptions(max_iterations=100, tolerance=1e-5)
   
   # Create and run solver
   solver = MultiGroupDiffusion(geometry, xs_data, options)
   k_eff, flux = solver.solve_steady_state()
   
   print(f"k-effective: {k_eff:.6f}")

Compute Power Distribution
---------------------------

.. code-block:: python

   # After solving
   total_power = 10e6  # 10 MW
   power_dist = solver.compute_power_distribution(total_power)
   
   print(f"Maximum power density: {power_dist.max():.2e} W/cm³")

Next Steps
----------

- See :doc:`examples` for more detailed examples
- Check :doc:`api_reference` for complete API documentation
- Review :doc:`installation` for advanced installation options

