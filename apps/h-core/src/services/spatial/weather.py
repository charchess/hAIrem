import logging

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Manages simulated exterior weather conditions (Epic 9).
    """

    def __init__(self, redis_client):
        self.redis = redis_client
        self.current_weather = "Clear"

    async def set_weather(self, weather_condition: str):
        """
        FR50: Exterior Space.
        Updates the simulated weather.
        """
        logger.info(f"WEATHER: Changing weather to '{weather_condition}'")
        self.current_weather = weather_condition
        # Could broadcast event here

    def get_context_string(self) -> str:
        """
        Returns a prompt context string describing the weather.
        """
        return f"Current exterior weather is {self.current_weather}."
