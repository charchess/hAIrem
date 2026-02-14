import asyncio
import json
import redis.asyncio as redis
import uuid
import time

async def run_debug_diagnostic():
    print("🔬 Quinn - DIAGNOSTIC PROFOND (DEBUG MODE)")
    print("-" * 60)
    
    r = redis.from_url("redis://localhost:6377", decode_responses=True)
    
    # 1. Inspection brute du Stream
    print("📥 1. Analyse brute du system_stream...")
    try:
        messages = await r.xrevrange("system_stream", count=10)
        if not messages:
            print("⚠️ Le Stream 'system_stream' est VIDE.")
        else:
            for m_id, fields in messages:
                print(f"   [{m_id}] Type: {fields.get('type')} | Sender: {fields.get('sender')[:50]}...")
                # Vérification du format du payload
                payload = fields.get('payload', '{}')
                if isinstance(payload, str) and payload.startswith('{'):
                    p_data = json.loads(payload)
                    if 'content' in p_data:
                        print(f"      -> Content: {str(p_data['content'])[:100]}")
    except Exception as e:
        print(f"❌ Erreur lecture Stream: {e}")

    # 2. Test de présence des Agents
    print("\n👥 2. État civil des agents...")
    agents = ["Lisa", "Electra", "Dieu", "Renarde"]
    for agent in agents:
        # On vérifie si l'agent a un canal PubSub actif
        res = await r.execute_command("PUBSUB", "CHANNELS", f"agent:{agent}")
        status = "✅ ACTIF" if res else "❌ INACTIF (N'écoute pas)"
        print(f"   Agent {agent.ljust(8)}: {status}")

    # 3. Test de réponse forcé (Bypass Bridge)
    print("\n📡 3. Test de réponse forcé (User -> Renarde)...")
    test_id = str(uuid.uuid4())
    # On construit un message HLink complet et correct
    msg = {
        "id": test_id,
        "timestamp": "2026-02-12T20:00:00Z",
        "type": "user_message",
        "sender": {"agent_id": "user", "role": "user"},
        "recipient": {"target": "Renarde"},
        "payload": {"content": "Test diagnostic Quinn, réponds 'OK'"},
        "metadata": {"priority": "normal", "ttl": 5}
    }
    
    # On publie directement sur le system_stream (ce que fait le Bridge)
    # On doit aplatir pour Redis Stream
    flattened = {k: json.dumps(v) if isinstance(v, dict) else str(v) for k, v in msg.items()}
    await r.xadd("system_stream", flattened)
    print(f"   Message envoyé (ID: {test_id})")

    print("   Attente d'activité LLM dans les logs...")
    start_time = time.time()
    found_resp = False
    while time.time() - start_time < 15:
        # On cherche une réponse narrative ou une erreur LLM
        latest = await r.xrevrange("system_stream", count=5)
        for _, f in latest:
            if f.get("sender") and "Renarde" in f.get("sender") and f.get("type") == "narrative.text":
                print(f"✅ RÉPONSE REÇUE DE RENARDE !")
                found_resp = True
                break
            if f.get("type") == "system.log" and "LLM" in str(f.get("payload")):
                print(f"   Log système: {f.get('payload')[:100]}")
        if found_resp: break
        await asyncio.sleep(1)

    if not found_resp:
        print("❌ Aucune réponse de Renarde reçue.")

    await r.aclose()
    print("-" * 60)

if __name__ == "__main__":
    asyncio.run(run_debug_diagnostic())
