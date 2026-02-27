# Copy air-gap scripts, docs, and workflow from Community repo to smrforge-pro.
# Run from smrforge (Community) repo root.
#
# Usage: .\scripts\airgap\copy_to_pro.ps1 -ProPath C:\path\to\smrforge-pro

param(
    [Parameter(Mandatory=$true)]
    [string]$ProPath
)

$ErrorActionPreference = "Stop"
$CommunityRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent

if (-not (Test-Path $ProPath -PathType Container)) {
    Write-Error "Pro repo path does not exist: $ProPath"
    exit 1
}

Write-Host "==> Copying air-gap content from $CommunityRoot to $ProPath"

# Scripts
$airgap = Join-Path $ProPath "scripts\airgap"
New-Item -ItemType Directory -Force -Path $airgap | Out-Null
Copy-Item "$CommunityRoot\scripts\airgap\bundle_wheels.sh"   $airgap -Force
Copy-Item "$CommunityRoot\scripts\airgap\bundle_wheels.ps1"  $airgap -Force
Copy-Item "$CommunityRoot\scripts\airgap\bundle_docker.sh"   $airgap -Force
Copy-Item "$CommunityRoot\scripts\airgap\README.md"         $airgap -Force

# Docs
$deploy = Join-Path $ProPath "docs\deployment"
New-Item -ItemType Directory -Force -Path $deploy | Out-Null
Copy-Item "$CommunityRoot\docs\deployment\air-gapped-pro.md" $deploy -Force

# Workflow
$workflows = Join-Path $ProPath ".github\workflows"
New-Item -ItemType Directory -Force -Path $workflows | Out-Null
Copy-Item "$CommunityRoot\.github\workflows\release-airgap.yml" $workflows -Force

Write-Host "==> Done. Pro repo has air-gap scripts, docs, and release workflow."
