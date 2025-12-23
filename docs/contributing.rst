Contributing
============

Thank you for your interest in contributing to SMRForge!

For detailed contribution guidelines, see `CONTRIBUTING.md <../CONTRIBUTING.md>`_ in the repository root.

Quick Start
-----------

1. Fork the repository
2. Clone your fork
3. Install in development mode:

.. code-block:: bash

   pip install -e ".[dev]"

4. Make your changes
5. Run tests: ``pytest``
6. Format code: ``black smrforge/ tests/``
7. Submit a pull request

Code Style
----------

- **Black** for code formatting (88 char line length)
- **isort** for import sorting
- **Type hints** encouraged
- **Google-style** docstrings

See `CONTRIBUTING.md <../CONTRIBUTING.md>`_ for complete guidelines.

Testing
-------

We aim for 80%+ test coverage on critical modules.

Run tests:
.. code-block:: bash

   pytest
   pytest --cov=smrforge --cov-report=html

Writing Tests
~~~~~~~~~~~~~

- Use pytest conventions
- Descriptive test names
- Use fixtures for common setup
- Mark slow tests with ``@pytest.mark.slow``

Areas for Contribution
----------------------

- Additional test cases
- Documentation improvements
- Bug fixes
- Performance optimizations
- New features (discuss in issues first)

For more information, see the full `CONTRIBUTING.md <../CONTRIBUTING.md>`_ guide.

