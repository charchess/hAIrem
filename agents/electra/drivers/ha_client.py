import os
import logging
import httpx
from typing import Any, Optional, Dict, List

logger = logging.getLogger(__name__)

class HaClient:
    """Async client for Home Assistant REST API, specialized for Electra."""
    
    def __init__(self):
        self.base_url = os.getenv("HA_URL", "http://homeassistant.local:8123/api")
        self.token = os.getenv("HA_TOKEN")
        
        if not self.token:
            logger.warning("HA_TOKEN is not set. Home Assistant integration will be restricted.")
            
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy initialization of the AsyncClient."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(headers=self.headers, timeout=10.0)
        return self._client

    async def close(self):
        """Close the underlying AsyncClient."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def get_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Fetch the state of a specific entity."""
        url = f"{self.base_url}/states/{entity_id}"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Error fetching state for {entity_id}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error connecting to HA: {e}")
            return None

    async def fetch_all_states(self) -> List[Dict[str, Any]]:
        """Fetch all entity states from Home Assistant for discovery."""
        url = f"{self.base_url}/states"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch all states: {e}")
            return []

    async def call_service(self, domain: str, service: str, service_data: Optional[Dict[str, Any]] = None) -> bool:
        """Call a Home Assistant service."""
        url = f"{self.base_url}/services/{domain}/{service}"
        try:
            response = await self.client.post(
                url, 
                json=service_data or {}
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
        try:
            response = await self.client.get(url)
            return response.status_code == 200 and "API running" in response.text
        except Exception:
            return False