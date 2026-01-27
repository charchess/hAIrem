import logging
import re
import json
import os
import httpx
import asyncio
import aiohttp
from typing import Any, Optional, Dict, List
from src.domain.agent import BaseAgent
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

logger = logging.getLogger(__name__)

class HaClient:
    def __init__(self):
        self.base_url = os.getenv("HA_URL", "https://homeassistant.truxonline.com/api")
        # Ensure we always append /api if missing from URL
        if not self.base_url.endswith("/api"):
            self.base_url = f"{self.base_url.rstrip('/')}/api"
            
        self.ws_url = self.base_url.replace("http", "ws").replace("/api", "/websocket")
        self.token = os.getenv("HA_TOKEN")
        
        if not self.token:
            logger.warning("ELECTRA_HA: No HA_TOKEN found in environment!")
            
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        self._client = None

    @property
    def client(self):
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(headers=self.headers, timeout=10.0)
        return self._client

    async def close(self):
        if self._client: await self._client.aclose()

    async def call_service(self, domain: str, service: str, data: dict):
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
            
            await asyncio.sleep(10) # Wait before reconnecting

class Agent(BaseAgent):
    def setup(self):
        super().setup()
        self.ha = HaClient()
        self.tools = {}
        self.tool("Get state")(self.get_entity_state)
        self.tool("Action")(self.call_ha_service)
        self.device_inventory = {} 
        logger.info("ELECTRA_LOGIC: Setup Complete.")

    async def async_setup(self):
        """Dynamic discovery of ALL lights from Home Assistant."""
        logger.info("ELECTRA_DISCOVERY: Scanning all devices...")
        all_states = await self.ha.fetch_all_states()
        
        if all_states:
            for state in all_states:
                eid = state.get("entity_id", "")
                if eid.startswith("light."):
                    friendly_name = state.get("attributes", {}).get("friendly_name", eid)
                    self.device_inventory[eid] = friendly_name
                    logger.info(f"ELECTRA_DISCOVERY: Loaded {eid} ('{friendly_name}')")
        
        logger.info(f"ELECTRA_DISCOVERY: Found {len(self.device_inventory)} lights.")

    async def teardown(self):
        """Ensure HaClient is closed on teardown."""
        if hasattr(self, 'ha'):
            await self.ha.close()
            logger.info(f"Agent {self.config.name} resources cleaned up.")

    @property
    def system_prompt(self) -> str:
        p = super().system_prompt
        if self.device_inventory:
            p += "\n\nTU AS LE CONTRÔLE SUR LES APPAREILS SUIVANTS :\n"
            for eid, name in self.device_inventory.items():
                p += f"- {eid} (nommé '{name}')\n"
            p += "\n**IMPORTANT :** Si l'utilisateur demande une action sur un nom ambigu (ex: 'plafonnier' alors qu'il y en a plusieurs), demande-lui de préciser lequel."
            p += "\nUtilise l'outil `call_ha_service` avec l'entity_id exact."
        else:
            p += "\n\nATTENTION : Aucun inventaire domotique trouvé. Signale-le."
        return p

    async def get_entity_state(self, eid):
        s = await self.ha.get_state(eid)
        return s.get("state") if s else "Unknown"

    async def call_ha_service(self, service, entity_id, **kwargs):
        """
        Appelle un service Home Assistant.
        Format attendu par l'API HA : POST /api/services/<domain>/<service>
        Payload attendu (PLAT) : {"entity_id": "light.xyz", "brightness": 100}
        """
        logger.info(f"ELECTRA_HA_CALL: raw_service={service}, entity_id={entity_id}, extra={kwargs}")
        
        # 1. Extraction du domaine et service (ex: 'light.turn_off' -> domain='light', service='turn_off')
        domain = "light"
        final_service = service
        if "." in service:
            parts = service.split(".", 1)
            domain = parts[0]
            final_service = parts[1]

        # 2. Resolve entity_id (Friendly Name -> ID)
        target_eid = entity_id
        if target_eid not in self.device_inventory:
            matches = []
            for eid, name in self.device_inventory.items():
                if target_eid.lower() in name.lower() or name.lower() in target_eid.lower():
                    matches.append(eid)
            
            if len(matches) == 1:
                target_eid = matches[0]
            elif len(matches) > 1:
                names = [self.device_inventory[m] for m in matches]
                return f"Error: Ambiguous name '{entity_id}'. Found: {', '.join(names)}"

        # 3. Construction du payload FINAL (doit être plat pour HA)
        # Exemple cible : {"entity_id": "light.tradfri_bulb_3", "brightness": 255}
        payload = {"entity_id": target_eid}
        
        # Gestion robuste des arguments supplémentaires
        # Grok envoie souvent 'kwargs': '{}' (string) ou 'kwargs': {} (dict)
        if "kwargs" in kwargs:
            extra = kwargs["kwargs"]
            # Cas 1 : Le LLM a envoyé une chaîne JSON (ex: '{"brightness": 100}')
            if isinstance(extra, str) and extra.strip() and extra != "{}":
                try:
                    parsed = json.loads(extra)
                    if isinstance(parsed, dict):
                        payload.update(parsed)
                except Exception as e:
                    logger.warning(f"ELECTRA_HA: Erreur parse JSON dans kwargs: {extra} - {e}")
            # Cas 2 : Le LLM a envoyé un vrai dictionnaire
            elif isinstance(extra, dict):
                payload.update(extra)

        # Cas 3 : Le LLM envoie des paramètres directs (ex: call_ha_service(..., brightness=100))
        for k, v in kwargs.items():
            if k != "kwargs" and v is not None and v != "":
                payload[k] = v

        logger.info(f"ELECTRA_HA_SENDING: domain={domain}, service={final_service}, payload={payload}")
        success = await self.ha.call_service(domain, final_service, payload)
        
        logger.info(f"ELECTRA_HA_RESULT: target={target_eid}, success={success}")
        return "Done" if success else "Failed to call Home Assistant (check logs for 400 error details)"
