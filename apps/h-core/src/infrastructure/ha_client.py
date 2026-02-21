import logging
import json
import os
import httpx
import asyncio
import aiohttp
from typing import Any, Optional, Dict, List

logger = logging.getLogger(__name__)


class HaClient:
    """
    Home Assistant Client for H-Core.
    Handles HTTP API calls and WebSocket event listening.
    """

    def __init__(self):
        self.base_url = os.getenv("HA_URL", "https://homeassistant.truxonline.com/api")
        # Ensure we always append /api if missing from URL
        if not self.base_url.endswith("/api"):
            self.base_url = f"{self.base_url.rstrip('/')}/api"

        self.ws_url = self.base_url.replace("http", "ws").replace("/api", "/websocket")
        self.token = os.getenv("HA_TOKEN")

        if not self.token:
            logger.warning("HA_CLIENT: No HA_TOKEN found in environment! HA integration will fail.")

        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        self._client = None

    @property
    def client(self):
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(headers=self.headers, timeout=10.0)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()

    async def call_service(self, domain: str, service: str, data: dict):
        if not self.token:
            return False
        url = f"{self.base_url}/services/{domain}/{service}"
        logger.info(f"HA_HTTP_POST: {url} | Payload: {json.dumps(data)}")
        try:
            r = await asyncio.wait_for(self.client.post(url, json=data), timeout=10.0)
            if r.status_code != 200:
                logger.error(f"HA_CALL_ERROR: Status={r.status_code}, Body={r.text}")
            return r.status_code == 200
        except asyncio.TimeoutError:
            logger.error(f"HA_CALL_TIMEOUT: {url}")
            return False
        except Exception as e:
            logger.error(f"HA_CALL_EXCEPTION: {e}")
            return False

    async def get_state(self, entity_id: str):
        if not self.token:
            return None
        try:
            r = await asyncio.wait_for(self.client.get(f"{self.base_url}/states/{entity_id}"), timeout=10.0)
            if r.status_code != 200:
                logger.error(f"HA_GET_STATE_ERROR: Entity={entity_id}, Status={r.status_code}, Body={r.text}")
            return r.json() if r.status_code == 200 else None
        except asyncio.TimeoutError:
            logger.error(f"HA_GET_STATE_TIMEOUT: {entity_id}")
            return None
        except Exception as e:
            logger.error(f"HA_GET_STATE_EXCEPTION: {e}")
            return None

    async def fetch_all_states(self) -> List[Dict[str, Any]]:
        """Fetch all entity states from Home Assistant for discovery."""
        if not self.token:
            return []
        url = f"{self.base_url}/states"
        try:
            r = await asyncio.wait_for(self.client.get(url), timeout=10.0)
            if r.status_code != 200:
                logger.error(f"HA_FETCH_ALL_ERROR: Status={r.status_code}, Body={r.text}")
                return []
            return r.json()
        except asyncio.TimeoutError:
            logger.error("HA_FETCH_ALL_TIMEOUT: Home Assistant did not respond in time.")
            return []
        except Exception as e:
            logger.error(f"HA_FETCH_ALL_EXCEPTION: {e}")
            return []

    async def listen_events(self, callback):
        """Persistent WebSocket listener for HA events with auto-reconnect."""
        if not self.token:
            logger.error("HA_WS: No token provided. Cannot listen.")
            return

        while True:
            logger.info(f"HA_WS: Connecting to {self.ws_url}...")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(self.ws_url, ssl=False) as ws:
                        # 1. Wait for 'auth_required'
                        msg = await ws.receive_json()
                        if msg.get("type") != "auth_required":
                            logger.error(f"HA_WS: Unexpected first message: {msg}")
                            await asyncio.sleep(5)
                            continue

                        # 2. Send 'auth'
                        await ws.send_json({"type": "auth", "access_token": self.token})

                        # 3. Check 'auth_ok'
                        msg = await ws.receive_json()
                        if msg.get("type") != "auth_ok":
                            logger.error(f"HA_WS: Auth failed: {msg}")
                            await asyncio.sleep(10)
                            continue

                        logger.info("HA_WS: Connected and Authenticated.")

                        # 4. Subscribe to state changes
                        await ws.send_json({"id": 1, "type": "subscribe_events", "event_type": "state_changed"})

                        # 5. Event Loop
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                if data.get("type") == "event":
                                    await callback(data.get("event", {}))
                            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                break
            except Exception as e:
                logger.error(f"HA_WS: Connection error: {e}. Retrying in 10s...")

            await asyncio.sleep(10)  # Wait before reconnecting
