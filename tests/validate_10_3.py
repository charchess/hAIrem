import asyncio
import os
import sys
import uuid
import json
from pathlib import Path

# Add apps/h-core to path
sys.path.append(str(Path(__file__).parent.parent / "apps" / "h-core"))

from src.infrastructure.redis import RedisClient
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

async def validate_cross_agent_collab():
    print("--- Validating Cross-Agent Collaboration (Story 10.3) ---")
    
    redis = RedisClient()
    await redis.connect()

    # 1. Simulate Expert-Domotique sending an internal note to Renarde
    # Scenario: The house is cold.
    note_content = "Il fait 16 degrés dans le salon, c'est un peu bas pour le confort de l'utilisateur."
    
    note = HLinkMessage(
        type=MessageType.AGENT_INTERNAL_NOTE,
        sender=Sender(agent_id="Expert-Domotique", role="Expert en Domotique"),
        recipient=Recipient(target="Renarde"),
        payload=Payload(content=note_content)
    )
    
    print(f"Expert-Domotique sending internal note to Renarde: {note_content}")
    await redis.publish("agent:Renarde", note)

    # 2. Simulate User asking 'Comment ça va ?'
    # We want to see if Renarde mentions the cold house.
    user_msg = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="Renarde"),
        payload=Payload(content="Coucou Renarde, comment ça va dans la maison ?")
    )
    
    print("User asking: Comment ça va ?")
    await redis.publish("agent:Renarde", user_msg)

    print("\nCheck the A2UI logs or H-Core output to verify Renarde's response.")
    print("Renarde should ideally mention the temperature issue learned from the internal note.")
    
    await redis.disconnect()

if __name__ == "__main__":
    asyncio.run(validate_cross_agent_collab())
