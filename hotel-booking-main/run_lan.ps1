<#
.SYNOPSIS
    Start the EasyBooking Django development server so the site is reachable both
    on this computer and from a phone/tablet on the same Wi-Fi network.

.DESCRIPTION
    Binds Django to 0.0.0.0 instead of 127.0.0.1, prints the LAN URL to open on
    the phone, applies pending migrations, and can optionally install the
    Windows Firewall inbound rule (requires approving a UAC prompt).

.EXAMPLE
    .\run_lan.ps1

.EXAMPLE
    .\run_lan.ps1 -Port 8080 -OpenFirewall
#>
param(
    [int]$Port = 8000,
    [switch]$OpenFirewall
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

# Pick a virtualenv that already has Django installed, falling back to PATH.
$candidates = @(
    (Join-Path $projectRoot 'venv314\Scripts\python.exe'),
    (Join-Path $projectRoot 'env\Scripts\python.exe'),
    (Join-Path $projectRoot '.venv\Scripts\python.exe')
)
$python = $null
foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
        & $candidate -c 'import django' 2>$null
        if ($LASTEXITCODE -eq 0) {
            $python = $candidate
            break
        }
    }
}
if (-not $python) {
    $python = (Get-Command python -ErrorAction Stop).Source
}

# Follow the default route so virtual/VPN adapters are ignored when detecting
# the address other devices on the Wi-Fi should use.
$route = Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue |
    Sort-Object RouteMetric | Select-Object -First 1
$lanIp = if ($route) {
    Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex $route.ifIndex -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty IPAddress
} else { $null }

if ($OpenFirewall) {
    $ruleName = "EasyBooking Django $Port"
    $netshArgs = "advfirewall firewall add rule name=`"$ruleName`" dir=in action=allow protocol=TCP localport=$Port profile=private,public"
    try {
        Start-Process -FilePath 'netsh.exe' -Verb RunAs -ArgumentList $netshArgs -ErrorAction Stop
        Write-Host 'Requested a Windows Firewall inbound rule - approve the UAC prompt.' -ForegroundColor Yellow
    } catch {
        Write-Host 'Firewall rule was not added (UAC was canceled); the site still starts locally.' -ForegroundColor Yellow
    }
}

Write-Host ''
Write-Host 'EasyBooking is starting...' -ForegroundColor Cyan
Write-Host "  This computer : http://127.0.0.1:$Port/"
if ($lanIp) {
    Write-Host "  Phone / LAN   : http://${lanIp}:$Port/" -ForegroundColor Green
} else {
    Write-Host '  Phone / LAN   : check `ipconfig` for the Wi-Fi IPv4 address.'
}
Write-Host '  Both devices must be connected to the same Wi-Fi network.' -ForegroundColor DarkGray
Write-Host ''

& $python manage.py migrate --noinput
& $python manage.py runserver "0.0.0.0:$Port"
