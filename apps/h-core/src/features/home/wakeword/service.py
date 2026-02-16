"""
Wakeword Service for hAIrem
Provides high-level interface for wakeword detection and integration with the event system.
"""

import logging
from typing import Dict, Any, Optional
from .wakeword import WakewordDetector

logger = logging.getLogger(__name__)


class WakewordService:
    """
    Service for managing wakeword detection in hAIrem.
    Integrates with Redis event bus and provides lifecycle management.
    """

    def __init__(self, config: Dict[str, Any], redis_client, surreal_client):
        self.config = config
        self.redis = redis_client
        self.surreal = surreal_client
        self.detector: Optional[WakewordDetector] = None
        self.is_active = False

    async def initialize(self) -> bool:
        """
        Initialize the wakeword service.

        Returns:
            bool: True if initialization successful
        """
        try:
            # Create wakeword detector
            self.detector = WakewordDetector(config=self.config.get("wakeword", {}), event_bus=self)

            # Initialize detector
            success = await self.detector.initialize()
            if success:
                logger.info("Wakeword service initialized successfully")
                return True
            else:
                logger.error("Failed to initialize wakeword detector")
                return False

        except Exception as e:
            logger.error(f"Failed to initialize wakeword service: {e}")
            return False

    async def start(self) -> bool:
        """
        Start wakeword detection.

        Returns:
            bool: True if started successfully
        """
        if not self.detector:
            logger.error("Wakeword detector not initialized")
            return False

        try:
            success = await self.detector.start_detection()
            if success:
                self.is_active = True
                logger.info("Wakeword detection started")
                return True
            else:
                logger.error("Failed to start wakeword detection")
                return False

        except Exception as e:
            logger.error(f"Failed to start wakeword service: {e}")
            return False

    async def stop(self) -> None:
        """Stop wakeword detection."""
        if self.detector:
            await self.detector.stop_detection()
            self.is_active = False
            logger.info("Wakeword detection stopped")

    async def publish(self, event: Dict[str, Any]) -> None:
        """
        Publish event to Redis event bus.
        This method makes WakewordService compatible with event bus interface.
        """
        try:
            # Publish to Redis channel
            channel = f"events:{event['type']}"
            await self.redis.publish(channel, event)
            logger.debug(f"Published wakeword event: {event['type']}")
        except Exception as e:
            logger.error(f"Failed to publish wakeword event: {e}")

    async def get_status(self) -> Dict[str, Any]:
        """
        Get current status of wakeword service.

        Returns:
            Dict containing status information
        """
        if not self.detector:
            return {"service": "wakeword", "initialized": False, "active": False, "error": "Detector not initialized"}

        detector_status = await self.detector.get_status()

        return {"service": "wakeword", "initialized": True, "active": self.is_active, "detector": detector_status}

    async def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        Update wakeword configuration.

        Args:
            new_config: New configuration dictionary

        Returns:
            bool: True if update successful
        """
        try:
            was_active = self.is_active

            # Stop if currently active
            if was_active:
                await self.stop()

            # Update configuration
            self.config["wakeword"].update(new_config)

            # Reinitialize detector with new config
            if self.detector:
                success = await self.detector.initialize()
                if not success:
                    logger.error("Failed to reinitialize detector with new config")
                    return False

            # Restart if was previously active
            if was_active:
                return await self.start()

            return True

        except Exception as e:
            logger.error(f"Failed to update wakeword config: {e}")
            return False
