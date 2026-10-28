<#
USwap - builds the Windows installer (dist\USwap-Setup-<version>.exe)

Needs, on your PC:  Python 3.8+  and  Inno Setup 6  (https://jrsoftware.org/isdl.php)
Run from the repository folder:

    powershell -ExecutionPolicy Bypass -File windows\build.ps1

Steps: makes uswap.exe with PyInstaller, downloads FFmpeg into build\tools,
then compiles windows\uswap.iss with Inno Setup. Pandoc, Poppler and the other
optional tools are not bundled: users add them from USwap > Optional formats.
#>
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'   # makes Invoke-WebRequest much faster
$root  = Resolve-Path (Join-Path $PSScriptRoot '..')
$build = Join-Path $root 'build'
$tools = Join-Path $build 'tools'
$dl    = Join-Path $build 'downloads'
Set-Location $root

function Step($m) { Write-Host "> $m" -ForegroundColor Red }

$version = (Select-String -Path uswap.py -Pattern '__version__ = "(.+)"').Matches[0].Groups[1].Value
Step "USwap $version"

# 1. uswap.exe -------------------------------------------------------------
Step 'Building uswap.exe with PyInstaller'
$venv = Join-Path $build 'venv'
if (-not (Test-Path "$venv\Scripts\python.exe")) {
    if (Get-Command py -ErrorAction SilentlyContinue) { py -3 -m venv $venv } else { python -m venv $venv }
}
& "$venv\Scripts\python.exe" -m pip install --quiet --upgrade pyinstaller
& "$venv\Scripts\pyinstaller.exe" (Join-Path $root 'uswap.py') --name uswap --onedir --noconfirm --clean `
    --icon (Join-Path $root 'assets\uswap.ico') --distpath $build --workpath (Join-Path $build 'pyinstaller') --specpath $build
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed' }

# 2. FFmpeg ---------------------------------------------------------------
Step 'Downloading FFmpeg'
Remove-Item $dl, $tools -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $dl, $tools | Out-Null
$zip = Join-Path $dl 'ffmpeg.zip'   # gyan.dev "essentials": x264, vpx, webp, lame, opus, vorbis
Invoke-WebRequest 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile $zip
Expand-Archive $zip -DestinationPath (Join-Path $dl 'ffmpeg') -Force
Get-ChildItem (Join-Path $dl 'ffmpeg') -Recurse -Include ffmpeg.exe, ffprobe.exe | Copy-Item -Destination $tools
foreach ($need in 'ffmpeg.exe', 'ffprobe.exe') {
    if (-not (Test-Path (Join-Path $tools $need))) { throw "missing $need" }
}

# 3. Installer ------------------------------------------------------------
Step 'Compiling the installer with Inno Setup'
$iscc = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
          "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw 'Inno Setup 6 not found. Install it from https://jrsoftware.org/isdl.php' }
& $iscc /Q "/DAppVersion=$version" windows\uswap.iss
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup failed' }

& (Join-Path $build 'uswap\uswap.exe') --version
Get-ChildItem "dist\USwap-Setup-$version.exe" | ForEach-Object { Write-Host "  ready: $($_.FullName)" -ForegroundColor Green }
