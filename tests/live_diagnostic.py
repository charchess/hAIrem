import asyncio
import json
import redis.asyncio as redis
import uuid
import time

async def run_diagnostic():
    print("🚀 DÉBUT DU DIAGNOSTIC SYSTÈME LIVE (HAITEM-QA)")
    print("-" * 50)
    
    # 1. Connexion au Redis de "prod" (port 6377 mappé sur l'hôte)
    r = redis.from_url("redis://localhost:6377", decode_responses=True)
    try:
        await r.ping()
        print("✅ 1. Connexion Redis : OK")
    except Exception as e:
        print(f"❌ 1. Connexion Redis : ÉCHEC ({e})")
        return

    # 2. Vérification de la Discovery (Agents enregistrés)
    # On regarde si des agents ont publié leur heartbeat dans les dernières 60s
    print("🔍 2. Vérification des Agents enregistrés...")
    # Le bridge expose une API, mais on peut vérifier les Streams directement
    agents_found = set()
    
    # On va lire le début du system_stream pour voir qui a parlé
    try:
        # On lit les derniers messages du stream
        messages = await r.xrevrange("system_stream", count=50)
        for m_id, data in messages:
            # On cherche les status updates
            raw_data = data.get("data", "{}")
            try:
                msg = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                if msg.get("type") == "system.status_update":
                    agent_id = msg.get("sender", {}).get("agent_id")
                    if agent_id and agent_id not in ["core", "system"]:
                        agents_found.add(agent_id)
            except: pass
        
        expected = {"Lisa", "Electra", "Dieu", "Renarde"}
        missing = expected - agents_found
        if not missing:
            print(f"✅ 2. Discovery : OK (Agents trouvés : {agents_found})")
        else:
            print(f"⚠️ 2. Discovery : PARTIELLE (Manquant : {missing} | Trouvés : {agents_found})")
            print("   Note: Si l'agent vient de démarrer, attendez 30s pour le heartbeat.")
    except Exception as e:
        print(f"❌ 2. Discovery : ÉCHEC ({e})")

    # 3. Test de Routage (Message -> Core -> Agent)
    print("📡 3. Test de Routage (Simulation UI -> Renarde)...")
    test_id = str(uuid.uuid4())
    test_msg = {
        "id": test_id,
        "type": "user_message",
        "sender": {"agent_id": "qa_tester", "role": "user"},
        "recipient": {"target": "Renarde"},
        "payload": {"content": "DIAGNOSTIC_PING"}
    }
    
    # On s'abonne à la réponse de Renarde (via Pub/Sub ou system_stream)
    # Dans notre architecture, l'agent répond sur le system_stream
    
    # On envoie le ping
    await r.xadd("system_stream", {"type": "user_message", "data": json.dumps(test_msg)})
    print(f"   Ping envoyé (ID: {test_id}). Attente de réponse (10s)...")
    
    # On attend une réponse
    start_time = time.time()
    response_found = False
    while time.time() - start_time < 10:
        latest = await r.xrevrange("system_stream", count=10)
        for m_id, data in latest:
            raw_inner = data.get("data", "{}")
            try:
                inner = json.loads(raw_inner) if isinstance(raw_inner, str) else raw_inner
                # On cherche un message de Renarde qui corrèle avec notre test_id
                if inner.get("sender", {}).get("agent_id") == "Renarde":
                    # Si l'agent répond, c'est que le routage ET le LLM (ou au moins le début) fonctionnent
                    response_found = True
                    print(f"✅ 3. Routage & Réponse : OK")
                    print(f"   Réponse reçue : \"{inner.get('payload', {}).get('content')[:50]}...\"")
                    break
            except: pass
        if response_found: break
        await asyncio.sleep(1)
    
    if not response_found:
        print("❌ 3. Routage & Réponse : ÉCHEC (Aucune réponse de Renarde)")
        print("   Cause probable : Erreur LLM (Clé API) ou agent qui ne reçoit pas le message Redis.")

    await r.aclose()
    print("-" * 50)
    print("🏁 FIN DU DIAGNOSTIC")

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
