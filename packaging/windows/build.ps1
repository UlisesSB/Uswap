<#
Builds dist\USwap-Setup.exe on your own Windows machine (same steps as the release workflow).

Requirements (one time):
    winget install Python.Python.3.12
    winget install JRSoftware.InnoSetup

Run from the repository root:
    powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1
#>
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..\..'))

function Step($m) { Write-Host "==> $m" -ForegroundColor Red }

Step 'Installing build requirements'
python -m pip install --upgrade pip
python -m pip install . pyinstaller
if ($LASTEXITCODE -ne 0) { throw 'pip failed' }

Step 'Building uswap.exe with PyInstaller'
Remove-Item dist, build\uswap -Recurse -Force -ErrorAction SilentlyContinue
python -m PyInstaller packaging/uswap_entry.py --name uswap --onedir --noconfirm --icon assets/uswap.ico `
    --add-data "uswap/locales;uswap/locales" `
    --collect-submodules PIL --collect-submodules watchdog --collect-submodules rich
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed' }
& dist\uswap\uswap.exe --version

Step 'Downloading FFmpeg, Pandoc and Poppler'
& (Join-Path $PSScriptRoot 'fetch-tools.ps1')

Step 'Compiling the installer'
$iscc = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe") |
    Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw 'Inno Setup 6 not found (winget install JRSoftware.InnoSetup)' }
$version = (Select-String -Path uswap\__init__.py -Pattern '__version__ = "(.+)"').Matches[0].Groups[1].Value
& $iscc "/DAppVersion=$version" packaging\windows\uswap.iss
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup failed' }

Step 'Done'
Write-Host "Installer: $(Resolve-Path dist\USwap-Setup.exe)"
Write-Host 'Upload it manually: GitHub > Releases > Draft a new release > attach USwap-Setup.exe'
