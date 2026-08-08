[CmdletBinding()]
param(
    [switch]$SkipDependencyInstall
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$frontendRoot = Join-Path $projectRoot "operator-console"
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        & $pyLauncher.Source -3.12 -m venv (Join-Path $projectRoot ".venv")
    } else {
        & python -m venv (Join-Path $projectRoot ".venv")
    }
    if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed." }
}

if (-not $SkipDependencyInstall) {
    & $venvPython -m pip install --disable-pip-version-check -r (Join-Path $projectRoot "requirements-desktop-build.txt")
    if ($LASTEXITCODE -ne 0) { throw "Python dependency installation failed." }
    Push-Location $frontendRoot
    try {
        npm ci
        if ($LASTEXITCODE -ne 0) { throw "Node dependency installation failed." }
    } finally {
        Pop-Location
    }
}

& $venvPython -m pytest -q --basetemp (Join-Path $projectRoot "build\pytest-desktop")
if ($LASTEXITCODE -ne 0) { throw "Backend validation failed." }

Push-Location $frontendRoot
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend production build failed." }
} finally {
    Pop-Location
}

& $venvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --name tradingengine-backend `
    --distpath (Join-Path $projectRoot "build\desktop-backend") `
    --workpath (Join-Path $projectRoot "build\pyinstaller") `
    --specpath (Join-Path $projectRoot "build\pyinstaller-spec") `
    --paths $projectRoot `
    --collect-all schwab `
    --hidden-import uvicorn.logging `
    --hidden-import uvicorn.loops.auto `
    --hidden-import uvicorn.protocols.http.auto `
    --hidden-import uvicorn.protocols.websockets.auto `
    --hidden-import uvicorn.lifespan.on `
    (Join-Path $projectRoot "desktop_backend.py")
if ($LASTEXITCODE -ne 0) { throw "Python backend packaging failed." }

Push-Location $frontendRoot
try {
    npx electron-builder --win
    if ($LASTEXITCODE -ne 0) { throw "Electron packaging failed." }
} finally {
    Pop-Location
}

Write-Output "TradingEngine desktop artifacts are available in:"
Write-Output (Join-Path $frontendRoot "release")
