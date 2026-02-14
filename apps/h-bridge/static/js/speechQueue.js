/**
 * Speech Queue Manager for A2UI
 * Handles sequential display of narrative messages.
 */

class SpeechQueue {
    constructor() {
        this.queue = [];
        this.isProcessing = false;
        this.displayDurationPerChar = 50; // ms per character
        this.minDisplayDuration = 2000; // minimum duration in ms
        this.maxDisplayDuration = 8000; // maximum duration in ms
    }

    enqueue(message) {
        // Only queue narrative messages
        if (message.type !== "narrative.text") return;
        
        console.log(`[SpeechQueue] Enqueuing message from ${message.sender.agent_id}:`, message.payload.content);
        this.queue.push(message);
        this.processQueue();
    }

    clear() {
        this.queue = [];
        this.isProcessing = false;
        console.log("[SpeechQueue] Cleared.");
    }

    async processQueue() {
        if (this.isProcessing) return;
        if (this.queue.length === 0) return;

        this.isProcessing = true;
        const message = this.queue.shift();
        
        await this.displayMessage(message);
        
        this.isProcessing = false;
        // Check if there are more messages
        if (this.queue.length > 0) {
            this.processQueue();
        }
    }

    async displayMessage(message) {
        const agentName = message.sender.agent_id;
        const content = message.payload.content;
        const correlationId = message.metadata ? message.metadata.correlation_id : null;
        const responseId = correlationId ? `${agentName}-${correlationId}` : null;
        
        console.log(`[SpeechQueue] Displaying: ${agentName} says "${content}"`);
        
        // 1. Trigger Renderer to update Visuals (Pose + Typewriter)
        if (window.renderer) {
            window.renderer.render(agentName, content);
            // Deduplicated add to history
            window.renderer.addMessageToHistory(agentName, content, false, responseId);
            
            // Highlight active speaker
            window.renderer.setActiveSpeaker(agentName);
        }

        // 2. Calculate duration based on text length
        const duration = this.calculateDuration(content);
        console.log(`[SpeechQueue] Locking for ${duration}ms`);

        // 3. Wait for the duration (Speech Lock)
        await new Promise(resolve => setTimeout(resolve, duration));

        // 4. Release Lock & Reset Active Speaker
        if (window.renderer) {
            window.renderer.setActiveSpeaker(null);
            // If queue is empty, set state to IDLE, otherwise keep processing
            if (this.queue.length === 0) {
                 window.renderer.setState('idle');
            }
        }
    }

    calculateDuration(text) {
        // Strip tags for length calculation
        const cleanText = text.replace(/\[pose:[^\]]+\]/g, '');
        let duration = cleanText.length * this.displayDurationPerChar;
        return Math.min(Math.max(duration, this.minDisplayDuration), this.maxDisplayDuration);
    }
}

// Global instance placeholder
window.speechQueue = null;

document.addEventListener('DOMContentLoaded', () => {
    window.speechQueue = new SpeechQueue();
});
