# Bundle wheels for air-gapped SMRForge Community installation.
# Run from smrforge (Community) repo root.
#
# Usage: .\scripts\bundle_offline_wheels.ps1 [-OutputDir ".\offline-wheels"]
#
# Tier: Community. For Pro air-gapped bundles, see smrforge-pro (scripts/airgap/).

param([string]$OutputDir = ".\offline-wheels")
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $RepoRoot

$ReqFile = "requirements-lock.txt"
if (-not (Test-Path $ReqFile)) { $ReqFile = "requirements.txt" }

Write-Host "==> Bundling SMRForge Community wheels to $OutputDir"
Write-Host "==> Using $ReqFile"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
pip download -r $ReqFile -d $OutputDir
pip download . -d $OutputDir

@"
# Air-Gap Installation (Community)

Transfer this directory to the air-gapped machine, then:

  pip install --no-index --find-links ./offline-wheels -r requirements-lock.txt
  pip install --no-index --find-links ./offline-wheels .

For nuclear data, also run scripts/bundle_nuclear_data.sh and transfer that archive.
See docs/guides/air-gapped-deployment.md for full guide.

Community tier includes: parametric builders (create_fuel_pin, create_moderator_block,
create_simple_prismatic_core), 2D Plotly flux maps (plot_flux_map_2d), diffusion,
built-in MC, OpenMC export. CAD/DAGMC import require Pro.
"@ | Out-File -FilePath (Join-Path $OutputDir "INSTALL.md") -Encoding utf8

Write-Host "==> Done. Transfer $OutputDir to air-gapped machine."
