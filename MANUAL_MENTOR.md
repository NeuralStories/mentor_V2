# 📘 Manual de Usuario e Instalación: MENTOR Enterprise AI Agent

Este documento proporciona una guía detallada sobre cómo configurar, instalar y operar el agente MENTOR.

---

## 1. Introducción
**MENTOR** es una solución de Inteligencia Artificial para el sector operativo y empresarial. Su propósito es actuar como un puente de conocimiento entre los manuales corporativos y los trabajadores en el campo, garantizando respuestas rápidas, seguras y precisas.

### Capacidades Core:
- **RAG (Retrieval-Augmented Generation)**: Consulta tus propios documentos.
- **Detección de Riesgos**: Clasifica urgencias y escala a humanos automáticamente.
- **Multicanal**: Notificaciones integradas en Slack, Teams y Webhooks.
- **Privacidad**: Redacción automática de datos sensibles (PII).

---

## 2. Guía de Creación de Cuentas

Para que el sistema sea funcional, necesitarás configurar los siguientes servicios:

### A. Proveedor de Inteligencia (Cerebro)
1.  **OpenAI**:
    - Ve a [platform.openai.com](https://platform.openai.com/).
    - Regístrate y crea una **API Key** en la sección "API Keys".
    - Recomendación: Usa el modelo `gpt-4o-mini` por su excelente balance entre velocidad y costo.
2.  **Anthropic** (Opcional):
    - Ve a [console.anthropic.com](https://console.anthropic.com/).
    - Genera una clave si prefieres usar modelos Claude.
3.  **Ollama** (Alternativa Local):
    - Descarga e instala [Ollama](https://ollama.com/).
    - No requiere cuenta ni internet para funcionar una vez descargado el modelo.

### B. Base de Datos (Supabase)
Supabase gestionará tu lista de trabajadores y los tickets de escalamiento.
1.  Crea una cuenta en [supabase.com](https://supabase.com/).
2.  Crea un nuevo Proyecto.
3.  Ve a **Project Settings -> Database**.
4.  Copia la **Connection String** de tipo "URI".
    - *Importante*: Asegúrate de que el formato sea `postgresql+asyncpg://...` para que sea compatible con el modo asíncrono de MENTOR.

### C. Comunicaciones (Slack/Teams)
1.  **Slack**:
    - Crea una App en tu espacio de trabajo.
    - Activa **Incoming Webhooks**.
    - Copia la URL del Webhook para el canal donde quieres recibir alertas.
2.  **Microsoft Teams**:
    - En el canal deseado, selecciona "Conectores".
    - Busca "Incoming Webhook" y configúralo.
    - Guarda la URL generada.

---

## 3. Instalación e Implementación

### Requisitos Previos:
- Python 3.10 o superior instalado.
- Git (opcional).

### Paso 1: Configuración del Entorno Virtual
```bash
# Navega a la carpeta del proyecto
cd Mentor

# Crea el entorno
python -m venv venv

# Actívalo
# En Windows:
.\venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

### Paso 2: Instalación de Dependencias
```bash
pip install -e ".[test,rag,redis,postgres]"
```

### Paso 3: Configuración de Variables (.env)
Copia el archivo `.env.example` y renómbralo a `.env`. Rellena tus claves:
```env
OPENAI_API_KEY=tu_clave_aqui
DATABASE_URL=tu_url_de_supabase_aqui
SLACK_WEBHOOK_URL=tu_webhook_aqui
```

### Paso 4: Inicialización de Datos
Ejecuta los siguientes comandos para poblar el sistema:
```bash
# Cargar base de conocimiento inicial
python -c "from src.core.engine import MentorEngine; e=MentorEngine(); e.kb.load_from_json('data/knowledge_base.json')"

# Cargar trabajadores de ejemplo
curl -X POST http://localhost:8000/api/v1/workers/load
```

---

## 4. Operación del Sistema

### Iniciar servidor:
```bash
make run
```
El servidor estará disponible en `http://localhost:8000`.

### Manual de Uso de API:
- **Consultas**: Envía un `POST` a `/api/v1/query` con el `worker_id` y tu pregunta.
- **Feedback**: Después de cada respuesta, puedes enviar `/api/v1/feedback` para mejorar el modelo.
- **Admin**: Usa `/api/v1/analytics` para ver el rendimiento del sistema en tiempo real.

---

## 5. Arquitectura del Motor (Engine)
Para soporte técnico, MENTOR opera bajo una arquitectura de flujo secuencial:
1. `Classifier` -> 2. `PII Cleaner` -> 3. `Cache` -> 4. `KB Search` -> 5. `Strategy Selector` -> 6. `LLM Generator` -> 7. `Escalator` -> 8. `Monitor`.

---

© 2026 MENTOR AI - Advanced Agentic Coding Team.
