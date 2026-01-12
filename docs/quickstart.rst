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

Advanced Features
-----------------

LWR SMR Transient Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~

Analyze safety transients for PWR SMRs:

.. code-block:: python

   from smrforge.safety.transients import (
       TransientType,
       TransientConditions,
       SteamLineBreakTransient,
   )
   from smrforge.geometry.lwr_smr import PWRSMRCore
   
   # Create PWR SMR core
   core = PWRSMRCore(name="NuScale-SMR", n_assemblies=37)
   
   # Create reactor spec
   class ReactorSpec:
       def __init__(self):
           self.name = "NuScale-SMR"
           self.power_thermal = 77e6
   
   reactor_spec = ReactorSpec()
   
   # Analyze steam line break
   slb = SteamLineBreakTransient(reactor_spec, core)
   conditions = TransientConditions(
       initial_power=77e6,
       initial_temperature=600.0,
       initial_flow_rate=100.0,
       initial_pressure=15.5e6,
       transient_type=TransientType.STEAM_LINE_BREAK,
       trigger_time=0.0,
       t_end=3600.0,
       scram_available=True,
   )
   
   result = slb.simulate(conditions, break_area=0.01)
   print(f"Peak power: {max(result['power'])/1e6:.2f} MWth")
   print(f"Min pressure: {min(result['pressure'])/1e6:.2f} MPa")

Advanced Burnup Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~

Track gadolinium depletion and assembly-wise burnup:

.. code-block:: python

   from smrforge.burnup.lwr_burnup import (
       GadoliniumDepletion,
       GadoliniumPoison,
       AssemblyWiseBurnupTracker,
   )
   from smrforge.core.reactor_core import NuclearDataCache, Nuclide
   
   # Initialize
   cache = NuclearDataCache()
   gd_depletion = GadoliniumDepletion(cache)
   
   # Create gadolinium poison
   gd155 = Nuclide(Z=64, A=155)
   gd157 = Nuclide(Z=64, A=157)
   gd_poison = GadoliniumPoison(
       nuclides=[gd155, gd157],
       initial_concentrations=[1e20, 1e20],  # atoms/cm³
   )
   
   # Calculate reactivity worth
   flux = 1e14  # n/cm²/s
   initial_worth = gd_depletion.calculate_reactivity_worth(gd_poison, flux, 0.0)
   print(f"Initial Gd worth: {initial_worth*1000:.1f} m$")
   
   # Track assembly burnup
   tracker = AssemblyWiseBurnupTracker(n_assemblies=37)
   for assembly_id in range(37):
       position = tracker.get_assembly_position(assembly_id)
       tracker.update_assembly(assembly_id, position, burnup=50.0, enrichment=0.045)
   
   print(f"Average burnup: {tracker.get_average_burnup():.2f} MWd/kgU")

Automated Data Download
~~~~~~~~~~~~~~~~~~~~~~~

Download ENDF data programmatically:

.. code-block:: python

   from smrforge.data_downloader import download_endf_data
   
   # Download common SMR nuclides
   stats = download_endf_data(
       library="ENDF/B-VIII.1",
       nuclide_set="common_smr",
       output_dir="~/ENDF-Data",
       show_progress=True,
       max_workers=5,  # Parallel downloads
   )
   
   print(f"Downloaded: {stats['downloaded']} files")
   print(f"Skipped: {stats['skipped']} files")

Complete Workflow Example
~~~~~~~~~~~~~~~~~~~~~~~~~~

See `examples/complete_smr_workflow_example.py` for a complete end-to-end example
demonstrating all SMRForge capabilities in a single script.

Next Steps
----------

- See :doc:`examples` for more detailed examples including:
  - `complete_smr_workflow_example.py` - **NEW**: Complete end-to-end workflow
  - `advanced_features_examples.py` - All new advanced features
  - `lwr_smr_example.py` - LWR SMR specific examples
  - `visualization_3d_example.py` - Advanced 3D visualization
- Check :doc:`guides/complete-workflow-examples` for comprehensive workflow examples
- Review :doc:`guides/lwr-smr-transient-analysis` for detailed transient analysis
- Review :doc:`guides/lwr-smr-burnup-guide` for advanced burnup analysis
- Check :doc:`api_reference` for complete API documentation
- Review :doc:`installation` for advanced installation options

