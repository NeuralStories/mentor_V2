#Requires -Version 5.1
param(
  [int]$BackendPort = 8765,
  [int]$FrontendPort = 8766,
  [switch]$NoBrowser,
  [switch]$SkipInstall,
  [switch]$Reset
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Assert-PortFree([int]$Port, [string]$Label) {
  $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  if ($listener) {
    $proc = Get-Process -Id $listener[0].OwningProcess -ErrorAction SilentlyContinue
    throw "Puerto $Port ocupado para $Label por PID $($listener[0].OwningProcess) ($($proc.ProcessName))."
  }
}

function Wait-Http([string]$Url, [int]$TimeoutSec = 45) {
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  while ((Get-Date) -lt $deadline) {
    try {
      $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
      if ($response.StatusCode -eq 200) { return $true }
    } catch {}
    Start-Sleep -Milliseconds 500
  }
  return $false
}

function Ensure-Ollama {
  $process = Get-Process ollama -ErrorAction SilentlyContinue
  if ($process) { return }

  $ollama = Get-Command ollama -ErrorAction SilentlyContinue
  if (-not $ollama) {
    Write-Warning "Ollama no está instalado. El backend arrancará pero el chat puede fallar."
    return
  }

  Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden | Out-Null
  Start-Sleep -Seconds 2
}

if ($Reset) {
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .\uploads, .\data
}

Assert-PortFree $BackendPort "backend"
Assert-PortFree $FrontendPort "frontend"

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

if (-not $SkipInstall) {
  python -m pip install --upgrade pip --quiet
  pip install -r requirements.txt --quiet
}

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
  Copy-Item .env.example .env
}

New-Item -ItemType Directory -Force -Path .\uploads, .\data, .\knowledge_base | Out-Null
Ensure-Ollama

$backend = Start-Process powershell -PassThru -WindowStyle Minimized -ArgumentList @(
  "-NoExit",
  "-Command",
  ". .\.venv\Scripts\Activate.ps1; uvicorn api.main:app --host 127.0.0.1 --port $BackendPort --reload"
)

if (-not (Wait-Http "http://127.0.0.1:$BackendPort/health" 45)) {
  Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
  throw "Backend no respondió a /health"
}

$frontend = Start-Process powershell -PassThru -WindowStyle Minimized -ArgumentList @(
  "-NoExit",
  "-Command",
  "python -m http.server $FrontendPort --directory frontend --bind 127.0.0.1"
)

Write-Host "Backend:  http://127.0.0.1:$BackendPort"
Write-Host "Frontend: http://127.0.0.1:$FrontendPort"
Write-Host "Docs:     http://127.0.0.1:$BackendPort/docs"

if (-not $NoBrowser) {
  Start-Process "http://127.0.0.1:$FrontendPort"
}

try {
  Wait-Process -Id $backend.Id
} finally {
  Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
}
