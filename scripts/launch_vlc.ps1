<#
.SYNOPSIS
    Launches VLC Media Player to view the CCTV RTSP stream.

.DESCRIPTION
    Reads the RTSP stream URL and credentials from .env, sanitizes the URL for display,
    and launches VLC Media Player with low-latency TCP streaming.

.EXAMPLE
    .\scripts\launch_vlc.ps1
#>

$VlcPath = "C:\Program Files\VideoLAN\VLC\vlc.exe"
$DefaultHost = "192.168.1.4:554/stream1"
$StreamUrl = "rtsp://$DefaultHost"
$Username = ""
$Password = ""

# Check if VLC is installed
if (-not (Test-Path $VlcPath)) {
    $VlcPath = "C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
    if (-not (Test-Path $VlcPath)) {
        Write-Error "VLC Media Player was not found at standard install locations."
        exit 1
    }
}

# Load .env if present
$EnvFile = Join-Path $PSScriptRoot "..\.env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $parts = $line.Split("=", 2)
            $key = $parts[0].Trim()
            $val = $parts[1].Trim()
            if ($key -eq "CCTV_RTSP_URL" -and $val) {
                $StreamUrl = $val
            }
            if ($key -eq "CCTV_USERNAME" -and $val) {
                $Username = $val
            }
            if ($key -eq "CCTV_PASSWORD" -and $val) {
                $Password = $val
            }
        }
    }
}

# Construct authenticated URL if credentials present and not already embedded
$AuthenticatedUrl = $StreamUrl
if ($Username -and $Password -and -not ($StreamUrl -match "://.*:.*@")) {
    $AuthenticatedUrl = $StreamUrl -replace "^rtsp://", "rtsp://$($Username):$($Password)@"
}

# Mask credentials for terminal output
$MaskedUrl = $AuthenticatedUrl -replace "(rtsp://)([^:]+):([^@]+)@", '$1***:***@'

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Launching VLC Media Player" -ForegroundColor Green
Write-Host "Target Stream: $MaskedUrl" -ForegroundColor Yellow
Write-Host "VLC Binary:    $VlcPath" -ForegroundColor Gray
Write-Host "Transport:     RTSP over TCP (--rtsp-tcp)" -ForegroundColor Gray
Write-Host "Caching:       1000ms" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan

Start-Process -FilePath $VlcPath -ArgumentList "`"$AuthenticatedUrl`"", "--network-caching=1000", "--rtsp-tcp"
