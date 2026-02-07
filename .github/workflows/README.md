# GitHub Actions Workflows

This directory contains CI/CD workflows for SMRForge.

## Enabling and selecting features

- **Global switch:** `.github/workflows-enabled` — set to `true` or `false`. When `false`, no workflow runs.
- **Per-feature config:** `.github/workflows-config.json` — optional. When present, each workflow runs only if both the global switch is on and its feature is `true` in the config.

**CLI (run from repo root):**

```bash
smrforge github status              # show global + per-feature status
smrforge github list                # list features and whether they run
smrforge github configure           # interactive: choose which features run
smrforge github configure --ci on --docs off --release on --nightly off   # non-interactive
smrforge github set docs on         # set one feature on or off
smrforge github enable              # turn on all workflows (global)
smrforge github disable             # turn off all workflows (global)
```

**Feature IDs:** `ci`, `ci-quick`, `docs`, `performance`, `security`, `release`, `nightly`, `docker`, `dependabot`, `stale`. Omit `workflows-config.json` to use only the global switch (all workflows follow it).

## Workflows

| Workflow | Feature ID | Triggers |
|----------|------------|----------|
| `ci.yml` | ci | push/PR to main, develop |
| `ci-quick.yml` | ci-quick | push/PR to main, develop |
| `docs.yml` | docs | push to main, manual |
| `performance.yml` | performance | weekly schedule, manual |
| `security.yml` | security | weekly schedule, manual |
| `release.yml` | release | push tags `v*`, manual |
| `nightly.yml` | nightly | daily schedule, manual |
| `docker.yml` | docker | push to main, tags `v*`, manual |
| `dependabot-ci.yml` | dependabot | PRs from dependabot[bot] |
| `stale.yml` | stale | daily schedule, manual |

### `performance.yml` - Performance benchmarks

Runs performance (time + memory) regression tests on a **weekly schedule** and via **workflow_dispatch**. Uses `--run-performance` and `--override-ini`; excluded from default pytest. See [performance-and-benchmarking-assessment](development/performance-and-benchmarking-assessment.md).

### `ci.yml` - Continuous Integration

This workflow runs on every push and pull request to `main` and `develop` branches.

**Jobs:**

1. **Test** - Runs test suite on multiple Python versions (3.8, 3.9, 3.10, 3.11)
   - Installs system dependencies
   - Installs core dependencies (without OpenMC for faster builds)
   - Optionally installs OpenMC (continues if it fails)
   - Runs pytest with coverage
   - Uploads coverage to Codecov

2. **Lint** - Checks code quality
   - Black (code formatting)
   - isort (import sorting)
   - flake8 (style checking)
   - mypy (type checking)

3. **Build** - Validates package builds correctly
   - Builds source and wheel distributions
   - Validates package with twine

## Usage

Workflows run automatically on push/PR. You can also trigger them manually from the GitHub Actions tab.

## Dependencies

The CI workflow requires:
- System packages: build-essential, gfortran, cmake, pkg-config, libhdf5-dev, libblas-dev, liblapack-dev, libxml2-dev, libpng-dev
- Python packages: Listed in `requirements.txt`

## Notes

- OpenMC installation is optional - the build continues even if OpenMC fails to install
- Coverage is uploaded to Codecov (requires Codecov token in repository settings). To enable PR comments with coverage diff, add a `codecov.yml` in the repo root with a `comment:` section (see [Codecov docs](https://docs.codecov.com/docs/pull-request-comments)).
- Linting checks are set to `continue-on-error: true` to avoid blocking merges while code is being improved
- **Release:** set `PYPI_API_TOKEN` (or use a `pypi` environment) for publishing. Create the `pypi` environment in repo Settings → Environments if using the release workflow.
- **Docker:** images are pushed to GitHub Container Registry (ghcr.io). Enable Packages write for the repo if needed.

## Implemented features

The following are enabled via the CLI and `workflows-config.json`:

- **release** – Build and publish to PyPI on version tags (`v*`). Uses `pypa/gh-action-pypi-publish` and `PYPI_API_TOKEN` (or `pypi` environment).
- **nightly** – Scheduled full test run (cron 02:00 UTC), plus manual trigger.
- **ci-quick** – Fast CI on push/PR: single Python, tests without coverage, quick lint.
- **docker** – Build and push image to GHCR on push to `main` or tags `v*`.
- **dependabot** – Runs tests only on PRs opened by `dependabot[bot]` when this feature is on.
- **stale** – `actions/stale` on a schedule to mark and close stale issues/PRs (configurable in `stale.yml`).

All workflows use **concurrency** to avoid overlapping runs; CI and quick CI cancel in-progress runs on new pushes.

## Optional / future

| Feature | What to add | CLI integration |
|--------|-------------|------------------|
| **Caching** | Use `actions/cache` for pip, conda, or build artifacts to speed up jobs (setup-python already uses `cache: 'pip'` where applicable). | None; controlled per workflow. |
| **Matrix for docs** | If docs build under multiple configs (e.g. Python 3.9 and 3.10), add a matrix to `docs.yml`. | None; still under existing `docs` feature. |
| **Security: SBOM / signing** | Generate SBOM (e.g. with syft) or sign artifacts; can live in `security.yml` or a dedicated workflow. | Keep under `security` or add `sbom` if you want it toggleable. |

### Adding a new feature to the CLI

1. Add an entry to `GITHUB_ACTIONS_FEATURES` in `smrforge/cli.py` (id, name, description).
2. Add the feature key to `scripts/github_workflow_check.py` (e.g. in the allowed set and default).
3. Create (or update) the workflow under `.github/workflows/` and add a `check-enabled` job that runs `python3 scripts/github_workflow_check.py <feature_id>` and set downstream jobs to `if: needs.check-enabled.outputs.enabled == 'true'`.
4. Document the new feature ID in this README under “Feature IDs” and in the tables above if relevant.

