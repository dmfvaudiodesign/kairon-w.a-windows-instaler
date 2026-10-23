[CmdletBinding()]
param(
    [string]$NodeExecutable = (Get-Command node -ErrorAction Stop).Source
)

$ErrorActionPreference = 'Stop'
$InstallerRoot = $PSScriptRoot
$RepositoryRoot = Split-Path -Parent $InstallerRoot
$AppSource = Join-Path $RepositoryRoot 'app'
$BuildRoot = Join-Path $InstallerRoot 'build'
$WorkRoot = Join-Path $BuildRoot 'work'
$PayloadRoot = Join-Path $BuildRoot 'payload'

if (Test-Path -LiteralPath $BuildRoot) {
    $resolved = (Resolve-Path -LiteralPath $BuildRoot).Path
    $expected = Join-Path $InstallerRoot 'build'
    if ($resolved -ne $expected) { throw "Caminho de build inesperado: $resolved" }
    [System.IO.Directory]::Delete($resolved, $true)
}

New-Item -ItemType Directory -Path $WorkRoot, $PayloadRoot | Out-Null

& robocopy $AppSource $WorkRoot /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 `
    /XD (Join-Path $AppSource 'node_modules') (Join-Path $AppSource 'dist') `
        (Join-Path $AppSource 'data') (Join-Path $AppSource 'dashboard\node_modules') `
        (Join-Path $AppSource 'dashboard\dist') `
    /XF '.env' '*.log' '*.db' '*.sqlite' '*.sqlite3' | Out-Null
if ($LASTEXITCODE -ge 8) { throw "Falha ao copiar o código-fonte: $LASTEXITCODE" }

Push-Location $WorkRoot
try {
    npm ci
    Push-Location (Join-Path $WorkRoot 'dashboard')
    try { npm ci } finally { Pop-Location }
    npm run build:all
    npm prune --omit=dev
} finally {
    Pop-Location
}

$PayloadApp = Join-Path $PayloadRoot 'app'
$PayloadRuntime = Join-Path $PayloadRoot 'runtime'
New-Item -ItemType Directory -Path $PayloadApp, $PayloadRuntime | Out-Null

Copy-Item -LiteralPath (Join-Path $WorkRoot 'dist') -Destination $PayloadApp -Recurse
New-Item -ItemType Directory -Path (Join-Path $PayloadApp 'dashboard') | Out-Null
Copy-Item -LiteralPath (Join-Path $WorkRoot 'dashboard\dist') -Destination (Join-Path $PayloadApp 'dashboard') -Recurse
Copy-Item -LiteralPath (Join-Path $WorkRoot 'node_modules') -Destination $PayloadApp -Recurse
Copy-Item -LiteralPath (Join-Path $WorkRoot 'scripts') -Destination $PayloadApp -Recurse
Copy-Item -LiteralPath (Join-Path $WorkRoot 'package.json'), (Join-Path $WorkRoot 'package-lock.json') -Destination $PayloadApp
Copy-Item -LiteralPath (Join-Path $InstallerRoot 'config\windows.env.example') -Destination (Join-Path $PayloadApp '.env')
Copy-Item -LiteralPath $NodeExecutable -Destination (Join-Path $PayloadRuntime 'node.exe')

$Required = @(
    'runtime\node.exe',
    'app\dist\main.js',
    'app\dashboard\dist\index.html',
    'app\node_modules\better-sqlite3\prebuilds\win32-x64.node',
    'app\scripts\postinstall.js',
    'app\scripts\patch-wwebjs-201832.js',
    'app\scripts\patch-baileys-pairing.js',
    'app\.env'
)

foreach ($relative in $Required) {
    $candidate = Join-Path $PayloadRoot $relative
    if (-not (Test-Path -LiteralPath $candidate)) { throw "Arquivo obrigatório ausente: $relative" }
}

Write-Host "Payload preparado em: $PayloadRoot"

