# 🪚 CarpinteroAI V2

Asistente inteligente experto para operarios de carpintería e instalación. Utiliza una arquitectura RAG dinámica con aprendizaje continuo basado en conversaciones reales.

## 🚀 Arquitectura V2
- **Core**: LangChain + Ollama (LLM Local).
- **RAG**: ChromaDB para búsqueda semántica técnica.
- **Memoria**: Supabase para persistencia de diálogos e incidencias.
- **Aprendizaje**: Pipeline automático de extracción de conocimiento técnico.
- **Voz**: Whisper local para entrada de audio en obra.
- **Frontend**: PWA ultra-ligera en Vanilla JS.

## 🛠️ Requisitos previos
1. **Docker** y Docker Compose.
2. **Supabase**: Proyecto creado en [supabase.com](https://supabase.com).
3. **Hardware**: Mínimo 8GB RAM (16GB recomendado para el LLM).

## 📥 Instalación Rápida

1. **Configurar Base de Datos**:
   - Crea un proyecto en Supabase.
   - Ejecuta el contenido de `scripts/setup_supabase.py` en el editor SQL de Supabase.
   - Copia tus credenciales al archivo `.env` (usa `.env.example` como base).

2. **Arrancar Servicios**:
   ```bash
   make build
   make up
   ```

3. **Inyectar Conocimiento Inicial**:
   ```bash
   make seed
   ```

4. **Acceso**:
   - Abre [http://localhost:8000](http://localhost:8000) en tu móvil o PC.

## 🧠 Sistema de Aprendizaje
El sistema analiza cada respuesta. Si detecta una "perla de sabiduría" técnica (ej. una solución a un descuadre), la guarda en Supabase marcada como `pending`. Un encargado puede validar estas entradas desde el panel de administración (/api/knowledge/pending) para que pasen a formar parte del cerebro colectivo (RAG).

## 📋 Endpoints Principales
- `POST /api/chat/`: Chat de texto.
- `POST /api/voice/chat-voice`: Chat de voz completo.
- `GET /api/knowledge/pending`: Listado de aprendizajes pendientes.
- `POST /api/knowledge/validate/{id}`: Aprobar nuevo conocimiento.
