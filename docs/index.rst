SMRForge Documentation
======================

.. image:: logo/nukepy-logo.png
   :alt: SMRForge Logo
   :align: center
   :width: 400

**Small Modular Reactor Design and Analysis Toolkit**

SMRForge is a comprehensive Python toolkit for nuclear reactor design, analysis, and optimization with a focus on Small Modular Reactors (SMRs).

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api_reference
   examples
   examples_tier_index

.. toctree::
   :maxdepth: 1
   :caption: Tier Documentation:

   community_index
   
.. toctree::
   :maxdepth: 1
   :caption: Guides:

   guides/dashboard-guide
   guides/usage
   guides/visualization-gallery
   guides/visual-analytics
   guides/data-downloader-guide
   guides/testing-notebooks

.. toctree::
   :maxdepth: 1
   :caption: Development:

   contributing
   

Installation
------------

.. code-block:: bash

   pip install smrforge

   # Or with uv (recommended)
   uv pip install smrforge

Quick Start
-----------

.. code-block:: python

   import smrforge as smr

   # Create a reactor from preset
   reactor = smr.create_reactor("valar-10")

   # Run neutronics analysis
   k_eff = reactor.solve_keff()
   print(f"k_eff: {k_eff:.6f}")

Features
--------

* **Neutronics**: Multi-group diffusion solver with power iteration and Arnoldi methods
* **Nuclear Data**: ENDF file parsing with resonance self-shielding, fission yields, delayed neutrons, thermal scattering laws
* **Geometry**: Prismatic, pebble bed, and LWR SMR core geometries
  - HTGR cores (prismatic, pebble bed)
  - LWR SMR cores (PWR, BWR with square lattice assemblies)
  - Integral reactor designs (in-vessel steam generators)
  - Compact SMR layouts
* **Visualization**: 2D/3D plots, animations, advanced 3D visualization (ray-traced geometry, interactive viewers, dashboards)
* **Thermal-Hydraulics**: Channel models with fluid properties
* **Safety Analysis**: Transient simulations (LOFC, ATWS, RIA, LOCA)
* **Burnup**: Nuclide inventory tracking, decay chain utilities, Bateman equation solver
* **Validation**: Pydantic-based input validation with physics checks
* **Presets**: Reference HTGR designs (Valar-10, GT-MHR, HTR-PM, Micro-HTGR)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

