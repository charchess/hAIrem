import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from redis.asyncio import Redis

# On suppose que le PYTHONPATH inclut apps/h-core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/h-core')))

from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

async def listener(redis_client):
    """Écoute et affiche les messages des agents."""
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("broadcast", "agent:user")
    
    while True:
        message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.1)
        if message:
            try:
                data = json.loads(message["data"])
                sender = data.get("sender", {}).get("agent_id", "Unknown")
                payload = data.get("payload", {})
                content = payload.get("content", "")
                msg_type = data.get("type", "")

                if msg_type == "narrative.chunk":
                    print(f"{content}", end="", flush=True)
                elif msg_type == "narrative.text":
                    print(f"\n[{sender}]: {content}")
                elif msg_type == "expert.response":
                    print(f"\n[SYSTEM]: {content}")
            except Exception:
                pass
        await asyncio.sleep(0.01)

async def sender(redis_client):
    """Prend l'entrée utilisateur et publie sur Redis."""
    print("=== hAIrem Simple Chat ===")
    print("Tapez 'exit' pour quitter.\n")
    print("Commandes: /Agent NomDeCommande Argument")
    
    loop = asyncio.get_event_loop()
    
    while True:
        text = await loop.run_in_executor(None, input, "Moi: ")
        
        if text.lower() == 'exit':
            break
        
        if not text.strip():
            continue

        if text.startswith('/'):
            # Slash Command
            parts = text[1:].split(' ')
            target = parts[0]
            cmd = parts[1] if len(parts) > 1 else "ping"
            args = " ".join(parts[2:]) if len(parts) > 2 else ""
            
            message = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "type": "expert.command",
                "sender": {"agent_id": "user", "role": "user"},
                "recipient": {"target": target},
                "payload": {"content": {"command": cmd, "args": args}, "format": "json"},
                "metadata": {"priority": "high", "ttl": 5}
            }
            channel = f"agent:{target}"
        else:
            # Narrative message
            message = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "type": "narrative.text",
                "sender": {"agent_id": "user", "role": "user"},
                "recipient": {"target": "broadcast"},
                "payload": {"content": text, "format": "text"},
                "metadata": {"priority": "normal", "ttl": 5}
            }
            channel = "agent:Renarde"

        await redis_client.publish(channel, json.dumps(message))

async def main():
    redis_client = Redis(host='localhost', port=6379, decode_responses=True)
    try:
        await asyncio.gather(
            listener(redis_client),
            sender(redis_client)
        )
    except Exception as e:
        print(f"Global Error: {e}")
    finally:
        await redis_client.close()

if __name__ == "__main__":
    asyncio.run(main())
