Installation Guide
===================

SMRForge requires Python 3.8 or higher.

Basic Installation
------------------

Using pip:

.. code-block:: bash

   pip install smrforge

Installation Options
--------------------

Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

To install in development mode (editable):

.. code-block:: bash

   git clone https://github.com/cmwhalen/smrforge.git
   cd smrforge
   pip install -e .

With Development Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install -e ".[dev]"

This includes:
- pytest (testing)
- black (code formatting)
- mypy (type checking)
- flake8 (linting)

With Documentation Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install -e ".[docs]"

This includes:
- sphinx
- sphinx-rtd-theme

Docker Installation
-------------------

See :doc:`docker_usage` for Docker installation instructions.

System Dependencies
-------------------

For SANDY (optional, for nuclear data):

- CMake
- gfortran
- pkg-config
- libhdf5-dev

On Ubuntu/Debian:

.. code-block:: bash

   sudo apt-get install build-essential gfortran cmake pkg-config libhdf5-dev

On macOS:

.. code-block:: bash

   brew install cmake gfortran hdf5 pkg-config

Verifying Installation
----------------------

Test your installation:

.. code-block:: python

   import smrforge as smr
   print(smr.__version__)

Troubleshooting
---------------

If you encounter issues:

1. Ensure Python 3.8+ is installed
2. Check that all dependencies are installed
3. See :doc:`troubleshooting` for common issues

