param(
    [int]$Port = 8765,
    [switch]$Open
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

Write-Host '[1/2] Building the browser renderer...'
npm.cmd --prefix (Join-Path $repoRoot 'apps\web') run build:desktop
if ($LASTEXITCODE -ne 0) { throw "desktop frontend build failed: $LASTEXITCODE" }

Write-Host '[2/2] Starting the local browser service...'
$serviceArgs = @('apps/desktop/server.cjs', '--port', [string]$Port)
if ($Open) { $serviceArgs += '--open' }
node @serviceArgs
