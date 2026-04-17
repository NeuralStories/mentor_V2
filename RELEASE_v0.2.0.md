# Release v0.2.0

## Resumen

`v0.2.0` consolida la nueva arquitectura de ingesta documental de Mentor by EgeAI:

- persistencia local de documentos y estados en SQLite
- deduplicación por `SHA-256`
- endpoint de polling real por documento
- parser PDF unificado con PyMuPDF
- OCR híbrido por página
- modo degradado sin dependencia obligatoria de Supabase
- panel admin con seguimiento de estados
- tests unitarios y E2E para parser, store e ingesta

## Cambios principales

### Backend

- `core/config.py`: Supabase opcional, nuevas variables de ingesta y CORS configurable.
- `api/main.py`: `lifespan`, CORS corregido y arranque local consistente en `127.0.0.1:8765`.
- `core/llm/provider.py`: migración a `langchain-ollama`.
- `core/supabase_client.py`: cliente tolerante a modo degradado.

### Ingesta

- `core/ingestion/models.py`: modelo `IngestionRecord`.
- `core/ingestion/store.py`: fuente de verdad SQLite con consulta por `sha256`.
- `api/routes/knowledge.py`: flujo `upload -> parsing -> ocr -> chunking -> indexing -> ready|failed`.
- `GET /api/knowledge/documents/{file_id}/status` para polling del frontend.

### Parser documental

- `core/tools/document_parser.py`: motor PDF unificado sobre PyMuPDF.
- OCR híbrido por página en PDFs mixtos.
- preprocesado básico de imagen antes de Tesseract.

### Frontend y DX

- `frontend/app.js`: polling real de estados, retry y feedback de ingesta.
- `run-local.ps1`: arranque endurecido con health checks.
- `scripts/doctor.py`: diagnóstico del entorno.
- `scripts/smoke_parser.py`: validación manual del parser.

### Calidad

- `tests/test_store_unit.py`
- `tests/test_parser_unit.py`
- `tests/test_ingestion_e2e.py`
- `pytest.ini`, `requirements-dev.txt` y workflow CI

## Validación ejecutada

- `doctor` sin errores con la `.venv` del proyecto
- tests:
  - `9 passed, 2 deselected`
- smoke real:
  - subida `txt` por API verificada de extremo a extremo hasta `ready`

## Notas

- OCR de documentos escaneados requiere `Tesseract` instalado en el host.
- El tag publicado para esta versión es `v0.2.0`.
