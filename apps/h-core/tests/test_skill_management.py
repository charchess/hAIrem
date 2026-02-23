import pytest
from unittest.mock import AsyncMock, MagicMock

from src.features.admin.skill_management.service import SkillGrantService, SkillManagementService
from src.skills.registry import SkillRegistry


@pytest.fixture
def mock_surreal():
    s = MagicMock()
    s._call = AsyncMock(return_value=[{"result": []}])
    return s


@pytest.fixture
def grant_service(mock_surreal):
    return SkillGrantService(surreal_client=mock_surreal)


@pytest.fixture
def mgmt_service(grant_service):
    return SkillManagementService(grant_service=grant_service)


@pytest.mark.asyncio
async def test_grant_returns_success(grant_service, mock_surreal):
    result = await grant_service.grant("Lisa", "home_assistant")
    assert result["success"] is True
    assert result["persona_id"] == "Lisa"
    assert result["skill_name"] == "home_assistant"
    assert result["active"] is True
    assert mock_surreal._call.called


@pytest.mark.asyncio
async def test_revoke_returns_success(grant_service):
    result = await grant_service.revoke("Lisa", "home_assistant")
    assert result["success"] is True
    assert result["active"] is False


@pytest.mark.asyncio
async def test_grant_unknown_skill_returns_error(grant_service):
    result = await grant_service.grant("Lisa", "nonexistent_skill_xyz")
    assert result["success"] is False
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_is_active_returns_true_when_no_record(grant_service, mock_surreal):
    mock_surreal._call.return_value = [{"result": []}]
    active = await grant_service.is_active("Lisa", "cooking")
    assert active is True


@pytest.mark.asyncio
async def test_is_active_returns_false_when_revoked(grant_service, mock_surreal):
    mock_surreal._call.return_value = [{"result": [{"active": False}]}]
    active = await grant_service.is_active("Lisa", "cooking")
    assert active is False


@pytest.mark.asyncio
async def test_is_active_returns_true_without_surreal():
    service = SkillGrantService(surreal_client=None)
    assert await service.is_active("Lisa", "cooking") is True


@pytest.mark.asyncio
async def test_unique_skill_blocked_when_already_granted(grant_service, mock_surreal):
    mock_surreal._call.return_value = [{"result": [{"persona_id": "Moka"}]}]
    result = await grant_service.grant("Lisa", "music")
    assert result["success"] is False
    assert "unique" in result["error"]
    assert "Moka" in result["error"]


@pytest.mark.asyncio
async def test_multiple_skill_can_be_granted_to_many(grant_service, mock_surreal):
    mock_surreal._call.return_value = [{"result": []}]
    result1 = await grant_service.grant("Lisa", "weather")
    result2 = await grant_service.grant("Moka", "weather")
    assert result1["success"] is True
    assert result2["success"] is True


@pytest.mark.asyncio
async def test_list_grants_returns_all_records(grant_service, mock_surreal):
    mock_surreal._call.return_value = [
        {
            "result": [
                {"persona_id": "Lisa", "skill_name": "cooking", "active": True},
                {"persona_id": "Moka", "skill_name": "music", "active": True},
            ]
        }
    ]
    grants = await grant_service.list_grants()
    assert len(grants) == 2


@pytest.mark.asyncio
async def test_list_skills_returns_badge_format(mgmt_service, mock_surreal):
    mock_surreal._call.return_value = [{"result": []}]
    skills = await mgmt_service.list_skills()
    assert len(skills) > 0
    for skill in skills:
        assert "skill_name" in skill
        assert "access" in skill
        assert "tools" in skill
        assert "active_for" in skill
        assert isinstance(skill["tools"], list)
        assert skill["access"] in ("unique", "multiple")


@pytest.mark.asyncio
async def test_list_skills_shows_active_personas(mgmt_service, mock_surreal):
    mock_surreal._call.return_value = [
        {
            "result": [
                {"persona_id": "Lisa", "skill_name": "home_assistant", "active": True},
            ]
        }
    ]
    skills = await mgmt_service.list_skills()
    ha = next((s for s in skills if s["skill_name"] == "home_assistant"), None)
    assert ha is not None
    assert "Lisa" in ha["active_for"]


@pytest.mark.asyncio
async def test_skill_registry_get_metadata_returns_access():
    registry = SkillRegistry()
    meta = registry.get_metadata("home_assistant")
    assert meta["access"] == "multiple"
    assert meta["name"] == "home_assistant"
    assert len(meta["tools"]) > 0


@pytest.mark.asyncio
async def test_skill_registry_music_is_unique():
    registry = SkillRegistry()
    meta = registry.get_metadata("music")
    assert meta["access"] == "unique"


@pytest.mark.asyncio
async def test_skill_registry_list_all_metadata():
    registry = SkillRegistry()
    all_meta = registry.list_all_metadata()
    names = [m["name"] for m in all_meta]
    assert "home_assistant" in names
    assert "music" in names
    for m in all_meta:
        assert "access" in m
