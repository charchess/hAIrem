/**
 * hAIrem Admin Panel — Metrics, Voice Enrollment, Onboarding
 * Extends the existing admin tabs with new capabilities.
 */

class AdminExtensions {
    constructor() {
        this._metricsInterval = null;
    }

    init() {
        this._bindMetricsTab();
        this._bindVoiceTab();
        this._bindOnboardingTab();
    }

    // ── Metrics ──────────────────────────────────────────────────────────────

    _bindMetricsTab() {
        const btn = document.getElementById('btn-refresh-metrics');
        if (btn) btn.addEventListener('click', () => this.loadMetrics());
    }

    async loadMetrics() {
        const container = document.getElementById('metrics-display');
        if (!container) return;
        container.textContent = 'Chargement…';
        try {
            const resp = await fetch('/api/metrics');
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            const counters = data.counters || {};
            const histograms = data.histograms || {};

            let html = '<table style="width:100%;border-collapse:collapse;font-family:monospace;font-size:12px;">';
            html += '<tr><th style="text-align:left;color:#00ffcc;padding:4px">Metric</th><th style="text-align:right;color:#00ffcc;padding:4px">Value</th></tr>';

            for (const [k, v] of Object.entries(counters)) {
                html += `<tr><td style="padding:3px 4px;border-bottom:1px solid #333">${k}</td><td style="padding:3px 4px;border-bottom:1px solid #333;text-align:right">${v}</td></tr>`;
            }
            for (const [k, v] of Object.entries(histograms)) {
                html += `<tr><td style="padding:3px 4px;border-bottom:1px solid #333">${k} (avg)</td><td style="padding:3px 4px;border-bottom:1px solid #333;text-align:right">${v.avg?.toFixed(3)}</td></tr>`;
                html += `<tr><td style="padding:3px 4px;border-bottom:1px solid #333">${k} (count)</td><td style="padding:3px 4px;border-bottom:1px solid #333;text-align:right">${v.count}</td></tr>`;
            }

            if (Object.keys(counters).length + Object.keys(histograms).length === 0) {
                html += '<tr><td colspan="2" style="padding:8px;color:#888">Aucune métrique disponible</td></tr>';
            }

            html += '</table>';
            container.innerHTML = html;
        } catch (e) {
            container.textContent = `Erreur : ${e.message}`;
        }
    }

    // ── Voice Enrollment ─────────────────────────────────────────────────────

    _bindVoiceTab() {
        const enrollBtn = document.getElementById('btn-voice-enroll');
        if (enrollBtn) enrollBtn.addEventListener('click', () => this._enrollVoice());

        const listBtn = document.getElementById('btn-voice-list');
        if (listBtn) listBtn.addEventListener('click', () => this._listVoiceProfiles());
    }

    async _enrollVoice() {
        const userId = document.getElementById('voice-user-id')?.value?.trim();
        const name = document.getElementById('voice-user-name')?.value?.trim();
        const status = document.getElementById('voice-enroll-status');

        if (!userId || !name) {
            if (status) status.textContent = '⚠️ User ID et Nom requis';
            return;
        }

        if (status) status.textContent = 'Enregistrement audio (3s)…';

        try {
            const audioBase64 = await this._recordAudioBase64(3000);
            const resp = await fetch('/api/voice/enroll', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, name, audio_data: audioBase64 }),
            });
            const data = await resp.json();
            if (status) {
                status.textContent = resp.ok
                    ? `✅ Voix enregistrée pour ${data.name} (${data.user_id})`
                    : `❌ Erreur : ${data.detail || 'inconnue'}`;
            }
        } catch (e) {
            if (status) status.textContent = `❌ ${e.message}`;
        }
    }

    async _listVoiceProfiles() {
        const container = document.getElementById('voice-profiles-list');
        if (!container) return;
        try {
            const resp = await fetch('/api/voice/profiles');
            const data = await resp.json();
            const profiles = data.profiles || [];
            if (profiles.length === 0) {
                container.innerHTML = '<em style="color:#888">Aucun profil vocal enregistré</em>';
            } else {
                container.innerHTML = profiles.map(p =>
                    `<div style="padding:4px 0;border-bottom:1px solid #333">🎤 <strong>${p.name}</strong> (${p.user_id})</div>`
                ).join('');
            }
        } catch (e) {
            container.textContent = `Erreur : ${e.message}`;
        }
    }

    async _recordAudioBase64(durationMs) {
        return new Promise(async (resolve, reject) => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const recorder = new MediaRecorder(stream);
                const chunks = [];
                recorder.ondataavailable = e => chunks.push(e.data);
                recorder.onstop = () => {
                    stream.getTracks().forEach(t => t.stop());
                    const blob = new Blob(chunks, { type: 'audio/webm' });
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        const b64 = reader.result.split(',')[1];
                        resolve(b64);
                    };
                    reader.readAsDataURL(blob);
                };
                recorder.start();
                setTimeout(() => recorder.stop(), durationMs);
            } catch (e) {
                reject(e);
            }
        });
    }

    // ── Onboarding ────────────────────────────────────────────────────────────

    _bindOnboardingTab() {
        const checkBtn = document.getElementById('btn-onboarding-check');
        if (checkBtn) checkBtn.addEventListener('click', () => this._checkOnboarding());

        const startBtn = document.getElementById('btn-onboarding-start');
        if (startBtn) startBtn.addEventListener('click', () => this._startOnboarding());
    }

    async _checkOnboarding() {
        const userId = document.getElementById('onboarding-user-id')?.value?.trim();
        const status = document.getElementById('onboarding-status');
        if (!userId) { if (status) status.textContent = '⚠️ User ID requis'; return; }
        try {
            const resp = await fetch(`/api/onboarding/status/${encodeURIComponent(userId)}`);
            const data = await resp.json();
            if (status) {
                status.textContent = data.onboarded
                    ? `✅ ${userId} — onboarding complété`
                    : `⏳ ${userId} — pas encore onboardé`;
            }
        } catch (e) {
            if (status) status.textContent = `❌ ${e.message}`;
        }
    }

    async _startOnboarding() {
        const userId = document.getElementById('onboarding-user-id')?.value?.trim();
        const name = document.getElementById('onboarding-user-name')?.value?.trim();
        const status = document.getElementById('onboarding-status');
        if (!userId) { if (status) status.textContent = '⚠️ User ID requis'; return; }
        try {
            const resp = await fetch('/api/onboarding/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, user_name: name || userId }),
            });
            const data = await resp.json();
            if (status) {
                status.textContent = data.status === 'already_onboarded'
                    ? `✅ ${userId} est déjà onboardé`
                    : `🚀 Interview démarrée — Q1: ${data.question}`;
            }
        } catch (e) {
            if (status) status.textContent = `❌ ${e.message}`;
        }
    }
}

window.adminExtensions = new AdminExtensions();
document.addEventListener('DOMContentLoaded', () => {
    window.adminExtensions.init();
});
