import asyncio
import pytest
import logging
from src.infrastructure.redis import RedisClient
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

# Configuration du logging pour voir ce qui se passe
logging.basicConfig(level=logging.INFO)

@pytest.mark.asyncio
async def test_real_redis_integration():
    """Test d'intégration réel avec le serveur Redis local."""
    
    # 1. Connexion (port 6377 pour hAImem Redis)
    client = RedisClient(host="localhost", port=6377)
    await client.connect()
    
    received_messages = []
    ready_event = asyncio.Event()

    async def message_handler(msg: HLinkMessage):
        logging.info(f"Message reçu : {msg}")
        received_messages.append(msg)
        ready_event.set()

    # 2. Création du message
    test_msg = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="integration-tester", role="qa"),
        recipient=Recipient(target="broadcast"),
        payload=Payload(content="Ceci est un test réel sur Redis")
    )

    # 3. Workflow Pub/Sub
    pub_task = None
    try:
        # On lance l'écoute
        sub_task = asyncio.create_task(client.subscribe("integration-channel", message_handler))
        
        # On attend que la souscription soit active (petit délai technique)
        await asyncio.sleep(0.5)
        
        # On publie
        await client.publish("integration-channel", test_msg)
        
        # On attend la réception (avec timeout de sécurité)
        await asyncio.wait_for(ready_event.wait(), timeout=2.0)
        
        # 4. Assertions
        assert len(received_messages) == 1
        received = received_messages[0]
        # Message reçu peut être un dict (désérialisé depuis Redis)
        if isinstance(received, dict):
            assert received["payload"]["content"] == "Ceci est un test réel sur Redis"
            assert received["sender"]["agent_id"] == "integration-tester"
        else:
            assert received.payload.content == "Ceci est un test réel sur Redis"
            assert received.sender.agent_id == "integration-tester"
        
        print("\n✅ Test d'intégration Redis RÉUSSI : Message reçu et validé.")

    except asyncio.TimeoutError:
        pytest.fail("Timeout: Le message n'a pas été reçu à temps.")
    except Exception as e:
        pytest.fail(f"Erreur inattendue: {e}")
    finally:
        # Nettoyage propre
        await client.disconnect()
        sub_task.cancel()
        try:
            await sub_task
        except asyncio.CancelledError:
            pass
