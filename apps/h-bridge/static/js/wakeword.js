/**
 * Wake Word Detection Module for hAIrem
 * Extends AudioCapture with continuous wake word monitoring
 */

class WakeWordDetector {
    constructor() {
        this.isActive = false;
        this.isMonitoring = false;
        this.audioContext = null;
        this.microphoneStream = null;
        this.analyser = null;
        this.scriptProcessor = null;
        this.confidenceThreshold = 0.7;
        this.wakeWords = ["hey lisa", "ok lisa", "lisent"];
        this.monitoringInterval = null;
        
        // Bind methods to maintain context
        this.startMonitoring = this.startMonitoring.bind(this);
        this.stopMonitoring = this.stopMonitoring.bind(this);
        this.initializeWakeWordDetection = this.initializeWakeWordDetection.bind(this);
    }
    
    async initializeWakeWordDetection() {
        try {
            console.log('Initializing Wake Word Detection...');
            
            // Create audio context for background monitoring
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Request microphone access for continuous monitoring
            this.microphoneStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: false
                }
            });
            
            // Setup audio analysis chain
            this.setupAudioProcessing();
            
            // Start background monitoring
            this.startBackgroundMonitoring();
            
            this.isActive = true;
            this.updateWakeWordStatus('active');
            
            console.log('Wake Word Detection initialized successfully');
            
        } catch (error) {
            console.warn('Wake Word Detection initialization failed:', error);
            this.updateWakeWordStatus('error');
            this.showErrorMessage('Wake word detection failed: ' + error.message);
        }
    }
    
    setupAudioProcessing() {
        // Create analyser for audio feature extraction
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 2048;
        this.analyser.smoothingTimeConstant = 0.8;
        
        // Create script processor for real-time audio analysis
        this.scriptProcessor = this.audioContext.createScriptProcessor(2048, 1);
        
        this.scriptProcessor.onaudioprocess = (event) => {
            const audioData = event.inputBuffer.getChannelData(0);
            const features = this.extractAudioFeatures(audioData);
            const wakeWordDetected = this.detectWakeWord(features);
            
            if (wakeWordDetected && !this.isRecording) {
                this.onWakeWordDetected(features.confidence);
            }
        };
        
        // Connect the audio processing chain
        const source = this.audioContext.createMediaStreamSource(this.microphoneStream);
        source.connect(this.analyser);
        this.analyser.connect(this.scriptProcessor);
        this.scriptProcessor.connect(this.audioContext.destination);
    }
    
    extractAudioFeatures(audioData) {
        if (audioData.length === 0) return { confidence: 0.0 };
        
        // Calculate energy (RMS)
        let energy = 0;
        for (let i = 0; i < audioData.length; i++) {
            energy += audioData[i] * audioData[i];
        }
        energy = Math.sqrt(energy / audioData.length);
        
        // Calculate zero crossing rate
        let zeroCrossings = 0;
        for (let i = 1; i < audioData.length; i++) {
            if ((audioData[i] >= 0) !== (audioData[i - 1] >= 0)) {
                zeroCrossings++;
            }
        }
        
        // Normalize features
        const normalizedEnergy = Math.min(energy / 0.1, 1.0); // Normalize to 0-1 range
        const normalizedZCR = Math.min(zeroCrossings / 100, 1.0); // Typical speech has ~50-200 ZCR per second
        
        // Simple heuristic for wake word detection
        // Wake words typically have energy > threshold and appropriate ZCR
        let confidence = 0.0;
        
        if (normalizedEnergy > 0.02) { // Energy threshold
            confidence += 0.4;
        }
        
        if (normalizedZCR > 0.1 && normalizedZCR < 0.8) { // ZCR in speech range
            confidence += 0.3;
        }
        
        // Additional spectral analysis (simplified)
        const spectralContent = this.analyzeSpectralContent(audioData);
        if (spectralContent.hasSpeech) {
            confidence += 0.3;
        }
        
        return {
            energy: normalizedEnergy,
            zcr: normalizedZCR,
            spectral: spectralContent,
            confidence: confidence
        };
    }
    
    analyzeSpectralContent(audioData) {
        // Simplified spectral analysis
        // In real implementation, this would use FFT
        // For now, use variance as a proxy for spectral content
        let variance = 0;
        const mean = audioData.reduce((sum, val) => sum + val, 0) / audioData.length;
        
        for (let i = 0; i < audioData.length; i++) {
            variance += Math.pow(audioData[i] - mean, 2);
        }
        variance /= audioData.length;
        
        // Speech typically has moderate variance
        const hasSpeech = variance > 0.0001 && variance < 0.1;
        
        return {
            hasSpeech: hasSpeech,
            variance: variance
        };
    }
    
    detectWakeWord(features) {
        // Rule-based wake word detection
        // In production, this would use a trained ML model
        // For now, use heuristic based on audio characteristics
        
        const { confidence, energy, zcr } = features;
        
        // Simple threshold-based detection
        const detected = confidence >= this.confidenceThreshold;
        
        if (detected) {
            console.log(`Wake word detected with confidence: ${confidence.toFixed(2)}`);
        }
        
        return detected;
    }
    
    startBackgroundMonitoring() {
        if (this.isMonitoring) return;
        this.isMonitoring = true;
        console.log('Starting background wake word monitoring...');
    }

    startMonitoring() {
        this.startBackgroundMonitoring();
    }

    stopMonitoring() {
        this.stopBackgroundMonitoring();
    }

    setupUIControls() {
        // Mock UI controls if needed
    }
    
    stopBackgroundMonitoring() {
        this.isMonitoring = false;
        console.log('Stopping background wake word monitoring...');
        
        // Stop audio processing
        if (this.microphoneStream) {
            this.microphoneStream.getTracks().forEach(track => track.stop());
            this.microphoneStream = null;
        }
        
        if (this.scriptProcessor) {
            this.scriptProcessor.disconnect();
            this.scriptProcessor = null;
        }
        
        if (this.analyser) {
            this.analyser.disconnect();
            this.analyser = null;
        }
        
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        
        // Send status update to backend
        this.sendWakeWordStatus('disable');
    }
    
    onWakeWordDetected(confidence) {
        console.log(`Wake word detected! Confidence: ${confidence.toFixed(2)}`);
        
        // Visual feedback
        this.updateWakeWordStatus('detected');
        
        // Flash the UI
        this.flashWakeWordIndicator();
        
        // Send detection event to backend
        if (window.websocket && window.websocket.readyState === WebSocket.OPEN) {
            const message = {
                type: 'wakeword_detected',
                sender: { agent_id: 'wakeword_detector', role: 'detector' },
                recipient: { target: 'wakeword_engine' },
                payload: {
                    content: 'Wake word detected',
                    confidence: confidence,
                    detection_time: Date.now()
                }
            };
            
            window.websocket.send(JSON.stringify(message));
        }
        
        // Reset status after a short delay
        setTimeout(() => {
            this.updateWakeWordStatus('active');
        }, 2000);
    }
    
    sendWakeWordStatus(action) {
        // Send wake word control message to backend
        if (window.websocket && window.websocket.readyState === WebSocket.OPEN) {
            const message = {
                type: `wakeword_${action}`,
                sender: { agent_id: 'ui_controller', role: 'user' },
                recipient: { target: 'wakeword_engine' },
                payload: {
                    action: action,
                    timestamp: Date.now()
                }
            };
            
            window.websocket.send(JSON.stringify(message));
        }
    }
    
    updateWakeWordStatus(status) {
        const statusElement = document.getElementById('wakeword-status');
        if (statusElement) {
            statusElement.textContent = status.toUpperCase();
            statusElement.className = `wakeword-status status-${status}`;
        }
        
        // Also log to console for debugging
        console.log(`Wake word status: ${status}`);
    }
    
    flashWakeWordIndicator() {
        // Flash visual indicator
        const stage = document.getElementById('the-stage');
        if (stage) {
            stage.style.transition = 'all 0.3s ease';
            stage.style.boxShadow = '0 0 30px rgba(0, 255, 136, 0.6)';
            stage.style.border = '2px solid rgba(0, 255, 136, 0.8)';
            
            setTimeout(() => {
                stage.style.boxShadow = '';
                stage.style.border = '';
            }, 500);
        }
    }
    
    showErrorMessage(message) {
        // Create error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'wakeword-error';
        errorDiv.textContent = message;
        errorDiv.style.cssText = `
            position: fixed;
            top: 120px;
            right: 20px;
            background: var(--panel-bg);
            color: var(--text-color);
            padding: 15px;
            border-radius: 8px;
            border:1px solid var(--accent-color);
            z-index: 1000;
            max-width: 300px;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }
    
    // Auto-initialize when DOM is ready
    async setup() {
        console.log('Initializing Wake Word Detector...');
        
        // Wait for WebSocket connection
        const checkWebSocket = setInterval(() => {
            if (window.network && window.network.socket && window.network.socket.readyState === WebSocket.OPEN) {
                clearInterval(checkWebSocket);
                this.initializeWakeWordDetection();
            }
        }, 500);
        
        // Setup UI controls
        this.setupUIControls();
    }
}

// Global instance
window.wakeWordDetector = new WakeWordDetector();

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    window.wakeWordDetector.setup();
});