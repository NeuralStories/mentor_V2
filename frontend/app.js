// Mentor by EgeAI PWA JavaScript
class MentorAI {
    constructor() {
        this.apiBaseUrl = this.getApiBaseUrl();
        this.sessionId = this.generateSessionId();
        this.userId = this.getUserId();
        this.isOnline = navigator.onLine;
        this.messageHistory = [];

        this.init();
    }

    init() {
        this.bindEvents();
        this.loadUserPreferences();
        this.checkConnection();
        this.registerServiceWorker();
        this.loadMessageHistory();
    }

    bindEvents() {
        // Message input
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');

        messageInput.addEventListener('input', () => {
            this.updateSendButton();
            this.autoResizeTextarea(messageInput);
        });

        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        sendButton.addEventListener('click', () => this.sendMessage());

        // Quick actions
        document.querySelectorAll('.quick-action').forEach(button => {
            button.addEventListener('click', () => {
                const action = button.dataset.action;
                this.handleQuickAction(action);
            });
        });

        // User role change
        document.getElementById('userRole').addEventListener('change', () => {
            this.saveUserPreferences();
        });

        // Connection monitoring
        window.addEventListener('online', () => this.updateConnectionStatus(true));
        window.addEventListener('offline', () => this.updateConnectionStatus(false));

        // Modal close
        document.querySelector('.modal-close').addEventListener('click', () => {
            this.hideErrorModal();
        });

        // Click outside modal
        document.getElementById('errorModal').addEventListener('click', (e) => {
            if (e.target === document.getElementById('errorModal')) {
                this.hideErrorModal();
            }
        });
    }

    getApiBaseUrl() {
        // In production, this should be the actual API URL
        // For development, assume it's on the same domain
        return window.location.protocol + '//' + window.location.hostname + ':8765/api';
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    getUserId() {
        let userId = localStorage.getItem('carpintero_user_id');
        if (!userId) {
            userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('carpintero_user_id', userId);
        }
        return userId;
    }

    saveUserPreferences() {
        const userRole = document.getElementById('userRole').value;
        localStorage.setItem('carpintero_user_role', userRole);
    }

    loadUserPreferences() {
        const userRole = localStorage.getItem('carpintero_user_role') || 'general';
        document.getElementById('userRole').value = userRole;
    }

    loadMessageHistory() {
        // Load from localStorage if available
        const savedHistory = localStorage.getItem('carpintero_messages');
        if (savedHistory) {
            this.messageHistory = JSON.parse(savedHistory);
            this.renderMessages();
        }
    }

    saveMessageHistory() {
        localStorage.setItem('carpintero_messages', JSON.stringify(this.messageHistory));
    }

    checkConnection() {
        this.updateConnectionStatus(navigator.onLine);
        // Check API health
        this.checkApiHealth();
    }

    async checkApiHealth() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/chat/health`);
            const data = await response.json();
            this.updateConnectionStatus(response.ok);
        } catch (error) {
            this.updateConnectionStatus(false);
        }
    }

    updateConnectionStatus(isOnline) {
        this.isOnline = isOnline;
        const statusIndicator = document.getElementById('connectionStatus');
        const icon = statusIndicator.querySelector('i');

        if (isOnline) {
            statusIndicator.innerHTML = '<i class="fas fa-circle"></i> Conectado';
            statusIndicator.className = 'status-indicator online';
            icon.style.color = 'var(--success-color)';
        } else {
            statusIndicator.innerHTML = '<i class="fas fa-circle"></i> Sin conexión';
            statusIndicator.className = 'status-indicator offline';
            icon.style.color = 'var(--accent-color)';
        }
    }

    updateSendButton() {
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const hasText = messageInput.value.trim().length > 0;

        sendButton.disabled = !hasText || !this.isOnline;
    }

    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();

        if (!message || !this.isOnline) return;

        // Clear input
        messageInput.value = '';
        this.updateSendButton();
        this.autoResizeTextarea(messageInput);

        // Hide welcome message and show chat
        document.querySelector('.welcome-message').style.display = 'none';
        document.getElementById('chatMessages').style.display = 'block';

        // Add user message to UI
        this.addMessageToUI('user', message);

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Send to API
            const response = await this.sendToAPI(message);

            // Hide typing indicator
            this.hideTypingIndicator();

            // Add bot response to UI
            this.addMessageToUI('bot', response.response);

            // Store conversation
            this.storeConversation(message, response);

        } catch (error) {
            this.hideTypingIndicator();
            this.showError('Error al enviar mensaje. Verifica tu conexión.');
            console.error('Error sending message:', error);
        }
    }

    async sendToAPI(message) {
        const userRole = document.getElementById('userRole').value;

        const payload = {
            message: message,
            user_id: this.userId,
            user_role: userRole,
            session_id: this.sessionId
        };

        const response = await fetch(`${this.apiBaseUrl}/chat/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    addMessageToUI(sender, content, persist = true) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        const avatar = sender === 'user' ? 'Tú' : 'AI';
        const avatarClass = sender === 'user' ? 'user-avatar' : 'bot-avatar';

        messageDiv.innerHTML = `
            <div class="message-avatar ${avatarClass}">${avatar.charAt(0)}</div>
            <div class="message-content">${this.formatMessage(content)}</div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Store in history
        if (persist) {
            this.messageHistory.push({
                sender: sender,
                content: content,
                timestamp: new Date().toISOString()
            });
            this.saveMessageHistory();
        }
    }

    formatMessage(content) {
        // Basic formatting for markdown-like content
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    storeConversation(userMessage, botResponse) {
        // Store conversation ID for feedback if needed
        if (botResponse.conversation_id) {
            this.lastConversationId = botResponse.conversation_id;
        }
    }

    showTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'flex';
    }

    hideTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'none';
    }

    handleQuickAction(action) {
        const templates = {
            'diagnostico': 'Tengo un problema con una instalación. Los síntomas son: [describe el problema]',
            'guia': 'Necesito una guía paso a paso para instalar [qué elemento]. ¿Me puedes ayudar?',
            'consulta': '¿Cuál es la medida estándar para [elemento] en [situación]?'
        };

        const messageInput = document.getElementById('messageInput');
        messageInput.value = templates[action];
        messageInput.focus();
        this.updateSendButton();
        this.autoResizeTextarea(messageInput);
    }

    showError(message) {
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.textContent = message;
        document.getElementById('errorModal').style.display = 'flex';
    }

    hideErrorModal() {
        document.getElementById('errorModal').style.display = 'none';
    }

    renderMessages() {
        // Render existing messages from history
        this.messageHistory.forEach(msg => {
            this.addMessageToUI(msg.sender, msg.content, false);
        });
    }

    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('sw.js')
                .then(registration => {
                    console.log('Service Worker registrado:', registration);
                })
                .catch(error => {
                    console.log('Error registrando Service Worker:', error);
                });
        }
    }
}

// Admin Panel functionality
class AdminPanel {
    constructor() {
        this.isOpen = false;
        this.uploadQueue = [];
        this.init();
    }

    init() {
        // Admin panel toggle
        document.getElementById('adminToggle').addEventListener('click', () => {
            this.togglePanel();
        });

        // Close admin panel
        document.getElementById('closeAdmin').addEventListener('click', () => {
            this.closePanel();
        });

        // File upload
        this.initFileUpload();

        // Document management
        this.initDocumentManagement();

        // System actions
        this.initSystemActions();

        // Close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.closePanel();
            }
        });

        // Close on outside click
        document.getElementById('adminPanel').addEventListener('click', (e) => {
            if (e.target === document.getElementById('adminPanel')) {
                this.closePanel();
            }
        });
    }

    togglePanel() {
        if (this.isOpen) {
            this.closePanel();
        } else {
            this.openPanel();
        }
    }

    openPanel() {
        document.getElementById('adminPanel').style.display = 'block';
        this.isOpen = true;
        this.loadDocuments();
    }

    closePanel() {
        document.getElementById('adminPanel').style.display = 'none';
        this.isOpen = false;
    }

    initFileUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const selectFilesBtn = document.getElementById('selectFilesBtn');
        const processQueueBtn = document.getElementById('processQueueBtn');

        // Click to select files
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        selectFilesBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.click();
        });

        // File selection
        fileInput.addEventListener('change', (e) => {
            this.handleFileSelection(e.target.files);
        });

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            this.handleFileSelection(e.dataTransfer.files);
        });

        // Process queue
        processQueueBtn.addEventListener('click', () => {
            this.processUploadQueue();
        });
    }

    handleFileSelection(files) {
        Array.from(files).forEach(file => {
            // Validate file type
            const allowedTypes = ['.pdf', '.docx', '.txt', '.md'];
            const fileExt = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));

            if (!allowedTypes.includes(fileExt)) {
                this.showNotification(`Tipo de archivo no soportado: ${file.name}`, 'error');
                return;
            }

            // Check file size (50MB limit)
            if (file.size > 50 * 1024 * 1024) {
                this.showNotification(`Archivo demasiado grande: ${file.name}`, 'error');
                return;
            }

            // Add to queue
            this.uploadQueue.push(file);
        });

        this.updateUploadQueue();
    }

    updateUploadQueue() {
        const queueContainer = document.getElementById('uploadQueue');
        const queueList = document.getElementById('queueList');
        const processBtn = document.getElementById('processQueueBtn');

        if (this.uploadQueue.length > 0) {
            queueContainer.style.display = 'block';
            processBtn.disabled = false;

            queueList.innerHTML = this.uploadQueue.map((file, index) => `
                <div class="queue-item">
                    <div>
                        <div class="queue-item-name">${file.name}</div>
                        <div class="queue-item-size">${this.formatFileSize(file.size)}</div>
                    </div>
                    <button class="queue-item-remove" onclick="mentorAI.adminPanel.removeFromQueue(${index})">
                        ×
                    </button>
                </div>
            `).join('');
        } else {
            queueContainer.style.display = 'none';
            processBtn.disabled = true;
        }
    }

    removeFromQueue(index) {
        this.uploadQueue.splice(index, 1);
        this.updateUploadQueue();
    }

    async processUploadQueue() {
        const collection = document.getElementById('uploadCollection').value;
        const autoProcess = document.getElementById('autoProcess').checked;

        for (const file of this.uploadQueue) {
            try {
                await this.uploadFile(file, collection, autoProcess);
                this.showNotification(`Archivo subido: ${file.name}`, 'success');
            } catch (error) {
                this.showNotification(`Error subiendo ${file.name}: ${error.message}`, 'error');
            }
        }

        this.uploadQueue = [];
        this.updateUploadQueue();
        this.loadDocuments(); // Refresh document list
    }

    async uploadFile(file, collection, autoProcess) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('collection', collection);
        formData.append('auto_process', autoProcess.toString());

        const response = await fetch(`${mentorAI.apiBaseUrl}/knowledge/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error subiendo archivo');
        }

        return await response.json();
    }

    initDocumentManagement() {
        document.getElementById('refreshDocsBtn').addEventListener('click', () => {
            this.loadDocuments();
        });
    }

    async loadDocuments() {
        try {
            const response = await fetch(`${mentorAI.apiBaseUrl}/knowledge/documents`);
            const data = await response.json();

            this.renderDocuments(data.documents);
        } catch (error) {
            console.error('Error cargando documentos:', error);
            this.showNotification('Error cargando documentos', 'error');
        }
    }

    renderDocuments(documents) {
        const container = document.getElementById('documentsList');

        if (documents.length === 0) {
            container.innerHTML = '<div class="loading">No hay documentos subidos aún</div>';
            return;
        }

        container.innerHTML = documents.map(doc => `
            <div class="document-item">
                <div class="document-info">
                    <div class="document-name">${doc.file_name}</div>
                    <div class="document-meta">
                        <span>${doc.file_format.toUpperCase()}</span>
                        <span>${this.formatFileSize(doc.file_size)}</span>
                        <span>${new Date(doc.upload_date).toLocaleDateString()}</span>
                        ${doc.word_count ? `<span>${doc.word_count} palabras</span>` : ''}
                    </div>
                </div>
                <div class="document-actions">
                    <span class="document-status status-${doc.status}">${this.getStatusText(doc.status)}</span>
                    ${doc.status !== 'processed' ? `
                        <button class="btn-action btn-process" onclick="mentorAI.adminPanel.processDocument('${doc.file_id}')">
                            <i class="fas fa-play"></i>
                        </button>
                    ` : ''}
                    <button class="btn-action btn-delete" onclick="mentorAI.adminPanel.deleteDocument('${doc.file_id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    getStatusText(status) {
        const statusMap = {
            'pdf': 'PDF',
            'docx': 'DOCX',
            'txt': 'TXT',
            'md': 'MD',
            'processed': 'Procesado',
            'errors': 'Error'
        };
        return statusMap[status] || status;
    }

    async processDocument(fileId) {
        try {
            const response = await fetch(`${mentorAI.apiBaseUrl}/knowledge/process/${fileId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    file_id: fileId,
                    collection: 'procedimientos'
                })
            });

            if (!response.ok) {
                throw new Error('Error procesando documento');
            }

            this.showNotification('Documento enviado a procesamiento', 'success');
            setTimeout(() => this.loadDocuments(), 2000); // Refresh after 2 seconds
        } catch (error) {
            this.showNotification(`Error procesando documento: ${error.message}`, 'error');
        }
    }

    async deleteDocument(fileId) {
        if (!confirm('¿Estás seguro de que quieres eliminar este documento?')) {
            return;
        }

        try {
            const response = await fetch(`${mentorAI.apiBaseUrl}/knowledge/documents/${fileId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Error eliminando documento');
            }

            this.showNotification('Documento eliminado', 'success');
            this.loadDocuments();
        } catch (error) {
            this.showNotification(`Error eliminando documento: ${error.message}`, 'error');
        }
    }

    initSystemActions() {
        document.getElementById('reindexBtn').addEventListener('click', async () => {
            try {
                const response = await fetch(`${mentorAI.apiBaseUrl}/knowledge/reindex`, {
                    method: 'POST'
                });

                if (!response.ok) {
                    throw new Error('Error iniciando reindexación');
                }

                this.showNotification('Reindexación iniciada en background', 'success');
            } catch (error) {
                this.showNotification(`Error en reindexación: ${error.message}`, 'error');
            }
        });

        document.getElementById('clearCacheBtn').addEventListener('click', () => {
            if (confirm('¿Limpiar toda la cache? Esta acción no se puede deshacer.')) {
                // Clear local storage
                localStorage.clear();
                // Clear service worker cache (if applicable)
                if ('caches' in window) {
                    caches.keys().then(names => {
                        names.forEach(name => {
                            caches.delete(name);
                        });
                    });
                }
                this.showNotification('Cache limpiada', 'success');
            }
        });
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showNotification(message, type = 'info') {
        // Simple notification - you could enhance this
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem;
            border-radius: 8px;
            color: white;
            background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
            z-index: 3000;
            animation: slideIn 0.3s ease-out;
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.mentorAI = new MentorAI();
    window.mentorAI.adminPanel = new AdminPanel();
});

// Global functions for HTML onclick handlers
function hideErrorModal() {
    if (window.mentorAI) {
        window.mentorAI.hideErrorModal();
    }
}
