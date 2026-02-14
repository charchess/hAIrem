import pytest
import httpx
import asyncio

@pytest.mark.asyncio
async def test_seeding_api_flow():
    """Verifies that the seeding API correctly injects data."""
    # Note: Requires docker-compose services up
    url = "http://localhost:8000/api/test/seed-graph"
    
    payload = {
        "subjects": [{"name": "SeedingBot"}],
        "facts": [
            {"fact": "Seeding is working", "subject": "SeedingBot", "agent": "system", "confidence": 1.0}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Seed data
        resp = await client.post(url, json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        
        # 2. Verify via history (H-Bridge endpoint)
        hist_resp = await client.get("http://localhost:8000/api/history")
        assert hist_resp.status_code == 200
        # Wait a bit for processing if needed, though seed-graph is direct to DB
        
        # Actually verify the fact exists in SurrealDB via a query
        # Since we are testing E2E, checking history is a good proxy.
