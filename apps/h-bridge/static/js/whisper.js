/**
 * Whisper Integration Module for hAIrem
 * Extends AudioCapture with real-time transcription capabilities
 */

class WhisperIntegration {
    constructor() {
        this.isTranscribing = false;
        this.currentSessionId = null;
        this.confidenceThreshold = 0.6;
        this.transcriptBuffer = [];
        this.maxBufferLength = 5; 
        
        this.startTranscription = this.startTranscription.bind(this);
        this.stopTranscription = this.stopTranscription.bind(this);
        this.updateTranscriptionStatus = this.updateTranscriptionStatus.bind(this);
        this.onWhisperResult = this.onWhisperResult.bind(this);
    }
    
    async initializeWhisperIntegration() {
        try {
            if (window.network && window.network.socket && window.network.socket.readyState === WebSocket.OPEN) {
                const message = {
                    type: 'whisper_status',
                    sender: { agent_id: 'ui_controller', role: 'user' },
                    payload: { action: 'status' }
                };
                window.network.socket.send(JSON.stringify(message));
            } else {
                setTimeout(() => this.initializeWhisperIntegration(), 500);
            }
        } catch (error) {
            console.error('Whisper init failed:', error);
        }
    }

    async startTranscription() {
        try {
            if (this.isTranscribing) return;
            if (!window.network || !window.network.socket) return;

            this.currentSessionId = 'session_' + Date.now().toString(36);
            
            const message = {
                type: 'whisper_session_start',
                sender: { agent_id: 'ui_controller', role: 'user' },
                payload: { session_id: this.currentSessionId }
            };
            window.network.socket.send(JSON.stringify(message));
            
            if (window.audioCapture && window.audioCapture.startCapture) {
                await window.audioCapture.startCapture();
                this.isTranscribing = true;
                this.updateTranscriptionStatus('transcribing');
                
                // Show transcript area
                const transcriptArea = document.getElementById('whisper-transcript');
                if (transcriptArea) transcriptArea.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Failed to start transcription:', error);
            this.updateTranscriptionStatus('error');
        }
    }
    
    stopTranscription() {
        try {
            if (!this.isTranscribing) return;
            
            if (this.currentSessionId && window.network && window.network.socket) {
                const message = {
                    type: 'whisper_session_end',
                    sender: { agent_id: 'ui_controller', role: 'user' },
                    payload: { session_id: this.currentSessionId }
                };
                window.network.socket.send(JSON.stringify(message));
                this.currentSessionId = null;
            }
            
            if (window.audioCapture && window.audioCapture.stopCapture) {
                window.audioCapture.stopCapture();
            }
            
            this.isTranscribing = false;
            this.updateTranscriptionStatus('ready');
            
            // Auto-hide transcript after 5s
            setTimeout(() => {
                if (!this.isTranscribing) {
                    const transcriptArea = document.getElementById('whisper-transcript');
                    if (transcriptArea) transcriptArea.classList.add('hidden');
                }
            }, 5000);
            
        } catch (error) {
            console.error('Failed to stop transcription:', error);
        }
    }
    
    updateTranscriptionStatus(status) {
        if (window.audioCapture) {
            window.audioCapture.updateRecordingStatus(status);
        }
    }
    
    onWhisperResult(data) {
        try {
            const result = typeof data === 'string' ? JSON.parse(data) : data;
            const { text, confidence } = result;
            
            if (!text) return;

            this.transcriptBuffer.push({
                text: text,
                confidence: confidence,
                timestamp: Date.now()
            });
            
            if (this.transcriptBuffer.length > this.maxBufferLength) {
                this.transcriptBuffer.shift();
            }
            
            this.updateTranscriptDisplay();
            
            if (confidence > this.confidenceThreshold) {
                if (window.audioCapture) window.audioCapture.forwardToLLM(text);
            }
        } catch (error) {
            console.error('Failed to process Whisper result:', error);
        }
    }
    
    updateTranscriptDisplay() {
        const transcriptElement = document.getElementById('whisper-transcript');
        if (!transcriptElement) return;
        
        const recentTranscripts = this.transcriptBuffer.slice(-3).reverse();
        
        const html = recentTranscripts.map(item => `
            <div class="transcript-segment">
                <div class="transcript-text">${item.text}</div>
                <div class="transcript-meta">${Math.round(item.confidence * 100)}% - ${new Date(item.timestamp).toLocaleTimeString()}</div>
            </div>
        `).join('');
        
        transcriptElement.innerHTML = html;
    }
    
    setup() {
        console.log('Whisper Integration setup');
        this.initializeWhisperIntegration();
        
        const checkReady = setInterval(() => {
            if (window.network && window.network.socket && window.network.socket.readyState === WebSocket.OPEN) {
                clearInterval(checkReady);
                window.network.socket.addEventListener('message', (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        if (data.type === 'transcription_update') {
                            this.onWhisperResult(data.payload);
                        } else if (data.type === 'transcription_status') {
                            this.updateTranscriptionStatus(data.payload.status || 'ready');
                        }
                    } catch (e) {}
                });
            }
        }, 500);
    }
}

window.whisperIntegration = new WhisperIntegration();
document.addEventListener('DOMContentLoaded', () => {
    window.whisperIntegration.setup();
});
