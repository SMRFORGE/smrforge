# SMRForge Feature Notebooks

This folder contains **Jupyter notebooks that run the existing manual feature test scripts** in `testing/test_*.py`.

They are meant to be the fastest way for users to **try each feature area interactively** (and see the printed output inline), without needing to copy/paste code into notebooks.

## Prerequisites

- Install SMRForge (editable recommended): `pip install -e ".[dev]"`
- Install Jupyter: `pip install jupyter`

## How to run

From the repo root:

```bash
jupyter lab
```

Then open any notebook in `testing/notebooks/` and run the first cell.

## Notes

- Notebooks locate the repo root automatically, so they work even if Jupyter’s working directory is not the repo root.
- Manual test data lives in `testing/test_data/`.
- Generated plots/HTML outputs are written under `testing/results/` (gitignored).

