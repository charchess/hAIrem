/**
 * hAIrem A2UI Renderer
 * Handles layer composition, visual states, and chat history.
 */

const States = {
    IDLE: 'idle',
    LISTENING: 'listening',
    THINKING: 'thinking',
    SPEAKING: 'speaking'
};

class Renderer {
    constructor() {
        this.layers = {
            bg: document.getElementById('layer-bg'),
            body: document.getElementById('layer-agent-body'),
            face: document.getElementById('layer-agent-face'),
            text: document.getElementById('dialogue-text'),
            name: document.getElementById('agent-name'),
            stage: document.getElementById('the-stage'),
            history: document.getElementById('chat-history')
        };
        this.currentState = States.IDLE;
        this.typewriterInterval = null;
        this.activeBubble = null;
    }

    /**
     * Adds a new message bubble to the history.
     */
    addMessageToHistory(senderName, text, isUser = false) {
        const bubble = document.createElement('div');
        bubble.className = `message-bubble ${isUser ? 'bubble-user' : 'bubble-agent'}`;
        
        const label = document.createElement('strong');
        label.textContent = `${senderName}: `;
        bubble.appendChild(label);

        const content = document.createElement('span');
        content.className = 'bubble-content';
        content.textContent = text;
        bubble.appendChild(content);

        this.layers.history.appendChild(bubble);
        this.scrollToBottom();
        return bubble;
    }

    scrollToBottom() {
        this.layers.history.scrollTop = this.layers.history.scrollHeight;
    }

    /**
     * Appends a chunk to the active bubble or creates a new one if needed.
     */
    handleChunk(agentName, chunk) {
        if (!this.activeBubble || this.activeBubble.dataset.sender !== agentName) {
            this.activeBubble = this.addMessageToHistory(agentName, "");
            this.activeBubble.dataset.sender = agentName;
        }
        const contentSpan = this.activeBubble.querySelector('.bubble-content');
        contentSpan.textContent += chunk;
        this.scrollToBottom();
    }

    setState(state) {
        console.log(`Transitioning to state: ${state}`);
        this.currentState = state;
        this.layers.body.classList.remove('pensive', 'listening', 'speaking');
        this.layers.stage.classList.remove('state-thinking', 'state-listening');

        switch (state) {
            case States.THINKING:
                this.layers.body.classList.add('pensive');
                this.layers.stage.classList.add('state-thinking');
                break;
            case States.LISTENING:
                this.layers.stage.classList.add('state-listening');
                break;
            case States.SPEAKING:
                this.layers.body.classList.add('speaking');
                break;
        }
    }

    typewrite(text, speed = 30) {
        if (this.typewriterInterval) clearInterval(this.typewriterInterval);
        
        this.layers.text.textContent = "";
        let i = 0;
        this.setState(States.SPEAKING);

        this.typewriterInterval = setInterval(() => {
            if (i < text.length) {
                this.layers.text.textContent += text.charAt(i);
                i++;
            } else {
                clearInterval(this.typewriterInterval);
                this.setState(States.IDLE);
                this.activeBubble = null; // Clear active bubble after full narrative
            }
        }, speed);
    }

    render(agentName, text, assets = {}) {
        if (agentName) this.layers.name.textContent = agentName;
        
        if (text) {
            this.typewrite(text);
            // We only add to history once the message is complete/sent
            // (Chunks are added separately via handleChunk)
        }

        if (assets.body) this.updateLayer(this.layers.body, assets.body);
        if (assets.face) this.updateLayer(this.layers.face, assets.face);
        if (assets.bg) this.updateLayer(this.layers.bg, assets.bg);
    }

    updateLayer(el, src) {
        el.style.opacity = 0;
        setTimeout(() => {
            if (src.startsWith('#')) {
                el.style.backgroundImage = 'none';
                el.style.backgroundColor = src;
            } else {
                el.style.backgroundImage = `url('${src}')`;
                el.style.backgroundColor = 'transparent';
            }
            el.style.opacity = 1;
        }, 150);
    }
}

window.renderer = new Renderer();

window.onload = () => {
    renderer.render("Renarde", "Historique de chat activé. Je me souviendrai de nos échanges.", {
        body: "#2c3e50",
        face: "#27ae60",
        bg: "#1a1a1a"
    });

    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');

    const sendMessage = () => {
        const text = chatInput.value;
        if (text.trim()) {
            window.network.sendUserMessage(text);
            // Add to history immediately for visual feedback
            window.renderer.addMessageToHistory("Moi", text, true);
            chatInput.value = "";
        }
    };

    if (chatSend) chatSend.onclick = sendMessage;
    if (chatInput) {
        chatInput.onkeydown = (e) => {
            if (e.key === 'Enter') sendMessage();
        };
    }
};
