import base64
import logging
import os
import tempfile
import json
import asyncio
from typing import Any, Optional

import httpx

from src.infrastructure.llm import LlmClient
from src.infrastructure.redis import RedisClient
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender
from src.services.visual.manager import AssetManager
from src.services.visual.provider import VisualProvider
from src.services.visual.bible import build_prompt, bible
from src.services.visual.vault import VaultService

logger = logging.getLogger(__name__)

try:
    from rembg import remove
    REMBG_AVAILABLE = True
    logger.info("POST_PROCESS: rembg is available.")
except ImportError:
    REMBG_AVAILABLE = False
    logger.warning("POST_PROCESS: rembg NOT FOUND. Background removal will be skipped.")

class VisualImaginationService:
    def __init__(
        self,
        visual_provider: VisualProvider,
        asset_manager: AssetManager,
        llm_client: LlmClient,
        redis_client: RedisClient,
        agents_base_path: str = "agents",
        vault_service: Optional[VaultService] = None,
    ):
        self.provider = visual_provider
        self.asset_manager = asset_manager
        self.llm = llm_client
        self.redis = redis_client
        self.agents_base_path = agents_base_path
        self.vault = vault_service or VaultService(self.asset_manager.db)

    async def _remove_background(self, local_path: str) -> bool:
        """Removes background from image using rembg in a separate thread."""
        if not REMBG_AVAILABLE: return False
        try:
            logger.info(f"POST_PROCESS: Removing background for {local_path}...")
            
            def _blocking_remove():
                with open(local_path, 'rb') as i:
                    input_data = i.read()
                    output_data = remove(input_data)
                    with open(local_path, 'wb') as o:
                        o.write(output_data)
            
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _blocking_remove)
            logger.info(f"POST_PROCESS_SUCCESS: Background removed for {local_path}")
            return True
        except Exception as e:
            logger.error(f"POST_PROCESS_FAILED: {e}")
            return False

    def get_agent_reference_image(self, agent_id: str) -> str | None:
        """Récupère la première image de référence définie dans le persona.yaml de l'agent."""
        # Query the bible for resolved reference paths
        ref_paths = bible.get_reference_images(agent_id)
        
        if not ref_paths:
            logger.warning(f"REFERENCE_MISSING: No valid reference sheet found for {agent_id}")
            return None

        # Take the first available reference
        ref_path = ref_paths[0]
        try:
            with open(ref_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                logger.info(f"REFERENCE_INJECTED: Loaded {ref_path} for {agent_id}")
                return f"data:image/png;base64,{encoded}"
        except Exception as e:
            logger.error(f"REFERENCE_ERROR: {e}")
            return None

    async def generate_for_agent(self, agent_id: str, prompt: str, **kwargs: Any) -> str:
        """Génère avec la Bible Visuelle et les images de référence du Persona."""
        full_prompt = build_prompt(agent_id=agent_id, description=prompt, **kwargs)
        
        # Inject Reference if available in Persona
        reference_image = self.get_agent_reference_image(agent_id)
        if reference_image:
            kwargs["reference_image"] = reference_image

        # Inject Negative Prompt from Bible if not provided
        if "negative_prompt" not in kwargs:
            kwargs["negative_prompt"] = bible.style.get("negative_prompt", "")
        
        # STORY 25.5 (FR25.8): Broadcast RAW_PROMPT for observability
        try:
            raw_payload = {"prompt": full_prompt, "agent_id": agent_id, **kwargs}
            # Clean base64 for broadcasting
            if "reference_image" in raw_payload and raw_payload["reference_image"].startswith("data:image"):
                raw_payload["reference_image"] = f"[BASE64_DATA:{len(raw_payload['reference_image'])} chars]"
            
            msg = HLinkMessage(
                type=MessageType.VISUAL_RAW_PROMPT,
                sender=Sender(agent_id="system", role="orchestrator"),
                recipient=Recipient(target="broadcast"),
                payload=Payload(content=raw_payload)
            )
            await self.redis.publish("broadcast", msg)
        except Exception as e:
            logger.warning(f"OBSERVABILITY: Failed to broadcast RAW_PROMPT: {e}")

        return await self.provider.generate(full_prompt, **kwargs)

    async def generate_and_index(self, agent_id: str, prompt: str, tags: list[str] = None, **kwargs: Any) -> tuple[str, str | None]:
        logger.info(f"VISUAL_SERVICE: Processing {agent_id}: {prompt[:50]}...")
        if agent_id.lower() != "system": kwargs["asset_type"] = "pose"
        asset_type = kwargs.get("asset_type", "background")
        
        try:
            embedding = await self.llm.get_embedding(prompt)
            existing = await self.asset_manager.get_asset_by_prompt(embedding, threshold=0.95)
            if existing:
                uri = existing[0]["url"]
                asset_id = existing[0]["id"]
                await self.notify_visual_asset(uri, prompt, agent_id, asset_type)
                return uri, asset_id

            # STORY 25.4: Resolve reference images
            ref_images = bible.get_reference_images(agent_id)
            ref_path = ref_images[0] if ref_images else ""

            image_url = await self.generate_for_agent(agent_id, prompt, **kwargs)
            
            # Support local file paths directly from provider (e.g. Google SDK)
            if image_url.startswith("file://") or image_url.startswith("/"):
                local_path = image_url.replace("file://", "")
                if not os.path.exists(local_path):
                    raise ValueError(f"Provider returned invalid local path: {local_path}")
            else:
                local_path = await self._download_image(image_url)
                
            if not local_path: raise ValueError("Download failed")
            
            if asset_type == "pose": await self._remove_background(local_path)
            
            asset_uri, asset_id = await self.index_generated_asset(local_path, agent_id, prompt, tags, reference_image_used=ref_path)
            await self.notify_visual_asset(asset_uri, prompt, agent_id, asset_type)
            return asset_uri, asset_id
        except Exception as e:
            logger.error(f"VISUAL_SERVICE: Error: {e}")
            raise

    async def index_generated_asset(self, local_path: str, agent_id: str, prompt: str, tags: list[str] = None, reference_image_used: str = "") -> tuple[str, str | None]:
        embedding = await self.llm.get_embedding(prompt)
        metadata = {
            "prompt": prompt, 
            "embedding": embedding, 
            "agent_id": agent_id, 
            "tags": tags or [],
            "reference_image_used": reference_image_used
        }
        return await self.asset_manager.save_asset(local_path, metadata)

    async def notify_visual_asset(self, url: str, prompt: str, agent_id: str, asset_type: str):
        # Convert local file path to public bridge URL for the frontend
        public_url = url
        if url.startswith("file:///media/generated/"):
            filename = url.replace("file:///media/generated/", "")
            # Assuming bridge is accessible relative to the UI or via configured base URL
            # For now we use relative path which works if served from same origin
            public_url = f"/media/{filename}"
        elif url.startswith("/media/generated/"):
             filename = url.replace("/media/generated/", "")
             public_url = f"/media/{filename}"

        msg = HLinkMessage(
            type=MessageType.VISUAL_ASSET,
            sender=Sender(agent_id="system", role="orchestrator"),
            recipient=Recipient(target="broadcast"),
            payload=Payload(content={"url": public_url, "alt_text": prompt, "agent_id": agent_id, "asset_type": asset_type})
        )
        await self.redis.publish("broadcast", msg)

    async def bootstrap_agent_avatar(self, agent_id: str, description: str):
        """Generates an initial avatar for an agent if none exist."""
        logger.info(f"BOOTSTRAP: Generating initial avatar for {agent_id}...")
        try:
            # We use generate_and_index which already handles caching and indexing
            await self.generate_and_index(
                agent_id=agent_id,
                prompt=f"Full body portrait of {agent_id}, {description}",
                tags=["avatar", "bootstrap"],
                asset_type="pose"
            )
            logger.info(f"BOOTSTRAP_SUCCESS: Initial avatar created for {agent_id}")
        except Exception as e:
            logger.error(f"BOOTSTRAP_FAILED: Could not bootstrap avatar for {agent_id}: {e}")

    async def _download_image(self, url: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=30.0)
                resp.raise_for_status()
                fd, path = tempfile.mkstemp(suffix=".png")
                with os.fdopen(fd, "wb") as tmp: tmp.write(resp.content)
                return path
        except: return None
