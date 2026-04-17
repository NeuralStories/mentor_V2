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
        const messageInput = document.getElementById("messageInput");
        const sendButton = document.getElementById("sendButton");

        messageInput.addEventListener("input", () => {
            this.updateSendButton();
            this.autoResizeTextarea(messageInput);
        });

        messageInput.addEventListener("keypress", (event) => {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                this.sendMessage();
            }
        });

        sendButton.addEventListener("click", () => this.sendMessage());

        document.querySelectorAll(".quick-action").forEach((button) => {
            button.addEventListener("click", () => this.handleQuickAction(button.dataset.action));
        });

        document.getElementById("userRole").addEventListener("change", () => this.saveUserPreferences());
        window.addEventListener("online", () => this.updateConnectionStatus(true));
        window.addEventListener("offline", () => this.updateConnectionStatus(false));
        document.querySelector(".modal-close").addEventListener("click", () => this.hideErrorModal());
        document.getElementById("errorModal").addEventListener("click", (event) => {
            if (event.target === document.getElementById("errorModal")) {
                this.hideErrorModal();
            }
        });
    }

    getApiBaseUrl() {
        return `${window.location.protocol}//${window.location.hostname}:8765/api`;
    }

    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;
    }

    getUserId() {
        let userId = localStorage.getItem("carpintero_user_id");
        if (!userId) {
            userId = `user_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;
            localStorage.setItem("carpintero_user_id", userId);
        }
        return userId;
    }

    saveUserPreferences() {
        localStorage.setItem("carpintero_user_role", document.getElementById("userRole").value);
    }

    loadUserPreferences() {
        document.getElementById("userRole").value = localStorage.getItem("carpintero_user_role") || "general";
    }

    loadMessageHistory() {
        const savedHistory = localStorage.getItem("carpintero_messages");
        if (savedHistory) {
            this.messageHistory = JSON.parse(savedHistory);
            this.renderMessages();
        }
    }

    saveMessageHistory() {
        localStorage.setItem("carpintero_messages", JSON.stringify(this.messageHistory));
    }

    checkConnection() {
        this.updateConnectionStatus(navigator.onLine);
        this.checkApiHealth();
    }

    async checkApiHealth() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/chat/health`);
            this.updateConnectionStatus(response.ok);
        } catch (_) {
            this.updateConnectionStatus(false);
        }
    }

    updateConnectionStatus(isOnline) {
        this.isOnline = isOnline;
        const statusIndicator = document.getElementById("connectionStatus");
        statusIndicator.innerHTML = isOnline
            ? '<i class="fas fa-circle"></i> Conectado'
            : '<i class="fas fa-circle"></i> Sin conexión';
        statusIndicator.className = `status-indicator ${isOnline ? "online" : "offline"}`;
    }

    updateSendButton() {
        const message = document.getElementById("messageInput").value.trim();
        document.getElementById("sendButton").disabled = !message || !this.isOnline;
    }

    autoResizeTextarea(textarea) {
        textarea.style.height = "auto";
        textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }

    async sendMessage() {
        const input = document.getElementById("messageInput");
        const message = input.value.trim();
        if (!message || !this.isOnline) {
            return;
        }

        input.value = "";
        this.updateSendButton();
        this.autoResizeTextarea(input);
        document.querySelector(".welcome-message").style.display = "none";
        document.getElementById("chatMessages").style.display = "block";

        this.addMessageToUI("user", message);
        this.showTypingIndicator();

        try {
            const response = await this.sendToAPI(message);
            this.hideTypingIndicator();
            this.addMessageToUI("bot", response.response);
            this.storeConversation(response);
        } catch (error) {
            this.hideTypingIndicator();
            this.showError("Error al enviar mensaje. Verifica tu conexión.");
            console.error("Error sending message:", error);
        }
    }

    async sendToAPI(message) {
        const response = await fetch(`${this.apiBaseUrl}/chat/message`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message,
                user_id: this.userId,
                user_role: document.getElementById("userRole").value,
                session_id: this.sessionId,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }

        return response.json();
    }

    addMessageToUI(sender, content, persist = true) {
        const messagesContainer = document.getElementById("chatMessages");
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${sender}`;
        messageDiv.innerHTML = `
            <div class="message-avatar ${sender === "user" ? "user-avatar" : "bot-avatar"}">${sender === "user" ? "T" : "A"}</div>
            <div class="message-content">${this.formatMessage(content)}</div>
        `;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        if (persist) {
            this.messageHistory.push({ sender, content, timestamp: new Date().toISOString() });
            this.saveMessageHistory();
        }
    }

    formatMessage(content) {
        return content
            .replace(/\n/g, "<br>")
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.*?)\*/g, "<em>$1</em>");
    }

    storeConversation(botResponse) {
        if (botResponse.conversation_id) {
            this.lastConversationId = botResponse.conversation_id;
        }
    }

    showTypingIndicator() {
        document.getElementById("typingIndicator").style.display = "flex";
    }

    hideTypingIndicator() {
        document.getElementById("typingIndicator").style.display = "none";
    }

    handleQuickAction(action) {
        const templates = {
            diagnostico: "Tengo un problema con una instalación. Los síntomas son: [describe el problema]",
            guia: "Necesito una guía paso a paso para instalar [qué elemento]. ¿Me puedes ayudar?",
            consulta: "¿Cuál es la medida estándar para [elemento] en [situación]?",
        };
        const input = document.getElementById("messageInput");
        input.value = templates[action] || "";
        input.focus();
        this.updateSendButton();
        this.autoResizeTextarea(input);
    }

    showError(message) {
        document.getElementById("errorMessage").textContent = message;
        document.getElementById("errorModal").style.display = "flex";
    }

    hideErrorModal() {
        document.getElementById("errorModal").style.display = "none";
    }

    renderMessages() {
        this.messageHistory.forEach((message) => this.addMessageToUI(message.sender, message.content, false));
    }

    registerServiceWorker() {
        if ("serviceWorker" in navigator) {
            navigator.serviceWorker.register("sw.js").catch((error) => {
                console.log("Error registrando Service Worker:", error);
            });
        }
    }
}

class AdminPanel {
    constructor() {
        this.isOpen = false;
        this.uploadQueue = [];
        this.documents = new Map();
        this.pollingIds = new Set();
        this.pollTimer = null;
        this.systemHealth = null;
        this.statusMeta = {
            uploaded: { label: "Subido", className: "status-uploaded", icon: "fa-upload" },
            parsing: { label: "Parseando", className: "status-processing", icon: "fa-file-lines" },
            ocr: { label: "OCR", className: "status-processing", icon: "fa-eye" },
            chunking: { label: "Fragmentando", className: "status-processing", icon: "fa-scissors" },
            indexing: { label: "Indexando", className: "status-processing", icon: "fa-magnifying-glass" },
            ready: { label: "Listo", className: "status-processed", icon: "fa-circle-check" },
            failed: { label: "Error", className: "status-error", icon: "fa-triangle-exclamation" },
        };
        this.init();
    }

    init() {
        document.getElementById("adminToggle").addEventListener("click", () => this.togglePanel());
        document.getElementById("closeAdmin").addEventListener("click", () => this.closePanel());
        document.getElementById("refreshDocsBtn").addEventListener("click", () => this.loadDocuments());
        document.getElementById("reindexBtn").addEventListener("click", () => this.reindexKnowledgeBase());
        document.getElementById("clearCacheBtn").addEventListener("click", () => this.clearCache());
        document.getElementById("adminPanel").addEventListener("click", (event) => {
            if (event.target === document.getElementById("adminPanel")) {
                this.closePanel();
            }
        });

        this.initFileUpload();
    }

    togglePanel() {
        if (this.isOpen) {
            this.closePanel();
        } else {
            this.openPanel();
        }
    }

    async openPanel() {
        document.getElementById("adminPanel").style.display = "block";
        this.isOpen = true;
        await Promise.all([this.loadDocuments(), this.loadSystemHealth()]);
    }

    closePanel() {
        document.getElementById("adminPanel").style.display = "none";
        this.isOpen = false;
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }
    }

    initFileUpload() {
        const uploadArea = document.getElementById("uploadArea");
        const fileInput = document.getElementById("fileInput");
        const selectFilesBtn = document.getElementById("selectFilesBtn");
        const processQueueBtn = document.getElementById("processQueueBtn");

        uploadArea.addEventListener("click", () => fileInput.click());
        selectFilesBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            fileInput.click();
        });
        fileInput.addEventListener("change", (event) => this.handleFileSelection(event.target.files));

        uploadArea.addEventListener("dragover", (event) => {
            event.preventDefault();
            uploadArea.classList.add("dragover");
        });
        uploadArea.addEventListener("dragleave", () => uploadArea.classList.remove("dragover"));
        uploadArea.addEventListener("drop", (event) => {
            event.preventDefault();
            uploadArea.classList.remove("dragover");
            this.handleFileSelection(event.dataTransfer.files);
        });

        processQueueBtn.addEventListener("click", () => this.processUploadQueue());
    }

    handleFileSelection(files) {
        Array.from(files).forEach((file) => {
            const extension = file.name.toLowerCase().slice(file.name.lastIndexOf("."));
            if (![".pdf", ".docx", ".txt", ".md"].includes(extension)) {
                this.showNotification(`Tipo de archivo no soportado: ${file.name}`, "error");
                return;
            }
            if (file.size > 50 * 1024 * 1024) {
                this.showNotification(`Archivo demasiado grande: ${file.name}`, "error");
                return;
            }
            this.uploadQueue.push(file);
        });
        this.updateUploadQueue();
    }

    updateUploadQueue() {
        const queueContainer = document.getElementById("uploadQueue");
        const queueList = document.getElementById("queueList");
        const processButton = document.getElementById("processQueueBtn");

        if (this.uploadQueue.length === 0) {
            queueContainer.style.display = "none";
            processButton.disabled = true;
            return;
        }

        queueContainer.style.display = "block";
        processButton.disabled = false;
        queueList.innerHTML = this.uploadQueue.map((file, index) => `
            <div class="queue-item">
                <div>
                    <div class="queue-item-name">${this.escapeHtml(file.name)}</div>
                    <div class="queue-item-size">${this.formatFileSize(file.size)}</div>
                </div>
                <button class="queue-item-remove" onclick="mentorAI.adminPanel.removeFromQueue(${index})">×</button>
            </div>
        `).join("");
    }

    removeFromQueue(index) {
        this.uploadQueue.splice(index, 1);
        this.updateUploadQueue();
    }

    async processUploadQueue() {
        const collection = document.getElementById("uploadCollection").value;
        const autoProcess = document.getElementById("autoProcess").checked;

        for (const file of this.uploadQueue) {
            try {
                const result = await this.uploadFile(file, collection, autoProcess);
                if (result.status === "duplicate") {
                    this.showNotification(`Documento duplicado: ${result.file_name}`, "info");
                } else {
                    this.trackDocument({
                        file_id: result.file_id,
                        filename: result.file_name,
                        file_format: result.file_format,
                        size_bytes: result.file_size,
                        collection,
                        status: autoProcess ? "parsing" : "uploaded",
                        updated_at: new Date().toISOString(),
                    });
                    this.showNotification(`Archivo subido: ${result.file_name}`, "success");
                }
            } catch (error) {
                this.showNotification(`Error subiendo ${file.name}: ${error.message}`, "error");
            }
        }

        this.uploadQueue = [];
        this.updateUploadQueue();
        this.renderDocuments();
    }

    async uploadFile(file, collection, autoProcess) {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("collection", collection);
        formData.append("auto_process", String(autoProcess));

        const response = await fetch(`${mentorAI.apiBaseUrl}/knowledge/upload`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const payload = await response.json().catch(() => ({}));
            throw new Error(payload.detail || "Error subiendo archivo");
        }

        return response.json();
    }

    async loadDocuments() {
        try {
            const response = await fetch(`${mentorAI.apiBaseUrl}/knowledge/documents`);
            const payload = await response.json();
            this.documents.clear();
            payload.documents.forEach((document) => this.trackDocument(document));
            this.renderDocuments();
        } catch (error) {
            console.error("Error cargando documentos:", error);
            this.showNotification("Error cargando documentos", "error");
        }
    }

    async loadSystemHealth() {
        try {
            const response = await fetch(`${mentorAI.apiBaseUrl}/../admin/system-health`);
            this.systemHealth = await response.json();
            this.renderSystemBanner();
        } catch (error) {
            console.error("Error cargando system health:", error);
        }
    }

    renderSystemBanner() {
        const container = document.querySelector(".documents-section");
        if (!container) {
            return;
        }
        container.querySelectorAll(".system-banner").forEach((node) => node.remove());

        if (this.systemHealth?.components?.database?.status !== "degraded") {
            return;
        }

        const banner = document.createElement("div");
        banner.className = "system-banner status-uploaded";
        banner.innerHTML = '<i class="fas fa-triangle-exclamation"></i> Supabase no disponible. El sistema funciona en modo local con SQLite.';
        container.prepend(banner);
    }

    trackDocument(document) {
        this.documents.set(document.file_id, document);
        if (!["ready", "failed"].includes(document.status)) {
            this.pollingIds.add(document.file_id);
            this.startPolling();
        } else {
            this.pollingIds.delete(document.file_id);
        }
    }

    startPolling() {
        if (this.pollTimer || this.pollingIds.size === 0) {
            return;
        }

        this.pollTimer = window.setInterval(async () => {
            if (!this.isOpen || this.pollingIds.size === 0) {
                clearInterval(this.pollTimer);
                this.pollTimer = null;
                return;
            }

            await Promise.all(Array.from(this.pollingIds).map(async (fileId) => {
                try {
                    const response = await fetch(`${mentorAI.apiBaseUrl}/knowledge/documents/${fileId}/status`);
                    if (!response.ok) {
                        throw new Error(`Status ${response.status}`);
                    }
                    const document = await response.json();
                    this.documents.set(fileId, document);
                    if (["ready", "failed"].includes(document.status)) {
                        this.pollingIds.delete(fileId);
                    }
                } catch (_) {
                    this.pollingIds.delete(fileId);
                }
            }));

            this.renderDocuments();

            if (this.pollingIds.size === 0) {
                clearInterval(this.pollTimer);
                this.pollTimer = null;
            }
        }, 2000);
    }

    renderDocuments() {
        const container = document.getElementById("documentsList");
        const documents = Array.from(this.documents.values()).sort((left, right) => {
            return String(right.updated_at || "").localeCompare(String(left.updated_at || ""));
        });

        if (documents.length === 0) {
            container.innerHTML = '<div class="loading">No hay documentos subidos aún</div>';
            return;
        }

        container.innerHTML = documents.map((document) => this.renderDocumentCard(document)).join("");
    }

    renderDocumentCard(document) {
        const status = this.statusMeta[document.status] || this.statusMeta.uploaded;
        const ocrBadge = document.ocr_used
            ? `<span class="document-chip" title="OCR usado en ${document.ocr_pages || "?"} páginas"><i class="fas fa-eye"></i> OCR</span>`
            : "";
        const errorBadge = document.error
            ? `<span class="document-chip document-chip-error" title="${this.escapeHtml(document.error)}"><i class="fas fa-circle-exclamation"></i> Error</span>`
            : "";

        return `
            <div class="document-item">
                <div class="document-info">
                    <div class="document-name">${this.escapeHtml(document.filename || document.file_name)}</div>
                    <div class="document-meta">
                        <span>${(document.file_format || "").toUpperCase()}</span>
                        <span>${this.formatFileSize(document.size_bytes || document.file_size || 0)}</span>
                        <span>${document.pages ?? "—"} págs</span>
                        <span>${document.chunks ?? "—"} chunks</span>
                        <span>${document.collection || "—"}</span>
                    </div>
                    <div class="document-meta">${ocrBadge} ${errorBadge}</div>
                </div>
                <div class="document-actions">
                    <span class="document-status ${status.className}">
                        <i class="fas ${status.icon}"></i> ${status.label}
                    </span>
                    ${document.status === "failed" ? `
                        <button class="btn-action btn-process" onclick="mentorAI.adminPanel.processDocument('${document.file_id}', '${document.collection || "procedimientos"}')">
                            <i class="fas fa-rotate-right"></i>
                        </button>
                    ` : ""}
                    <button class="btn-action btn-delete" onclick="mentorAI.adminPanel.deleteDocument('${document.file_id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }

    async processDocument(fileId, collection = "procedimientos") {
        try {
            const response = await fetch(`${mentorAI.apiBaseUrl}/knowledge/process/${fileId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ collection }),
            });

            if (!response.ok) {
                throw new Error("Error procesando documento");
            }

            const current = this.documents.get(fileId) || {};
            this.trackDocument({
                ...current,
                file_id: fileId,
                collection,
                status: "parsing",
                updated_at: new Date().toISOString(),
            });
            this.renderDocuments();
            this.showNotification("Documento enviado a procesamiento", "success");
        } catch (error) {
            this.showNotification(`Error procesando documento: ${error.message}`, "error");
        }
    }

    async deleteDocument(fileId) {
        if (!confirm("¿Estás seguro de que quieres eliminar este documento?")) {
            return;
        }

        try {
            const response = await fetch(`${mentorAI.apiBaseUrl}/knowledge/documents/${fileId}`, {
                method: "DELETE",
            });

            if (!response.ok) {
                throw new Error("Error eliminando documento");
            }

            this.documents.delete(fileId);
            this.pollingIds.delete(fileId);
            this.renderDocuments();
            this.showNotification("Documento eliminado", "success");
        } catch (error) {
            this.showNotification(`Error eliminando documento: ${error.message}`, "error");
        }
    }

    async reindexKnowledgeBase() {
        try {
            const response = await fetch(`${mentorAI.apiBaseUrl}/knowledge/reindex`, { method: "POST" });
            if (!response.ok) {
                throw new Error("Error iniciando reindexación");
            }
            this.showNotification("Reindexación iniciada en background", "success");
        } catch (error) {
            this.showNotification(`Error en reindexación: ${error.message}`, "error");
        }
    }

    clearCache() {
        if (!confirm("¿Limpiar toda la cache? Esta acción no se puede deshacer.")) {
            return;
        }

        localStorage.clear();
        if ("caches" in window) {
            caches.keys().then((names) => names.forEach((name) => caches.delete(name)));
        }
        this.showNotification("Cache limpiada", "success");
    }

    formatFileSize(bytes) {
        if (!bytes) {
            return "0 Bytes";
        }
        const units = ["Bytes", "KB", "MB", "GB"];
        const index = Math.floor(Math.log(bytes) / Math.log(1024));
        return `${parseFloat((bytes / (1024 ** index)).toFixed(2))} ${units[index]}`;
    }

    escapeHtml(value) {
        return String(value ?? "").replace(/[&<>"']/g, (character) => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
        }[character]));
    }

    showNotification(message, type = "info") {
        const notification = document.createElement("div");
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem;
            border-radius: 8px;
            color: white;
            background: ${type === "success" ? "#27ae60" : type === "error" ? "#e74c3c" : "#3498db"};
            z-index: 3000;
        `;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.mentorAI = new MentorAI();
    window.mentorAI.adminPanel = new AdminPanel();
});

function hideErrorModal() {
    if (window.mentorAI) {
        window.mentorAI.hideErrorModal();
    }
}
