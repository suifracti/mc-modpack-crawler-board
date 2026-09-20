param(
    [ValidateSet('portable', 'dir')]
    [string]$Target = 'portable',
    [switch]$SkipRuntimeDownload
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$buildRoot = Join-Path $repoRoot 'build\desktop'
$runtimeRoot = Join-Path $buildRoot 'runtime'
$sourceRoot = Join-Path $buildRoot 'source'

if (Test-Path -LiteralPath $buildRoot) {
    Remove-Item -LiteralPath $buildRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $buildRoot, $runtimeRoot, $sourceRoot | Out-Null

Write-Host '[1/5] Installing frontend dependencies and building the desktop renderer...'
npm.cmd --prefix (Join-Path $repoRoot 'apps\web') ci
if ($LASTEXITCODE -ne 0) { throw "apps/web npm ci failed: $LASTEXITCODE" }
npm.cmd --prefix (Join-Path $repoRoot 'apps\web') run build:desktop
if ($LASTEXITCODE -ne 0) { throw "desktop frontend build failed: $LASTEXITCODE" }

Write-Host '[2/5] Installing Electron packaging dependencies...'
npm.cmd --prefix (Join-Path $repoRoot 'apps\desktop') install
if ($LASTEXITCODE -ne 0) { throw "apps/desktop npm install failed: $LASTEXITCODE" }

Write-Host '[3/5] Preparing the embedded Python runtime and collector sources...'
$runtimeFiles = @('collector_worker.py', 'snapshot_pipeline.py')
foreach ($file in $runtimeFiles) {
    Copy-Item -LiteralPath (Join-Path $repoRoot "apps\desktop\$file") -Destination (Join-Path $runtimeRoot $file)
}

$crawlerFiles = @(
    'bilibili_crawler.py',
    'mcmod_full_crawler.py',
    'bbsmc_crawler.py',
    'xyebbs_crawler.py',
    'modrinth_crawler.py',
    'curseforge_full_crawler.py'
)
foreach ($file in $crawlerFiles) {
    Copy-Item -LiteralPath (Join-Path $repoRoot $file) -Destination (Join-Path $sourceRoot $file)
}

$pipelineFiles = @(
    'pipeline\__init__.py',
    'pipeline\build_canonical_db.py',
    'pipeline\models\__init__.py',
    'pipeline\models\canonical.py',
    'pipeline\adapters\__init__.py',
    'pipeline\adapters\base.py',
    'pipeline\adapters\mcmod.py',
    'pipeline\adapters\bilibili.py',
    'pipeline\adapters\bbsmc.py',
    'pipeline\adapters\xyebbs.py',
    'pipeline\adapters\modrinth.py',
    'pipeline\adapters\curseforge.py',
    'pipeline\db\__init__.py',
    'pipeline\db\connection.py',
    'pipeline\db\schema.sql'
)
foreach ($file in $pipelineFiles) {
    $destination = Join-Path $sourceRoot $file
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
    Copy-Item -LiteralPath (Join-Path $repoRoot $file) -Destination $destination
}

if (-not $SkipRuntimeDownload) {
    $pythonVersion = '3.12.10'
    $pythonZip = Join-Path $env:TEMP "python-$pythonVersion-embed-amd64.zip"
    $pythonUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion-embed-amd64.zip"
    if (-not (Test-Path -LiteralPath $pythonZip)) {
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonZip
    }
    Expand-Archive -LiteralPath $pythonZip -DestinationPath $runtimeRoot -Force
}

$runtimeMarker = [ordered]@{
    runtime = if ($SkipRuntimeDownload) { 'system-python-development-mode' } else { 'python-3.12.10-embed-amd64' }
    generatedAt = (Get-Date).ToUniversalTime().ToString('o')
    sourceFiles = $crawlerFiles
    includesCredentials = $false
    includesGit = $false
    includesAuditDirectory = $false
}
$runtimeMarker | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimeRoot 'runtime-manifest.json') -Encoding utf8

Write-Host '[4/5] Verifying the portable resource boundary...'
if (Test-Path -LiteralPath (Join-Path $runtimeRoot '.git')) { throw 'runtime contains .git' }
if (Get-ChildItem -LiteralPath $runtimeRoot -Recurse -File | Where-Object { $_.Name -match 'cookie|token|profile' }) { throw 'runtime contains a credential/profile-like file' }

Write-Host "[5/5] Packaging Electron target: $Target"
if ($Target -eq 'dir') {
    npm.cmd --prefix (Join-Path $repoRoot 'apps\desktop') run package:dir
} else {
    npm.cmd --prefix (Join-Path $repoRoot 'apps\desktop') run package:portable
}
if ($LASTEXITCODE -ne 0) { throw "Electron packaging failed: $LASTEXITCODE" }

Write-Host "Desktop package output: $(Join-Path $repoRoot 'dist\desktop')"
