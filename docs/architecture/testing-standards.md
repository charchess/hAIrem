# Standards de Test — hAIrem

> Document de référence pour la pratique TDD dans hAIrem.  
> À lire avant d'écrire n'importe quel test.

---

## 1. Philosophie

**RED → GREEN → REFACTOR.** Sans exception.

1. **Écrire le test d'abord** — il doit échouer (RED)
2. **Écrire le minimum de code** pour le faire passer (GREEN)
3. **Refactorer** sans casser les tests

Ne pas écrire de code de production sans test. Ne pas écrire de test après le code — ce n'est pas du TDD, c'est du test-washing.

---

## 2. Structure des Tests

```
apps/h-core/tests/
├── conftest.py              # Fixtures partagées globales
├── unit/                    # Tests purs, zéro I/O (tout mocké)
│   ├── conftest.py
│   ├── test_scoring.py
│   └── ...
├── integration/             # Tests avec services réels (docker-compose)
│   ├── conftest.py          # Setup Redis/SurrealDB de test
│   ├── test_memory_integration.py
│   └── ...
├── test_{story_id}_{feature}.py   # Tests liés à une story spécifique
└── ...
```

**Convention de nommage :**
- Fichier : `test_{module_ou_story}.py`
- Fonction : `test_{action}_{condition}_{expected_result}()`
- Exemple : `test_arbiter_names_agent_when_mentioned_in_message()`

---

## 3. Fixtures Partagées

### conftest.py racine (apps/h-core/tests/conftest.py)

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.redis import RedisClient
from src.infrastructure.surrealdb import SurrealDbClient
from src.infrastructure.llm import LlmClient
from src.models.agent import AgentConfig
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender


@pytest.fixture
def mock_redis() -> AsyncMock:
    """RedisClient entièrement mocké."""
    mock = AsyncMock(spec=RedisClient)
    mock.publish = AsyncMock(return_value=True)
    mock.publish_event = AsyncMock(return_value=True)
    mock.listen_stream = AsyncMock()
    return mock


@pytest.fixture
def mock_surreal() -> AsyncMock:
    """SurrealDbClient entièrement mocké."""
    mock = AsyncMock(spec=SurrealDbClient)
    mock.insert_graph_memory = AsyncMock(return_value={"id": "fact:test"})
    mock.semantic_search = AsyncMock(return_value=[])
    mock.get_unprocessed_messages = AsyncMock(return_value=[])
    mock.mark_as_processed = AsyncMock()
    mock.apply_decay_to_all_memories = AsyncMock(return_value=0)
    mock.cleanup_orphaned_facts = AsyncMock(return_value=0)
    return mock


@pytest.fixture
def mock_llm() -> AsyncMock:
    """LlmClient mocké retournant des réponses fixture."""
    mock = AsyncMock(spec=LlmClient)
    mock.get_completion = AsyncMock(return_value='{"facts": [], "causal_links": [], "concepts": []}')
    mock.get_embedding = AsyncMock(return_value=[0.1] * 768)
    mock.model = "mock-model"
    return mock


@pytest.fixture
def base_agent_config() -> AgentConfig:
    """Config d'agent minimale pour les tests."""
    return AgentConfig(
        name="test_agent",
        role="assistant",
        prompt="Tu es un agent de test.",
        capabilities=["testing"],
        llm_config={"provider": "mock", "model": "mock-model"},
    )


@pytest.fixture
def sample_hlink_message() -> HLinkMessage:
    """Message HLink de test standard."""
    return HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="broadcast"),
        payload=Payload(content="Message de test"),
    )
```

### conftest.py intégration

```python
import pytest
import asyncio
import os

@pytest.fixture(scope="session")
async def test_redis():
    """Redis de test (nécessite docker-compose up)."""
    from src.infrastructure.redis import RedisClient
    client = RedisClient(host=os.getenv("TEST_REDIS_HOST", "localhost"))
    await client.connect()
    yield client

@pytest.fixture(scope="session")  
async def test_surreal():
    """SurrealDB de test."""
    from src.infrastructure.surrealdb import SurrealDbClient
    client = SurrealDbClient(
        url=os.getenv("TEST_SURREALDB_URL", "ws://localhost:8000/rpc"),
        user="root", password="root"
    )
    await client.connect()
    yield client
    # Cleanup: supprimer les données de test
    await client._call("query", "DELETE fact; DELETE subject; DELETE concept;")
```

---

## 4. Patterns de Test par Type

### Test Unitaire (zéro I/O)

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.domain.memory import MemoryConsolidator


@pytest.mark.asyncio
async def test_consolidator_extracts_facts_from_conversation(mock_surreal, mock_llm, mock_redis):
    """Given des messages non traités, When consolidation, Then faits extraits et stockés."""
    # Arrange
    mock_surreal.get_unprocessed_messages.return_value = [
        {"id": "msg:1", "sender": {"agent_id": "user"}, "payload": {"content": "J'adore le café"}}
    ]
    mock_llm.get_completion.return_value = '{"facts": [{"fact": "User likes coffee", "subject": "user", "agent": "system", "confidence": 0.9}], "causal_links": [], "concepts": []}'
    
    consolidator = MemoryConsolidator(mock_surreal, mock_llm, mock_redis)
    
    # Act
    count = await consolidator.consolidate()
    
    # Assert
    assert count == 1
    mock_surreal.insert_graph_memory.assert_called_once()
    call_args = mock_surreal.insert_graph_memory.call_args[0][0]
    assert "coffee" in call_args["fact"].lower()
```

### Test d'Intégration (avec vrais services)

```python
import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_stored_and_retrieved_from_surrealdb(test_surreal, mock_llm, mock_redis):
    """Round-trip : stocker un fait → le retrouver par recherche sémantique."""
    from src.domain.memory import MemoryConsolidator
    
    consolidator = MemoryConsolidator(test_surreal, mock_llm, mock_redis)
    fact = {"fact": "User prefers dark mode", "subject": "user", "agent": "system", "confidence": 0.9, "embedding": [0.1] * 768}
    
    await test_surreal.insert_graph_memory(fact)
    results = await test_surreal.semantic_search([0.1] * 768, limit=5)
    
    assert any("dark mode" in r.get("content", "") for r in results)
```

### Test d'Agent (avec mock de l'infra)

```python
@pytest.mark.asyncio
async def test_agent_responds_to_direct_message(mock_redis, mock_surreal, mock_llm, base_agent_config):
    """Given message direct, When agent process, Then réponse publiée sur Redis."""
    from src.domain.agent import BaseAgent
    from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload
    
    mock_llm.get_completion.return_value = "Je vais bien, merci !"
    agent = BaseAgent(base_agent_config, mock_redis, mock_llm, mock_surreal)
    
    msg = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="test_agent"),
        payload=Payload(content="Comment tu vas ?"),
    )
    
    await agent.process_message(msg)
    
    mock_redis.publish.assert_called()
    published_msg = mock_redis.publish.call_args[0][1]
    assert "merci" in str(published_msg.payload.content).lower()
```

---

## 5. Marqueurs pytest

```ini
# pyproject.toml (à ajouter dans [tool.pytest.ini_options])
[tool.pytest.ini_options]
testpaths = ["apps/h-core/tests"]
pythonpath = ["apps/h-core/src"]
asyncio_mode = "auto"
markers = [
    "unit: tests unitaires sans I/O",
    "integration: tests avec services réels (nécessite docker-compose)",
    "e2e: tests end-to-end complets",
    "slow: tests > 5s",
]
```

**Lancer uniquement les tests rapides :**
```bash
pytest -m "unit" apps/h-core/tests/
```

**Lancer les tests d'intégration :**
```bash
docker-compose -f docker-compose.test.yml up -d
pytest -m "integration" apps/h-core/tests/
```

---

## 6. Ce qu'on ne fait PAS

- ❌ `except Exception: pass` dans les tests — toujours assert quelque chose
- ❌ Tests qui sleep un nombre fixe de secondes — utiliser `asyncio.wait_for()` avec timeout
- ❌ Tests qui dépendent de l'ordre d'exécution — chaque test est indépendant
- ❌ Mock de ce qu'on est censé tester — mocker les dépendances, pas le SUT
- ❌ Test écrit après l'implémentation — TDD strict

---

## 7. Couverture Minimale

```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

Cible : **≥ 80%** sur `apps/h-core/src/`.  
Les modules d'infrastructure (redis, surrealdb, llm) sont exemptés si couverts par les tests d'intégration.
