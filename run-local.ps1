$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = "C:\Users\Usuari\AppData\Local\Programs\Python\Python313\python.exe"

if (-not (Test-Path $python)) {
    throw "Python no encontrado en $python"
}

$backendCommand = @"
Set-Location '$root'
& '$python' -m uvicorn api.main:app --host 127.0.0.1 --port 8765 --reload
"@

$frontendCommand = @"
Set-Location '$root\frontend'
& '$python' -m http.server 8766
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand | Out-Null
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand | Out-Null

Write-Host "Backend:  http://127.0.0.1:8765"
Write-Host "Frontend: http://127.0.0.1:8766"
Write-Host "Docs:     http://127.0.0.1:8765/docs"
