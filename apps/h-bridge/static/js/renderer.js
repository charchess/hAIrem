/**
 * hAIrem A2UI Renderer
 * Zero-Flicker Edition (v4.2)
 */

const States = { IDLE: 'idle', LISTENING: 'listening', THINKING: 'thinking', SPEAKING: 'speaking' };

class Renderer {
    constructor() {
        this.layers = {};
        this.currentState = States.IDLE;
        this.typewriterInterval = null;
        this.isLogPaused = false;
        this.logMaxLines = 100;
        this.agents = {}; 
        this.activeOutfits = {}; 
        this.activeView = 'stage';
        this.activeSpeakerId = null;
        this.activeAdminTab = 'system';
        this.selectedAgentForConfig = null;
        this.systemStatus = { ws: 'checking', redis: 'checking', llm: 'checking', brain: 'checking' };

        console.log("Renderer: Initializing...");
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initDOM());
        } else {
            this.initDOM();
        }
    }

    initDOM() {
        this.layers = {
            bg: document.getElementById('layer-bg'),
            bgNext: document.getElementById('layer-bg-next'),
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
            adminPanel: document.getElementById('admin-panel'),
            avatar: document.getElementById('avatar')
        };

        if (!this.layers.bg) return;

        // Shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            if (e.key.toLowerCase() === 'l') { this.layers.logViewer.classList.toggle('hidden'); }
            if (e.key === 'Escape') {
                this.layers.crewPanel.classList.add('hidden');
                this.layers.adminPanel.classList.add('hidden');
                this.layers.logViewer.classList.add('hidden');
                this.activeView = 'stage';
            }
        });

        // Navigation
        document.getElementById('nav-admin').onclick = (e) => { e.stopPropagation(); this.togglePanel('admin'); };
        document.getElementById('nav-crew').onclick = (e) => { e.stopPropagation(); this.togglePanel('crew'); };
        document.getElementById('nav-logs').onclick = (e) => { e.stopPropagation(); this.layers.logViewer.classList.toggle('hidden'); };
        document.getElementById('close-crew').onclick = () => this.togglePanel('crew');
        document.getElementById('close-admin').onclick = () => this.togglePanel('admin');
        document.getElementById('close-logs').onclick = () => this.layers.logViewer.classList.add('hidden');

        // Admin Tabs
        document.querySelectorAll('.admin-tab[data-tab]').forEach(tab => {
            tab.onclick = (e) => { e.stopPropagation(); this.switchAdminTab(e.target.closest('.admin-tab').dataset.tab); };
        });

        // Log Settings
        document.getElementById('save-log-config').onclick = () => {
            const level = document.getElementById('log-level-select').value;
            this.logMaxLines = parseInt(document.getElementById('log-max-lines').value) || 100;
            localStorage.setItem('hairem_log_level', level);
            localStorage.setItem('hairem_log_max', this.logMaxLines);
            if (window.network) window.network.send('system.config_update', { log_level: level });
            this.addLog(`Settings updated: ${level}, Max lines: ${this.logMaxLines}`);
        };

        // Modal close
        document.addEventListener('click', (event) => {
            if (this.activeView === 'stage') return;
            const panels = [ { id: 'crew-panel', btnId: 'nav-crew' }, { id: 'admin-panel', btnId: 'nav-admin' } ];
            panels.forEach(p => {
                const panel = document.getElementById(p.id);
                const btn = document.getElementById(p.btnId);
                if (panel && !panel.classList.contains('hidden')) {
                    if (!panel.contains(event.target) && (!btn || !btn.contains(event.target))) {
                        panel.classList.add('hidden');
                        this.activeView = 'stage';
                    }
                }
            });
        });

        // Save Overrides
        document.getElementById('save-global-llm').onclick = () => {
            const cfg = { provider: document.getElementById('global-llm-provider').value, model: document.getElementById('global-llm-model').value, api_key: document.getElementById('global-llm-key').value };
            if (window.network) window.network.send('system.config_update', { llm_config: cfg });
        };
        document.getElementById('save-agent-override').onclick = () => {
            if (!this.selectedAgentForConfig) return;
            const cfg = { model: document.getElementById('agent-llm-model').value, api_key: document.getElementById('agent-llm-key').value };
            if (window.network) window.network.send('agent.config_update', { agent_id: this.selectedAgentForConfig, llm_config: cfg });
        };

        if (this.layers.send) this.layers.send.onclick = () => this.handleSend();
        if (this.layers.input) this.layers.input.onkeypress = (e) => { if (e.key === 'Enter') this.handleSend(); };

        this.updateLayer(this.layers.bg, "/static/assets/backgrounds/background.png");
        this.render("Lisa", "Prête.", {}, true);
        this.updateSpatialBadge();
    }

    switchAdminTab(tabId) {
        this.activeAdminTab = tabId;
        document.querySelectorAll('.admin-tab[data-tab]').forEach(t => t.classList.toggle('active', t.dataset.tab === tabId));
        document.querySelectorAll('.admin-tab-content').forEach(c => c.classList.toggle('active', c.id === `tab-${tabId}`));
    }

    selectAgentForConfig(agentId) {
        this.selectedAgentForConfig = agentId;
        document.querySelectorAll('#agent-sub-tabs .admin-tab').forEach(t => t.classList.toggle('active', t.dataset.agent === agentId));
        document.getElementById('agent-config-title').textContent = `Config: ${agentId}`;
        document.getElementById('agent-llm-model').value = this.agents[agentId]?.llm_model || '';
    }

    populateAgentSubTabs() {
        const container = document.getElementById('agent-sub-tabs');
        if (!container) return;
        container.innerHTML = '';
        Object.keys(this.agents).forEach(id => {
            if (this.agents[id].isSystem) return;
            const btn = document.createElement('button');
            btn.className = `admin-tab ${this.selectedAgentForConfig === id ? 'active' : ''}`;
            btn.dataset.agent = id; btn.textContent = id;
            btn.onclick = (e) => { e.stopPropagation(); this.selectAgentForConfig(id); };
            container.appendChild(btn);
        });
    }

    togglePanel(panelId) {
        const panel = (panelId === 'crew') ? this.layers.crewPanel : this.layers.adminPanel;
        const other = (panelId === 'crew') ? this.layers.adminPanel : this.layers.crewPanel;
        other.classList.add('hidden');
        panel.classList.toggle('hidden');
        this.activeView = panel.classList.contains('hidden') ? 'stage' : panelId;
        if (panelId === 'crew' && !panel.classList.contains('hidden')) this.renderAgentGrid();
        if (panelId === 'admin' && !panel.classList.contains('hidden')) this.populateAgentSubTabs();
    }

    handleSend() {
        const text = this.layers.input.value.trim();
        const target = document.getElementById('target-agent-select').value;
        if (!text || !window.network) return;
        window.network.sendUserMessage(text, target);
        this.addMessageToHistory("user", text);
        this.layers.input.value = '';
        this.setState(States.THINKING);
    }

    setState(state) {
        this.currentState = state;
        if (!this.layers.body) return;
        this.layers.body.classList.remove('pensive', 'listening', 'speaking');
        this.layers.stage.classList.remove('state-thinking', 'state-listening');
        if (this.layers.avatar) this.layers.avatar.classList.remove('active-speaker');

        if (state === States.THINKING) {
            this.layers.body.classList.add('pensive');
            this.layers.stage.classList.add('state-thinking');
        }
        else if (state === States.LISTENING) {
            this.layers.stage.classList.add('state-listening');
        }
        else if (state === States.SPEAKING) {
            this.layers.body.classList.add('speaking');
            if (this.layers.avatar) this.layers.avatar.classList.add('active-speaker');
        }
    }

    render(agentName, text, assets = {}, skipTypewriter = false) {
        if (!this.layers.name || !agentName) return;
        this.layers.name.textContent = agentName;
        const agentId = agentName.toLowerCase();
        this.activeSpeakerId = agentId;

        const { cleanedText } = this.extractPose(text);
        if (!["core", "system", "bridge", "user"].includes(agentId)) {
            const bodySrc = assets.body || this.activeOutfits[agentId] || `/agents/${agentId}/media/character_sheet_neutral.png`;
            this.updateLayer(this.layers.body, bodySrc, `/static/assets/agents/${agentId}/${agentId}_neutral_01.png`);
            if (this.layers.body) {
                this.layers.body.style.display = 'block';
                this.layers.body.style.opacity = '1';
            }
        }
        if (cleanedText && !skipTypewriter) this.typewrite(cleanedText);
        if (assets.bg) this.updateBackgroundWithFade(assets.bg);
    }

    updateLayer(el, src, fallbackSrc = null) {
        if (!el || !src) return;
        const img = new Image();
        img.onload = () => { el.style.backgroundImage = `url('${src}')`; el.style.opacity = 1; };
        img.onerror = () => { if (fallbackSrc) this.updateLayer(el, fallbackSrc); };
        img.src = src;
    }

    updateBackgroundWithFade(src) {
        if (!this.layers.bg || !this.layers.bgNext) return;
        const img = new Image();
        img.onload = () => {
            this.layers.bgNext.style.backgroundImage = `url('${src}')`; this.layers.bgNext.style.opacity = 1;
            setTimeout(() => { this.layers.bg.style.backgroundImage = `url('${src}')`; this.layers.bgNext.style.opacity = 0; }, 1000);
        };
        img.src = src;
    }

    typewrite(text, speed = 30) {
        if (this.typewriterInterval) clearInterval(this.typewriterInterval);
        this.layers.text.textContent = "";
        let i = 0; this.setState(States.SPEAKING);
        this.typewriterInterval = setInterval(() => {
            if (i < text.length) { this.layers.text.textContent += text.charAt(i); i++; }
            else { clearInterval(this.typewriterInterval); this.setState(States.IDLE); }
        }, speed);
    }

    extractPose(text) {
        if (typeof text !== 'string') return { cleanedText: '', pose: null };
        const poseMatch = text.match(/\[pose:([a-z]+)\]/i);
        return { cleanedText: text.replace(/\[pose:[a-z]+\]/gi, '').trim(), pose: poseMatch ? poseMatch[1].toLowerCase() : null };
    }

    updateSpatialBadge() {
        const roomNameDisp = document.getElementById('current-room-name');
        const roomSelect = document.getElementById('user-room-select');
        document.getElementById('spatial-badge').classList.remove('hidden');
        if (roomNameDisp && roomSelect) roomNameDisp.textContent = roomSelect.value;
    }

    updateAgents(agentsList) {
        if (!Array.isArray(agentsList)) return;
        agentsList.forEach(a => this.updateAgentStatus(a.id, a.active ? 'idle' : 'disabled', null, a.prompt_tokens, a.completion_tokens, a.total_tokens, a.commands, a.location, a.preferred_location, a.cost, a.skills, a.llm_model));
    }

    updateAgentStatus(agentId, status, mood, pTokens, cTokens, tTokens, commands, location, prefLocation, cost, skills, llmModel) {
        if (!agentId) return;
        const agentIdLower = agentId.toLowerCase();
        const isSystem = ["core", "system", "bridge", "dieu", "admin", "orchestrator", "user", "ha_worker"].includes(agentIdLower);
        if (!this.agents[agentId]) {
            this.agents[agentId] = { id: agentId, isSystem: isSystem };
            if (!isSystem) {
                const select = document.getElementById('target-agent-select');
                if (select && !Array.from(select.options).some(o => o.value === agentId)) {
                    const opt = document.createElement('option'); opt.value = agentId; opt.textContent = agentId; select.appendChild(opt);
                }
            }
        }
        const a = this.agents[agentId];
        if (status) a.status = status;
        if (pTokens !== null) a.prompt_tokens = pTokens;
        if (cTokens !== null) a.completion_tokens = cTokens;
        if (tTokens !== null) a.total_tokens = tTokens;
        if (cost !== undefined) a.cost = cost;
        if (commands) a.commands = commands;
        if (location) a.location = location;
        if (prefLocation) a.preferred_location = prefLocation;
        if (skills) a.skills = skills;
        if (llmModel) a.llm_model = llmModel;
        if (this.activeView === 'crew') this.renderAgentGrid();
    }

    renderAgentGrid() {
        const grid = document.getElementById('agent-grid');
        if (!grid || this.activeView !== 'crew') return;
        Object.keys(this.agents).forEach(id => {
            const agent = this.agents[id];
            let card = document.getElementById(`agent-card-${id}`);
            const isEnabled = agent.status !== 'disabled';
            const skillsHtml = (agent.skills || []).map(s => `<span class="skill-badge ${s.active ? 'active' : 'inactive'}">${s.name}</span>`).join('');
            const cardHtml = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 30px; height: 30px; border-radius: 50%; background: #333; border: 1px solid var(--accent-color); overflow: hidden;">
                            <img src="/agents/${id.toLowerCase()}/media/portrait.png" onerror="this.src='/static/assets/placeholder_portrait.png'" style="width: 100%; height: 100%; object-fit: cover;">
                        </div>
                        <strong>${id}</strong>
                    </div>
                    <div style="display: flex; align-items: center; gap: 5px;">
                        <span style="font-size: 0.7rem; padding: 2px 6px; border-radius: 10px; background: #333;">${agent.status}</span>
                        <input type="checkbox" ${isEnabled ? 'checked' : ''} onchange="window.network.toggleAgent('${id}', this.checked)">
                    </div>
                </div>
                <div style="display: flex; gap: 8px; margin-bottom: 8px; font-size: 10px;">
                    <div>📍 ${agent.location || 'Inconnu'}</div>
                    <div style="border: 1px dashed var(--accent-dim); padding: 0 4px;">🏠 ${agent.preferred_location || 'Aucune'}</div>
                </div>
                <div style="margin-bottom: 8px; font-size: 10px; color: #aaa; font-style: italic;">
                    🧠 ${agent.llm_model || 'Standard'}
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px;">${skillsHtml}</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; font-size: 10px; gap: 2px;">
                    <div>IN: ${agent.prompt_tokens || 0}</div><div>OUT: ${agent.completion_tokens || 0}</div>
                    <div style="color: var(--accent-color)">$${(agent.cost || 0).toFixed(4)}</div>
                </div>
            `;
            if (!card) {
                card = document.createElement('div'); card.id = `agent-card-${id}`;
                card.style.cssText = "background: rgba(255,255,255,0.05); border: 1px solid #333; padding: 15px; border-radius: 4px; margin-bottom: 10px;";
                grid.appendChild(card);
            }
            const stateKey = JSON.stringify({s: agent.status, t: agent.total_tokens, sk: (agent.skills || []).length});
            if (card.dataset.state !== stateKey) { card.innerHTML = cardHtml; card.className = `agent-card ${isEnabled ? '' : 'disabled'}`; card.dataset.state = stateKey; }
        });
    }

    addMessageToHistory(sender, text) {
        if (!this.layers.history) return;
        const div = document.createElement('div'); div.className = `chat-msg ${sender === 'user' ? 'msg-user' : 'msg-agent'}`;
        div.innerHTML = `<strong>${sender}:</strong> <span>${text}</span>`;
        this.layers.history.appendChild(div);
        this.layers.history.scrollTop = this.layers.history.scrollHeight;
    }

    renderHistory(messages) {
        if (!this.layers.history || !Array.isArray(messages)) return;
        this.layers.history.innerHTML = '';
        [...messages].reverse().forEach(m => this.addMessageToHistory(m.agent || m.subject || 'unknown', m.content || m.fact));
    }

    addLog(content) {
        if (this.isLogPaused || !this.layers.logs) return;
        if (content.includes('heartbeat') && !content.includes('DEBUG')) return;
        const entry = document.createElement('div'); entry.style.cssText = "font-size: 11px; font-family: monospace; color: #888; border-bottom: 1px solid #222; padding: 2px 0;";
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${content}`;
        this.layers.logs.appendChild(entry);
        while (this.layers.logs.children.length > this.logMaxLines) this.layers.logs.removeChild(this.layers.logs.firstChild);
        this.layers.logs.scrollTop = this.layers.logs.scrollHeight;
    }

    updateSystemStatus(component, status) {
        this.systemStatus[component] = status;
        const cssStatus = (status === 'ok' || status === 'online' || status === 'connected') ? 'ok' : status;
        const adminIndicator = document.getElementById(`status-${component}-admin`);
        if (adminIndicator) { adminIndicator.textContent = status.toUpperCase(); adminIndicator.className = `status-indicator ${cssStatus}`; }
    }
}

window.renderer = null;
document.addEventListener('DOMContentLoaded', () => { window.renderer = new Renderer(); });
