geometry.importers module
=========================

This module provides geometry import functionality for reading reactor geometries
from various file formats including JSON, OpenMC XML, and Serpent input files.

.. automodule:: smrforge.geometry.importers
   :members:
   :undoc-members:
   :show-inheritance:

Examples
--------

Import from JSON:

.. code-block:: python

   from pathlib import Path
   from smrforge.geometry.importers import GeometryImporter

   # Import previously exported geometry
   core = GeometryImporter.from_json(Path("geometry.json"))
   print(f"Imported: {core.name}, Blocks: {len(core.blocks)}")

   # Validate imported geometry
   validation = GeometryImporter.validate_imported_geometry(core)
   if validation["valid"]:
       print("Geometry is valid!")
   else:
       print(f"Errors: {validation['errors']}")

Import from OpenMC XML:

.. code-block:: python

   from pathlib import Path
   from smrforge.geometry.importers import GeometryImporter

   # Import from OpenMC geometry.xml file
   core = GeometryImporter.from_openmc_xml(Path("geometry.xml"))
   print(f"Core diameter: {core.core_diameter} cm")
   print(f"Core height: {core.core_height} cm")

   Note: OpenMC import handles simple geometries with z-cylinder and z-plane surfaces.
   Complex CSG geometries may raise NotImplementedError.

Import from Serpent:

.. code-block:: python

   from pathlib import Path
   from smrforge.geometry.importers import GeometryImporter

   # Import from Serpent input file
   core = GeometryImporter.from_serpent(Path("geometry.inp"))
   print(f"Core diameter: {core.core_diameter} cm")

   Note: Serpent import handles simple geometries with cz, pz, and hexprism surfaces.
   Complex geometries may raise NotImplementedError.

See also
--------

* :doc:`examples/geometry_import_example` - Complete examples of geometry import/export
* :mod:`smrforge.geometry.core_geometry` - Core geometry classes
* :mod:`smrforge.geometry` - Geometry module overview
