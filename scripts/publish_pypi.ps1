# Publish SMRForge Community tier to PyPI.
# Prerequisites: pip install build twine
# PyPI token: $env:TWINE_USERNAME = "__token__"; $env:TWINE_PASSWORD = "pypi-xxx"
#
# Usage:
#   .\scripts\publish_pypi.ps1           # Upload to PyPI
#   .\scripts\publish_pypi.ps1 -Test     # Upload to TestPyPI first

param([switch]$Test)

Set-Location $PSScriptRoot\..

$version = python -c "from smrforge import __version__; print(__version__)"
Write-Host "Building smrforge v$version"

# Clean previous builds
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue dist, build, smrforge.egg-info

# Build
pip install -q build
python -m build

# Check
python -m twine check dist\*

# Upload
if ($Test) {
    Write-Host "Uploading to TestPyPI..."
    python -m twine upload --repository testpypi dist\*
    Write-Host "Test install: pip install -i https://test.pypi.org/simple/ smrforge"
} else {
    Write-Host "Uploading to PyPI..."
    python -m twine upload dist\*
    Write-Host "Verify: pip install smrforge && python -c 'import smrforge; print(smrforge.__version__)'"
}
