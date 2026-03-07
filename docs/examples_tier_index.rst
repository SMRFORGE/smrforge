Examples by Tier
================

SMRForge examples are organized by edition: **Community** (free) and **Pro** (licensed).

Community Examples
------------------

**Path:** ``examples/`` (Community repo root)

Community examples cover:
- Multi-group neutronics, burnup, decay heat
- Geometry creation, mesh extraction, visualization
- Presets, convenience API, workflows
- Data download, nuclear data setup

See: ``examples/community/README.md`` for the full index with workflow and required data.

Quick start (no data required):

.. code-block:: bash

   python examples/quick_start_community.py
   python examples/convenience_methods_example.py
   python examples/preset_designs.py
   python examples/basic_neutronics.py

Pro Examples
------------

**Pro examples live in the smrforge-pro repository** (private, licensed): https://github.com/SMRFORGE/smrforge-pro

Pro is not included in the Community repo. Pro examples cover:
- Serpent export/import
- OpenMC export/import
- Benchmark suite and benchmark reproduction
- Report generator
- Natural-language design
- Code-to-code verification
- Regulatory submission package
- Multi-objective optimization
- Physics-informed surrogates
- PINN surrogate modeling

To run Pro examples, install SMRForge Pro from the Pro repo and see ``examples/pro/`` there.

Documentation
-------------

* Community: :doc:`community/README <community/README>` — Feature matrix, workflows, required data
* Pro: See `docs/pro-tier-overview.md` and the smrforge-pro repo for Pro documentation
