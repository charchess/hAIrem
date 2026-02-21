/**
 * hAIrem A2UI Network Client
 * Manages WebSocket connection to H-Core.
 */

class NetworkClient {
    constructor(url = `ws://${window.location.hostname}:${window.location.port}/ws`) {
        this.url = url;
        this.socket = null;
        this.agentMetadata = [];
        this.isFetchingMetadata = false;
        this.connect();
    }

    async fetchGlobalConfig() {
        try {
            const response = await fetch('/api/config');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            
            const modelInput = document.getElementById('global-llm-model');
            const providerSelect = document.getElementById('global-llm-provider');
            
            if (modelInput) modelInput.value = data.llm_model || '';
            if (providerSelect) providerSelect.value = data.llm_provider || 'ollama';
            
            console.log("Global config loaded:", data);
        } catch (e) {
            console.error("Failed to fetch global config:", e);
        }
    }

    async fetchMetadata() {
        if (this.isFetchingMetadata) return;
        this.isFetchingMetadata = true;
        try {
            const response = await fetch('/api/agents');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            
            if (Array.isArray(data)) {
                this.agentMetadata = data;
            } else {
                console.warn("Invalid agent metadata format received");
                this.agentMetadata = [
                    { id: "Renarde", commands: ["ping"] },
                    { id: "system", commands: ["imagine"] }
                ];
            }
            
            console.log("Agent metadata loaded:", this.agentMetadata);
            if (window.renderer) {
                window.renderer.updateAgents(this.agentMetadata);
            }
        } catch (e) {
            console.error("Failed to fetch agent metadata:", e);
            setTimeout(() => {
                this.isFetchingMetadata = false; 
                this.fetchMetadata();
            }, 10000); 
            return; 
        }
        this.isFetchingMetadata = false;
    }

    async fetchHistory() {
        try {
            const response = await fetch('/api/history');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            
            if (data.status === "connecting") {
                console.log("Database still connecting, retrying history in 5s...");
                setTimeout(() => this.fetchHistory(), 5000);
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
        if (window.renderer && window.renderer.updateSystemStatus) {
            window.renderer.updateSystemStatus('ws', 'checking');
        }
        
        this.socket = new WebSocket(this.url);

        this.socket.onopen = () => {
            console.log("Connected to H-Core bus.");
            if (window.renderer && window.renderer.updateSystemStatus) {
                window.renderer.updateSystemStatus('ws', 'ok');
            }
            
            // Sync initial log level
            const savedLevel = localStorage.getItem('hairem_log_level') || 'INFO';
            this.send('system.config_update', { log_level: savedLevel });

            this.fetchMetadata();
            this.fetchHistory();
            this.fetchGlobalConfig();

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
            if (window.renderer && window.renderer.setReady) {
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
        // console.log(`NETWORK: Received ${message.type}`);
        
        if ((message.type === "narrative.text" || message.type === "narrative.chunk" || message.type === "expert.response") && window.renderer && window.renderer.setProcessingState) {
            window.renderer.setProcessingState(false);
        }

        if (message.type === "narrative.text") {
            if (message.sender && message.sender.agent_id === "user") return;
            if (window.speechQueue) {
                window.speechQueue.enqueue(message);
            } else if (window.renderer && window.renderer.render) {
                window.renderer.render(message.sender.agent_id, message.payload.content); 
                window.renderer.addMessageToHistory(message.sender.agent_id, message.payload.content);
            }
        } else if (message.type === "system.heartbeat") {
            // Signal WebSocket is OK upon receiving heartbeat
            if (window.renderer) window.renderer.updateSystemStatus('ws', 'ok');

            const payload = message.payload.content;
            if (!payload) return;

            // 1. Update Health Indicators
            if (payload.health) {
                Object.entries(payload.health).forEach(([comp, status]) => {
                    if (window.renderer && window.renderer.updateSystemStatus) {
                        window.renderer.updateSystemStatus(comp, status);
                    }
                });
            }

            // 2. Update Agents Discovery & Stats
            if (payload.agents) {
                if (window.renderer && window.renderer.updateAgents) {
                    const agentsArray = Object.entries(payload.agents).map(([id, data]) => ({
                        id: id,
                        ...data
                    }));
                    window.renderer.updateAgents(agentsArray);
                }
            }
        } else if (message.type === "system.log") {
            if (window.renderer && window.renderer.addLog) {
                window.renderer.addLog(message.payload.content);
            }
        } else if (message.type === "visual.asset") {
            const payload = message.payload.content;
            let url = payload.url;
            if (url.startsWith('file:///media/generated/')) url = url.replace('file:///media/generated/', '/media/');
            else if (url.includes('/media/generated/')) url = '/media/' + url.split('/media/generated/')[1];
            if (url.startsWith('http://h-bridge:8000/')) url = url.replace('http://h-bridge:8000/', '/');
            url += (url.includes('?') ? '&' : '?') + 't=' + Date.now();
            
            if (window.renderer && window.renderer.renderVisualAsset) {
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
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    send(type, content) {
        const message = {
            id: this.generateUUID(),
            timestamp: new Date().toISOString(),
            type: type,
            sender: { agent_id: "user", role: "user" },
            recipient: { target: "system" },
            payload: { content: content } // Proper HLink wrapper
        };
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(message));
        }
    }

    sendUserMessage(text, target = "broadcast") {
        if (!text.trim()) return;
        const currentRoom = localStorage.getItem('hairem_device_room') || 'Salon';
        const message = {
            id: this.generateUUID(),
            timestamp: new Date().toISOString(),
            type: "narrative.text",
            sender: { agent_id: "user", role: "user" },
            recipient: { target: target },
            payload: { 
                content: text, 
                format: "text",
                room_id: currentRoom 
            },
            metadata: { priority: "normal", ttl: 5 }
        };

        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(message));
        }
    }

    toggleAgent(agentId, isActive) {
        this.send("agent.config_update", { agent_id: agentId, active: isActive });
    }

    toggleSkill(agentId, skillName, isActive) {
        this.send("agent.config_update", { 
            agent_id: agentId, 
            skill_update: { name: skillName, active: isActive } 
        });
    }
}

window.network = new NetworkClient();
