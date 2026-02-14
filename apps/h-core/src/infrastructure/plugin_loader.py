import asyncio
import importlib.util
import logging
import os
from typing import Any

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src.models.agent import AgentConfig

logger = logging.getLogger(__name__)

class AgentRegistry:
    def __init__(self):
        self.agents: dict[str, Any] = {}

    def add_agent(self, agent: Any):
        self.agents[agent.config.name] = agent
        logger.info(f"AGENT_REGISTRY: Agent '{agent.config.name}' registered successfully.")

class AgentFileHandler(FileSystemEventHandler):
    def __init__(self, registry: AgentRegistry, loop: asyncio.AbstractEventLoop, redis_client, llm_client, surreal_client=None, visual_service=None):
        self.registry = registry
        self.loop = loop
        self.redis = redis_client
        self.llm = llm_client
        self.surreal = surreal_client
        self.visual_service = visual_service

    def on_modified(self, event):
        if event.is_directory: return
        filename = os.path.basename(event.src_path)
        if filename in ["manifest.yaml", "persona.yaml", "logic.py"]:
            manifest_path = event.src_path
            if filename != "manifest.yaml":
                manifest_path = os.path.join(os.path.dirname(event.src_path), "manifest.yaml")
            
            if os.path.exists(manifest_path):
                self.loop.call_soon_threadsafe(asyncio.create_task, self._load_agent(manifest_path))

    def on_created(self, event):
        if event.is_directory:
            manifest_path = os.path.join(event.src_path, "manifest.yaml")
            if os.path.exists(manifest_path):
                logger.info(f"PLUGIN_LOADER: New agent folder detected: {event.src_path}")
                self.loop.call_soon_threadsafe(asyncio.create_task, self._load_agent(manifest_path))

    async def _load_agent(self, manifest_path: str):
        pass

class PluginLoader:
    def __init__(self, agents_dir: str, registry: AgentRegistry, redis_client, llm_client, surreal_client=None, visual_service=None, token_tracking_service=None):
        self.agents_dir = os.path.abspath(agents_dir)
        self.registry = registry
        self.redis = redis_client
        self.llm = llm_client
        self.surreal = surreal_client
        self.visual_service = visual_service
        self.token_tracking_service = token_tracking_service
        self.observer = Observer()
        logger.info(f"PLUGIN_LOADER: Initialized with path {self.agents_dir}")

    async def start(self):
        logger.info("PLUGIN_LOADER: Starting initial scan...")
        await self._initial_scan()
        
        try:
            loop = asyncio.get_running_loop()
            handler = AgentFileHandler(self.registry, loop, self.redis, self.llm, self.surreal, self.visual_service)
            handler._load_agent = self._load_agent # type: ignore
            
            self.observer.schedule(handler, self.agents_dir, recursive=True)
            self.observer.start()
            logger.info(f"PLUGIN_LOADER: Watcher started on {self.agents_dir}")
        except Exception as e:
            logger.error(f"PLUGIN_LOADER: Failed to start watcher: {e}")

    async def _initial_scan(self):
        if not os.path.exists(self.agents_dir):
            logger.error(f"PLUGIN_LOADER: Directory not found: {self.agents_dir}")
            return

        logger.info(f"PLUGIN_LOADER: Scanning {self.agents_dir}...")
        count = 0
        for root, _dirs, files in os.walk(self.agents_dir):
            if "manifest.yaml" in files:
                await self._load_agent(os.path.join(root, "manifest.yaml"))
                count += 1
        logger.info(f"PLUGIN_LOADER: Initial scan complete. {count} agents found.")

    async def _load_agent(self, manifest_path: str):
        logger.info(f"PLUGIN_LOADER: Loading agent bundle from {manifest_path}")
        try:
            agent_dir = os.path.dirname(manifest_path)
            
            with open(manifest_path) as f:
                manifest_data = yaml.safe_load(f) or {}
            
            persona_path = os.path.join(agent_dir, "persona.yaml")
            persona_data = {}
            if os.path.exists(persona_path):
                with open(persona_path) as f:
                    persona_data = yaml.safe_load(f) or {}
            
            combined_data = {**manifest_data, **persona_data}
            if "system_prompt" in combined_data and "prompt" not in combined_data:
                combined_data["prompt"] = combined_data.pop("system_prompt")
            
            if "name" not in combined_data and "id" in combined_data:
                combined_data["name"] = combined_data["id"]

            if not combined_data.get("name"):
                logger.error(f"PLUGIN_LOADER: Missing 'name' or 'id' in {manifest_path}")
                return

            if "role" not in combined_data:
                combined_data["role"] = "Unknown"

            config = AgentConfig.model_validate(combined_data)
            
            agent_llm = self.llm
            if config.llm_config:
                from src.infrastructure.llm import LlmClient
                agent_llm = LlmClient(cache=self.llm.cache, config_override=config.llm_config)

            agent_class = None
            logic_path = os.path.join(agent_dir, "logic.py")
            
            if os.path.exists(logic_path):
                try:
                    spec = importlib.util.spec_from_file_location(f"agent_logic_{config.name.replace('-', '_')}", logic_path)
                    module = importlib.util.module_from_spec(spec) # type: ignore
                    spec.loader.exec_module(module) # type: ignore
                    if hasattr(module, "Agent"):
                        loaded_class = module.Agent
                        from src.domain.agent import BaseAgent
                        if issubclass(loaded_class, BaseAgent):
                            agent_class = loaded_class
                except Exception as e:
                    logger.error(f"PLUGIN_LOADER: Failed to load custom logic from {logic_path}: {e}")

            if not agent_class:
                from src.domain.agent import BaseAgent
                agent_class = BaseAgent

            instance = agent_class(
                config=config, 
                redis_client=self.redis, 
                llm_client=agent_llm, 
                surreal_client=self.surreal, 
                visual_service=self.visual_service,
                token_tracking_service=self.token_tracking_service
            )
            
            if config.name in self.registry.agents:
                old_agent = self.registry.agents[config.name]
                await old_agent.stop()

            await instance.start()
            self.registry.add_agent(instance)

            # STORY 25.1 DEVIATION: Automatic Avatar Bootstrap
            if self.visual_service and config.name.lower() not in ["dieu", "system"]:
                ref_path = os.path.join(agent_dir, "media", "character_sheet_neutral.png")
                if not os.path.exists(ref_path):
                    description = config.prompt or config.role or "A unique AI persona"
                    asyncio.create_task(self.visual_service.bootstrap_agent_avatar(config.name, description))

        except Exception as e:
            logger.error(f"PLUGIN_LOADER: Failed to load agent {manifest_path}: {e}")

    def stop(self):
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        logger.info("PLUGIN_LOADER: Stopped.")

    async def load_agent_from_folder(self, folder_path: str):
        manifest_path = os.path.join(folder_path, "manifest.yaml")
        if os.path.exists(manifest_path):
            await self._load_agent(manifest_path)
            return True
        logger.warning(f"PLUGIN_LOADER: No manifest.yaml found in {folder_path}")
        return False

    async def create_agent_folder(self, agent_data: dict[str, Any]) -> str | None:
        try:
            agent_name = agent_data.get("name")
            if not agent_name:
                return None
            
            agent_folder = os.path.join(self.agents_dir, agent_name)
            os.makedirs(agent_folder, exist_ok=True)
            
            manifest_path = os.path.join(agent_folder, "manifest.yaml")
            with open(manifest_path, "w") as f:
                yaml.dump(agent_data, f, default_flow_style=False)
            
            logger.info(f"PLUGIN_LOADER: Created agent folder at {agent_folder}")
            return agent_folder
        except Exception as e:
            logger.error(f"PLUGIN_LOADER: Failed to create agent folder: {e}")
            return None