/**
 * Audio Capture Module for hAIrem Audio Ingestion
 * Handles microphone access, recording, and WebSocket transmission
 */

class AudioCapture {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.sampleRate = 16000; // Standard for speech recognition
        this.stream = null;
        this.websocket = null;
        
        // Bind methods to maintain context
        this.startCapture = this.startCapture.bind(this);
        this.stopCapture = this.stopCapture.bind(this);
        this.sendAudioToBridge = this.sendAudioToBridge.bind(this);
        
        console.log('AudioCapture initialized');
    }
    
    async initWebSocket() {
        // Use the global network socket if available
        if (window.network && window.network.socket) {
            this.websocket = window.network.socket;
            console.log('Audio capture using shared network WebSocket');
            return;
        }
        
        // Wait for network client
        await new Promise(resolve => setTimeout(resolve, 500));
        return this.initWebSocket();
    }
    
    updateRecordingStatus(status) {
        // Update UI status indicators
        const buttonElement = document.getElementById('voice-trigger');
        const dotElement = document.getElementById('voice-status-dot');
        
        if (dotElement) {
            dotElement.className = `status-dot status-${status}`;
            dotElement.title = `Micro: ${status.toUpperCase()}`;
        }
        
        if (buttonElement) {
            const label = buttonElement.querySelector('label');
            const icon = buttonElement.querySelector('span');
            if (label) label.textContent = status === 'recording' ? 'STOP' : 'PARLER';
            if (icon) icon.textContent = status === 'recording' ? '⏹️' : '🎤';
            
            buttonElement.classList.toggle('active', status === 'recording');
            buttonElement.disabled = false;
        }
    }
    
    async startCapture() {
        try {
            if (!this.websocket) {
                await this.initWebSocket();
            }
            
            if (this.isRecording) {
                console.warn('Already recording');
                return;
            }
            
            // Request microphone access
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: this.sampleRate,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: false
                }
            });
            
            // Setup media recorder
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: 'audio/webm;codecs=opus',
                audioBitsPerSecond: 128000 // 128 kbps for good quality
            });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(this.audioChunks, {
                    type: 'audio/webm;codecs=opus'
                });
                
                this.sendAudioToBridge(audioBlob);
                this.audioChunks = [];
            };
            
            this.mediaRecorder.start(); 
            this.isRecording = true;
            
            // Story 14.1: Barge-in (Stop current speech)
            if (window.speechQueue) {
                window.speechQueue.clear();
            }
            if (window.audioPlayer) {
                window.audioPlayer.stopAll();
            }
            if (window.renderer) {
                window.renderer.setState('listening');
            }
            
            this.updateRecordingStatus('recording');
            console.log('Audio recording started');
            
        } catch (error) {
            console.warn('Audio capture failed:', error);
            this.updateRecordingStatus('error');
        }
    }
    
    stopCapture() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Stop the stream
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
                this.stream = null;
            }
            
            this.updateRecordingStatus('processing');
            console.log('Audio recording stopped');
        }
    }
    
    sendAudioToBridge(audioBlob) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            console.error('WebSocket not ready for audio transmission');
            return;
        }
        
        // Convert to base64 and send via WebSocket
        const reader = new FileReader();
        reader.onloadend = () => {
            const base64Audio = reader.result.split(',')[1]; 
            
            const currentRoom = localStorage.getItem('hairem_device_room') || 'Salon';
            const message = {
                type: 'user_audio',
                sender: { agent_id: 'user', role: 'user' },
                recipient: { target: 'audio_processor' },
                payload: {
                    content: base64Audio,
                    format: 'webm',
                    sample_rate: this.sampleRate,
                    duration: Date.now(),
                    room_id: currentRoom // Story 19.1
                }
            };
            
            this.websocket.send(JSON.stringify(message));
            console.log('Audio data sent to bridge');
        };
        
        reader.readAsDataURL(audioBlob);
    }
    
    showErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'audio-error-message';
        errorDiv.textContent = message;
        errorDiv.style.cssText = `
            position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
            background: var(--panel-bg); color: var(--text-color); padding: 15px;
            border-radius: 8px; border: 1px solid var(--accent-color); z-index: 1000;
            max-width: 400px; text-align: center; font-size: 14px;
        `;
        document.body.appendChild(errorDiv);
        setTimeout(() => { if (errorDiv.parentNode) errorDiv.parentNode.removeChild(errorDiv); }, 5000);
    }
    
    forwardToLLM(text) {
        if (window.network && window.network.sendUserMessage) {
            window.network.sendUserMessage(text, 'broadcast');
        } else {
            console.error('Network client not available for LLM forwarding');
        }
    }

    async setup() {
        console.log('Setting up Audio Capture...');
        const toggleButton = document.getElementById('voice-trigger');
        if (toggleButton) {
            toggleButton.addEventListener('click', () => {
                if (window.whisperIntegration) {
                    if (window.whisperIntegration.isTranscribing) {
                        window.whisperIntegration.stopTranscription();
                    } else {
                        window.whisperIntegration.startTranscription();
                    }
                } else {
                    if (this.isRecording) this.stopCapture();
                    else this.startCapture();
                }
            });
        }
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(t => t.stop());
            this.updateRecordingStatus('ready');
        } catch (error) {
            this.updateRecordingStatus('error');
        }
    }
}

window.audioCapture = new AudioCapture();
document.addEventListener('DOMContentLoaded', () => {
    window.audioCapture.setup();
});
