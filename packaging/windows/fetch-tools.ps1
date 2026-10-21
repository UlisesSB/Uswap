<#
Downloads FFmpeg, Pandoc and Poppler for Windows and flattens their executables
into build\tools so the installer can ship them. Used by the release workflow.
Requires the GitHub CLI (`gh`, preinstalled on GitHub runners) with GH_TOKEN set.
#>
$ErrorActionPreference = 'Stop'
$root  = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$work  = Join-Path $root 'build\downloads'
$tools = Join-Path $root 'build\tools'
Remove-Item $work, $tools -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $work, $tools | Out-Null

function Get-Release($repo, $pattern, $tag) {
    $ghArgs = @('release', 'download')
    if ($tag) { $ghArgs += $tag }
    $ghArgs += @('--repo', $repo, '--pattern', $pattern, '--dir', $work)
    & gh @ghArgs
    if ($LASTEXITCODE -ne 0) { throw "download failed: $repo $pattern" }
}

# FFmpeg (GPL build: needed for libx264 / libvpx / libopus / libvorbis / libmp3lame)
Get-Release 'BtbN/FFmpeg-Builds' 'ffmpeg-master-latest-win64-gpl.zip' 'latest'
Expand-Archive (Join-Path $work 'ffmpeg-master-latest-win64-gpl.zip') -DestinationPath (Join-Path $work 'ffmpeg') -Force
Get-ChildItem (Join-Path $work 'ffmpeg') -Recurse -Include ffmpeg.exe, ffprobe.exe | Copy-Item -Destination $tools

# Pandoc
Get-Release 'jgm/pandoc' 'pandoc-*-windows-x86_64.zip' $null
Get-ChildItem $work -Filter 'pandoc-*-windows-x86_64.zip' | ForEach-Object {
    Expand-Archive $_.FullName -DestinationPath (Join-Path $work 'pandoc') -Force
}
Get-ChildItem (Join-Path $work 'pandoc') -Recurse -Filter pandoc.exe | Copy-Item -Destination $tools

# Poppler (pdftoppm, pdftotext + the DLLs they need)
Get-Release 'oschwartz10612/poppler-windows' 'Release-*.zip' $null
Get-ChildItem $work -Filter 'Release-*.zip' | ForEach-Object {
    Expand-Archive $_.FullName -DestinationPath (Join-Path $work 'poppler') -Force
}
$popplerBin = Get-ChildItem (Join-Path $work 'poppler') -Recurse -Filter pdftoppm.exe | Select-Object -First 1
Copy-Item (Join-Path $popplerBin.DirectoryName '*') -Destination $tools -Recurse -Force

Write-Host 'Tools ready:'
Get-ChildItem $tools -Filter *.exe | ForEach-Object { Write-Host "  $($_.Name)" }
foreach ($need in 'ffmpeg.exe', 'ffprobe.exe', 'pandoc.exe', 'pdftoppm.exe', 'pdftotext.exe') {
    if (-not (Test-Path (Join-Path $tools $need))) { throw "missing $need in build\tools" }
}
