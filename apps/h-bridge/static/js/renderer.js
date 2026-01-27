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
            send: document.getElementById('chat-send'),
            crewPanel: document.getElementById('crew-panel'),
            adminPanel: document.getElementById('admin-panel')
        };
        this.currentState = States.IDLE;
        this.typewriterInterval = null;
        this.activeBubble = null;
        this.streamingBubbles = {};
        this.isLogPaused = false;
        this.agents = {}; 
        this.activeView = 'stage';
        this.activeSpeakerId = null;

        this.systemStatus = {
            ws: 'checking',
            redis: 'checking',
            llm: 'checking',
            brain: 'checking'
        };

        this.poseMap = {
            'idle': 'neutral',
            'neutral': 'neutral',
            'happy': 'happy',
            'joy': 'happy',
            'smile': 'happy',
            'delighted': 'happy',
            'sad': 'sad',
            'triste': 'sad',
            'crying': 'sad',
            'depressed': 'sad',
            'angry': 'angry',
            'colere': 'angry',
            'furious': 'angry',
            'alert': 'alert',
            'surprise': 'alert',
            'shocked': 'alert',
            'emergency': 'emergency',
            'fear': 'emergency',
            'peur': 'emergency',
            'confused': 'confused',
            'disgust': 'confused',
            'skeptical': 'confused',
            'thinking': 'thinking',
            'pensive': 'thinking',
            'shy': 'shy',
            'blush': 'shy',
            'timid': 'shy',
            'seductive': 'shy',
            'flirty': 'happy',
            'glitch': 'glitch',
            'error': 'glitch'
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
        
        // 1. Identify complete tags for visual triggering
        const poseRegex = /\[pose:([a-z0-9_-]+)\]/gi;
        let poseName = null;
        let match;
        while ((match = poseRegex.exec(text)) !== null) {
            poseName = match[1].toLowerCase();
        }
        
        // 2. Hide both complete and partial tags from display (Story 19.3)
        // Matches [pose: followed by any valid chars, ending with ] OR end of string
        const hideRegex = /\[pose:[a-z0-9_-]*\]?/gi;
        const cleanedText = text.replace(hideRegex, '').trim();
        
        return { cleanedText, pose: poseName };
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
        
        const select = document.getElementById('target-agent-select');
        if (select) {
            const currentVal = select.value;
            select.innerHTML = '<option value="broadcast">Tous</option>';
            agentList.forEach(agent => {
                // Default to true if not specified
                const personified = agent.personified !== false;
                if (personified) {
                    const opt = document.createElement('option');
                    opt.value = agent.id;
                    opt.textContent = agent.id;
                    select.appendChild(opt);
                }
            });
            select.value = currentVal;
        }

        agentList.forEach(agent => {
            if (!agent || !agent.id) return;
            const personified = agent.personified !== false;
            
            if (!this.agents[agent.id]) {
                this.agents[agent.id] = { 
                    id: agent.id, 
                    status: 'idle', 
                    mood: 'neutral', 
                    personified: personified,
                    commands: agent.commands || [],
                    prompt_tokens: agent.prompt_tokens || 0,
                    completion_tokens: agent.completion_tokens || 0,
                    total_tokens: agent.total_tokens || 0
                };
            } else {
                this.agents[agent.id].commands = agent.commands || this.agents[agent.id].commands;
                this.agents[agent.id].personified = personified;
                if (agent.prompt_tokens !== undefined) this.agents[agent.id].prompt_tokens = agent.prompt_tokens;
                if (agent.completion_tokens !== undefined) this.agents[agent.id].completion_tokens = agent.completion_tokens;
                if (agent.total_tokens !== undefined) this.agents[agent.id].total_tokens = agent.total_tokens;
            }
        });
        this.renderAgentGrid();
    }

    updateAgentStatus(agentId, status, mood = null, pTokens = null, cTokens = null, tTokens = null, commands = null) {
        if (!this.agents[agentId]) {
            this.agents[agentId] = { 
                id: agentId, 
                status: status, 
                mood: mood || 'neutral', 
                commands: commands || [],
                prompt_tokens: pTokens || 0,
                completion_tokens: cTokens || 0,
                total_tokens: tTokens || 0
            };
        } else {
            if (this.agents[agentId].status !== status) {
                this.triggerStatusFlash(agentId);
            }
            this.agents[agentId].status = status;
            if (mood) this.agents[agentId].mood = mood;
            if (commands) this.agents[agentId].commands = commands;
            if (pTokens !== undefined && pTokens !== null) this.agents[agentId].prompt_tokens = pTokens;
            if (cTokens !== undefined && cTokens !== null) this.agents[agentId].completion_tokens = cTokens;
            if (tTokens !== undefined && tTokens !== null) this.agents[agentId].total_tokens = tTokens;
        }
        this.renderAgentGrid();
    }

    triggerStatusFlash(agentId) {
        this.agents[agentId].lastUpdate = Date.now();
    }

    setActiveSpeaker(agentId) {
        this.activeSpeakerId = agentId;
        this.renderAgentGrid();
    }

    updateSystemStatus(component, status) {
        // Map status names to CSS classes
        const statusMap = {
            'online': 'ok',
            'ok': 'ok',
            'error': 'error',
            'checking': 'checking'
        };
        const cssClass = statusMap[status] || status;
        
        this.systemStatus[component] = cssClass;
        const el = document.getElementById(`status-${component}`);
        if (el) {
            el.className = `status-indicator ${cssClass}`;
            el.title = `${component.toUpperCase()}: ${status.toUpperCase()}`;
        }
        const elAdmin = document.getElementById(`status-${component}-admin`);
        if (elAdmin) {
            elAdmin.className = `status-indicator ${cssClass}`;
            elAdmin.textContent = status.toUpperCase();
        }

        if (component === 'ws') {
            const isDown = status === 'error';
            if (this.layers.input) {
                this.layers.input.disabled = isDown;
                this.layers.input.placeholder = isDown ? "Connection lost. Reconnecting..." : "Parler aux agents...";
            }
            if (this.layers.send) this.layers.send.disabled = isDown;
        }
    }

    setProcessingState(isProcessing) {
        if (this.layers.send) {
            this.layers.send.classList.toggle('loading', isProcessing);
            this.layers.send.textContent = isProcessing ? "..." : "Envoyer";
        }
    }

    switchView(viewName) {
        if (viewName === 'stage') {
            this.setPanelVisibility('crew', false);
            this.setPanelVisibility('admin', false);
            this.setStageVisibility(true);
        } else if (viewName === 'crew') {
            this.setPanelVisibility('admin', false);
            this.setPanelVisibility('crew', true);
            this.renderAgentGrid();
        } else if (viewName === 'admin') {
            this.setPanelVisibility('crew', false);
            this.setPanelVisibility('admin', true);
        }
    }

    setPanelVisibility(panelName, visible) {
        const panel = panelName === 'crew' ? this.layers.crewPanel : this.layers.adminPanel;
        if (panel) {
            panel.classList.toggle('hidden', !visible);
        }
    }

    setStageVisibility(visible) {
        const stageUI = [this.layers.history, document.getElementById('dialogue-container'), document.getElementById('chat-input-container')];
        stageUI.forEach(el => { if (el) el.style.opacity = visible ? '1' : '0.2'; });
    }

    renderAgentGrid() {
        const grid = document.getElementById('agent-grid');
        if (!grid) return;
        grid.innerHTML = '';
        Object.values(this.agents).forEach(agent => {
            const isActive = this.activeSpeakerId && (agent.id === this.activeSpeakerId);
            const isFresh = agent.lastUpdate && (Date.now() - agent.lastUpdate < 500);
            const card = document.createElement('div');
            card.className = `agent-card ${isActive ? 'active-speaker' : ''}`;
            const moodMap = { 'happy': '😊', 'pensive': '🤔', 'neutral': '😐', 'angry': '😠', 'surprised': '😲', 'technical': '⚙️' };
            const moodIcon = moodMap[agent.mood] || '😐';
            const badgeClass = `agent-status-badge status-${agent.status} ${isFresh ? 'flash-update' : ''}`;
            const isEnabled = agent.active !== false;
            card.innerHTML = `
                <div class="agent-card-header">
                    <div class="agent-info">
                        <span class="agent-card-name">${agent.id}</span>
                        <span class="agent-card-role">Agent Active</span>
                    </div>
                    <span class="agent-mood" title="Current mood: ${agent.mood}">${moodIcon}</span>
                </div>
                <div class="agent-controls">
                    <span class="${badgeClass}">${agent.status}</span>
                    <label class="toggle-switch">
                        <input type="checkbox" ${isEnabled ? 'checked' : ''} onchange="window.network.toggleAgent('${agent.id}', this.checked)">
                        <span class="slider round"></span>
                    </label>
                </div>
                <div class="agent-stats">
                    <div class="stat-tag" title="Tokens IN (Prompt)">IN: ${agent.prompt_tokens || 0}</div>
                    <div class="stat-tag" title="Tokens OUT (Completion)">OUT: ${agent.completion_tokens || 0}</div>
                    <div class="stat-tag" title="Total Tokens">TOT: ${agent.total_tokens || 0}</div>
                </div>
                <div class="agent-capabilities">${agent.commands.map(cmd => `<span class="capability-tag">${cmd}</span>`).join('')}</div>
            `;
            if (!isEnabled) card.classList.add('disabled');
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

    clearLogs() {
        if (this.layers.logs) {
            this.layers.logs.innerHTML = "";
            this.addLog("Logs cleared.");
        }
    }

    togglePauseLogs() {
        this.isLogPaused = !this.isLogPaused;
        const btn = document.getElementById('pause-logs');
        if (btn) {
            btn.textContent = this.isLogPaused ? "▶️" : "⏸";
            btn.title = this.isLogPaused ? "Resume scrolling" : "Pause scrolling";
        }
        this.addLog(this.isLogPaused ? "Log scrolling PAUSED." : "Log scrolling RESUMED.");
    }

    addMessageToHistory(senderName, text, isUser = false, msgId = null) {
        if (msgId && document.getElementById(`msg-${msgId}`)) {
            const existing = document.getElementById(`msg-${msgId}`);
            const content = existing.querySelector('.bubble-content');
            if (content) content.textContent = this.extractPose(text).cleanedText;
            this.scrollToBottom();
            return existing;
        }
        const { cleanedText } = this.extractPose(text);
        const bubble = document.createElement('div');
        bubble.className = `message-bubble ${isUser ? 'bubble-user' : 'bubble-agent'}`;
        if (msgId) bubble.id = `msg-${msgId}`;
        const label = document.createElement('strong');
        label.textContent = `${senderName}: `;
        bubble.appendChild(label);
        const content = document.createElement('span');
        content.className = 'bubble-content';
        content.textContent = cleanedText;
        bubble.appendChild(content);
        const timestamp = document.createElement('span');
        timestamp.className = 'bubble-timestamp';
        timestamp.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        bubble.appendChild(timestamp);
        this.layers.history.appendChild(bubble);
        this.scrollToBottom();
        return bubble;
    }

    scrollToBottom() { if (this.layers.history) this.layers.history.scrollTop = this.layers.history.scrollHeight; }

    handleChunk(message) {
        const agentName = message.sender.agent_id;
        const chunk = message.payload.content.content;
        const correlationId = message.metadata ? message.metadata.correlation_id : null;
        const responseId = correlationId ? `${agentName}-${correlationId}` : null;
        
        if (responseId) {
            if (!this.streamingBubbles[responseId]) {
                this.streamingBubbles[responseId] = this.addMessageToHistory(agentName, "", false, responseId);
                this.streamingBubbles[responseId].rawText = ""; // Story 19.3: Store raw text for tag processing
            }
            
            const bubble = this.streamingBubbles[responseId];
            const contentSpan = bubble.querySelector('.bubble-content');
            
            bubble.rawText += chunk;
            const { cleanedText, pose } = this.extractPose(bubble.rawText);
            
            // Always display the cleaned version
            contentSpan.textContent = cleanedText;
            
            if (pose) {
                this.render(agentName, `[pose:${pose}]`, {}, true); 
            }
        }
        this.scrollToBottom();
    }

    setState(state) {
        this.currentState = state;
        this.layers.body.classList.remove('pensive', 'listening', 'speaking');
        this.layers.stage.classList.remove('state-thinking', 'state-listening');
        const isBusy = (state === States.THINKING || state === States.SPEAKING);
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
            }
        }, speed);
    }

    updateLayer(el, src, fallbackSrc = null) {
        if (!el) return;
        const img = new Image();
        img.onload = () => {
            el.style.backgroundImage = `url('${src}')`;
            el.style.opacity = 1;
        };
        img.onerror = () => { 
            if (fallbackSrc && src !== fallbackSrc) {
                this.updateLayer(el, fallbackSrc);
            } else {
                el.style.opacity = 1; 
            }
        };
        img.src = src;
    }

    render(agentName, text, assets = {}, skipTypewriter = false) {
        if (agentName) this.layers.name.textContent = agentName;
        const { cleanedText, pose } = this.extractPose(text);
        const agentData = this.agents[agentName];
        
        // Story 19.3 FIX: Default to true if agentData exists but personified is undefined
        const isPersonified = (agentData && agentData.personified !== undefined) ? agentData.personified : true;
        
        let fallbackBody = null;
        if (agentName && isPersonified) {
            let agentId = agentName.toLowerCase();
            if (agentId === 'renarde') agentId = 'test_model';
            const suffix = (pose && this.poseMap[pose]) ? this.poseMap[pose] : 'neutral';
            const assetUrl = `/public/assets/agents/${agentId}/${agentId}_${suffix}_01.png`;
            fallbackBody = `/public/assets/agents/${agentId}/${agentId}_neutral_01.png`;
            assets.body = assetUrl;
            if (this.layers.body) this.layers.body.style.display = 'block';
            if (this.layers.face) this.layers.face.style.display = 'block';
        } else if (agentName && !isPersonified) {
            if (this.layers.body) this.layers.body.style.display = 'none';
            if (this.layers.face) this.layers.face.style.display = 'none';
        }
        if (cleanedText && !skipTypewriter) this.typewrite(cleanedText);
        if (assets.body && isPersonified) this.updateLayer(this.layers.body, assets.body, fallbackBody);
        if (assets.bg) this.updateLayer(this.layers.bg, assets.bg);
        else if (!this.layers.bg.style.backgroundImage) {
            this.updateLayer(this.layers.bg, "/public/assets/backgrounds/background.png");
        }
    }
}

window.renderer = new Renderer();

window.onload = () => {
    window.network.fetchHistory();
    renderer.render("Renarde", "Système hAIrem initialisé. [pose:idle]", {
        bg: "/public/assets/backgrounds/background.png"
    });

    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');
    const targetSelect = document.getElementById('target-agent-select');
    const suggestionMenu = document.getElementById('suggestion-menu');

    const sendMessage = () => {
        try {
            const text = chatInput.value;
            const target = targetSelect ? targetSelect.value : 'broadcast';
            console.log("UI_SEND: Attempting to send", text, "to", target);
            if (text.trim()) {
                window.network.sendUserMessage(text, target);
                window.renderer.addMessageToHistory("Moi", text, true);
                chatInput.value = "";
                suggestionMenu.classList.add('hidden');
            }
        } catch (e) {
            console.error("UI_SEND_ERROR:", e);
            alert("Erreur lors de l'envoi : " + e.message);
        }
    };

    if (targetSelect) {
        targetSelect.onchange = (e) => {
            const target = e.target.value;
            chatInput.placeholder = target === 'broadcast' ? "Parler à tous..." : `Parler à ${target}...`;
        };
    }

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

    window.addEventListener('keydown', (e) => {
        if (document.activeElement.tagName === 'TEXTAREA' || document.activeElement.tagName === 'INPUT') return;
        if (e.key.toLowerCase() === 'l') renderer.toggleLogViewer();
        if (e.key === 'Escape') renderer.switchView('stage');
    });

    document.getElementById('nav-admin').onclick = () => renderer.switchView('admin');
    document.getElementById('nav-crew').onclick = () => renderer.switchView('crew');
    document.getElementById('close-crew').onclick = () => renderer.switchView('stage');
    document.getElementById('close-admin').onclick = () => renderer.switchView('stage');
    document.getElementById('close-logs').onclick = () => renderer.toggleLogViewer();
    document.getElementById('clear-logs').onclick = () => renderer.clearLogs();
    document.getElementById('pause-logs').onclick = () => renderer.togglePauseLogs();

    const logSelect = document.getElementById('log-level-select');
    if (logSelect) {
        const savedLevel = localStorage.getItem('hairem_log_level') || 'INFO';
        logSelect.value = savedLevel;
        logSelect.onchange = (e) => {
            const level = e.target.value;
            localStorage.setItem('hairem_log_level', level);
            window.network.send('system.config_update', { log_level: level });
        };
    }

    document.addEventListener('click', (e) => {
        const adminPanel = document.getElementById('admin-panel');
        const crewPanel = document.getElementById('crew-panel');
        const navAdmin = document.getElementById('nav-admin');
        const navCrew = document.getElementById('nav-crew');
        if (!adminPanel.classList.contains('hidden') && !adminPanel.contains(e.target) && e.target !== navAdmin && !navAdmin.contains(e.target)) {
            renderer.switchView('stage');
        }
        if (!crewPanel.classList.contains('hidden') && !crewPanel.contains(e.target) && e.target !== navCrew && !navCrew.contains(e.target)) {
            if (!e.target.closest('.toggle-switch')) {
                 renderer.switchView('stage');
            }
        }
    });
};