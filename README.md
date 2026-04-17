# Mentor by EgeAI

Asistente técnico para operarios de carpintería e instalación, con backend FastAPI, memoria en Supabase, RAG en ChromaDB y modelos locales vía Ollama.

## Estado actual

La base arrancable es esta carpeta: `mentor_ai/`.

Incluye:
- API FastAPI en `api/`
- núcleo del agente en `core/`
- PWA estática en `frontend/`
- scripts de preparación en `scripts/`

No incluye todavía:
- integración real de voz con Whisper
- panel de administración dedicado
- automatización completa del SQL de Supabase

## Requisitos

- Python 3.11 recomendado
- Ollama instalado y accesible
- proyecto de Supabase ya creado
- conexión local a internet solo para acceder a Supabase

## Variables de entorno

Copia `.env.example` a `.env` y completa:

```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_anon_key
SUPABASE_SERVICE_KEY=tu_service_role_key
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.1:8b
EMBEDDING_MODEL=nomic-embed-text
APP_DEBUG=true
AUTO_LEARN=true
REQUIRE_VALIDATION=true
```

## Preparación de Supabase

El script `scripts/setup_supabase.py` no crea tablas automáticamente. Imprime el SQL que debes ejecutar en el panel de Supabase.

Pasos:
1. Abre tu proyecto en Supabase.
2. Entra en `SQL Editor`.
3. Ejecuta el SQL que imprime `python scripts/setup_supabase.py`.
4. Vuelve al terminal y deja que el script verifique las tablas.

## Preparación de Ollama

Arranca Ollama:

```powershell
ollama serve
```

Descarga los modelos requeridos si todavía no están:

```powershell
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

## Instalación local

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Cargar conocimiento base

La carpeta `knowledge_base/` ya incluye documentación mínima para pruebas. Una vez Supabase y Ollama estén listos, ejecuta:

```powershell
python scripts/seed_knowledge.py
```

## Arranque del backend

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8765 --reload
```

Health checks útiles:
- `http://localhost:8765/health`
- `http://localhost:8765/api/chat/health`
- `http://localhost:8765/api/admin/system-health`

## Arranque del frontend

Desde `frontend/` sirve los archivos estáticos en otro terminal:

```powershell
cd frontend
python -m http.server 8766
```

Luego abre:

`http://localhost:8766`

El frontend llama al backend en `http://localhost:8765/api`.

## Arranque rápido en Windows

También puedes lanzar ambos con:

```powershell
powershell -ExecutionPolicy Bypass -File .\run-local.ps1
```

## Flujo mínimo de validación

1. Verifica `/health`.
2. Verifica `/api/admin/system-health`.
3. Ejecuta `python scripts/seed_knowledge.py`.
4. Prueba una búsqueda POST a `/api/knowledge/search`.
5. Prueba un chat POST a `/api/chat/message`.

## Comandos útiles

```powershell
python -m pytest
python -m uvicorn api.main:app --reload
python scripts/setup_supabase.py
python scripts/seed_knowledge.py
```

Si usas `make`:

```powershell
make install
make run
make test
make clean
```

## 🔥 Nueva Funcionalidad: Zona de Ingesta de Conocimiento

**Panel completo para gestión de documentos:**

### **Subida y Procesamiento**
- 📤 **Subida de archivos** por drag & drop
- 📄 **Formatos soportados**: PDF, DOCX, TXT, MD
- ⚡ **Procesamiento automático** con parsing inteligente
- 🧠 **Indexación RAG** en tiempo real
- 📊 **Feedback visual** del progreso

### **Interfaz de Administración**
- 🎛️ **Panel de admin** integrado en el frontend
- 📋 **Vista de documentos** con estados
- 🔄 **Procesamiento individual** de archivos
- 🗑️ **Gestión completa** de documentos
- 📈 **Reindexación** del sistema

### **API para Desarrolladores**
```bash
# Subir archivo
curl -X POST http://localhost:8765/api/knowledge/upload \
  -F "file=@documento.pdf" \
  -F "collection=procedimientos"

# Listar documentos
curl http://localhost:8765/api/knowledge/documents

# Procesar documento
curl -X POST http://localhost:8765/api/knowledge/process/{file_id}
```

### **Acceso al Panel**
1. Abre el frontend: `http://localhost:8766`
2. Haz clic en el **botón de engranaje** (⚙️)
3. Accede a la **Zona de Ingesta**

### **Cómo subir archivos**
1. Abre `http://localhost:8766`
2. Pulsa el botón de engranaje
3. Arrastra archivos o usa `Seleccionar Archivos`
4. Elige la colección destino
5. Deja activado `Procesar automáticamente` si quieres indexación inmediata

Formatos soportados:
- PDF
- DOCX
- TXT
- MD

### **OCR para PDFs escaneados**
El OCR es opcional y solo se usa si un PDF no trae texto extraíble.

En `.env`:
```env
OCR_ENABLED=true
OCR_LANGUAGE=spa
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

Además necesitas:
- instalar `Tesseract OCR` en Windows
- tener las dependencias Python de OCR del `requirements.txt`

Comportamiento:
- PDF con texto normal: se indexa sin OCR
- PDF escaneado: intenta OCR si `OCR_ENABLED=true`
- si OCR no está disponible, el documento se sube pero no extraerá texto útil

## Limitaciones conocidas

- `api/routes/voice.py` es placeholder.
- El primer mensaje de chat puede tardar bastante si Ollama está frío.
- Sin Supabase configurado, la API arranca, pero el flujo completo de memoria y aprendizaje queda degradado.
- La documentación de `Mentor/` no es la fuente de verdad para arrancar esta versión.
