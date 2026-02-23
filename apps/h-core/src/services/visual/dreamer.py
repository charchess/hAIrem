import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

try:
    from electra.drivers.ha_client import HaClient
except ImportError:
    try:
        from agents.electra.drivers.ha_client import HaClient
    except ImportError:
        logger.warning("Dreamer: HaClient not found, using mock")
        HaClient = None

from src.services.visual.service import VisualImaginationService


class Dreamer:
    """
    Orchestrates proactive image generation during sleep cycles.
    """

    def __init__(
        self,
        ha_client: Any,
        visual_service: VisualImaginationService,
        llm_client: Any = None,
        surreal_client: Any = None,
    ):
        self.ha = ha_client
        self.visual_service = visual_service
        self.llm = llm_client
        self.surreal = surreal_client

    async def get_weather_context(self) -> str:
        """Fetch weather condition from Home Assistant."""
        state = await self.ha.get_state("weather.home")
        if state:
            return state.get("state", "clear-night")
        return "clear"

    async def get_time_of_day_context(self) -> str:
        """Fetch sun state or use current hour to determine time of day."""
        sun_state = await self.ha.get_state("sun.sun")
        if sun_state:
            is_above_horizon = sun_state.get("state") == "above_horizon"
            if not is_above_horizon:
                return "night"

            # More granular if possible, but sun.sun is basic
            # We can use elevation if available
            elevation = sun_state.get("attributes", {}).get("elevation", 0)
            if elevation < 10:
                return "golden hour"
            return "daylight"

        # Fallback to local time
        hour = datetime.now().hour
        if 5 <= hour < 8:
            return "dawn"
        if 8 <= hour < 17:
            return "daylight"
        if 17 <= hour < 20:
            return "sunset"
        return "night"

    async def generate_creative_impulse(self, agent_id: str, persona_description: str) -> str:
        if not self.llm:
            return f"A dreamlike, artistic portrait of {agent_id} in an unexpected visual style"

        prompt_request = [
            {
                "role": "system",
                "content": (
                    "You are a creative director generating short image generation prompts. "
                    "Return ONLY a concise prompt (max 30 words), no explanations."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Agent persona: {persona_description}\n"
                    "Generate one unexpected, creative visual style or outfit this agent might dream about tonight. "
                    "Make it distinct from standard looks. Pure image prompt only."
                ),
            },
        ]
        try:
            result = await self.llm.get_completion(prompt_request)
            return result.strip() if isinstance(result, str) else f"Ethereal dreamscape portrait of {agent_id}"
        except Exception as e:
            logger.error(f"DREAMER: LLM creative impulse failed for {agent_id}: {e}")
            return f"Ethereal dreamscape portrait of {agent_id}"

    async def prepare_daily_assets(self, agent_id: str = "system", agents: list[dict[str, Any]] | None = None):
        """
        Analyzes context, constructs prompt, and triggers proactive generation via VisualImaginationService.
        """
        logger.info("DREAMER: Starting proactive asset generation...")

        try:
            weather = await self.get_weather_context()
            time_of_day = await self.get_time_of_day_context()

            background_prompt = (
                f"A view from the window, {weather} weather, {time_of_day}, cinematic style, high detail, masterpiece"
            )
            logger.info(f"DREAMER: Generated background prompt: {background_prompt}")

            asset_uri, _ = await self.visual_service.generate_and_index(
                agent_id=agent_id,
                prompt=background_prompt,
                tags=["proactive", f"weather:{weather}", f"time:{time_of_day}"],
            )

            logger.info(f"DREAMER: Proactive background asset ready at {asset_uri}")

        except Exception as e:
            logger.error(f"DREAMER: Failed to prepare proactive background: {e}")

        if not agents:
            return

        for agent in agents:
            aid = agent.get("id", "")
            persona = agent.get("persona", f"A creative AI character named {aid}")
            if not aid:
                continue
            try:
                creative_prompt = await self.generate_creative_impulse(aid, persona)
                logger.info(f"DREAMER: Creative impulse for {aid}: {creative_prompt}")

                asset_uri, asset_record = await self.visual_service.generate_and_index(
                    agent_id=aid,
                    prompt=creative_prompt,
                    tags=["dream", "creative", aid],
                )

                if self.surreal and asset_record:
                    asset_id = str(asset_record).replace("visual_asset:", "")
                    if asset_id:
                        await self.surreal.store_dream(aid, creative_prompt, asset_id)
                        logger.info(f"DREAMER: Dream stored for {aid} → asset {asset_id}")

            except Exception as e:
                logger.error(f"DREAMER: Creative dreaming failed for {aid}: {e}")
