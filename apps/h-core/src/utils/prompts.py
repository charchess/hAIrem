"""
Fallback utilities for prompts and agent configuration
Provides minimal implementations when full prompt module is not available
"""

import logging

logger = logging.getLogger(__name__)


class MultiLayerPromptBuilder:
    """Fallback prompt builder implementation."""
    
    def __init__(self):
        self.layers = []
        logger.warning("Using fallback prompt builder - limited functionality")
    
    def add_layer(self, layer_name: str, content: str):
        """Add a layer to the prompt."""
        self.layers.append({
            "name": layer_name,
            "content": content
        })
    
    def build(self) -> str:
        """Build the complete prompt from layers."""
        if not self.layers:
            return "Fallback prompt - no layers configured"
        
        return "\n".join([f"Layer: {layer['name']} - {layer['content']}" for layer in self.layers])


def build_agent_prompt(agent_id: str, context: str, task: str = None) -> str:
    """Fallback agent prompt building."""
    logger.warning(f"Using fallback agent prompt building for {agent_id}")
    
    prompt_parts = [
        f"Agent: {agent_id}",
        f"Context: {context}"
    ]
    
    if task:
        prompt_parts.append(f"Task: {task}")
    
    return "\n".join(prompt_parts)