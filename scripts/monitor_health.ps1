# monitor_health.ps1 - Script to check if YTGUI is running and healthy
$port = if ($env:LUNAWAVE_PORT) { $env:LUNAWAVE_PORT } else { "8765" }
$url = "http://localhost:$port/health"

try {
    $response = Invoke-RestMethod -Uri $url -Method Get -ErrorAction Stop
    if ($response.status -ne "ok") {
        Write-Host "[!] YTGUI DEGRADED: $($response | ConvertTo-Json -Compress)"
    } else {
        Write-Host "[+] YTGUI is healthy."
    }
} catch {
    Write-Host "[!] YTGUI DOWN: Server is not reachable."
}
