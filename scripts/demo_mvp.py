import asyncio
import logging
import sys
import os
from unittest.mock import AsyncMock, MagicMock

# Setup path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/h-core')))

from src.infrastructure.redis import RedisClient
from src.domain.agent import BaseAgent
from src.agents.expert_domotique import ExpertDomotiqueAgent
from src.models.agent import AgentConfig
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DEMO")

# --- MOCKS ---

class MockLlmClient:
    def __init__(self):
        self.call_count = 0

    async def get_completion(self, messages, stream=False, tools=None, return_full_object=False):
        self.call_count += 1
        logger.info(f"[LLM Mock] Call #{self.call_count} received.")
        
        if self.call_count == 1:
            # 1er appel : Le LLM décide d'utiliser l'outil
            logger.info("[LLM Mock] Decision: Use Tool 'toggle_device'")
            mock_response = MagicMock()
            message = MagicMock()
            message.tool_calls = [
                MagicMock(
                    id="call_123",
                    function=MagicMock(
                        name="toggle_device",
                        arguments='{"entity_id": "light.living_room", "action": "turn_on"}'
                    )
                )
            ]
            message.content = None
            mock_response.choices = [MagicMock(message=message)]
            return mock_response
            
        elif self.call_count == 2:
            # 2ème appel : Le LLM confirme l'action en streaming
            logger.info("[LLM Mock] Decision: Confirm action narratively")
            async def generator():
                yield "C'est "
                await asyncio.sleep(0.1)
                yield "fait, "
                await asyncio.sleep(0.1)
                yield "le "
                await asyncio.sleep(0.1)
                yield "salon "
                await asyncio.sleep(0.1)
                yield "est "
                await asyncio.sleep(0.1)
                yield "allumé."
            return generator()

class MockHaClient:
    async def call_service(self, domain, service, service_data=None):
        logger.info(f"[HA Mock] Service called: {domain}.{service} with {service_data}")
        return True

# --- MAIN ---

async def main():
    print("\n--- 🎬 DÉMARRAGE DE LA DÉMO MVP hAIrem 🎬 ---\n")
    
    # 1. Setup Infra
    redis_client = RedisClient(host="localhost", port=6379)
    await redis_client.connect()
    
    llm_client = MockLlmClient()
    
    # 2. Setup Agent
    config = AgentConfig(
        name="Expert-Domotique",
        role="Tech",
        prompt="Tu es un expert.",
        capabilities=["technical"]
    )
    
    # Injection du Mock HA dans l'agent
    agent = ExpertDomotiqueAgent(config, redis_client, llm_client)
    agent.ha_client = MockHaClient() # Override le client réel par le mock
    
    # Démarrage de l'agent (écoute Redis)
    await agent.start()
    
    # 3. Simulation Frontend (Listener)
    print("👀 Interface A2UI à l'écoute...\n")
    
    async def ui_listener(msg: HLinkMessage):
        if msg.type == MessageType.NARRATIVE_CHUNK:
            print(f"🖥️  [A2UI Stream] {msg.payload.content['content']}", end="", flush=True)
        elif msg.type == MessageType.NARRATIVE_TEXT:
            print(f"\n✅ [A2UI Final] {msg.payload.content}")
        elif msg.type == MessageType.SYSTEM_LOG:
            print(f"⚙️  [System] {msg.payload.content}")

    ui_task = asyncio.create_task(redis_client.subscribe("broadcast", ui_listener))
    await asyncio.sleep(1) # Attente souscription

    # 4. Action Utilisateur
    user_msg = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="User", role="user"),
        recipient=Recipient(target="broadcast"), # L'agent écoute son channel spécifique "agent:Expert-Domotique" normalement, mais ici on simplifie ou on envoie direct
        payload=Payload(content="Allume le salon s'il te plaît.")
    )
    
    # Pour la démo, on envoie directement à l'agent pour être sûr qu'il le prenne (le BaseAgent écoute agent:{name})
    # Mais le BaseAgent n'écoute PAS broadcast par défaut dans le code actuel (voir BaseAgent.start).
    # Il faut donc envoyer sur "agent:Expert-Domotique".
    
    print("👤 User: \"Allume le salon s'il te plaît.\"\n")
    await redis_client.publish(f"agent:Expert-Domotique", user_msg)

    # 5. Attente
    await asyncio.sleep(5)
    
    print("\n\n--- 🎬 FIN DE LA DÉMO 🎬 ---")
    await redis_client.disconnect()
    ui_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
