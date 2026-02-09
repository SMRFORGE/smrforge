Examples by Tier
================

SMRForge examples are organized by edition: **Community** (free) and **Pro** (licensed).

Community Examples
------------------

**Path:** ``examples/community/``

Community examples cover:
- Multi-group neutronics, burnup, decay heat
- Geometry creation, mesh extraction, visualization
- Presets, convenience API, workflows
- Data download, nuclear data setup

See: ``examples/community/README.md`` for the full index with workflow and required data.

Quick start (no data required):

.. code-block:: bash

   python examples/convenience_methods_example.py
   python examples/preset_designs.py
   python examples/basic_neutronics.py

Pro Examples
------------

**Path:** ``examples/pro/`` (requires SMRForge Pro)

Pro examples cover:
- Serpent export/import
- OpenMC export/import
- Benchmark suite
- Report generator

See: ``examples/pro/README.md`` for the full index.

.. code-block:: bash

   python examples/pro/serpent_export_example.py
   python examples/pro/openmc_export_example.py
   python examples/pro/benchmark_suite_example.py

Documentation
-------------

* Community: :doc:`community/README <community/README>` — Feature matrix, workflows, required data
* Pro: :doc:`pro/README <pro/README>` — Serpent/OpenMC, benchmarks, reporting
