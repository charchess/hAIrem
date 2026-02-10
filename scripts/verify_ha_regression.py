import asyncio
import json
import uuid
import logging
from src.infrastructure.redis import RedisClient
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HA_SIMULATOR")

async def simulate_ha_command():
    redis = RedisClient(host="localhost")
    await redis.connect()
    
    # 1. Simulate User sending command to Electra (New 17.4 Format)
    msg_id = uuid.uuid4()
    command_msg = HLinkMessage(
        id=msg_id,
        type=MessageType.EXPERT_COMMAND,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="Electra"),
        payload={
            "content": {
                "command": "ping",
                "args": {}
            }
        }
    )
    
    # Subscribe to feedback
    pubsub = redis.client.pubsub()
    await pubsub.subscribe("agent:user", "broadcast")
    
    logger.info(f"Sending 'ping' command to Electra (Targeted channel: agent:Electra)")
    await redis.publish("agent:Electra", command_msg)
    
    # 2. Wait for response
    logger.info("Waiting for response...")
    try:
        async with asyncio.timeout(5.0):
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    m_type = data.get("type")
                    sender = data.get("sender", {}).get("agent_id")
                    payload = data.get("payload", {})
                    
                    logger.info(f"RECV: Type={m_type} from {sender} | Content={payload.get('content') or payload.get('status')}")
                    
                    if m_type == "expert.response" and sender == "Electra":
                        logger.info("✅ SUCCESS: Electra responded to the command!")
                        return True
    except asyncio.TimeoutError:
        logger.error("❌ FAILURE: Timeout waiting for Electra's response.")
        return False
    finally:
        await pubsub.unsubscribe()

if __name__ == "__main__":
    # Ensure PYTHONPATH is set before running
    asyncio.run(simulate_ha_command())
