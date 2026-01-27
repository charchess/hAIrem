import asyncio
import json
from redis.asyncio import Redis
from uuid import uuid4

async def run():
    r = Redis(host="localhost", port=6379)
    msg = {
        "id": str(uuid4()),
        "type": "system.log",
        "sender": {"agent_id": "system", "role": "orchestrator"},
        "recipient": {"target": "broadcast"},
        "payload": {"content": "[ERROR] CRITICAL_SYSTEM_FAILURE: Manual test error for Quinn"}
    }
    await r.publish("broadcast", json.dumps(msg))
    print("Sent log message to Redis.")

if __name__ == "__main__":
    asyncio.run(run())
