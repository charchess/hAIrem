import asyncio
import json
import os
import sys
import logging
from redis.asyncio import Redis

# Setup path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/h-core')))

from src.infrastructure.redis import RedisClient
from src.agents.expert_domotique import ExpertDomotiqueAgent
from src.models.agent import AgentConfig
from src.infrastructure.llm import LlmClient

logging.basicConfig(level=logging.INFO)

async def main():
    print("--- 🚀 Test Intégration Directe H-Link 🚀 ---")
    
    # 1. Setup
    redis_client = RedisClient(host="localhost", port=6379)
    await redis_client.connect()
    
    # On mocke le LLM car on n'en a pas besoin pour /echo
    llm_client = LlmClient() 
    
    config = AgentConfig(name="Expert-Domotique", role="Tech")
    agent = ExpertDomotiqueAgent(config, redis_client, llm_client)
    
    # 2. Démarrage Agent
    await agent.start()
    print("✅ Agent 'Expert-Domotique' à l'écoute.")

    # 3. Simulation du message de l'utilisateur (Slash Command)
    slash_msg = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2026-01-21T10:00:00Z",
        "type": "expert.command",
        "sender": {"agent_id": "user", "role": "user"},
        "recipient": {"target": "Expert-Domotique"},
        "payload": {"content": {"command": "echo", "args": "C'est_Genial"}, "format": "json"},
        "metadata": {"priority": "high", "ttl": 5}
    }

    # 4. Écoute de la réponse
    pubsub = redis_client.client.pubsub()
    await pubsub.subscribe("agent:user")
    print("👀 En attente de la réponse sur 'agent:user'...")

    # Publie la commande
    await asyncio.sleep(2) # Attente pour être sûr que le sub est actif
    print("📤 Publication de la commande...")
    await redis_client.client.publish("agent:Expert-Domotique", json.dumps(slash_msg))

    # Récupère la réponse
    for _ in range(10):
        message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
        if message:
            data = json.loads(message["data"])
            print(f"\n🎉 RÉPONSE REÇUE : {data['payload']['content']}")
            break
        await asyncio.sleep(0.5)
    else:
        print("\n❌ Pas de réponse reçue.")

    await redis_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
