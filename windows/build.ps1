<#
USwap - builds the Windows installer (dist\USwap-Setup-2.0.0.exe)

Needs, on your PC:  Python 3.8+  and  Inno Setup 6  (https://jrsoftware.org/isdl.php)
Run from the repository folder:

    powershell -ExecutionPolicy Bypass -File windows\build.ps1

Steps: makes uswap.exe with PyInstaller, downloads FFmpeg, Pandoc and Poppler
into build\tools, then compiles windows\uswap.iss with Inno Setup.
#>
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'   # makes Invoke-WebRequest much faster
$root  = Resolve-Path (Join-Path $PSScriptRoot '..')
$build = Join-Path $root 'build'
$dl    = Join-Path $build 'downloads'
$tools = Join-Path $build 'tools'
Set-Location $root

function Step($m) { Write-Host "> $m" -ForegroundColor Red }

function Get-Asset($repo, $pattern) {
    $rel = Invoke-RestMethod "https://api.github.com/repos/$repo/releases/latest"
    $asset = $rel.assets | Where-Object { $_.name -like $pattern } | Select-Object -First 1
    if (-not $asset) { throw "no $pattern in the latest release of $repo" }
    $file = Join-Path $dl $asset.name
    Write-Host "  $($asset.name)"
    Invoke-WebRequest $asset.browser_download_url -OutFile $file
    return $file
}

function Expand-To($zip, $name) {
    $dest = Join-Path $dl $name
    Expand-Archive $zip -DestinationPath $dest -Force
    return $dest
}

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

# 2. FFmpeg, Pandoc, Poppler ----------------------------------------------
Step 'Downloading FFmpeg, Pandoc and Poppler'
Remove-Item $dl, $tools -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $dl, $tools | Out-Null

$zip = Join-Path $dl 'ffmpeg.zip'   # gyan.dev "essentials": x264, vpx, webp, lame, opus, vorbis
Write-Host '  ffmpeg-release-essentials.zip'
Invoke-WebRequest 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile $zip
Get-ChildItem (Expand-To $zip 'ffmpeg') -Recurse -Include ffmpeg.exe, ffprobe.exe | Copy-Item -Destination $tools

$zip = Get-Asset 'jgm/pandoc' 'pandoc-*-windows-x86_64.zip'
Get-ChildItem (Expand-To $zip 'pandoc') -Recurse -Filter pandoc.exe | Copy-Item -Destination $tools

$zip = Get-Asset 'oschwartz10612/poppler-windows' 'Release-*.zip'
$bin = Get-ChildItem (Expand-To $zip 'poppler') -Recurse -Filter pdftoppm.exe | Select-Object -First 1
Copy-Item (Join-Path $bin.DirectoryName '*') -Destination $tools -Recurse -Force

foreach ($need in 'ffmpeg.exe', 'ffprobe.exe', 'pandoc.exe', 'pdftoppm.exe', 'pdftotext.exe') {
    if (-not (Test-Path (Join-Path $tools $need))) { throw "missing $need" }
}

# 3. Installer ------------------------------------------------------------
Step 'Compiling the installer with Inno Setup'
$iscc = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
          "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw 'Inno Setup 6 not found. Install it from https://jrsoftware.org/isdl.php' }
& $iscc /Q windows\uswap.iss
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup failed' }

& (Join-Path $build 'uswap\uswap.exe') --version
Get-ChildItem dist\USwap-Setup-*.exe | ForEach-Object { Write-Host "  ready: $($_.FullName)" -ForegroundColor Green }
