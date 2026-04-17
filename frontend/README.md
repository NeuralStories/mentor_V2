# Mentor by EgeAI Frontend

Progressive Web App (PWA) para el asistente de mentoría técnica y educativa.

## Características

- ✨ **Interfaz moderna**: Diseño responsive y intuitivo
- 🔄 **PWA completa**: Funciona offline con Service Worker
- 💬 **Chat en tiempo real**: Comunicación fluida con el backend
- 🎯 **Acciones rápidas**: Templates para consultas comunes
- 📱 **Mobile-first**: Optimizado para dispositivos móviles
- 🌙 **Modo oscuro**: Soporte futuro para tema oscuro
- 🔔 **Notificaciones**: Alertas push (futuro)

## Estructura de archivos

```
frontend/
├── index.html          # Página principal
├── styles.css          # Estilos CSS
├── app.js             # Lógica JavaScript
├── sw.js              # Service Worker
├── manifest.json      # Manifiesto PWA
└── README.md          # Esta documentación
```

## Desarrollo

### Requisitos previos

- Backend de Mentor by EgeAI ejecutándose en puerto 8000
- Navegador moderno con soporte PWA

### Instalación

1. Asegúrate de que el backend esté ejecutándose
2. Abre `index.html` en un navegador moderno
3. La PWA se instalará automáticamente o aparecerá el prompt de instalación

### Desarrollo local

Para desarrollo local con live reload:

```bash
# Instalar un servidor local simple
npx serve frontend/

# O usar Python
python -m http.server 3000
```

### Funcionalidades

#### Chat
- Envío de mensajes con Enter o botón
- Indicador de escritura
- Historial de conversación
- Auto-resize del textarea

#### Acciones rápidas
- **Diagnosticar**: Template para problemas
- **Guía paso a paso**: Template para instrucciones
- **Consultar**: Template para preguntas técnicas

#### PWA
- Instalación en dispositivo
- Funcionamiento offline básico
- Cache inteligente de recursos
- Sincronización en background (futuro)

## API Integration

La aplicación se conecta automáticamente al backend en `http://localhost:8000/api`.

Endpoints utilizados:
- `POST /api/chat/message` - Enviar mensajes
- `GET /api/chat/health` - Verificar estado
- `POST /api/chat/feedback` - Enviar feedback

## Personalización

### Colores
Los colores se definen en `:root` en `styles.css`:
```css
--primary-color: #2c3e50;
--secondary-color: #3498db;
--accent-color: #e74c3c;
```

### Idioma
Actualmente en español. Para añadir más idiomas, modificar:
- Textos en `index.html`
- Mensajes en `app.js`
- `manifest.json`

## Próximas funcionalidades

- [ ] Modo oscuro
- [ ] Notificaciones push
- [ ] Sincronización offline
- [ ] Compartir conversaciones
- [ ] Historial avanzado
- [ ] Integración con voz

## Troubleshooting

### No se conecta al backend
- Verificar que el backend esté ejecutándose en puerto 8000
- Revisar CORS en la configuración del backend
- Verificar que no haya firewalls bloqueando

### PWA no se instala
- El sitio debe servir HTTPS en producción
- El Service Worker debe estar registrado correctamente
- Verificar que el manifest.json sea válido

### Problemas de cache
- Forzar recarga (Ctrl+F5)
- Limpiar storage del navegador
- Desregistrar Service Worker desde DevTools

## Contribución

Para contribuir al frontend:

1. Seguir la estructura de archivos existente
2. Mantener responsive design
3. Usar CSS variables para colores
4. Comentar código JavaScript
5. Probar en múltiples dispositivos