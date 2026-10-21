<#
.SYNOPSIS
    USwap - Windows Explorer context-menu installer (per-user, no admin needed).

.DESCRIPTION
    Adds "Convert with USwap" to the right-click menu of every file by writing
    HKCU\Software\Classes\*\shell\USwap. On Windows 11 the entry lives under
    "Show more options" (Shift+F10).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\install.ps1
    powershell -ExecutionPolicy Bypass -File scripts\install.ps1 -Uninstall
#>
[CmdletBinding()]
param(
    [switch]$Uninstall,
    [string]$UswapPath
)

$ErrorActionPreference = 'Stop'

# Use the .NET registry API: PowerShell treats '*' in registry paths as a wildcard.
$subKey  = 'Software\Classes\*\shell\USwap'
$hkcu    = [Microsoft.Win32.Registry]::CurrentUser
$iconDir = Join-Path $env:LOCALAPPDATA 'uswap'
$iconDst = Join-Path $iconDir 'uswap.ico'

if ($Uninstall) {
    $hkcu.DeleteSubKeyTree($subKey, $false)
    if (Test-Path $iconDir) { Remove-Item $iconDir -Recurse -Force }
    Write-Host 'USwap context-menu entry removed. (The program itself is untouched: pipx uninstall uswap)'
    return
}

# Locate uswap.exe
if (-not $UswapPath) {
    $cmd = Get-Command uswap -ErrorAction SilentlyContinue
    if ($cmd) { $UswapPath = $cmd.Source }
}
if (-not $UswapPath -or -not (Test-Path $UswapPath)) {
    Write-Error "'uswap' was not found on PATH. Install it first (pipx install .  or  pip install --user .) or pass -UswapPath."
    return
}

# Optional icon
$iconValue = $null
$iconSrc = Join-Path $PSScriptRoot '..\assets\uswap.ico'
if (Test-Path $iconSrc) {
    New-Item -ItemType Directory -Force -Path $iconDir | Out-Null
    Copy-Item $iconSrc $iconDst -Force
    $iconValue = $iconDst
}

$key = $hkcu.CreateSubKey($subKey)
$key.SetValue('', 'Convert with USwap')
if ($iconValue) { $key.SetValue('Icon', $iconValue) }
$key.Close()

$cmdKey = $hkcu.CreateSubKey("$subKey\command")
# uswap.exe is a console program, so Explorer opens a terminal window for it.
$cmdKey.SetValue('', "`"$UswapPath`" `"%1`"")
$cmdKey.Close()

Write-Host "Installed. Right-click any file > 'Convert with USwap'  (Windows 11: Show more options)."
Write-Host "Command: `"$UswapPath`" `"%1`""
