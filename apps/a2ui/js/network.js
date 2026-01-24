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
            
            // Fallback for Story 11.4: Ensure Renarde is always available for testing
            if (this.agentMetadata.length === 0) {
                this.agentMetadata = [{
                    id: "Renarde",
                    commands: ["ping", "status", "pose", "help"]
                }];
            }
            
            console.log("Agent metadata loaded:", this.agentMetadata);
            window.renderer.updateAgentCards(this.agentMetadata);
        } catch (e) {
            console.error("Failed to fetch agent metadata:", e);
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
        this.socket = new WebSocket(this.url);

        this.socket.onopen = () => {
            console.log("Connected to H-Core bus.");
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
            if (window.renderer) window.renderer.setReady(false);
            setTimeout(() => this.connect(), 5000);
        };

        this.socket.onerror = (error) => {
            console.error("WebSocket error:", error);
        };
    }

    handleMessage(message) {
        // Route to renderer
        if (message.type === "narrative.text") {
            const agentName = message.sender.agent_id;
            const text = message.payload.content;
            window.renderer.render(agentName, text); 
            window.renderer.addMessageToHistory(agentName, text);
        } else if (message.type === "narrative.chunk") {
            const agentName = message.sender.agent_id;
            const chunk = message.payload.content.content;
            
            // Handle streaming chunks in history
            window.renderer.handleChunk(agentName, chunk);
            
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
            const status = message.payload.content.status;
            const mood = message.payload.content.mood;
            window.renderer.updateAgentStatus(agentId, status, mood);
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

    sendUserMessage(text) {
        if (!text.trim()) return;

        let message;
        if (text.startsWith('/')) {
            // Slash Command Mode: /target_agent command_name args...
            const parts = text.slice(1).split(' ');
            const target = parts[0] || "broadcast";
            const command = parts[1] || "ping";
            const args = parts.slice(2).join(' ');

            message = {
                id: this.generateUUID(),
                timestamp: new Date().toISOString(),
                type: "expert.command",
                sender: { agent_id: "user", role: "user" },
                recipient: { target: target },
                payload: {
                    content: { command: command, args: args },
                    format: "json"
                },
                metadata: { priority: "high", ttl: 5 }
            };
            console.log(`Executing direct command on ${target}:`, command);
        } else {
            // Normal Narrative Mode
            message = {
                id: this.generateUUID(),
                timestamp: new Date().toISOString(),
                type: "narrative.text",
                sender: { agent_id: "user", role: "user" },
                recipient: { target: "broadcast" },
                payload: { content: text, format: "text" },
                metadata: { priority: "normal", ttl: 5 }
            };
        }

        console.log("Sending to H-Core:", message);
        this.socket.send(JSON.stringify(message));
        if (window.renderer) window.renderer.setState('thinking');
    }

    send(type, content) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({ type, content }));
        }
    }
}

// Global instance
window.network = new NetworkClient();
