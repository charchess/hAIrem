import asyncio
import os
import sys

# Add apps/h-core to path
sys.path.append(os.path.join(os.getcwd(), 'apps/h-core'))

from src.infrastructure.redis import RedisClient
from src.infrastructure.llm import LlmClient
from src.models.agent import AgentConfig
from src.domain.agent import BaseAgent
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

async def test_routing():
    print("--- Verifying 17.4 Routing Logic ---")
    
    redis_client = RedisClient()
    await redis_client.connect()
    llm_client = LlmClient()
    
    config = AgentConfig(name="Lisa", role="Assistant")
    agent = BaseAgent(config=config, redis_client=redis_client, llm_client=llm_client)
    
    # Mock _process_narrative to avoid actual LLM calls
    processed = False
    async def mock_process(msg):
        nonlocal processed
        processed = True
        print(f"DEBUG: Agent {agent.config.name} is processing message.")

    agent._process_narrative = mock_process
    
    # Case 1: Addressed to Lisa via recipient, no mention in text
    msg1 = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="Lisa"),
        payload=Payload(content="Salut !")
    )
    
    print("Testing Case 1: Explicit recipient 'Lisa', no mention in text.")
    await agent.on_message(msg1)
    
    if processed:
        print("✅ Case 1 SUCCESS: Lisa processed the message.")
    else:
        print("❌ Case 1 FAILURE: Lisa ignored the message.")
        
    processed = False
    
    # Case 2: Addressed to Broadcast, no mention of Lisa
    msg2 = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="broadcast"),
        payload=Payload(content="Bonjour tout le monde !")
    )
    
    print("\nTesting Case 2: Recipient 'broadcast', no mention of Lisa.")
    processed = False
    await agent.on_message(msg2)
    
    if processed:
        print("✅ Case 2 SUCCESS: Lisa processed the broadcast (Default behavior for broadcast).")
    else:
        print("❌ Case 2 FAILURE: Lisa ignored the broadcast.")

    # Case 3: Addressed to Renarde, Lisa ignored
    msg3 = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="Renarde"),
        payload=Payload(content="Renarde, tu es là ?")
    )
    
    print("\nTesting Case 3: Explicit recipient 'Renarde'.")
    processed = False
    await agent.on_message(msg3)
    
    if not processed:
        print("✅ Case 3 SUCCESS: Lisa ignored message for Renarde.")
    else:
        print("❌ Case 3 FAILURE: Lisa processed message for Renarde.")

    # Case 4: Addressed to Broadcast, but Lisa IS mentioned
    msg4 = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="broadcast"),
        payload=Payload(content="Lisa, tu m'entends ?")
    )
    
    print("\nTesting Case 4: Recipient 'broadcast', Lisa IS mentioned.")
    processed = False
    await agent.on_message(msg4)
    
    if processed:
        print("✅ Case 4 SUCCESS: Lisa processed the broadcast because she was mentioned.")
    else:
        print("❌ Case 4 FAILURE: Lisa ignored the broadcast despite being mentioned.")

if __name__ == "__main__":
    asyncio.run(test_routing())
