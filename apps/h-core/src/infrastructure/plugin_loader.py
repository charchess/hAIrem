import os
import yaml
import logging
import asyncio
from typing import Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.models.agent import AgentConfig, AgentInstance
from src.agents.expert_domotique import ExpertDomotiqueAgent

logger = logging.getLogger(__name__)

class AgentRegistry:
    def __init__(self):
        self.agents: Dict[str, Any] = {} # Use Any to allow subclasses

    def add_agent(self, agent: Any):
        self.agents[agent.config.name] = agent
        logger.info(f"Agent '{agent.config.name}' registered/updated successfully.")

class AgentFileHandler(FileSystemEventHandler):
    def __init__(self, registry: AgentRegistry, loop: asyncio.AbstractEventLoop, redis_client, llm_client):
        self.registry = registry
        self.loop = loop
        self.redis = redis_client
        self.llm = llm_client

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith("expert.yaml"):
            logger.info(f"Detection of modification in: {event.src_path}")
            self.loop.call_soon_threadsafe(asyncio.create_task, self._load_agent(event.src_path))

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith("expert.yaml"):
            logger.info(f"New agent file detected: {event.src_path}")
            self.loop.call_soon_threadsafe(asyncio.create_task, self._load_agent(event.src_path))

    async def _load_agent(self, file_path: str):
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            config = AgentConfig.model_validate(data)
            
            # Instanciation de la classe spécifique si nécessaire
            if config.name == "Expert-Domotique":
                instance = ExpertDomotiqueAgent(config=config, redis_client=self.redis, llm_client=self.llm)
            else:
                from src.domain.agent import BaseAgent
                instance = BaseAgent(config=config, redis_client=self.redis, llm_client=self.llm)
            
            await instance.start()
            self.registry.add_agent(instance)
        except Exception as e:
            logger.error(f"Failed to load agent from {file_path}: {e}")

class PluginLoader:
    def __init__(self, agents_dir: str, registry: AgentRegistry, redis_client, llm_client):
        self.agents_dir = agents_dir
        self.registry = registry
        self.redis = redis_client
        self.llm = llm_client
        self.observer = Observer()

    async def start(self):
        # Initial scan
        await self._initial_scan()
        
        # Start watching
        loop = asyncio.get_running_loop()
        handler = AgentFileHandler(self.registry, loop, self.redis, self.llm)
        self.observer.schedule(handler, self.agents_dir, recursive=True)
        self.observer.start()
        logger.info(f"Plugin Loader started. Watching directory: {self.agents_dir}")

    async def _initial_scan(self):
        logger.info("Performing initial agent scan...")
        for root, _, files in os.walk(self.agents_dir):
            for file in files:
                if file == "expert.yaml":
                    await self._load_agent(os.path.join(root, file))

    async def _load_agent(self, file_path: str):
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            config = AgentConfig.model_validate(data)
            
            if config.name == "Expert-Domotique":
                instance = ExpertDomotiqueAgent(config=config, redis_client=self.redis, llm_client=self.llm)
            else:
                from src.domain.agent import BaseAgent
                instance = BaseAgent(config=config, redis_client=self.redis, llm_client=self.llm)
            
            await instance.start()
            self.registry.add_agent(instance)
        except Exception as e:
            logger.error(f"Initial load failed for {file_path}: {e}")

    def stop(self):
        self.observer.stop()
        self.observer.join()
        logger.info("Plugin Loader stopped.")
