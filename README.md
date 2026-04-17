# Mentor by EgeAI

Asistente técnico con FastAPI, RAG local sobre ChromaDB, modelos vía Ollama e ingesta documental persistente.

## Quickstart

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
.\run-local.ps1
```

Frontend: `http://127.0.0.1:8766`
Backend: `http://127.0.0.1:8765`

## Modo degradado

Si no defines `SUPABASE_URL` y `SUPABASE_KEY`, la app arranca igualmente y guarda la metadata de ingesta en `data/ingestion.sqlite`.

## Ingesta

Estados: `uploaded -> parsing -> ocr -> chunking -> indexing -> ready|failed`

Endpoint de polling:

```text
GET /api/knowledge/documents/{file_id}/status
```

## OCR

Actívalo solo si tienes Tesseract instalado:

```env
OCR_ENABLED=true
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

## Tests

```powershell
pip install -r requirements-dev.txt
pytest tests/test_parser_unit.py tests/test_store_unit.py -v
pytest tests/test_ingestion_e2e.py -v -m "not requires_tesseract"
```

## Utilidades

```powershell
python -m scripts.doctor --fix
python -m scripts.smoke_parser ruta\\archivo.pdf
```
