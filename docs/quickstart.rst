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

Create LWR SMR Geometry
------------------------

Create a PWR SMR core (NuScale-style):

.. code-block:: python

   from smrforge.geometry.lwr_smr import PWRSMRCore
   
   # Create PWR SMR core
   core = PWRSMRCore(name="NuScale-Example")
   core.build_square_lattice_core(
       n_assemblies_x=4,
       n_assemblies_y=4,
       assembly_pitch=21.5,  # cm
       lattice_size=17,  # 17x17 fuel rods per assembly
       rod_pitch=1.26,  # cm
   )
   
   print(f"Created {core.n_assemblies} fuel assemblies")
   print(f"Total fuel rods: {sum(len(a.fuel_rods) for a in core.assemblies)}")

Advanced Visualization
---------------------

Create ray-traced 3D visualization:

.. code-block:: python

   from smrforge.visualization.advanced import plot_ray_traced_geometry, create_dashboard
   
   # Ray-traced geometry view
   fig = plot_ray_traced_geometry(
       core,
       origin=(0, 0, 200),
       width=(300, 300, 400),
       backend='plotly'
   )
   
   # Multi-view dashboard
   dashboard = create_dashboard(
       core,
       flux=flux,
       power=power,
       views=['xy', 'xz', 'yz', '3d'],
       backend='plotly'
   )

Resonance Self-Shielding
-------------------------

Get cross-sections with self-shielding correction:

.. code-block:: python

   from smrforge.core.reactor_core import (
       NuclearDataCache, Nuclide,
       get_cross_section_with_self_shielding
   )
   
   cache = NuclearDataCache()
   u238 = Nuclide(Z=92, A=238)
   
   # Get shielded cross-section
   energy, xs = get_cross_section_with_self_shielding(
       cache,
       u238,
       "capture",
       temperature=900.0,  # K
       sigma_0=1000.0,  # Background cross-section [barns]
   )

Nuclide Inventory Tracking
---------------------------

Track nuclide concentrations for burnup:

.. code-block:: python

   from smrforge.core.reactor_core import NuclideInventoryTracker, Nuclide
   
   tracker = NuclideInventoryTracker()
   u235 = Nuclide(Z=92, A=235)
   u238 = Nuclide(Z=92, A=238)
   
   # Add initial nuclides
   tracker.add_nuclide(u235, atom_density=0.0005)
   tracker.add_nuclide(u238, atom_density=0.02)
   
   # Update after burnup
   tracker.update_nuclide(u235, atom_density=0.0004)
   tracker.burnup = 10.0  # MWd/kgU

Next Steps
----------

- See :doc:`examples` for more detailed examples including:
  - `advanced_features_examples.py` - All new advanced features
  - `lwr_smr_example.py` - LWR SMR specific examples
  - `visualization_3d_example.py` - Advanced 3D visualization
- Check :doc:`api_reference` for complete API documentation
- Review :doc:`installation` for advanced installation options

