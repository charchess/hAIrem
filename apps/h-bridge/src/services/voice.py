import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class VoiceProfile:
    agent_id: str
    name: str
    voice_id: Optional[str] = None
    pitch: float = 1.0
    rate: float = 1.0
    volume: float = 1.0
    language: str = "fr-FR"
    gender: str = "neutral"
    quality: str = "high"
    custom_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "voice_id": self.voice_id,
            "pitch": self.pitch,
            "rate": self.rate,
            "volume": self.volume,
            "language": self.language,
            "gender": self.gender,
            "quality": self.quality,
            "custom_params": self.custom_params,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VoiceProfile":
        return cls(
            agent_id=data.get("agent_id", ""),
            name=data.get("name", "default"),
            voice_id=data.get("voice_id"),
            pitch=data.get("pitch", 1.0),
            rate=data.get("rate", 1.0),
            volume=data.get("volume", 1.0),
            language=data.get("language", "fr-FR"),
            gender=data.get("gender", "neutral"),
            quality=data.get("quality", "high"),
            custom_params=data.get("custom_params", {}),
        )


DEFAULT_VOICES = {
    "amalia": VoiceProfile(
        agent_id="amalia",
        name="Amalia",
        voice_id="fr-FR",
        pitch=1.1,
        rate=1.0,
        volume=1.0,
        language="fr-FR",
        gender="female",
        quality="high",
    ),
    "marcus": VoiceProfile(
        agent_id="marcus",
        name="Marcus",
        voice_id="fr-FR",
        pitch=0.9,
        rate=0.95,
        volume=1.0,
        language="fr-FR",
        gender="male",
        quality="high",
    ),
    "elena": VoiceProfile(
        agent_id="elena",
        name="Elena",
        voice_id="fr-FR",
        pitch=1.15,
        rate=1.05,
        volume=0.95,
        language="fr-FR",
        gender="female",
        quality="high",
    ),
    "default": VoiceProfile(
        agent_id="default",
        name="Default",
        voice_id="fr-FR",
        pitch=1.0,
        rate=1.0,
        volume=1.0,
        language="fr-FR",
        gender="neutral",
        quality="high",
    ),
}


class VoiceProfileService:
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self._profiles: Dict[str, VoiceProfile] = {}
        self._load_default_profiles()

    def _load_default_profiles(self):
        for agent_id, profile in DEFAULT_VOICES.items():
            self._profiles[agent_id] = profile

    async def initialize(self):
        if self.redis_client:
            await self._load_profiles_from_storage()
        logger.info(f"Voice profiles initialized: {len(self._profiles)} profiles")

    async def _load_profiles_from_storage(self):
        try:
            if self.redis_client and self.redis_client.client:
                for agent_id in DEFAULT_VOICES.keys():
                    key = f"voice:profile:{agent_id}"
                    data = await self.redis_client.client.get(key)
                    if data:
                        import json

                        profile_data = json.loads(data)
                        self._profiles[agent_id] = VoiceProfile.from_dict(profile_data)
        except Exception as e:
            logger.warning(f"Could not load voice profiles from storage: {e}")

    async def _save_profile_to_storage(self, profile: VoiceProfile):
        if self.redis_client and self.redis_client.client:
            try:
                import json

                key = f"voice:profile:{profile.agent_id}"
                await self.redis_client.client.set(key, json.dumps(profile.to_dict()))
            except Exception as e:
                logger.warning(f"Could not save voice profile: {e}")

    async def get_profile(self, agent_id: str) -> VoiceProfile:
        if agent_id in self._profiles:
            return self._profiles[agent_id]

        # Try to get neural assignment
        try:
            from services.neural_voice_assignment import neural_voice_assignment_service

            neural_voice = await neural_voice_assignment_service.assign_voice_to_agent(agent_id)
            if neural_voice:
                # Create a profile from neural characteristics
                profile = VoiceProfile(
                    agent_id=agent_id,
                    name=f"Neural-{agent_id}",
                    voice_id=f"neural-{neural_voice.gender}",
                    pitch=neural_voice.pitch,
                    rate=neural_voice.rate,
                    volume=neural_voice.volume,
                    language="fr-FR",
                    gender=neural_voice.gender,
                    quality="neural",
                    custom_params={"neural_assigned": True, "personality_traits": neural_voice.personality_traits},
                )
                self._profiles[agent_id] = profile
                await self._save_profile_to_storage(profile)
                return profile
        except Exception as e:
            logger.warning(f"Failed to get neural voice assignment for {agent_id}: {e}")

        # Fallback to default
        return self._profiles.get("default")

    async def set_profile(self, agent_id: str, profile: VoiceProfile) -> VoiceProfile:
        profile.agent_id = agent_id
        self._profiles[agent_id] = profile
        await self._save_profile_to_storage(profile)
        return profile

    async def update_profile(self, agent_id: str, updates: Dict[str, Any]) -> VoiceProfile:
        existing = self.get_profile(agent_id)
        profile_data = existing.to_dict()
        profile_data.update(updates)
        new_profile = VoiceProfile.from_dict(profile_data)
        return await self.set_profile(agent_id, new_profile)

    def list_profiles(self) -> Dict[str, VoiceProfile]:
        return self._profiles.copy()

    def get_all_agent_ids(self) -> list:
        return [aid for aid in self._profiles.keys() if aid != "default"]

    async def apply_to_tts_params(self, agent_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        profile = await self.get_profile(agent_id)
        result = params.copy()
        result["pitch"] = profile.pitch
        result["rate"] = profile.rate
        result["volume"] = profile.volume
        result["voice_id"] = profile.voice_id
        result["language"] = profile.language
        return result


voice_profile_service = VoiceProfileService()


async def get_voice_profile(agent_id: str) -> VoiceProfile:
    return voice_profile_service.get_profile(agent_id)


async def set_voice_profile(agent_id: str, profile_data: Dict[str, Any]) -> VoiceProfile:
    profile = VoiceProfile.from_dict({**profile_data, "agent_id": agent_id})
    return await voice_profile_service.set_profile(agent_id, profile)
