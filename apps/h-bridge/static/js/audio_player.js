/**
 * Audio Player for hAIrem
 * Handles streaming TTS playback with low latency
 */

class AudioPlayer {
    constructor() {
        this.audioContext = null;
        this.isPlaying = false;
        this.audioQueue = [];
        this.startTime = 0;
        this.bufferTime = 0.1; // 100ms buffer
    }
    
    initialize() {
        // Initialize AudioContext on first user interaction to comply with browser policy
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        // Listen for TTS messages via existing WebSocket
        // Note: WebSocket handling is centralized, we hook into it
        this.setupWebSocketHook();
    }
    
    setupWebSocketHook() {
        // This assumes global websocket or event bus
        // We'll expose a method to be called by the main WS handler
    }
    
    handleTTSMessage(message) {
        if (!this.audioContext) this.initialize();
        
        const type = message.type;
        const payload = message.payload || {};
        const content = payload.content || {};
        
        if (type === 'tts_start') {
            console.log('TTS Started:', content.text);
            this.audioQueue = [];
            this.startTime = this.audioContext.currentTime + this.bufferTime;
            this.updateStatus('speaking');
        } 
        else if (type === 'tts_audio_chunk') {
            this.queueAudioChunk(content.audio_chunk);
        }
        else if (type === 'tts_end') {
            console.log('TTS Ended');
            // Reset status after playback
            // Note: In streaming, end message might arrive before audio finishes playing
            // We should ideally track playback duration
            setTimeout(() => this.updateStatus('ready'), 1000); 
        }
    }
    
    async queueAudioChunk(base64Data) {
        try {
            // Convert base64 to array buffer
            const binaryString = window.atob(base64Data);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            // Decode audio data
            const audioBuffer = await this.audioContext.decodeAudioData(bytes.buffer);
            this.playBuffer(audioBuffer);
            
        } catch (e) {
            console.error('Error decoding audio chunk:', e);
        }
    }
    
    playBuffer(buffer) {
        const source = this.audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(this.audioContext.destination);
        
        // Schedule playback
        // If start time is in the past, reset it to now
        if (this.startTime < this.audioContext.currentTime) {
            this.startTime = this.audioContext.currentTime;
        }
        
        source.start(this.startTime);
        
        // Advance start time for next chunk
        this.startTime += buffer.duration;
    }
    
    updateStatus(status) {
        const indicator = document.getElementById('agent-status');
        if (indicator) {
            if (status === 'speaking') {
                indicator.classList.add('speaking');
                indicator.textContent = '🗣️ Speaking';
            } else {
                indicator.classList.remove('speaking');
                indicator.textContent = 'ready';
            }
        }
        
        // Also update avatar if possible
        const avatar = document.getElementById('avatar');
        if (avatar && status === 'speaking') {
            avatar.classList.add('talking');
        } else if (avatar) {
            avatar.classList.remove('talking');
        }
    }
}

// Global instance
window.audioPlayer = new AudioPlayer();

// Hook into WebSocket message handler
// STORY 14.4: Use window.network.socket from network.js
function setupAudioPlayerHook() {
    if (window.network && window.network.socket) {
        window.network.socket.addEventListener('message', (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type && data.type.startsWith('tts_')) {
                    window.audioPlayer.handleTTSMessage(data);
                }
            } catch (e) {}
        });
        console.log('AudioPlayer hooked to NetworkClient WebSocket');
    } else {
        // Retry
        setTimeout(setupAudioPlayerHook, 500);
    }
}

document.addEventListener('DOMContentLoaded', setupAudioPlayerHook);