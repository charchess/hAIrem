import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from features.admin.token_tracking.repository import TokenTrackingRepository
from features.admin.token_tracking.models import TokenUsage


def make_surreal():
    surreal = MagicMock()
    surreal.client = MagicMock()
    surreal._call = AsyncMock(return_value=[{"result": []}])
    return surreal


def make_usage(**kwargs):
    defaults = dict(agent_id="lisa", input_tokens=100, output_tokens=50, model="gpt-4", provider="openai")
    defaults.update(kwargs)
    return TokenUsage(**defaults)


class TestTokenTrackingRepositoryNoSurreal:
    @pytest.mark.asyncio
    async def test_setup_schema_no_surreal(self):
        repo = TokenTrackingRepository(None)
        await repo.setup_schema()

    @pytest.mark.asyncio
    async def test_save_usage_no_surreal(self):
        repo = TokenTrackingRepository(None)
        result = await repo.save_token_usage(make_usage())
        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_usage_no_surreal(self):
        repo = TokenTrackingRepository(None)
        result = await repo.get_all_usage()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_usage_by_agent_no_surreal(self):
        repo = TokenTrackingRepository(None)
        result = await repo.get_usage_by_agent("lisa")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_usage_by_time_range_no_surreal(self):
        repo = TokenTrackingRepository(None)
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()
        result = await repo.get_usage_by_time_range(start, end)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_cost_summary_no_surreal(self):
        repo = TokenTrackingRepository(None)
        result = await repo.get_cost_summary_by_agent()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_daily_trends_no_surreal(self):
        repo = TokenTrackingRepository(None)
        result = await repo.get_daily_trends()
        assert result == []


class TestTokenTrackingRepositoryWithSurreal:
    @pytest.mark.asyncio
    async def test_setup_schema_success(self):
        surreal = make_surreal()
        repo = TokenTrackingRepository(surreal)
        await repo.setup_schema()
        surreal._call.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_schema_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = TokenTrackingRepository(surreal)
        await repo.setup_schema()

    @pytest.mark.asyncio
    async def test_save_usage_success(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value={"id": "tu:1"})
        repo = TokenTrackingRepository(surreal)
        result = await repo.save_token_usage(make_usage())
        assert result is True

    @pytest.mark.asyncio
    async def test_save_usage_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = TokenTrackingRepository(surreal)
        result = await repo.save_token_usage(make_usage())
        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_usage_with_data(self):
        surreal = make_surreal()
        usage_data = {
            "agent_id": "lisa",
            "input_tokens": 100,
            "output_tokens": 50,
            "model": "gpt-4",
            "provider": "openai",
            "timestamp": "2024-01-15T10:30:00",
        }
        surreal._call = AsyncMock(return_value=[{"result": [usage_data]}])
        repo = TokenTrackingRepository(surreal)
        result = await repo.get_all_usage()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_all_usage_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = TokenTrackingRepository(surreal)
        result = await repo.get_all_usage()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_usage_by_agent_with_data(self):
        surreal = make_surreal()
        usage_data = {
            "agent_id": "lisa",
            "input_tokens": 100,
            "output_tokens": 50,
            "model": "gpt-4",
            "provider": "openai",
            "timestamp": "2024-01-15T10:30:00",
        }
        surreal._call = AsyncMock(return_value=[{"result": [usage_data]}])
        repo = TokenTrackingRepository(surreal)
        result = await repo.get_usage_by_agent("lisa")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_usage_by_agent_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = TokenTrackingRepository(surreal)
        result = await repo.get_usage_by_agent("lisa")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_usage_by_time_range_no_agent(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value=[{"result": []}])
        repo = TokenTrackingRepository(surreal)
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()
        result = await repo.get_usage_by_time_range(start, end)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_usage_by_time_range_with_agent(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value=[{"result": []}])
        repo = TokenTrackingRepository(surreal)
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()
        result = await repo.get_usage_by_time_range(start, end, agent_id="lisa")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_usage_by_time_range_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = TokenTrackingRepository(surreal)
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()
        result = await repo.get_usage_by_time_range(start, end)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_cost_summary_no_time_range(self):
        surreal = make_surreal()
        summary_data = {"agent_id": "lisa", "total_input_tokens": 500, "total_output_tokens": 200, "request_count": 10}
        surreal._call = AsyncMock(return_value=[{"result": [summary_data]}])
        repo = TokenTrackingRepository(surreal)
        result = await repo.get_cost_summary_by_agent()
        assert len(result) == 1
        assert result[0].agent_id == "lisa"

    @pytest.mark.asyncio
    async def test_get_cost_summary_with_time_range(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(return_value=[{"result": []}])
        repo = TokenTrackingRepository(surreal)
        start = datetime.utcnow() - timedelta(days=30)
        end = datetime.utcnow()
        result = await repo.get_cost_summary_by_agent(start_time=start, end_time=end)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_cost_summary_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = TokenTrackingRepository(surreal)
        result = await repo.get_cost_summary_by_agent()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_daily_trends_no_agent(self):
        surreal = make_surreal()
        trend_data = {
            "day": 15,
            "month": 1,
            "year": 2024,
            "total_input_tokens": 300,
            "total_output_tokens": 150,
            "request_count": 5,
        }
        surreal._call = AsyncMock(return_value=[{"result": [trend_data]}])
        repo = TokenTrackingRepository(surreal)
        result = await repo.get_daily_trends()
        assert len(result) == 1
        assert "2024-01-15" in result[0].period

    @pytest.mark.asyncio
    async def test_get_weekly_trends_with_agent(self):
        surreal = make_surreal()
        trend_data = {
            "week": 3,
            "year": 2024,
            "total_input_tokens": 300,
            "total_output_tokens": 150,
            "request_count": 5,
        }
        surreal._call = AsyncMock(return_value=[{"result": [trend_data]}])
        repo = TokenTrackingRepository(surreal)
        result = await repo.get_weekly_trends(agent_id="lisa")
        assert len(result) == 1
        assert "W03" in result[0].period

    @pytest.mark.asyncio
    async def test_get_monthly_trends_with_agent(self):
        surreal = make_surreal()
        trend_data = {
            "month": 1,
            "year": 2024,
            "total_input_tokens": 300,
            "total_output_tokens": 150,
            "request_count": 5,
        }
        surreal._call = AsyncMock(return_value=[{"result": [trend_data]}])
        repo = TokenTrackingRepository(surreal)
        result = await repo.get_monthly_trends(agent_id="lisa")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_daily_trends_with_agent(self):
        surreal = make_surreal()
        trend_data = {
            "day": 1,
            "month": 2,
            "year": 2024,
            "total_input_tokens": 100,
            "total_output_tokens": 50,
            "request_count": 2,
        }
        surreal._call = AsyncMock(return_value=[{"result": [trend_data]}])
        repo = TokenTrackingRepository(surreal)
        result = await repo.get_daily_trends(agent_id="lisa")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_weekly_trends_no_agent(self):
        surreal = make_surreal()
        trend_data = {
            "week": 5,
            "year": 2024,
            "total_input_tokens": 200,
            "total_output_tokens": 100,
            "request_count": 3,
        }
        surreal._call = AsyncMock(return_value=[{"result": [trend_data]}])
        repo = TokenTrackingRepository(surreal)
        result = await repo.get_weekly_trends()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_monthly_trends_no_agent(self):
        surreal = make_surreal()
        trend_data = {
            "month": 3,
            "year": 2024,
            "total_input_tokens": 200,
            "total_output_tokens": 100,
            "request_count": 3,
        }
        surreal._call = AsyncMock(return_value=[{"result": [trend_data]}])
        repo = TokenTrackingRepository(surreal)
        result = await repo.get_monthly_trends()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_daily_trends_exception(self):
        surreal = make_surreal()
        surreal._call = AsyncMock(side_effect=Exception("fail"))
        repo = TokenTrackingRepository(surreal)
        result = await repo.get_daily_trends()
        assert result == []
