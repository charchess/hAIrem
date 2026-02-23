import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.seeding import SeedingService


@pytest.fixture
def mock_surreal():
    s = MagicMock()
    s._call = AsyncMock()
    s.insert_graph_memory = AsyncMock()
    s.client = MagicMock()
    return s


@pytest.fixture
def mock_redis():
    r = MagicMock()
    r.client = MagicMock()
    r.connect = AsyncMock()
    r.delete = AsyncMock()
    r.client.delete = AsyncMock()
    return r


@pytest.fixture
def service(mock_surreal, mock_redis):
    return SeedingService(surreal=mock_surreal, redis=mock_redis)


@pytest.mark.asyncio
async def test_seed_graph_creates_subjects(service, mock_surreal):
    data = {
        "subjects": [{"name": "Lisa"}, {"name": "Entropy"}],
        "facts": [],
    }
    await service.seed_graph(data)

    assert mock_surreal._call.call_count == 2
    first_call = mock_surreal._call.call_args_list[0]
    assert "INSERT INTO subject" in first_call[0][1]


@pytest.mark.asyncio
async def test_seed_graph_inserts_facts(service, mock_surreal):
    data = {
        "subjects": [],
        "facts": [
            {"fact": "Lisa loves coffee", "subject": "Lisa", "agent": "system", "confidence": 1.0},
            {"fact": "Entropy is chaotic", "subject": "Entropy", "agent": "system", "confidence": 0.9},
        ],
    }
    await service.seed_graph(data)

    assert mock_surreal.insert_graph_memory.call_count == 2


@pytest.mark.asyncio
async def test_seed_graph_skips_unnamed_subjects(service, mock_surreal):
    data = {"subjects": [{"name": ""}, {}], "facts": []}
    await service.seed_graph(data)
    assert mock_surreal._call.call_count == 0


@pytest.mark.asyncio
async def test_generate_initial_relationships_creates_knows_and_trusts(service, mock_surreal):
    agents = [
        {"name": "Lisa", "role": "assistant"},
        {"name": "Entropy", "role": "guardian"},
    ]
    await service.generate_initial_relationships(agents)

    calls = mock_surreal._call.call_args_list
    queries = [c[0][1] for c in calls]
    knows_calls = [q for q in queries if "KNOWS" in q]
    trusts_calls = [q for q in queries if "TRUSTS" in q]

    assert len(knows_calls) == 2
    assert len(trusts_calls) == 2


@pytest.mark.asyncio
async def test_generate_initial_relationships_same_role_higher_trust(service, mock_surreal):
    agents = [
        {"name": "Lisa", "role": "assistant"},
        {"name": "Electra", "role": "assistant"},
    ]
    await service.generate_initial_relationships(agents)

    calls = mock_surreal._call.call_args_list
    trusts_queries = [c[0][1] for c in calls if "TRUSTS" in c[0][1]]
    assert all("0.8" in q for q in trusts_queries)


@pytest.mark.asyncio
async def test_reset_streams_deletes_streams(service, mock_redis):
    await service.reset_streams(["stream_a", "stream_b"])

    assert mock_redis.delete.call_count == 2
