import asyncio
import logging
import os
import sys

# Add apps/h-core/src to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "h-core")))

from src.infrastructure.surrealdb import SurrealDbClient
from src.domain.memory import MemoryConsolidator
from src.infrastructure.llm import LlmClient
from src.infrastructure.redis import RedisClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("TEST-13-2")
logging.getLogger("src.infrastructure.surrealdb").setLevel(logging.DEBUG)

async def validate_decay():
    logger.info("Starting validation for Story 13.2 (Semantic Decay)...")
    
    # Initialize clients
    surreal = SurrealDbClient(
        url=os.getenv("SURREALDB_URL", "ws://localhost:8002/rpc"),
        user=os.getenv("SURREALDB_USER", "root"),
        password=os.getenv("SURREALDB_PASS", "root")
    )
    await surreal.connect()
    
    # Mock LLM and Redis for the consolidator
    class MockLlm:
        async def get_completion(self, *args, **kwargs): return "[]"
        async def get_embedding(self, *args, **kwargs): return [0.0] * 384
    
    class MockRedis:
        async def publish(self, *args, **kwargs): pass

    consolidator = MemoryConsolidator(surreal, MockLlm(), MockRedis()) # type: ignore

    # 1. Setup Test Data
    logger.info("1. Setting up test facts...")
    await surreal._call("query", "DELETE BELIEVES, fact, subject;")
    
    # Create subjects
    await surreal._call("query", "CREATE subject:user SET name = 'Test User';")
    await surreal._call("query", "CREATE subject:system SET name = 'System';")
    
    # Create facts and relations
    # Fact 1: Normal (0.8 strength)
    res1 = await surreal._call("create", "fact", {"content": "I like coffee"})
    f1_id = res1[0]["id"]
    await surreal._call("query", f"RELATE subject:system->BELIEVES->{f1_id} SET strength = 0.8, permanent = false;")
    
    # Fact 2: Permanent (1.0 strength)
    res2 = await surreal._call("create", "fact", {"content": "My name is User"})
    f2_id = res2[0]["id"]
    await surreal._call("query", f"RELATE subject:system->BELIEVES->{f2_id} SET strength = 1.0, permanent = true;")
    
    # Fact 3: Weak (0.15 strength, should decay to < 0.1 and be removed)
    res3 = await surreal._call("create", "fact", {"content": "I wore a blue shirt yesterday"})
    f3_id = res3[0]["id"]
    await surreal._call("query", f"RELATE subject:system->BELIEVES->{f3_id} SET strength = 0.15, permanent = false;")

    # 2. Run Decay
    logger.info("2. Running decay cycle (decay_rate=0.5)...")
    # Using 0.5 to make it very visible
    removed = await consolidator.apply_decay(decay_rate=0.5, threshold=0.1)
    
    # 3. Verify Results
    logger.info("3. Verifying results...")
    
    # Check Fact 1 (0.8 * 0.5 = 0.4)
    res = await surreal._call("query", f"SELECT strength FROM BELIEVES WHERE out = {f1_id};")
    s1 = res[0]["result"][0]["strength"]
    logger.info(f"Fact 1 strength: {s1} (Expected ~0.4)")
    assert 0.39 < s1 < 0.41, f"Fact 1 decay failed: {s1}"
    
    # Check Fact 2 (Permanent, should be 1.0)
    res = await surreal._call("query", f"SELECT strength FROM BELIEVES WHERE out = {f2_id};")
    s2 = res[0]["result"][0]["strength"]
    logger.info(f"Fact 2 strength: {s2} (Expected 1.0)")
    assert s2 == 1.0, f"Fact 2 (permanent) decayed! {s2}"
    
    # Check Fact 3 (0.15 * 0.5 = 0.075 < 0.1, should be deleted)
    res = await surreal._call("query", f"SELECT count() FROM BELIEVES WHERE out = {f3_id};")
    count3 = res[0]["result"][0]["count"] if res[0]["result"] else 0
    logger.info(f"Fact 3 belief count: {count3} (Expected 0)")
    assert count3 == 0, f"Fact 3 was not removed: {count3}"
    
    # Check orphaned fact node removal
    res = await surreal._call("query", f"SELECT count() FROM fact WHERE id = {f3_id};")
    f3_count = res[0]["result"][0]["count"] if res[0]["result"] else 0
    logger.info(f"Fact 3 node count: {f3_count} (Expected 0)")
    assert f3_count == 0, f"Orphaned fact node was not removed: {f3_count}"
    
    logger.info("✅ ALL TESTS PASSED for Story 13.2!")
    await surreal.close()

if __name__ == "__main__":
    asyncio.run(validate_decay())
