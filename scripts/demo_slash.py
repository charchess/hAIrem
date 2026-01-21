import asyncio
import logging
import sys
import os
import json

# Setup path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/h-core')))

from src.infrastructure.redis import RedisClient
from src.agents.expert_domotique import ExpertDomotiqueAgent
from src.models.agent import AgentConfig
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DEMO-SLASH")

async def main():
    print("\n--- ⚡ DÉMO SLASH COMMANDS hAIrem ⚡ ---\n")
    
    redis_client = RedisClient(host="localhost", port=6379)
    await redis_client.connect()
    
    # Init Agent (On simule un agent sans LLM pour prouver le bypass)
    config = AgentConfig(name="Expert-Domotique", role="Tech")
    agent = ExpertDomotiqueAgent(config, redis_client, None) # Pas de LLM
    await agent.start()

    # Listener pour la réponse
    print("👀 Attente de la réponse sur le canal utilisateur...")
    
    async def response_handler(msg: HLinkMessage):
        if msg.type == MessageType.EXPERT_RESPONSE:
            print(f"📥 Réponse reçue de {msg.sender.agent_id}: {msg.payload.content}")

    # L'utilisateur écoute sur son propre canal fictif
    await redis_client.subscribe("agent:user", response_handler)
    await asyncio.sleep(1)

    # Simulation de l'envoi du message Slash par network.js
    # Commande: /Expert-Domotique ping
    slash_msg = HLinkMessage(
        type=MessageType.EXPERT_COMMAND,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="Expert-Domotique"),
        payload=Payload(content={"command": "ping", "args": ""})
    )

    print("📤 Envoi de la commande: /Expert-Domotique ping")
    await redis_client.publish("agent:Expert-Domotique", slash_msg)

    await asyncio.sleep(2)
    print("\n--- ⚡ FIN DE LA DÉMO ⚡ ---")
    await redis_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
