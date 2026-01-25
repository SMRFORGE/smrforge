How to use the SMRForge API
===========================

This page is a practical, user-focused guide to the **Python API**. For the full
reference documentation (all functions/classes), see :doc:`modules`.

Quick start (recommended)
-------------------------

Most users should start with the **convenience API** exposed at the package
top-level.

.. code-block:: python

   import smrforge as smr

   # List built-in reactor presets
   presets = smr.list_presets()
   print(presets)

   # Create a reactor from a preset (recommended starting point)
   reactor = smr.create_reactor("valar-10")

   # Solve k-eff only
   k = reactor.solve_keff()
   print(f"k-eff: {k:.6f}")

   # Or run a fuller analysis (returns a dict of results)
   results = reactor.solve()
   print(results.keys())

Creating a custom reactor
-------------------------

You can also construct a simple custom reactor directly:

.. code-block:: python

   import smrforge as smr

   reactor = smr.create_reactor(
       name="My-Custom-Reactor",
       power_mw=10,
       enrichment=0.195,
   )

   k = reactor.solve_keff()

Saving and loading
------------------

.. code-block:: python

   from pathlib import Path
   import smrforge as smr

   reactor = smr.create_reactor("valar-10")
   out = Path("reactor.json")
   reactor.save(out)

   reactor2 = smr.SimpleReactor.load(out)

Nuclear data (ENDF) setup
-------------------------

Many advanced capabilities require ENDF data files.

1. Run the setup wizard:

.. code-block:: bash

   python -m smrforge.core.endf_setup

2. Use a cache in Python:

.. code-block:: python

   from pathlib import Path
   from smrforge.core.reactor_core import NuclearDataCache

   cache = NuclearDataCache(local_endf_dir=Path("C:/path/to/ENDF-B-VIII.1"))

Workflows (parameter sweeps)
----------------------------

.. code-block:: python

   from smrforge.workflows.parameter_sweep import ParameterSweep, SweepConfig

   config = SweepConfig(
       parameters={"enrichment": [0.15, 0.19, 0.23]},
       analysis_types=["keff"],
       reactor_template={"name": "valar-10"},
       parallel=False,
   )

   sweep = ParameterSweep(config)
   results = sweep.run()
   results.save("testing/results/sweep_results.json")

Validation
----------

SMRForge provides a validation layer to sanity-check designs and results.

- For CLI usage, see ``docs/guides/cli-guide.md``.
- For deeper validation/benchmarking, see ``docs/validation/*``.

Visualization
-------------

Visualization lives under ``smrforge.visualization``. Many users will start with
the Plot API:

.. code-block:: python

   from smrforge.visualization.plot_api import Plot
   import smrforge as smr

   reactor = smr.create_reactor("valar-10")
   core = reactor._get_core()  # advanced use; see docs/guides for higher-level patterns

   plot = Plot(
       plot_type="voxel",
       origin=(0, 0, 0),
       width=(200, 200, 400),
       basis="xyz",
       color_by="material",
       backend="plotly",
       output_file="testing/results/geometry_3d.html",
   )
   plot.plot(core)

Where to go next
----------------

- Tutorial: ``docs/guides/tutorial.md``
- Usage guide: ``docs/guides/usage.md``
- Interactive notebooks: ``docs/guides/testing-notebooks.md`` and ``testing/notebooks/``

