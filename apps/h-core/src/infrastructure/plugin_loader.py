import os
import yaml
import logging
import asyncio
import importlib.util
from typing import Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.models.agent import AgentConfig, AgentInstance

logger = logging.getLogger(__name__)

class AgentRegistry:
    def __init__(self):
        self.agents: Dict[str, Any] = {}

    def add_agent(self, agent: Any):
        self.agents[agent.config.name] = agent
        logger.info(f"AGENT_REGISTRY: Agent '{agent.config.name}' registered successfully.")

class AgentFileHandler(FileSystemEventHandler):
    def __init__(self, registry: AgentRegistry, loop: asyncio.AbstractEventLoop, redis_client, llm_client, surreal_client=None):
        self.registry = registry
        self.loop = loop
        self.redis = redis_client
        self.llm = llm_client
        self.surreal = surreal_client

    def on_modified(self, event):
        if event.is_directory: return
        if event.src_path.endswith("expert.yaml"):
            self.loop.call_soon_threadsafe(asyncio.create_task, self._load_agent(event.src_path))

    async def _load_agent(self, file_path: str):
        # Implementation hidden for brevity, same as below
        pass

class PluginLoader:
    def __init__(self, agents_dir: str, registry: AgentRegistry, redis_client, llm_client, surreal_client=None):
        self.agents_dir = os.path.abspath(agents_dir)
        self.registry = registry
        self.redis = redis_client
        self.llm = llm_client
        self.surreal = surreal_client
        self.observer = Observer()
        logger.info(f"PLUGIN_LOADER: Initialized with path {self.agents_dir}")

    async def start(self):
        logger.info("PLUGIN_LOADER: Starting initial scan...")
        await self._initial_scan()
        
        try:
            loop = asyncio.get_running_loop()
            handler = AgentFileHandler(self.registry, loop, self.redis, self.llm, self.surreal)
            self.observer.schedule(handler, self.agents_dir, recursive=True)
            self.observer.start()
            logger.info(f"PLUGIN_LOADER: Watcher started on {self.agents_dir}")
        except Exception as e:
            logger.error(f"PLUGIN_LOADER: Failed to start watcher: {e}")

    async def _initial_scan(self):
        if not os.path.exists(self.agents_dir):
            logger.error(f"PLUGIN_LOADER: Directory not found: {self.agents_dir}")
            return

        count = 0
        for root, _, files in os.walk(self.agents_dir):
            for file in files:
                if file == "expert.yaml" or file == "agent.yaml":
                    logger.info(f"PLUGIN_LOADER: Found agent config at {os.path.join(root, file)}")
                    await self._load_agent(os.path.join(root, file))
                    count += 1
        logger.info(f"PLUGIN_LOADER: Initial scan complete. {count} agents found.")

    async def _load_agent(self, file_path: str):
        logger.info(f"PLUGIN_LOADER: Loading agent from {file_path}")
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Simple validation to avoid pydantic errors blocking everything
            if not data or 'name' not in data:
                logger.error(f"PLUGIN_LOADER: Invalid config in {file_path}")
                return

            config = AgentConfig.model_validate(data)
            from src.domain.agent import BaseAgent
            instance = BaseAgent(config=config, redis_client=self.redis, llm_client=self.llm, surreal_client=self.surreal)
            
            await instance.start()
            self.registry.add_agent(instance)
            logger.info(f"PLUGIN_LOADER: Agent {config.name} is now LIVE.")
        except Exception as e:
            logger.error(f"PLUGIN_LOADER: Failed to load agent {file_path}: {e}")

    def stop(self):
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        logger.info("PLUGIN_LOADER: Stopped.")
