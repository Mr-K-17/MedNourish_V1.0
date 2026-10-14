# ==============================================================================
# MedNourish — One-Command Startup Script (start_all.ps1)
# ==============================================================================
# Starts all MedNourish services in the background with PID tracking and logging:
# 1. Firebase Auth Emulator (port 9099)
# 2. ML Lab Microservice (port 8001)
# 3. Backend FastAPI (port 8000)
# 4. Frontend Vite Dev Server (port 5173)
# ==============================================================================

$ErrorActionPreference = "Continue"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path "$scriptDir\.."
$logDir = Join-Path $scriptDir "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$pidFile = Join-Path $scriptDir ".pids.json"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting MedNourish Application Stack (Academic Demo)  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Repository Root: $repoRoot" -ForegroundColor Gray
Write-Host "Logs Directory:  $logDir" -ForegroundColor Gray

# Clean any existing processes on target ports first
Write-Host "`n[1/5] Checking target ports (9099, 8001, 8000, 5173)..." -ForegroundColor Yellow
$targetPorts = @(9099, 8001, 8000, 5173)
foreach ($port in $targetPorts) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($conns) {
            $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
            foreach ($p in $pids) {
                if ($p -gt 0) {
                    Write-Host "  Freeing port $port (PID $p)..." -ForegroundColor DarkYellow
                    Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
                }
            }
        }
    } catch {}
}

$pidsDict = @{}

# [2/5] Firebase Auth Emulator
Write-Host "[2/5] Starting Firebase Auth Emulator (Port 9099)..." -ForegroundColor Yellow
$infraDir = Join-Path $repoRoot "infra"
$firebaseCmd = Join-Path $infraDir "node_modules\.bin\firebase.cmd"
if (Test-Path $firebaseCmd) {
    $authProc = Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/c", "`"$firebaseCmd`"", "emulators:start", "--only", "auth", "--project", "demo-mednourish" `
        -WorkingDirectory $infraDir `
        -RedirectStandardOutput (Join-Path $logDir "auth_emulator.log") `
        -RedirectStandardError (Join-Path $logDir "auth_emulator.err.log") `
        -WindowStyle Hidden `
        -PassThru
    $pidsDict["auth_emulator"] = $authProc.Id
    Write-Host "  Auth Emulator PID: $($authProc.Id)" -ForegroundColor Green
} else {
    Write-Host "  Firebase CLI not found in infra/node_modules; skipping emulator start." -ForegroundColor DarkGray
}

# [3/5] ML Lab Microservice
Write-Host "[3/5] Starting ML Lab Microservice (Port 8001)..." -ForegroundColor Yellow
$mlPython = Join-Path $repoRoot "tf\.venv\Scripts\python.exe"
$mlServiceDir = Join-Path $repoRoot "ml\service"
if (Test-Path $mlPython) {
    $mlProc = Start-Process -FilePath $mlPython `
        -ArgumentList "-m", "uvicorn", "app:app", "--port", "8001", "--host", "127.0.0.1" `
        -WorkingDirectory $mlServiceDir `
        -RedirectStandardOutput (Join-Path $logDir "ml_service.log") `
        -RedirectStandardError (Join-Path $logDir "ml_service.err.log") `
        -WindowStyle Hidden `
        -PassThru
    $pidsDict["ml_service"] = $mlProc.Id
    Write-Host "  ML Microservice PID: $($mlProc.Id)" -ForegroundColor Green
} else {
    Write-Host "  tf/.venv not found; ML microservice will run in fallback mode." -ForegroundColor DarkYellow
}

# [4/5] Backend FastAPI
Write-Host "[4/5] Starting Backend FastAPI (Port 8000)..." -ForegroundColor Yellow
$backendPython = Join-Path $repoRoot "backend\.venv\Scripts\python.exe"
$backendDir = Join-Path $repoRoot "backend"
$backendProc = Start-Process -FilePath $backendPython `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--port", "8000", "--host", "127.0.0.1" `
    -WorkingDirectory $backendDir `
    -RedirectStandardOutput (Join-Path $logDir "backend.log") `
    -RedirectStandardError (Join-Path $logDir "backend.err.log") `
    -WindowStyle Hidden `
    -PassThru
$pidsDict["backend"] = $backendProc.Id
Write-Host "  Backend FastAPI PID: $($backendProc.Id)" -ForegroundColor Green

# [5/5] Frontend Vite Dev Server
Write-Host "[5/5] Starting Frontend Dev Server (Port 5173)..." -ForegroundColor Yellow
$frontendDir = Join-Path $repoRoot "frontend"
$frontendProc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c", "npm", "run", "dev" `
    -WorkingDirectory $frontendDir `
    -RedirectStandardOutput (Join-Path $logDir "frontend.log") `
    -RedirectStandardError (Join-Path $logDir "frontend.err.log") `
    -WindowStyle Hidden `
    -PassThru
$pidsDict["frontend"] = $frontendProc.Id
Write-Host "  Frontend PID: $($frontendProc.Id)" -ForegroundColor Green

# Save tracked PIDs
$pidsDict | ConvertTo-Json | Set-Content -Path $pidFile -Encoding UTF8

Write-Host "`nWaiting for services to become responsive (5 seconds)..." -ForegroundColor Gray
Start-Sleep -Seconds 5

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  MedNourish Stack Successfully Started!                 " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Frontend UI:          http://localhost:5173" -ForegroundColor Cyan
Write-Host "  Backend API:          http://localhost:8000" -ForegroundColor Cyan
Write-Host "  OpenAPI Docs:         http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Health Check:         http://localhost:8000/v1/health" -ForegroundColor Cyan
Write-Host "  ML Microservice:      http://localhost:8001" -ForegroundColor Cyan
Write-Host "  Firebase Auth Emul:   http://127.0.0.1:9099" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "To stop all services cleanly, run: .\scripts\stop_all.ps1`n" -ForegroundColor Yellow
