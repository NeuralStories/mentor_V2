# Zona de Ingesta de Conocimiento - Mentor by EgeAI

Sistema completo de gestión de documentos para alimentar la base de conocimientos de Mentor by EgeAI.

## 🚀 Características

### ✅ **Subida de Documentos**
- **Formatos soportados**: PDF, DOCX, TXT, MD
- **Arrastrar y soltar** archivos
- **Selección múltiple** de archivos
- **Validación automática** de tipo y tamaño (50MB límite)
- **Progreso visual** durante la subida

### ✅ **Procesamiento Inteligente**
- **Parsing automático** según formato
- **Extracción de metadatos**: título, autor, páginas, palabras
- **Chunking inteligente** con solapamiento
- **Indexación vectorial** automática en ChromaDB
- **Organización por colecciones**: procedimientos, materiales, problemas, etc.

### ✅ **Gestión de Documentos**
- **Vista de documentos** subidos con estado
- **Procesamiento individual** de documentos
- **Eliminación** de documentos no deseados
- **Reindexación** completa del sistema
- **Limpieza de cache** del navegador

### ✅ **Interfaz de Administración**
- **Panel de admin** integrado en el frontend
- **Vista de cola** de archivos pendientes
- **Feedback visual** de operaciones
- **Navegación intuitiva** con atajos de teclado

## 📁 Estructura de Archivos

```
uploads/
├── pdf/           # Archivos PDF subidos
├── docx/          # Archivos Word subidos
├── txt/           # Archivos de texto subidos
├── md/            # Archivos Markdown subidos
├── processed/     # Archivos procesados exitosamente
└── errors/        # Archivos con errores de procesamiento
```

## 🔧 API Endpoints

### **Subida de Archivos**
```http
POST /api/knowledge/upload
Content-Type: multipart/form-data

Parámetros:
- file: Archivo a subir
- collection: Colección destino (procedimientos, materiales, etc.)
- auto_process: Boolean para procesamiento automático
```

### **Gestión de Documentos**
```http
GET    /api/knowledge/documents     # Lista todos los documentos
POST   /api/knowledge/process/{id}  # Procesa documento específico
DELETE /api/knowledge/documents/{id} # Elimina documento
POST   /api/knowledge/reindex       # Reindexa toda la base
```

## 🎨 Uso de la Interfaz

### **Acceder al Panel de Admin**
1. Abre el frontend: `mentor_ai/frontend/index.html`
2. Haz clic en el **botón de engranaje** (⚙️) en la esquina superior derecha
3. Se abre el **panel de administración**

### **Subir Documentos**
1. **Arrastrar archivos** al área de subida O hacer clic en "Seleccionar Archivos"
2. Seleccionar la **colección** destino
3. Marcar **"Procesar automáticamente"** si deseas
4. Hacer clic en **"Procesar Archivos"**

### **Gestionar Documentos**
- **Ver estado**: Cada documento muestra su estado (PDF, Procesado, Error)
- **Procesar**: Haz clic en el botón play (▶️) para documentos pendientes
- **Eliminar**: Haz clic en la papelera (🗑️) para eliminar documentos

### **Acciones del Sistema**
- **Reindexar**: Actualiza toda la base de conocimientos
- **Limpiar Cache**: Elimina datos temporales del navegador

## 📊 Estados de Documentos

| Estado | Descripción | Acciones Disponibles |
|--------|-------------|----------------------|
| `pdf/docx/txt/md` | Recién subido, pendiente de procesamiento | Procesar, Eliminar |
| `processed` | Procesado e indexado correctamente | Eliminar |
| `errors` | Error durante procesamiento | Reintentar, Eliminar |

## 🔍 Monitoreo y Debugging

### **Logs del Servidor**
```bash
# Ver logs en tiempo real
tail -f server_logs.log
```

### **Verificación de ChromaDB**
```python
# Desde Python console
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collections = client.list_collections()
print(f"Colecciones: {len(collections)}")
```

### **API Health Check**
```bash
curl http://localhost:8001/health
curl http://localhost:8001/api/knowledge/documents
```

## ⚠️ Consideraciones de Seguridad

- **Validación de archivos**: Solo formatos permitidos, límite de tamaño
- **Procesamiento en background**: No bloquea la interfaz
- **Manejo de errores**: Fallos no afectan otros documentos
- **Limpieza automática**: Archivos procesados se mueven a `processed/`

## 🚀 Próximas Mejoras

- [ ] **Preview de documentos** antes de procesar
- [ ] **Watcher de carpetas** para subida automática
- [ ] **OCR para PDFs escaneados**
- [ ] **Extracción de imágenes** de documentos
- [ ] **Versionado de documentos**
- [ ] **Búsqueda avanzada** en documentos
- [ ] **Exportación de resultados**

## 🐛 Troubleshooting

### **Error: "Formato no soportado"**
- Verifica que el archivo tenga extensión correcta (.pdf, .docx, .txt, .md)

### **Error: "Archivo demasiado grande"**
- Límite actual: 50MB por archivo
- Comprime o divide archivos grandes

### **Documentos no aparecen en la lista**
- Haz clic en "Actualizar" para refrescar
- Verifica que el servidor esté ejecutándose

### **Error procesando documento**
- Revisa logs del servidor
- Verifica que Ollama esté ejecutándose
- Intenta procesar individualmente

## 📈 Métricas de Rendimiento

- **PDF típico**: 10-30 segundos para procesar
- **DOCX pequeño**: 2-5 segundos
- **TXT/MD**: < 1 segundo
- **Límite concurrente**: 3 documentos simultáneos

**¡La zona de ingesta está completamente operativa y lista para usar!** 🎉