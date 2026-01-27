import asyncio
import os
from src.infrastructure.surrealdb import SurrealDbClient

async def test_full_epic_13():
    print("--- STARTING EPIC 13 LIVE VALIDATION ---")
    url = os.getenv("SURREALDB_URL", "ws://localhost:8001/rpc")
    client = SurrealDbClient(url, "root", "root")
    await client.connect()
    
    # 1. Test Graph Insertion (Story 13.1)
    print("\n[13.1] Inserting Graph Memory...")
    fact_data = {
        "fact": "Le ciel est bleu.",
        "subject": "ciel",
        "agent": "Lisa",
        "confidence": 0.9,
        "embedding": [0.1] * 768
    }
    await client.insert_graph_memory(fact_data)
    
    # Verify insertion
    res = await client._call('query', "SELECT * FROM fact WHERE content = 'Le ciel est bleu.';")
    print(f"DEBUG RESP FACT: {res}")
    
    # Robust parsing
    def get_result(r):
        if not r: return []
        if isinstance(r, list):
            if 'result' in r[0]: return r[0]['result']
            return r
        return r.get('result', [])

    facts = get_result(res)
    if not facts:
        print("ERROR: Fact not found after insertion.")
        return
        
    fact_id = facts[0]['id']
    print(f"Fact Found: {fact_id}")

    # 2. Test Subjective Retrieval (Story 13.3)
    print("\n[13.3] Testing Subjective Retrieval...")
    # Lisa should see it
    res_lisa = await client.semantic_search([0.1]*768, agent_id="Lisa", limit=1)
    print(f"Lisa sees: {len(res_lisa)} facts (Expected 1)")
    
    # Electra should NOT see it
    res_electra = await client.semantic_search([0.1]*768, agent_id="Electra", limit=1)
    print(f"Electra sees: {len(res_electra)} facts (Expected 0)")

    # 3. Test Decay (Story 13.2)
    print("\n[13.2] Testing Decay...")
    # Check initial strength
    edge_res = await client._call('query', f"SELECT * FROM BELIEVES WHERE out = {fact_id};")
    edges = get_result(edge_res)
    if edges:
        print(f"Initial Strength: {edges[0]['strength']}")
    else:
        print("ERROR: Belief edge not found.")
    
    # Apply massive decay
    print("Applying massive decay...")
    await client.apply_decay_to_all_memories(decay_rate=100.0, threshold=0.5)
    
    # Verify deletion
    edge_after = await client._call('query', f"SELECT * FROM BELIEVES WHERE out = {fact_id};")
    if not get_result(edge_after):
        print("Fact correctly forgotten (Edge deleted).")
    else:
        print(f"Fact still exists with strength: {get_result(edge_after)[0]['strength']}")

    # 4. Test Conflict Resolution (Story 13.4)
    print("\n[13.4] Testing Conflict Merge...")
    await client.insert_graph_memory(fact_data)
    res = await client._call('query', "SELECT * FROM fact WHERE content = 'Le ciel est bleu.';")
    new_facts = get_result(res)
    new_fact_id = new_facts[0]['id']
    
    resolution = {"action": "OVERRIDE", "resolution": "Le ciel est gris aujourd'hui."}
    await client.merge_or_override_fact(new_fact_id, {"fact": "Le ciel est gris.", "embedding": [0.2]*768}, resolution)
    
    updated_res = await client._call('query', f"SELECT * FROM {new_fact_id};")
    updated = get_result(updated_res)
    print(f"Updated Content: {updated[0]['content'] if updated else 'FAILED'}")

    await client.close()
    print("\n--- EPIC 13 VALIDATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(test_full_epic_13())