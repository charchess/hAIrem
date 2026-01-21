import asyncio
import logging
import sys
import os

# Ajout du path pour importer les modules du h-core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/h-core')))

from src.infrastructure.plugin_loader import AgentRegistry, PluginLoader
from src.infrastructure.redis import RedisClient

logging.basicConfig(level=logging.INFO)

async def main():
    print("--- Validation End-to-End Sprint 2 ---")
    
    # 1. Setup Redis
    redis_client = RedisClient(host="localhost", port=6379)
    try:
        await redis_client.connect()
        print("✅ Redis: Connecté")
    except Exception as e:
        print(f"❌ Redis: Échec connexion ({e})")
        sys.exit(1)

    # 2. Setup Loader
    registry = AgentRegistry()
    loader = PluginLoader(agents_dir="agents", registry=registry)
    
    # 3. Chargement Agents
    print("\n--- Chargement des Agents ---")
    await loader._initial_scan()
    
    loaded_agents = list(registry.agents.keys())
    print(f"Agents chargés : {loaded_agents}")
    
    agents_ok = "Renarde" in loaded_agents and "Expert-Domotique" in loaded_agents
    if agents_ok:
        print("✅ Agents: Chargement OK")
    else:
        print("❌ Agents: Chargement incomplet")

    # 4. Cleanup
    await redis_client.disconnect()
    
    if agents_ok:
        print("\n🎉 SUCCÈS TOTAL : Le système est prêt.")
    else:
        print("\n⚠️ ÉCHEC PARTIEL")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())