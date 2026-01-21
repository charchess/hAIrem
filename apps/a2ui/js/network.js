/**
 * hAIrem A2UI Network Client
 * Manages WebSocket connection to H-Core.
 */

class NetworkClient {
    constructor(url = `ws://${window.location.hostname}:8000/ws`) {
        this.url = url;
        this.socket = null;
        this.connect();
    }

    connect() {
        console.log(`Connecting to H-Core at ${this.url}...`);
        this.socket = new WebSocket(this.url);

        this.socket.onopen = () => {
            console.log("Connected to H-Core bus.");
        };

        this.socket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                console.log("H-Link message received:", message);
                this.handleMessage(message);
            } catch (e) {
                console.error("Failed to parse WebSocket message:", e);
            }
        };

        this.socket.onclose = () => {
            console.warn("Disconnected from H-Core. Retrying in 5s...");
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
            window.renderer.render(agentName, text); // Final text with typewriter
        } else if (message.type === "narrative.chunk") {
            const agentName = message.sender.agent_id;
            const chunk = message.payload.content.content;
            
            // Handle streaming chunks in history
            window.renderer.handleChunk(agentName, chunk);
            
        } else if (message.type === "system.log") {


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
                id: crypto.randomUUID(),
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
                id: crypto.randomUUID(),
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
    }

    send(type, content) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({ type, content }));
        }
    }
}

// Global instance
window.network = new NetworkClient();
