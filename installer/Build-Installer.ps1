[CmdletBinding()]
param(
    [string]$IsccPath = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
)

$ErrorActionPreference = 'Stop'
$Payload = Join-Path $PSScriptRoot 'build\payload'
$Manifest = Join-Path $PSScriptRoot 'KAIRON-WA.iss'

$Required = @(
    'runtime\node.exe',
    'app\dist\main.js',
    'app\dashboard\dist\index.html',
    'app\scripts\postinstall.js',
    'app\scripts\patch-wwebjs-201832.js'
)

foreach ($relative in $Required) {
    if (-not (Test-Path -LiteralPath (Join-Path $Payload $relative))) {
        throw "Payload incompleto: $relative. Execute Prepare-Payload.ps1 primeiro."
    }
}

$UiAssets = Join-Path $PSScriptRoot 'assets\ui'
foreach ($screen in 'welcome_100.bmp','installing_100.bmp','finished_100.bmp','progress_100.bmp') {
    if (-not (Test-Path -LiteralPath (Join-Path $UiAssets $screen))) {
        throw "Telas do instalador ausentes: assets\ui\$screen. Execute: python installer/tools/render_ui.py"
    }
}

if (-not (Test-Path -LiteralPath $IsccPath)) {
    throw "Inno Setup 6 não encontrado em: $IsccPath"
}

& $IsccPath $Manifest
if ($LASTEXITCODE -ne 0) { throw "Falha na compilação do instalador: $LASTEXITCODE" }

