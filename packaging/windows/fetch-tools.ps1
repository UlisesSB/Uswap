<#
Downloads FFmpeg, Pandoc and Poppler for Windows and flattens their executables
into build\tools so the installer can ship them.

Uses only the public GitHub API (no GitHub CLI needed). If GH_TOKEN / GITHUB_TOKEN is
set (as on GitHub Actions) it is used to avoid API rate limits.
#>
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'   # makes Invoke-WebRequest much faster on Windows PowerShell 5.1
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$root  = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$work  = Join-Path $root 'build\downloads'
$tools = Join-Path $root 'build\tools'
Remove-Item $work, $tools -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $work, $tools | Out-Null

$headers = @{ 'User-Agent' = 'uswap-build'; 'Accept' = 'application/vnd.github+json' }
$token = if ($env:GH_TOKEN) { $env:GH_TOKEN } else { $env:GITHUB_TOKEN }
if ($token) { $headers['Authorization'] = "Bearer $token" }

# Download the first asset of a GitHub release whose name matches the wildcard $pattern.
function Get-ReleaseAsset([string]$repo, [string]$pattern, [string]$tag) {
    $url = if ($tag) { "https://api.github.com/repos/$repo/releases/tags/$tag" } else { "https://api.github.com/repos/$repo/releases/latest" }
    Write-Host "  $repo ($pattern)"
    $release = Invoke-RestMethod -Uri $url -Headers $headers
    $asset = $release.assets | Where-Object { $_.name -like $pattern } | Select-Object -First 1
    if (-not $asset) {
        $names = ($release.assets | ForEach-Object { $_.name }) -join ', '
        throw "No asset matching '$pattern' in $repo. Available: $names"
    }
    $dest = Join-Path $work $asset.name
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $dest -Headers @{ 'User-Agent' = 'uswap-build' }
    return $dest
}

Write-Host 'Downloading tools...'

# FFmpeg (GPL build: needed for libx264 / libvpx / libopus / libvorbis / libmp3lame)
$zip = Get-ReleaseAsset 'BtbN/FFmpeg-Builds' 'ffmpeg-master-latest-win64-gpl.zip' 'latest'
Expand-Archive $zip -DestinationPath (Join-Path $work 'ffmpeg') -Force
Get-ChildItem (Join-Path $work 'ffmpeg') -Recurse -Include ffmpeg.exe, ffprobe.exe | Copy-Item -Destination $tools

# Pandoc
$zip = Get-ReleaseAsset 'jgm/pandoc' 'pandoc-*-windows-x86_64.zip' $null
Expand-Archive $zip -DestinationPath (Join-Path $work 'pandoc') -Force
Get-ChildItem (Join-Path $work 'pandoc') -Recurse -Filter pandoc.exe | Copy-Item -Destination $tools

# Poppler (pdftoppm, pdftotext + the DLLs they need)
$zip = Get-ReleaseAsset 'oschwartz10612/poppler-windows' 'Release-*.zip' $null
Expand-Archive $zip -DestinationPath (Join-Path $work 'poppler') -Force
$popplerBin = Get-ChildItem (Join-Path $work 'poppler') -Recurse -Filter pdftoppm.exe | Select-Object -First 1
Copy-Item (Join-Path $popplerBin.DirectoryName '*') -Destination $tools -Recurse -Force

Write-Host 'Tools ready in build\tools:'
Get-ChildItem $tools -Filter *.exe | ForEach-Object { Write-Host "  $($_.Name)" }
foreach ($need in 'ffmpeg.exe', 'ffprobe.exe', 'pandoc.exe', 'pdftoppm.exe', 'pdftotext.exe') {
    if (-not (Test-Path (Join-Path $tools $need))) { throw "missing $need in build\tools" }
}
