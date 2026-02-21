from typing import Optional


class NeuralVoiceAssignment:
    DEFAULT_VOICES: dict[str, str] = {
        "lisa": "FR-Lisa",
        "renarde": "FR-Renarde",
        "electra": "FR-Electra",
        "dieu": "FR-Neutral",
        "entropy": "FR-Neutral",
        "default": "FR-Default",
    }

    def get_voice(self, agent_id: str, config_voice_id: Optional[str] = None) -> str:
        if config_voice_id:
            return config_voice_id
        return self.DEFAULT_VOICES.get(agent_id.lower(), self.DEFAULT_VOICES["default"])
