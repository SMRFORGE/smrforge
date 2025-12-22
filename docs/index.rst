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

   # Create a reactor
   reactor = smr.Reactor(name="SMR-160")

   # Run neutronics analysis
   solver = smr.neutronics.NeutronicsSolver(reactor)
   k_eff = solver.solve_eigenvalue()

Features
--------

* **Neutronics**: Multi-group diffusion solver
* **Thermal-Hydraulics**: Channel models
* **Safety Analysis**: Transient simulations
* **Validation**: Pydantic-based input validation
* **Presets**: Reference HTGR designs

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

