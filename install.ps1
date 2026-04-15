<#
.SYNOPSIS
Instalador interactivo para MENTOR Enterprise AI Agent.

.DESCRIPTION
Este script guía al usuario paso a paso para configurar el entorno virtual,
instalar las dependencias y generar el archivo .env necesario para ejecutar MENTOR.
#>

$ErrorActionPreference = "Stop"

function Write-ColorMessage {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        [ConsoleColor]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Prompt-User {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Question,
        [string]$DefaultValue = ""
    )
    if ($DefaultValue) {
        $promptMsg = "${Question} [$DefaultValue]: "
    } else {
        $promptMsg = "${Question}: "
    }
    
    $response = Read-Host -Prompt $promptMsg
    if ([string]::IsNullOrWhiteSpace($response) -and $DefaultValue) {
        return $DefaultValue
    }
    return $response
}

function Prompt-Confirm {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Question,
        [bool]$Default = $false
    )
    $defStr = if ($Default) { "S/n" } else { "s/N" }
    $promptMsg = "$Question ($defStr): "
    
    $response = Read-Host -Prompt $promptMsg
    if ([string]::IsNullOrWhiteSpace($response)) {
        return $Default
    }
    if ($response -match "^(?i)s(i|í)?$") { return $true }
    if ($response -match "^(?i)n(o)?$") { return $false }
    return $Default
}

Clear-Host
Write-ColorMessage "=====================================================" -Color Cyan
Write-ColorMessage "   Bienvenido al Instalador de MENTOR Enterprise AI" -Color Cyan
Write-ColorMessage "=====================================================" -Color Cyan
Write-Host ""

# 1. Comprobacion de Python
Write-ColorMessage "[1/5] Verificando requisitos del sistema..." -Color Yellow
try {
    $pythonVersion = python --version
    Write-ColorMessage "Python detectado: $pythonVersion" -Color Green
} catch {
    Write-ColorMessage "ERROR: Python no esta instalado o no esta en el PATH." -Color Red
    Write-Host "Por favor, instala Python 3.10 o superior y vuelve a intentar."
    exit 1
}

# 2. Entorno Virtual
Write-ColorMessage "`n[2/5] Configurando Entorno Virtual..." -Color Yellow
$venvPath = ".\venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creando entorno virtual en $venvPath..."
    python -m venv venv
} else {
    Write-Host "Entorno virtual detectado."
}

# 3. Instalacion de dependencias
Write-ColorMessage "`n[3/5] Instalando dependencias de MENTOR..." -Color Yellow
if (Test-Path ".\venv\Scripts\activate.ps1") {
    # Activar venv temporalmente para la instalacion
    $env:VIRTUAL_ENV = "$PWD\venv"
    $env:PATH = "$PWD\venv\Scripts;$env:PATH"
    
    Write-Host "Actualizando pip e instalando dependencias (esto puede tardar unos minutos)..."
    python -m pip install --upgrade pip
    pip install -e ".[test,rag,redis,postgres]"
} else {
    Write-ColorMessage "Ocurrio un problema al verificar el entorno virtual." -Color Red
    exit 1
}

# 4. Configuracion .env
Write-ColorMessage "`n[4/5] Configuracion de Variables de Entorno..." -Color Yellow
$envContent = @"
# ===== MENTOR - Configuración Generada por Instalador =====

APP_NAME=Mentor
APP_VERSION=1.0.0
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000
JWT_SECRET=change-this-secret-in-production

"@

Write-Host "--- Configuracion de Inteligencia Artificial (Cerebro) ---" -ForegroundColor Cyan
$llmProvider = Prompt-User "Que proveedor LLM deseas usar? (openai / anthropic / ollama)" "openai"
$envContent += "LLM_PROVIDER=$llmProvider`n"

if ($llmProvider -eq "openai") {
    $apiKey = Prompt-User "Ingresa tu OPENAI_API_KEY"
    $envContent += "OPENAI_API_KEY=$apiKey`n"
    $envContent += "MODEL_NAME=gpt-4o-mini`n"
} elseif ($llmProvider -eq "anthropic") {
    $apiKey = Prompt-User "Ingresa tu ANTHROPIC_API_KEY"
    $envContent += "ANTHROPIC_API_KEY=$apiKey`n"
    $envContent += "MODEL_NAME=claude-3-haiku-20240307`n"
} elseif ($llmProvider -eq "ollama") {
    $baseUrl = Prompt-User "URL base de Ollama" "http://localhost:11434"
    $modelName = Prompt-User "Nombre del modelo local (ej. llama3)" "llama3"
    $envContent += "OLLAMA_BASE_URL=$baseUrl`n"
    $envContent += "MODEL_NAME=$modelName`n"
}

$envContent += "EMBEDDING_MODEL=text-embedding-3-small`n"
$envContent += "MAX_TOKENS=4096`n"
$envContent += "TEMPERATURE=0.7`n`n"

Write-Host "`n--- Configuracion de Base de Datos ---" -ForegroundColor Cyan
$useSupabase = Prompt-Confirm "Deseas usar Supabase para almacenamiento en la nube?" $false

if ($useSupabase) {
    $supabaseUrl = Prompt-User "Ingresa tu SUPABASE_URL"
    $supabaseKey = Prompt-User "Ingresa tu SUPABASE_KEY (anon_key)"
    $dbUrl = Prompt-User "Ingresa tu DATABASE_URL (Connection String de Supabase PostgreSQL)"
    
    $envContent += "USE_SUPABASE=true`n"
    $envContent += "SUPABASE_URL=$supabaseUrl`n"
    $envContent += "SUPABASE_KEY=$supabaseKey`n"
    $envContent += "DATABASE_URL=$dbUrl`n`n"
} else {
    Write-Host "Usando SQLite local por defecto."
    $envContent += "USE_SUPABASE=false`n"
    $envContent += "DATABASE_URL=sqlite+aiosqlite:///./mentor.db`n`n"
}

Write-Host "`n--- Notificaciones y Escalamiento ---" -ForegroundColor Cyan
if (Prompt-Confirm "Deseas configurar Webhooks para Slack/Teams ahora?") {
    $slackUrl = Prompt-User "SLACK_WEBHOOK_URL (Dejar vacio si no aplica)"
    if ($slackUrl) { $envContent += "SLACK_WEBHOOK_URL=$slackUrl`n" }
    
    $teamsUrl = Prompt-User "TEAMS_WEBHOOK_URL (Dejar vacio si no aplica)"
    if ($teamsUrl) { $envContent += "TEAMS_WEBHOOK_URL=$teamsUrl`n" }
    
    $escUrl = Prompt-User "ESCALATION_WEBHOOK_URL (Dejar vacio si no aplica)"
    if ($escUrl) { $envContent += "ESCALATION_WEBHOOK_URL=$escUrl`n" }
}

$envContent += "`n# -- Cache y Vector Store --`n"
$envContent += "REDIS_URL=redis://localhost:6379/0`n"
$envContent += "VECTOR_DB_PATH=./data/vectorstore`n"

# Guardar .env
Set-Content -Path ".\.env" -Value $envContent -Encoding UTF8
Write-ColorMessage "Archivo .env generado exitosamente en la raiz del proyecto." -Color Green

# 5. Carga de datos iniciales
Write-ColorMessage "`n[5/5] Inicializando Datos del Sistema..." -Color Yellow
$loadData = Prompt-Confirm "Deseas cargar la Base de Conocimiento y Trabajadores de prueba ahora?" $true
if ($loadData) {
    Write-Host "Cargando base de conocimiento..."
    python -c "from src.core.engine import MentorEngine; e=MentorEngine(); e.kb.load_from_json('data/knowledge_base.json')"
    Write-Host "Los trabajadores podran cargarse al iniciar la API usando: curl -X POST http://localhost:8000/api/v1/workers/load"
}

Write-Host ""
Write-ColorMessage "=====================================================" -Color Cyan
Write-ColorMessage "  ¡Instalacion Completada con Exito!" -Color Green
Write-ColorMessage "=====================================================" -Color Cyan
Write-Host ""
Write-Host "Siguientes Pasos:"
Write-Host "1. Activa el entorno virtual si no lo esta:"
Write-ColorMessage "   .\venv\Scripts\activate" -Color Yellow
Write-Host "2. Inicia el servidor de MENTOR:"
Write-ColorMessage "   make run  O  uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload" -Color Yellow
Write-Host "3. Visita la documentacion API en:"
Write-ColorMessage "   http://localhost:8000/docs" -Color Blue
Write-Host ""
