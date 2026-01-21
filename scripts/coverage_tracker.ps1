# Coverage tracker wrapper script (PowerShell)
# Convenient wrapper for track_coverage.py

param(
    [Parameter(Position=0)]
    [string]$Action = "--generate"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

& python "$ScriptDir\track_coverage.py" $Action $args
