import os
import logging
import httpx
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)

class HaClient:
    """Async client for Home Assistant REST API."""
    
    def __init__(self):
        self.base_url = os.getenv("HA_URL", "http://homeassistant.local:8123/api")
        self.token = os.getenv("HA_TOKEN")
        
        if not self.token:
            logger.warning("HA_TOKEN is not set. Home Assistant integration will be restricted.")
            
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def get_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Fetch the state of a specific entity."""
        url = f"{self.base_url}/states/{entity_id}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Error fetching state for {entity_id}: {e.response.status_code}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error connecting to HA: {e}")
                return None

    async def call_service(self, domain: str, service: str, service_data: Optional[Dict[str, Any]] = None) -> bool:
        """Call a Home Assistant service (e.g. light.turn_on)."""
        url = f"{self.base_url}/services/{domain}/{service}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url, 
                    headers=self.headers, 
                    json=service_data or {},
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Successfully called service {domain}.{service}")
                return True
            except Exception as e:
                logger.error(f"Failed to call service {domain}.{service}: {e}")
                return False

    async def check_connection(self) -> bool:
        """Verify the connection and token validity."""
        url = f"{self.base_url}/"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers)
                return response.status_code == 200 and "API running" in response.text
            except Exception:
                return False
