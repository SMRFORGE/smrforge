# Interactive Feature Notebooks

SMRForge includes a **notebook-based feature testing set** intended for users to quickly try out each major feature area (CLI, reactor creation, burnup, sweeps, visualization, etc.) in an interactive environment.

## Where they live

- Notebooks: `testing/notebooks/`
- Underlying scripts (what the notebooks run): `testing/test_*.py`
- Generated test data: `testing/test_data/`
- Notebook/script outputs (plots/HTML/CSVs): `testing/results/` (gitignored)

## Quick start (local)

```bash
pip install -e ".[dev]"
pip install jupyter
jupyter lab
```

Open any notebook under `testing/notebooks/` and run the first cell.

## Quick start (Docker)

If you prefer Docker, follow the manual testing guide and run the scripts directly inside the container:

- `testing/README.md` (manual testing guide)

You can also run notebooks inside the dev container, but it requires installing Jupyter in the container and exposing a port (see `testing/README.md` for detailed steps).

## What each notebook does

Each notebook is intentionally small: it **runs one feature test script** and prints the output inline. This keeps notebooks easy to maintain while still giving users an interactive experience.

## Notebook ↔ feature map

| Notebook | Feature area | Script |
|---|---|---|
| `testing/notebooks/01_CLI_Commands.ipynb` | CLI | `testing/test_01_cli_commands.py` |
| `testing/notebooks/02_Reactor_Creation.ipynb` | Reactor creation / quick analysis | `testing/test_02_reactor_creation.py` |
| `testing/notebooks/03_Burnup.ipynb` | Burnup API + checkpoint options | `testing/test_03_burnup.py` |
| `testing/notebooks/04_Parameter_Sweep.ipynb` | Parameter sweep workflow | `testing/test_04_parameter_sweep.py` |
| `testing/notebooks/05_Templates.ipynb` | Templates | `testing/test_05_templates.py` |
| `testing/notebooks/06_Constraints.ipynb` | Constraints | `testing/test_06_constraints.py` |
| `testing/notebooks/07_IO_Converters.ipynb` | I/O converters | `testing/test_07_io_converters.py` |
| `testing/notebooks/08_Data_Management.ipynb` | Data management | `testing/test_08_data_management.py` |
| `testing/notebooks/09_Validation.ipynb` | Validation | `testing/test_09_validation.py` |
| `testing/notebooks/10_Visualization.ipynb` | Visualization | `testing/test_10_visualization.py` |
| `testing/notebooks/11_Workflows.ipynb` | Workflow runner | `testing/test_11_workflows.py` |
| `testing/notebooks/12_Config.ipynb` | Config | `testing/test_12_config.py` |
| `testing/notebooks/13_Advanced.ipynb` | Advanced features | `testing/test_13_advanced.py` |

