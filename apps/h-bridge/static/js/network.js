/**
 * hAIrem A2UI Network Client
 * Manages WebSocket connection to H-Core.
 */

class NetworkClient {
    constructor(url = `ws://${window.location.hostname}:${window.location.port}/ws`) {
        this.url = url;
        this.socket = null;
        this.agentMetadata = [];
        this.connect();
    }

    async fetchMetadata() {
        if (this.isFetchingMetadata) return;
        this.isFetchingMetadata = true;
        try {
            const response = await fetch('/api/agents');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            this.agentMetadata = Array.isArray(data) ? data : (data.agents || []);
            
            // Retry if empty (backend might be warming up)
            if (this.agentMetadata.length === 0) {
                console.warn("Agent list empty, retrying in 2s...");
                setTimeout(() => {
                    this.isFetchingMetadata = false; 
                    this.fetchMetadata();
                }, 2000);
                
                // Temporary Fallback
                this.agentMetadata = [
                    { id: "Renarde", commands: ["ping"] },
                    { id: "system", commands: ["imagine"] }
                ];
            }
            
            console.log("Agent metadata loaded:", this.agentMetadata);
            // Populate agents map in renderer immediately
            if (window.renderer) {
                window.renderer.updateAgentCards(this.agentMetadata);
            }
        } catch (e) {
            console.error("Failed to fetch agent metadata:", e);
            // Retry on error too
            setTimeout(() => {
                this.isFetchingMetadata = false; 
                this.fetchMetadata();
            }, 3000);
        } finally {
            this.isFetchingMetadata = false;
        }
    }

    async fetchHistory() {
        try {
            const response = await fetch('/api/history');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            
            if (data.status === "connecting") {
                console.log("Database still connecting, retrying history in 2s...");
                setTimeout(() => this.fetchHistory(), 2000);
                return;
            }

            const messages = Array.isArray(data) ? data : (data.messages || []);
            console.log("Chat history loaded:", messages.length, "messages");
            window.renderer.renderHistory(messages);
        } catch (e) {
            console.error("Failed to fetch chat history:", e);
        }
    }

    connect() {
        console.log(`Connecting to H-Core at ${this.url}...`);
        if (window.renderer) window.renderer.updateSystemStatus('ws', 'checking');
        
        this.socket = new WebSocket(this.url);

        this.socket.onopen = () => {
            console.log("Connected to H-Core bus.");
            if (window.renderer) window.renderer.updateSystemStatus('ws', 'ok');
            
            // STORY 17.2: Sync initial log level
            const savedLevel = localStorage.getItem('hairem_log_level') || 'INFO';
            this.send('system.config_update', { log_level: savedLevel });

            // Retry fetching metadata now that connection implies backend is likely up
            this.fetchMetadata();

            // Wait a tiny bit to ensure renderer class is fully instantiated
            setTimeout(() => {
                if (window.renderer && typeof window.renderer.setReady === 'function') {
                    window.renderer.setReady(true);
                }
            }, 100);
        };

        this.socket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            } catch (e) {
                console.error("Failed to parse WebSocket message:", e);
            }
        };

        this.socket.onclose = () => {
            console.warn("Disconnected from H-Core. Retrying in 5s...");
            if (window.renderer) {
                window.renderer.setReady(false);
                window.renderer.updateSystemStatus('ws', 'error');
            }
            setTimeout(() => this.connect(), 5000);
        };

        this.socket.onerror = (error) => {
            console.error("WebSocket error:", error);
        };
    }

    handleMessage(message) {
        console.log(`NETWORK: Received ${message.type} from ${message.sender ? message.sender.agent_id : 'unknown'}`);
        // Clear processing state on any narrative response
        if ((message.type === "narrative.text" || message.type === "narrative.chunk" || message.type === "expert.response") && window.renderer) {
            window.renderer.setProcessingState(false);
        }

        // Route to renderer
        if (message.type === "narrative.text") {
            // Queue narrative messages
            if (window.speechQueue) {
                window.speechQueue.enqueue(message);
            } else {
                // Fallback if queue not loaded
                const agentName = message.sender.agent_id;
                const text = message.payload.content;
                window.renderer.render(agentName, text); 
                window.renderer.addMessageToHistory(agentName, text);
            }
        } else if (message.type === "narrative.chunk") {
            // Handle streaming chunks in history with full message context
            window.renderer.handleChunk(message);
            
        } else if (message.type === "expert.response") {
            const agentName = message.sender.agent_id;
            const payload = message.payload.content;
            const text = typeof payload === 'object' ? (payload.result || payload.error || JSON.stringify(payload)) : payload;
            window.renderer.addMessageToHistory(agentName, text);
            
        } else if (message.type === "system.log") {
            const logEntry = message.payload.content;
            window.renderer.addLog(logEntry);
        } else if (message.type === "system.status_update") {
            const agentId = message.sender.agent_id;
            const statusPayload = message.payload.content;
            console.log(`NETWORK: Status update for ${agentId}:`, statusPayload);
            
            // Handle Global System Health Updates
            // STORY 23.3: Recognize both "system" target or "brain" component
            if ((message.recipient && message.recipient.target === "system") || statusPayload.component === "brain") {
                if (statusPayload.component) {
                    window.renderer.updateSystemStatus(statusPayload.component, statusPayload.status);
                }
                return;
            }

            // Sync metadata for autocomplete
            const existingAgent = this.agentMetadata.find(a => a.id === agentId);
            if (existingAgent) {
                if (statusPayload.commands) existingAgent.commands = statusPayload.commands;
            }

            window.renderer.updateAgentStatus(
                agentId, 
                statusPayload.status, 
                statusPayload.mood, 
                statusPayload.prompt_tokens, 
                statusPayload.completion_tokens, 
                statusPayload.total_tokens,
                statusPayload.commands
            );
        } else if (message.type === "visual.asset") {
            const payload = message.payload.content;
            let url = payload.url;
            
            // Map internal paths/hosts to web-accessible paths
            if (url.startsWith('file:///media/generated/')) {
                url = url.replace('file:///media/generated/', '/media/');
            } else if (url.includes('/media/generated/')) {
                // Handle cases where it might be a full URI or mixed path
                url = '/media/' + url.split('/media/generated/')[1];
            }
            
            if (url.startsWith('http://h-bridge:8000/')) {
                url = url.replace('http://h-bridge:8000/', '/');
            }
            
            // Story 25.6: Add cache busting
            url += (url.includes('?') ? '&' : '?') + 't=' + Date.now();
            
            console.log("NETWORK: Visual asset received:", url);
            if (window.renderer) {
                window.renderer.addLog(`🎨 Image reçue: ${url}`);
                window.renderer.renderVisualAsset({
                    url: url,
                    alt_text: payload.alt_text,
                    agent_id: payload.agent_id,
                    asset_type: payload.asset_type || "background"
                });
            }
        }
    }

    generateUUID() {
        // Fallback for non-secure contexts (http) where crypto.randomUUID is not available
        try {
            if (window.crypto && window.crypto.randomUUID) {
                return window.crypto.randomUUID();
            }
        } catch (e) {}
        
        // Manual UUID v4 generation
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    toggleAgent(agentId, isActive) {
        console.log(`Toggling agent ${agentId} to ${isActive}`);
        
        // Optimistic UI update
        if (window.renderer.agents[agentId]) {
            window.renderer.agents[agentId].active = isActive;
            window.renderer.renderAgentGrid();
        }

        const message = {
            id: this.generateUUID(),
            timestamp: new Date().toISOString(),
            type: "system.status_update",
            sender: { agent_id: "user", role: "admin" },
            recipient: { target: "system" },
            payload: {
                content: {
                    agent_id: agentId,
                    active: isActive
                }
            },
            metadata: { priority: "system" }
        };
        this.socket.send(JSON.stringify(message));
    }

    sendUserMessage(text, target = "broadcast") {
        console.log("NETWORK_SEND_START: Target =", target, "Text =", text);
        if (!text.trim()) return;

        let message;
        const globalCommands = ['imagine', 'outfit', 'vault', 'location'];
        const firstWord = text.slice(1).split(' ')[0].toLowerCase();

        if (text.startsWith('/') && !globalCommands.includes(firstWord)) {
            // Slash Command Mode for specific agents: /target_agent command_name args...
            const parts = text.slice(1).split(' ');
            const slashTarget = parts[0] || "broadcast";
            const command = parts[1] || "ping";
            const args = parts.slice(2).join(' ');

            message = {
                id: this.generateUUID(),
                timestamp: new Date().toISOString(),
                type: "expert.command",
                sender: { agent_id: "user", role: "user" },
                recipient: { target: slashTarget },
                payload: {
                    content: null,
                    command: command,
                    args: args,
                    format: "json"
                },
                metadata: { priority: "high", ttl: 5 }
            };
            console.log(`Executing direct command on ${slashTarget}:`, command);
        } else {
            // Normal Narrative Mode
            message = {
                id: this.generateUUID(),
                timestamp: new Date().toISOString(),
                type: "narrative.text",
                sender: { agent_id: "user", role: "user" },
                recipient: { target: target },
                payload: { content: text, format: "text" },
                metadata: { priority: "normal", ttl: 5 }
            };
        }

        console.log("Sending to H-Core:", JSON.stringify(message));
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            try {
                this.socket.send(JSON.stringify(message));
                console.log("NETWORK_SEND_SUCCESS");
            } catch (e) {
                console.error("NETWORK_SEND_EXCEPTION:", e);
            }
        } else {
            console.error("NETWORK_SEND_FAILURE: WebSocket NOT open. State =", this.socket ? this.socket.readyState : "NULL");
        }
        
        if (window.renderer) {
            window.renderer.setState('thinking');
            window.renderer.setProcessingState(true);
        }
    }

    send(type, content) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({ type, content }));
        }
    }
}

// Global instance
window.network = new NetworkClient();