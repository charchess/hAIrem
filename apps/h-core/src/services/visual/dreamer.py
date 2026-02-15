import logging
from datetime import datetime

# Define logger FIRST
logger = logging.getLogger(__name__)

try:
    from electra.drivers.ha_client import HaClient
except ImportError:
    # Handle both absolute and relative if sys.path is messed up
    try:
        from agents.electra.drivers.ha_client import HaClient
    except ImportError:
        logger.warning("Dreamer: HaClient not found, using mock")
        class HaClient:
            async def get_state(self, *args, **kwargs): return {}
from src.services.visual.service import VisualImaginationService


class Dreamer:
    """
    Orchestrates proactive image generation during sleep cycles.
    """

    def __init__(self, ha_client: HaClient, visual_service: VisualImaginationService):
        self.ha = ha_client
        self.visual_service = visual_service

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

    async def prepare_daily_assets(self, agent_id: str = "system"):
        """
        Analyzes context, constructs prompt, and triggers proactive generation via VisualImaginationService.
        """
        logger.info("DREAMER: Starting proactive asset generation...")

        try:
            weather = await self.get_weather_context()
            time_of_day = await self.get_time_of_day_context()

            prompt = (
                f"A view from the window, {weather} weather, {time_of_day}, cinematic style, high detail, masterpiece"
            )
            logger.info(f"DREAMER: Generated prompt: {prompt}")

            # Use the consolidated service logic
            asset_uri, _ = await self.visual_service.generate_and_index(
                agent_id=agent_id,
                prompt=prompt,
                tags=["proactive", f"weather:{weather}", f"time:{time_of_day}"]
            )
            
            logger.info(f"DREAMER: Proactive asset ready at {asset_uri}")

        except Exception as e:
            logger.error(f"DREAMER: Failed to prepare proactive assets: {e}")