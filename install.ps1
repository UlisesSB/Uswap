<#
.SYNOPSIS
    USwap - one-step installer for Windows (per-user, no administrator needed).

.DESCRIPTION
    1. Finds Python 3.10+ (installs it with winget if missing)
    2. Creates a private virtualenv in %LOCALAPPDATA%\uswap and installs USwap
    3. Adds the `uswap` command to your PATH
    4. Installs FFmpeg, Pandoc and Poppler with winget (if missing)
    5. Adds "Convert with USwap" to the Explorer right-click menu

    Prefer a classic installer? Download USwap-Setup.exe from the GitHub Releases page.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File install.ps1
    powershell -ExecutionPolicy Bypass -File install.ps1 -Uninstall
    powershell -ExecutionPolicy Bypass -File install.ps1 -NoSystemDeps -NoMenu
#>
[CmdletBinding()]
param(
    [switch]$Uninstall,
    [switch]$NoSystemDeps,
    [switch]$NoMenu
)

$ErrorActionPreference = 'Stop'
$Root    = $PSScriptRoot
$AppHome = Join-Path $env:LOCALAPPDATA 'uswap'
$Venv    = Join-Path $AppHome 'venv'
$Bin     = Join-Path $AppHome 'bin'
$VenvPy  = Join-Path $Venv 'Scripts\python.exe'
$VenvExe = Join-Path $Venv 'Scripts\uswap.exe'
$MenuScript = Join-Path $Root 'scripts\menu-windows.ps1'

function Step($msg) { Write-Host "==> $msg" -ForegroundColor Red }
function Info($msg) { Write-Host "    $msg" }

function Refresh-Path {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user    = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
}

function Update-UserPath([string]$Dir, [bool]$Add) {
    $current = [Environment]::GetEnvironmentVariable('Path', 'User')
    $parts = @()
    if ($current) { $parts = $current.Split(';') | Where-Object { $_ -and ($_.TrimEnd('\') -ne $Dir.TrimEnd('\')) } }
    if ($Add) { $parts += $Dir }
    [Environment]::SetEnvironmentVariable('Path', ($parts -join ';'), 'User')
}

# ---------------------------------------------------------------- uninstall
if ($Uninstall) {
    Step 'Removing USwap'
    if (Test-Path $MenuScript) { & powershell -NoProfile -ExecutionPolicy Bypass -File $MenuScript -Uninstall }
    Update-UserPath $Bin $false
    if (Test-Path $AppHome) { Remove-Item $AppHome -Recurse -Force }
    Info 'Done. Your settings (%APPDATA%\uswap) were kept; FFmpeg/Pandoc/Poppler were not removed.'
    return
}

# ------------------------------------------------------------------- python
function Find-Python {
    $candidates = @(@('py', '-3'), @('python'), @('python3'))
    foreach ($c in $candidates) {
        try {
            $exe = $c[0]
            $extra = @(); if ($c.Length -gt 1) { $extra = $c[1..($c.Length - 1)] }
            $out = & $exe @extra -c "import sys; print(sys.executable); sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $out) { return ($out | Select-Object -Last 1).Trim() }
        } catch { }
    }
    return $null
}

Step 'Checking Python'
$py = Find-Python
if (-not $py) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Info 'Python 3.10+ not found. Installing Python 3.12 with winget...'
        winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
        Refresh-Path
        $py = Find-Python
    }
}
if (-not $py) {
    Write-Error 'Python 3.10+ is required. Install it from https://www.python.org/downloads/ (tick "Add python.exe to PATH") and run this script again.'
    return
}
Info "using $py"

# --------------------------------------------------------------------- venv
Step 'Installing USwap'
New-Item -ItemType Directory -Force -Path $AppHome, $Bin | Out-Null
if (-not (Test-Path $VenvPy)) { & $py -m venv $Venv; if ($LASTEXITCODE -ne 0) { throw 'could not create the virtualenv' } }
& $VenvPy -m pip install --quiet --upgrade pip
& $VenvPy -m pip install --quiet --upgrade $Root
if ($LASTEXITCODE -ne 0) { throw 'pip install failed' }

# `uswap` command on PATH: a tiny shim that forwards to the venv.
Set-Content -Path (Join-Path $Bin 'uswap.cmd') -Encoding ASCII -Value "@echo off`r`n`"$VenvExe`" %*"
Update-UserPath $Bin $true
$env:Path = "$Bin;$env:Path"
Info "installed: $(& $VenvExe --version)"

# -------------------------------------------------------------- system deps
if (-not $NoSystemDeps) {
    Step 'Checking FFmpeg, Pandoc and Poppler'
    $wanted = @(
        @{ Cmd = 'ffmpeg';   Id = 'Gyan.FFmpeg' },
        @{ Cmd = 'pandoc';   Id = 'JohnMacFarlane.Pandoc' },
        @{ Cmd = 'pdftoppm'; Id = 'oschwartz10612.Poppler' }
    )
    $hasWinget = [bool](Get-Command winget -ErrorAction SilentlyContinue)
    foreach ($w in $wanted) {
        if (Get-Command $w.Cmd -ErrorAction SilentlyContinue) { Info "$($w.Cmd): found"; continue }
        if (-not $hasWinget) { Info "$($w.Cmd): missing (install winget or get it manually; images still work)"; continue }
        Info "$($w.Cmd): installing $($w.Id) ..."
        try {
            winget install -e --id $w.Id --accept-source-agreements --accept-package-agreements
        } catch { Info "could not install $($w.Id); run 'uswap --doctor' for hints" }
    }
    Refresh-Path
    $env:Path = "$Bin;$env:Path"
}

# --------------------------------------------------------------------- menu
if (-not $NoMenu) {
    Step 'Adding the right-click menu entry'
    & powershell -NoProfile -ExecutionPolicy Bypass -File $MenuScript -UswapPath $VenvExe
}

Write-Host ''
Step 'Done'
& $VenvExe --doctor
Info 'Open a NEW terminal so PATH changes apply, then run:  uswap'
Info 'Or right-click any file > Convert with USwap  (Windows 11: Show more options).'
