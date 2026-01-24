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
            history: document.getElementById('chat-history'),
            logs: document.getElementById('log-content'),
            logViewer: document.getElementById('log-viewer'),
            input: document.getElementById('chat-input'),
            send: document.getElementById('chat-send')
        };
        this.currentState = States.IDLE;
        this.typewriterInterval = null;
        this.activeBubble = null;
        this.isLogPaused = false;
        this.agents = {}; 
        this.activeView = 'stage';

        this.poseMap = {
            'idle': 'neutral', 'happy': 'happy', 'sad': 'sad', 'angry': 'angry',
            'alert': 'alert', 'emergency': 'emergency', 'confused': 'confused',
            'thinking': 'thinking', 'shy': 'shy', 'glitch': 'glitch'
        };
        
        console.log("Renderer initialized.");
        this.setReady(false);
    }

    setReady(ready) {
        console.log("Setting UI Ready State:", ready);
        if (this.layers.input) this.layers.input.disabled = !ready;
        if (this.layers.send) {
            this.layers.send.disabled = !ready;
            this.layers.send.style.opacity = ready ? "1" : "0.3";
            this.layers.send.style.cursor = ready ? "pointer" : "not-allowed";
        }
    }

    extractPose(text) {
        if (!text) return { cleanedText: "", pose: null };
        const poseRegex = /\[pose:([a-z0-9_-]+)\]/i;
        const match = text.match(poseRegex);
        if (match) {
            const poseName = match[1].toLowerCase();
            const cleanedText = text.replace(poseRegex, '').trim();
            return { cleanedText, pose: poseName };
        }
        return { cleanedText: text, pose: null };
    }

    renderHistory(messages) {
        if (!messages) return;
        messages.forEach(msg => {
            const sender = msg.sender ? msg.sender.agent_id : "unknown";
            const content = msg.payload ? msg.payload.content : "";
            if (msg.type === "narrative.text" || msg.type === "expert.response") {
                const text = typeof content === 'object' ? (content.result || content.error || JSON.stringify(content)) : content;
                this.addMessageToHistory(sender === "user" ? "Moi" : sender, text, sender === "user");
            }
        });
    }

    updateAgentCards(agentList) {
        if (!agentList) return;
        agentList.forEach(agent => {
            if (!agent || !agent.id) return;
            if (!this.agents[agent.id]) {
                this.agents[agent.id] = { id: agent.id, status: 'idle', mood: 'neutral', commands: agent.commands || [] };
            } else {
                this.agents[agent.id].commands = agent.commands || this.agents[agent.id].commands;
            }
        });
        this.renderAgentGrid();
    }

    updateAgentStatus(agentId, status, mood = null) {
        if (!this.agents[agentId]) {
            this.agents[agentId] = { id: agentId, status: status, mood: mood || 'neutral', commands: [] };
        } else {
            this.agents[agentId].status = status;
            if (mood) this.agents[agentId].mood = mood;
        }
        this.renderAgentGrid();
    }

    renderAgentGrid() {
        const grid = document.getElementById('agent-grid');
        if (!grid) return;
        grid.innerHTML = '';
        Object.values(this.agents).forEach(agent => {
            const card = document.createElement('div');
            card.className = 'agent-card';
            const moodMap = { 'happy': '😊', 'pensive': '🤔', 'neutral': '😐', 'angry': '😠', 'surprised': '😲', 'technical': '⚙️' };
            const moodIcon = moodMap[agent.mood] || '😐';
            card.innerHTML = `
                <div class="agent-card-header">
                    <div class="agent-info"><span class="agent-card-name">${agent.id}</span><span class="agent-card-role">Agent Active</span></div>
                    <span class="agent-mood" title="${agent.mood}">${moodIcon}</span>
                </div>
                <div><span class="agent-status-badge status-${agent.status}">${agent.status}</span></div>
                <div class="agent-capabilities">${agent.commands.map(cmd => `<span class="capability-tag">${cmd}</span>`).join('')}</div>
            `;
            grid.appendChild(card);
        });
    }

    addLog(text) {
        if (!this.layers.logs) return;
        const line = document.createElement('div');
        line.className = 'log-line';
        if (text.includes('ERROR')) line.classList.add('log-error');
        else if (text.includes('WARNING') || text.includes('WARN')) line.classList.add('log-warn');
        else if (text.includes('DEBUG')) line.classList.add('log-debug');
        else line.classList.add('log-info');
        const timestamp = new Date().toLocaleTimeString();
        line.innerHTML = `<span style="color:#666">[${timestamp}]</span> ${text}`;
        this.layers.logs.appendChild(line);
        if (!this.isLogPaused) this.layers.logs.scrollTop = this.layers.logs.scrollHeight;
        if (line.classList.contains('log-error')) this.layers.logViewer.classList.remove('hidden');
    }

    toggleLogViewer() { if (this.layers.logViewer) this.layers.logViewer.classList.toggle('hidden'); }

    addMessageToHistory(senderName, text, isUser = false) {
        const { cleanedText } = this.extractPose(text);
        const bubble = document.createElement('div');
        bubble.className = `message-bubble ${isUser ? 'bubble-user' : 'bubble-agent'}`;
        const label = document.createElement('strong');
        label.textContent = `${senderName}: `;
        bubble.appendChild(label);
        const content = document.createElement('span');
        content.className = 'bubble-content';
        content.textContent = cleanedText;
        bubble.appendChild(content);
        this.layers.history.appendChild(bubble);
        this.scrollToBottom();
        return bubble;
    }

    scrollToBottom() { if (this.layers.history) this.layers.history.scrollTop = this.layers.history.scrollHeight; }

    handleChunk(agentName, chunk) {
        if (!this.activeBubble || this.activeBubble.dataset.sender !== agentName) {
            this.activeBubble = this.addMessageToHistory(agentName, "");
            this.activeBubble.dataset.sender = agentName;
        }
        const contentSpan = this.activeBubble.querySelector('.bubble-content');
        contentSpan.textContent += chunk;
        const { cleanedText, pose } = this.extractPose(contentSpan.textContent);
        if (pose) {
            contentSpan.textContent = cleanedText;
            this.render(agentName, `[pose:${pose}]`);
        }
        this.scrollToBottom();
    }

    setState(state) {
        this.currentState = state;
        this.layers.body.classList.remove('pensive', 'listening', 'speaking');
        this.layers.stage.classList.remove('state-thinking', 'state-listening');
        
        // Story 11.4: Dynamic control locking
        const isBusy = (state === States.THINKING || state === States.SPEAKING);
        if (this.layers.input) this.layers.input.disabled = isBusy;
        if (this.layers.send) {
            this.layers.send.disabled = isBusy;
            this.layers.send.style.opacity = isBusy ? "0.5" : "1";
            this.layers.send.style.backgroundColor = isBusy ? "#555" : "#00ffcc";
        }

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
                this.activeBubble = null;
            }
        }, speed);
    }

    render(agentName, text, assets = {}) {
        if (agentName) this.layers.name.textContent = agentName;
        
        const { cleanedText, pose } = this.extractPose(text);
        
        if (agentName) {
            let agentId = agentName.toLowerCase();
            // Story 11.4: Redirect Renarde to test_model
            if (agentId === 'renarde') agentId = 'test_model';
            
            const suffix = (pose && this.poseMap[pose]) ? this.poseMap[pose] : 'neutral';
            // Correct Path: /public/assets/agents/test_model/test_model_neutral_01.png
            const assetUrl = `/public/assets/agents/${agentId}/${agentId}_${suffix}_01.png`;
            
            console.log(`DEBUG RENDER: Agent=${agentName}, Pose=${suffix}, URL=${assetUrl}`);
            assets.body = assetUrl;
        }

        if (text) this.typewrite(cleanedText);
        if (assets.body) this.updateLayer(this.layers.body, assets.body);
        if (assets.bg) this.updateLayer(this.layers.bg, assets.bg);
    }

    updateLayer(el, src) {
        if (!el) return;
        console.log(`DEBUG LAYER: Updating ${el.id} with ${src}`);
        el.style.opacity = 0;
        const img = new Image();
        img.onload = () => {
            el.style.backgroundImage = `url('${src}')`;
            el.style.opacity = 1;
            console.log(`DEBUG LAYER: Success ${el.id}`);
        };
        img.onerror = () => { 
            console.error(`DEBUG LAYER: Failed to load ${src}`);
            el.style.opacity = 1; 
        };
        img.src = src;
    }

    switchView(viewName) {
        if (this.activeView === viewName) return;
        this.activeView = viewName;
        document.getElementById('nav-stage').classList.toggle('active', viewName === 'stage');
        document.getElementById('nav-dashboard').classList.toggle('active', viewName === 'dashboard');
        if (viewName === 'dashboard') {
            this.setStageVisibility(false);
            this.setDashboardVisibility(true);
        } else {
            this.setStageVisibility(true);
            this.setDashboardVisibility(false);
        }
    }

    setStageVisibility(visible) {
        const layers = [this.layers.bg, this.layers.body, this.layers.face, this.layers.history, document.getElementById('dialogue-container')];
        layers.forEach(el => { if (el) el.style.opacity = visible ? '1' : '0'; });
    }

    setDashboardVisibility(visible) {
        const dashboard = document.getElementById('agent-dashboard');
        if (dashboard) {
            dashboard.classList.toggle('hidden', !visible);
            if (visible) this.renderAgentGrid();
        }
    }
}

window.renderer = new Renderer();

window.onload = () => {
    window.network.fetchMetadata();
    window.network.fetchHistory();

    renderer.render("Renarde", "Système hAIrem initialisé. [pose:idle]", {
        bg: "/public/assets/backgrounds/background.png"
    });

    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');
    const suggestionMenu = document.getElementById('suggestion-menu');

    const sendMessage = () => {
        const text = chatInput.value;
        if (text.trim()) {
            window.network.sendUserMessage(text);
            window.renderer.addMessageToHistory("Moi", text, true);
            chatInput.value = "";
            suggestionMenu.classList.add('hidden');
        }
    };

    if (chatSend) chatSend.onclick = sendMessage;
    
    if (chatInput) {
        let selectedIndex = -1;
        let currentSuggestions = [];

        const renderSuggestions = (suggestions) => {
            currentSuggestions = suggestions;
            if (suggestions.length === 0) {
                suggestionMenu.classList.add('hidden');
                return;
            }
            suggestionMenu.innerHTML = '';
            suggestions.forEach((s, index) => {
                const item = document.createElement('div');
                item.className = 'suggestion-item' + (index === selectedIndex ? ' active' : '');
                item.innerHTML = `<span>${s.text}</span><span class="type-label">${s.type}</span>`;
                item.onmousedown = (e) => { e.preventDefault(); selectSuggestion(index); };
                suggestionMenu.appendChild(item);
            });
            suggestionMenu.classList.remove('hidden');
        };

        const selectSuggestion = (index) => {
            const s = currentSuggestions[index];
            if (!s) return;
            const text = chatInput.value;
            const parts = text.split(' ');
            if (s.type === 'agent') {
                chatInput.value = `/${s.text} `;
                selectedIndex = -1;
                updateSuggestions(); 
            } else {
                chatInput.value = `/${parts[0].slice(1)} ${s.text} `;
                suggestionMenu.classList.add('hidden');
                selectedIndex = -1;
            }
            chatInput.focus();
        };

        const updateSuggestions = () => {
            const text = chatInput.value;
            if (text.startsWith('/')) {
                const parts = text.slice(1).split(' ');
                const agentQuery = parts[0].toLowerCase();
                const commandQuery = parts[1] ? parts[1].toLowerCase() : "";
                let suggestions = [];
                if (parts.length <= 1) {
                    suggestions = (window.network.agentMetadata || [])
                        .filter(a => a && a.id && a.id.toLowerCase().startsWith(agentQuery))
                        .map(a => ({ text: a.id, type: 'agent' }));
                } else {
                    const agent = (window.network.agentMetadata || []).find(a => a && a.id && a.id.toLowerCase() === agentQuery);
                    if (agent) {
                        suggestions = (agent.commands || [])
                            .filter(c => c.toLowerCase().startsWith(commandQuery))
                            .map(c => ({ text: c, type: 'command' }));
                    }
                }
                renderSuggestions(suggestions);
            } else {
                suggestionMenu.classList.add('hidden');
            }
        };

        chatInput.oninput = updateSuggestions;
        
        chatInput.onkeydown = (e) => {
            const isMenuOpen = !suggestionMenu.classList.contains('hidden');
            if (isMenuOpen) {
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    selectedIndex = (selectedIndex + 1) % currentSuggestions.length;
                    renderSuggestions(currentSuggestions);
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    selectedIndex = (selectedIndex - 1 + currentSuggestions.length) % currentSuggestions.length;
                    renderSuggestions(currentSuggestions);
                } else if (e.key === 'Tab' || e.key === 'Enter') {
                    e.preventDefault();
                    selectSuggestion(selectedIndex >= 0 ? selectedIndex : 0);
                } else if (e.key === 'Escape') {
                    suggestionMenu.classList.add('hidden');
                }
            } else if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        };
    }

    // Global shortcuts
    window.addEventListener('keydown', (e) => {
        if (document.activeElement.tagName === 'TEXTAREA' || document.activeElement.tagName === 'INPUT') return;
        if (e.key.toLowerCase() === 'l') renderer.toggleLogViewer();
    });

    document.getElementById('nav-stage').onclick = () => renderer.switchView('stage');
    document.getElementById('nav-dashboard').onclick = () => renderer.switchView('dashboard');
    document.getElementById('close-logs').onclick = () => renderer.toggleLogViewer();
};
