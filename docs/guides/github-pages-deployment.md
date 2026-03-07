# Deploy Community Documentation to GitHub Pages

This guide explains how to deploy SMRForge Community tier documentation to GitHub Pages.

## Prerequisites

- Push access to the `SMRFORGE/smrforge` repository
- Admin access to repository Settings (for GitHub Pages)

## Step 1: Enable Workflows

The docs workflow is gated by the global workflows switch. Enable it:

**Option A – CLI (recommended):**
```bash
smrforge github enable          # Turn on all workflows
smrforge github set docs on     # Ensure docs feature is on
```

**Option B – Manual:**
1. Edit `.github/workflows-enabled`
2. Set content to `true` (not `false`)
3. Commit and push to `main`

Verify: `smrforge github status` should show workflows enabled and docs on.

## Step 2: Enable GitHub Pages in Repository Settings

1. Go to https://github.com/SMRFORGE/smrforge
2. **Settings** → **Pages** (left sidebar)
3. Under **Build and deployment** → **Source**, select **GitHub Actions**
4. Save (no branch selection needed)

## Step 3: Trigger Deployment

**Option A – Push to main:**
```bash
git push origin main
```

**Option B – Manual trigger:**
1. Go to **Actions**
2. Select **Build and Deploy Documentation**
3. **Run workflow** → **Run workflow**

## Step 4: Verify

1. In **Actions**, wait for the workflow to finish (about 3–5 minutes)
2. Open https://SMRFORGE.github.io/smrforge/
3. Confirm the docs load correctly

## What Gets Deployed

- **Community tier only** – no Pro content
- Sphinx HTML docs from `docs/`
- API reference generated from `smrforge` package
- Guides, examples, and tutorials

## Workflow Details

| Step | Action |
|------|--------|
| Check | Verifies workflows are enabled |
| Install | `pip install -e ".[dev,docs]"` |
| API docs | Regenerates `docs/api/*.rst` from source |
| Build | `sphinx-build -b html docs docs/_build/html` |
| Deploy | Uploads to GitHub Pages |

## Troubleshooting

### Workflow doesn't run
- Ensure `.github/workflows-enabled` contains `true`
- Ensure `workflows-config.json` has `"docs": true` (or omit the key)
- Run `smrforge github status` to check

### Build fails
- Check the **Actions** log for the failing step
- Test locally: `pip install -e ".[docs]" && cd docs && sphinx-build -b html . _build/html`
- Common causes: import errors, missing deps, Sphinx/RST errors

### 404 or blank page
- GitHub Pages can take 5–10 minutes after the first deploy
- Confirm **Settings** → **Pages** shows a green success message
- URL format: `https://<org>.github.io/<repo>/` (trailing slash matters for some paths)

### Docs are stale
- The workflow regenerates API docs on each run
- Push to `main` or manually trigger the workflow to refresh

## Related

- [Read the Docs deployment](readthedocs-deployment.md) – alternative hosting
- [.github/workflows/docs.yml](../../.github/workflows/docs.yml) – workflow definition
