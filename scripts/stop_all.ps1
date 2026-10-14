# ==============================================================================
# MedNourish — Clean Shutdown Script (stop_all.ps1)
# ==============================================================================
# Cleanly terminates all tracked MedNourish processes and frees ports:
# 9099 (Firebase Auth), 8001 (ML Microservice), 8000 (Backend), 5173 (Frontend).
# ==============================================================================

$ErrorActionPreference = "Continue"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $scriptDir ".pids.json"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Stopping MedNourish Application Stack                  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Stop tracked PIDs from file
if (Test-Path $pidFile) {
    try {
        $pidsJson = Get-Content -Path $pidFile -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($prop in $pidsJson.PSObject.Properties) {
            $name = $prop.Name
            $p = $prop.Value
            if ($p -and ($p -gt 0)) {
                Write-Host "Stopping $name (PID $p)..." -ForegroundColor Yellow
                Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
            }
        }
    } catch {
        Write-Host "Warning reading PID file: $_" -ForegroundColor DarkGray
    }
    Remove-Item -Path $pidFile -Force -ErrorAction SilentlyContinue
}

# 2. Check and clean any lingering processes on ports
$targetPorts = @(9099, 8001, 8000, 5173)
foreach ($port in $targetPorts) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($conns) {
            $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
            foreach ($p in $pids) {
                if ($p -gt 0) {
                    Write-Host "Cleaning lingering process on port $port (PID $p)..." -ForegroundColor Yellow
                    Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
                }
            }
        }
    } catch {}
}

Write-Host "`nAll MedNourish services stopped cleanly." -ForegroundColor Green
Write-Host "==========================================================`n" -ForegroundColor Cyan
