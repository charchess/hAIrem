import httpx
import asyncio
import json

async def check():
    print("Checking internal health...")
    async with httpx.AsyncClient() as client:
        try:
            # Check agents
            resp = await client.get('http://h-bridge:8000/api/agents', timeout=5.0)
            print(f"Bridge API (/api/agents) status: {resp.status_code}")
            agents = resp.json()
            print(f"Discovered Agents: {[a['id'] for a in agents]}")
            
            # Check status
            resp = await client.get('http://h-bridge:8000/api/status', timeout=5.0)
            print(f"Bridge API (/api/status) status: {resp.status_code}")
            print(f"System Status: {resp.json()}")
            
        except Exception as e:
            print(f"Internal Health Check FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(check())
