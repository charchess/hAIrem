import asyncio
import json
import redis.asyncio as redis
import uuid
import time
import os

async def run_final_validation():
    print("🕵️ Quinn - VALIDATION FINALE DU SYSTÈME")
    print("-" * 60)
    
    r = redis.from_url("redis://localhost:6377", decode_responses=True)
    
    # 1. Vérification de la Discovery (API Bridge)
    print("🔍 1. Test Discovery (Les agents parlent-ils au Bridge ?)...")
    agents_found = []
    # On simule un appel à l'API agents
    try:
        # On va regarder les agents enregistrés dans le Stream Redis (ce que fait le Bridge)
        messages = await r.xrevrange("system_stream", count=100)
        for _, data in messages:
            raw_inner = data.get("data", "{}")
            try:
                msg = json.loads(raw_inner) if isinstance(raw_inner, str) else raw_inner
                if msg.get("type") == "system.status_update":
                    agent_id = msg.get("sender", {}).get("agent_id")
                    if agent_id and agent_id not in ["core", "system", "QA_TEST_AGENT"]:
                        if agent_id not in agents_found:
                            agents_found.append(agent_id)
            except: pass
        
        if len(agents_found) >= 4:
            print(f"✅ Discovery : SUCCÈS ({len(agents_found)} agents trouvés : {agents_found})")
        else:
            print(f"⚠️ Discovery : INCOMPLÈTE ({len(agents_found)}/4 agents : {agents_found})")
    except Exception as e:
        print(f"❌ Discovery : ERREUR ({e})")

    # 2. Test de Routage (Message -> Core -> Agent -> LLM)
    print("📡 2. Test de Réponse de Renarde (Flux complet)...")
    test_id = str(uuid.uuid4())
    # Format exact attendu par le Core
    test_msg = {
        "id": test_id,
        "type": "user_message",
        "sender": {"agent_id": "user", "role": "user"},
        "recipient": {"target": "Renarde"},
        "payload": {"content": "DIAGNOSTIC_FINAL_CHECK"}
    }
    
    await r.xadd("system_stream", {"type": "user_message", "data": json.dumps(test_msg)})
    print(f"   Message envoyé à Renarde. Attente de réponse...")

    # 3. Écoute des logs LLM et de la réponse
    response_received = False
    llm_error_detected = False
    
    start_time = time.time()
    while time.time() - start_time < 15:
        # On regarde les messages récents sur system_stream
        messages = await r.xrevrange("system_stream", count=10)
        for _, data in messages:
            raw_inner = data.get("data", "{}")
            try:
                inner = json.loads(raw_inner) if isinstance(raw_inner, str) else raw_inner
                # Si Renarde répond
                if inner.get("sender", {}).get("agent_id") == "Renarde" and inner.get("type") == "narrative.text":
                    response_received = True
                    print(f"✅ 2. Réponse Renarde : REÇUE")
                    print(f"   Message : \"{inner.get('payload', {}).get('content')}\"")
                    break
                # Si le Core logue une erreur LLM
                if inner.get("type") == "system.log" and "AuthenticationError" in str(inner.get("payload", {}).get("content")):
                    llm_error_detected = True
            except: pass
        
        if response_received or llm_error_detected:
            break
        await asyncio.sleep(1)

    if not response_received:
        if llm_error_detected:
            print("❌ 2. Réponse Renarde : BLOQUÉE (Erreur d'authentification LLM détectée)")
            print("   => Le pont fonctionne, mais la clé API est rejetée par OpenRouter.")
        else:
            print("❌ 2. Réponse Renarde : ÉCHEC (Pas de réponse, timeout)")

    await r.aclose()
    print("-" * 60)

if __name__ == "__main__":
    asyncio.run(run_final_validation())
