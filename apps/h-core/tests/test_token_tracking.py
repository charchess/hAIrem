import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from src.features.admin.token_tracking.models import TokenUsage, AgentCostSummary, TimePeriodTrend
from src.features.admin.token_tracking.pricing import ProviderPricing, get_pricing, calculate_cost, PROVIDER_PRICING
from src.features.admin.token_tracking.repository import TokenTrackingRepository
from src.features.admin.token_tracking.service import TokenTrackingService


class TestTokenUsageModel:
    def test_token_usage_creation(self):
        usage = TokenUsage(
            agent_id="agent-1",
            input_tokens=100,
            output_tokens=200,
            model="gpt-4",
            provider="openai",
        )
        assert usage.agent_id == "agent-1"
        assert usage.input_tokens == 100
        assert usage.output_tokens == 200
        assert usage.model == "gpt-4"
        assert usage.provider == "openai"

    def test_total_tokens_property(self):
        usage = TokenUsage(
            agent_id="agent-1",
            input_tokens=100,
            output_tokens=200,
            model="gpt-4",
            provider="openai",
        )
        assert usage.total_tokens == 300

    def test_to_dict(self):
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        usage = TokenUsage(
            agent_id="agent-1",
            input_tokens=100,
            output_tokens=200,
            model="gpt-4",
            provider="openai",
            timestamp=timestamp,
        )
        data = usage.to_dict()
        assert data["agent_id"] == "agent-1"
        assert data["input_tokens"] == 100
        assert data["output_tokens"] == 200
        assert data["total_tokens"] == 300
        assert data["model"] == "gpt-4"
        assert data["provider"] == "openai"
        assert data["timestamp"] == "2024-01-15T10:30:00"

    def test_from_dict(self):
        data = {
            "agent_id": "agent-1",
            "input_tokens": 100,
            "output_tokens": 200,
            "model": "gpt-4",
            "provider": "openai",
            "timestamp": "2024-01-15T10:30:00",
        }
        usage = TokenUsage.from_dict(data)
        assert usage.agent_id == "agent-1"
        assert usage.input_tokens == 100
        assert usage.output_tokens == 200
        assert usage.timestamp == datetime(2024, 1, 15, 10, 30, 0)

    def test_from_dict_with_missing_timestamp(self):
        data = {
            "agent_id": "agent-1",
            "input_tokens": 100,
            "output_tokens": 200,
            "model": "gpt-4",
            "provider": "openai",
        }
        usage = TokenUsage.from_dict(data)
        assert usage.timestamp is not None


class TestAgentCostSummary:
    def test_agent_cost_summary_creation(self):
        summary = AgentCostSummary(
            agent_id="agent-1",
            total_input_tokens=1000,
            total_output_tokens=2000,
            request_count=10,
        )
        assert summary.agent_id == "agent-1"
        assert summary.total_input_tokens == 1000
        assert summary.total_output_tokens == 2000
        assert summary.request_count == 10
        assert summary.total_cost == 0.0

    def test_total_tokens_property(self):
        summary = AgentCostSummary(
            agent_id="agent-1",
            total_input_tokens=1000,
            total_output_tokens=2000,
            request_count=10,
        )
        assert summary.total_tokens == 3000

    def test_to_dict(self):
        summary = AgentCostSummary(
            agent_id="agent-1",
            total_input_tokens=1000,
            total_output_tokens=2000,
            total_cost=0.05,
            request_count=10,
        )
        data = summary.to_dict()
        assert data["agent_id"] == "agent-1"
        assert data["total_input_tokens"] == 1000
        assert data["total_output_tokens"] == 2000
        assert data["total_tokens"] == 3000
        assert data["total_cost"] == 0.05
        assert data["request_count"] == 10


class TestTimePeriodTrend:
    def test_time_period_trend_creation(self):
        trend = TimePeriodTrend(
            period="2024-01",
            total_input_tokens=10000,
            total_output_tokens=20000,
            request_count=100,
        )
        assert trend.period == "2024-01"
        assert trend.total_input_tokens == 10000
        assert trend.total_output_tokens == 20000
        assert trend.request_count == 100
        assert trend.total_cost == 0.0

    def test_to_dict(self):
        trend = TimePeriodTrend(
            period="2024-01",
            total_input_tokens=10000,
            total_output_tokens=20000,
            total_cost=0.5,
            request_count=100,
        )
        data = trend.to_dict()
        assert data["period"] == "2024-01"
        assert data["total_input_tokens"] == 10000
        assert data["total_output_tokens"] == 20000
        assert data["total_tokens"] == 30000
        assert data["total_cost"] == 0.5
        assert data["request_count"] == 100


class TestProviderPricing:
    def test_calculate_cost_gpt4(self):
        pricing = ProviderPricing(
            provider="openai",
            model="gpt-4",
            input_cost_per_1m=30.0,
            output_cost_per_1m=60.0,
        )
        cost = pricing.calculate_cost(1_000_000, 1_000_000)
        assert cost == 90.0

    def test_calculate_cost_claude3_haiku(self):
        pricing = PROVIDER_PRICING["anthropic:claude-3-haiku"]
        cost = pricing.calculate_cost(1_000_000, 1_000_000)
        assert cost == 1.5

    def test_calculate_cost_small_tokens(self):
        pricing = PROVIDER_PRICING["openai:gpt-3.5-turbo"]
        cost = pricing.calculate_cost(1000, 500)
        expected = (1000 / 1_000_000) * 0.5 + (500 / 1_000_000) * 1.5
        assert cost == expected

    def test_get_pricing_known_provider(self):
        pricing = get_pricing("openai", "gpt-4")
        assert pricing.provider == "openai"
        assert pricing.model == "gpt-4"
        assert pricing.input_cost_per_1m == 30.0
        assert pricing.output_cost_per_1m == 60.0

    def test_get_pricing_unknown_provider(self):
        pricing = get_pricing("unknown", "unknown-model")
        assert pricing == PROVIDER_PRICING["default"]
        assert pricing.input_cost_per_1m == 1.0
        assert pricing.output_cost_per_1m == 3.0

    def test_calculate_cost_function(self):
        cost = calculate_cost("openai", "gpt-4", 1_000_000, 1_000_000)
        assert cost == 90.0

    def test_calculate_cost_unknown_model(self):
        cost = calculate_cost("unknown", "model", 1_000_000, 1_000_000)
        assert cost == 4.0

    def test_all_defined_pricing_models(self):
        assert "openai:gpt-4" in PROVIDER_PRICING
        assert "openai:gpt-4-turbo" in PROVIDER_PRICING
        assert "openai:gpt-3.5-turbo" in PROVIDER_PRICING
        assert "anthropic:claude-3-opus" in PROVIDER_PRICING
        assert "anthropic:claude-3-sonnet" in PROVIDER_PRICING
        assert "anthropic:claude-3-haiku" in PROVIDER_PRICING
        assert "google:gemini-pro" in PROVIDER_PRICING
        assert "default" in PROVIDER_PRICING


class TestTokenTrackingRepository:
    @pytest.fixture
    def mock_surreal(self):
        mock = MagicMock()
        mock.client = AsyncMock()
        mock._call = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_setup_schema(self, mock_surreal):
        repo = TokenTrackingRepository(mock_surreal)
        await repo.setup_schema()
        mock_surreal._call.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_token_usage_success(self, mock_surreal):
        repo = TokenTrackingRepository(mock_surreal)
        usage = TokenUsage(
            agent_id="agent-1",
            input_tokens=100,
            output_tokens=200,
            model="gpt-4",
            provider="openai",
        )
        mock_surreal._call.return_value = {"id": "some_id"}
        result = await repo.save_token_usage(usage)
        assert result is True

    @pytest.mark.asyncio
    async def test_save_token_usage_no_client(self):
        repo = TokenTrackingRepository(None)
        usage = TokenUsage(
            agent_id="agent-1",
            input_tokens=100,
            output_tokens=200,
            model="gpt-4",
            provider="openai",
        )
        result = await repo.save_token_usage(usage)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_usage(self, mock_surreal):
        repo = TokenTrackingRepository(mock_surreal)
        mock_surreal._call.return_value = [{
            "result": [
                {
                    "agent_id": "agent-1",
                    "input_tokens": 100,
                    "output_tokens": 200,
                    "model": "gpt-4",
                    "provider": "openai",
                    "timestamp": "2024-01-15T10:30:00",
                }
            ]
        }]
        result = await repo.get_all_usage()
        assert len(result) == 1
        assert result[0].agent_id == "agent-1"

    @pytest.mark.asyncio
    async def test_get_all_usage_no_client(self):
        repo = TokenTrackingRepository(None)
        result = await repo.get_all_usage()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_usage_by_agent(self, mock_surreal):
        repo = TokenTrackingRepository(mock_surreal)
        mock_surreal._call.return_value = [{
            "result": [
                {
                    "agent_id": "agent-1",
                    "input_tokens": 100,
                    "output_tokens": 200,
                    "model": "gpt-4",
                    "provider": "openai",
                    "timestamp": "2024-01-15T10:30:00",
                }
            ]
        }]
        result = await repo.get_usage_by_agent("agent-1")
        assert len(result) == 1
        assert result[0].agent_id == "agent-1"

    @pytest.mark.asyncio
    async def test_get_usage_by_time_range(self, mock_surreal):
        repo = TokenTrackingRepository(mock_surreal)
        mock_surreal._call.return_value = [{
            "result": [
                {
                    "agent_id": "agent-1",
                    "input_tokens": 100,
                    "output_tokens": 200,
                    "model": "gpt-4",
                    "provider": "openai",
                    "timestamp": "2024-01-15T10:30:00",
                }
            ]
        }]
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        result = await repo.get_usage_by_time_range(start, end)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_usage_by_time_range_with_agent(self, mock_surreal):
        repo = TokenTrackingRepository(mock_surreal)
        mock_surreal._call.return_value = [{"result": []}]
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        result = await repo.get_usage_by_time_range(start, end, "agent-1")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_cost_summary_by_agent(self, mock_surreal):
        repo = TokenTrackingRepository(mock_surreal)
        mock_surreal._call.return_value = [{
            "result": [
                {
                    "agent_id": "agent-1",
                    "total_input_tokens": 1000,
                    "total_output_tokens": 2000,
                    "request_count": 10,
                }
            ]
        }]
        result = await repo.get_cost_summary_by_agent()
        assert len(result) == 1
        assert result[0].agent_id == "agent-1"
        assert result[0].total_input_tokens == 1000


class TestTokenTrackingService:
    @pytest.fixture
    def mock_surreal(self):
        mock = MagicMock()
        mock.client = AsyncMock()
        mock._call = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_initialize(self, mock_surreal):
        service = TokenTrackingService(mock_surreal)
        assert service._initialized is False
        await service.initialize()
        assert service._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_twice(self, mock_surreal):
        service = TokenTrackingService(mock_surreal)
        await service.initialize()
        await service.initialize()
        assert service._initialized is True

    @pytest.mark.asyncio
    async def test_record_token_usage(self, mock_surreal):
        service = TokenTrackingService(mock_surreal)
        mock_surreal._call.return_value = {"id": "some_id"}
        usage = await service.record_token_usage(
            agent_id="agent-1",
            input_tokens=100,
            output_tokens=200,
            model="gpt-4",
            provider="openai",
        )
        assert usage.agent_id == "agent-1"
        assert usage.input_tokens == 100
        assert usage.output_tokens == 200

    @pytest.mark.asyncio
    async def test_get_agent_usage(self, mock_surreal):
        service = TokenTrackingService(mock_surreal)
        mock_surreal._call.return_value = [{
            "result": [
                {
                    "agent_id": "agent-1",
                    "input_tokens": 100,
                    "output_tokens": 200,
                    "model": "gpt-4",
                    "provider": "openai",
                    "timestamp": "2024-01-15T10:30:00",
                }
            ]
        }]
        result = await service.get_agent_usage("agent-1")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_all_usage(self, mock_surreal):
        service = TokenTrackingService(mock_surreal)
        mock_surreal._call.return_value = [{"result": []}]
        result = await service.get_all_usage()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_usage_by_time_range(self, mock_surreal):
        service = TokenTrackingService(mock_surreal)
        mock_surreal._call.return_value = [{"result": []}]
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        result = await service.get_usage_by_time_range(start, end)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_cost_summary_by_agent(self, mock_surreal):
        service = TokenTrackingService(mock_surreal)
        mock_surreal._call.side_effect = [
            [{"result": [{"agent_id": "agent-1", "total_input_tokens": 1000, "total_output_tokens": 2000, "request_count": 10}]}],
            [{"result": [
                {
                    "agent_id": "agent-1",
                    "input_tokens": 500,
                    "output_tokens": 1000,
                    "model": "gpt-4",
                    "provider": "openai",
                    "timestamp": "2024-01-15T10:30:00",
                }
            ]}],
        ]
        result = await service.get_cost_summary_by_agent()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_daily_trends(self, mock_surreal):
        service = TokenTrackingService(mock_surreal)
        mock_surreal._call.return_value = [{
            "result": [
                {
                    "day": 15,
                    "month": 1,
                    "year": 2024,
                    "total_input_tokens": 1000,
                    "total_output_tokens": 2000,
                    "request_count": 10,
                }
            ]
        }]
        result = await service.get_daily_trends(days=30)
        assert len(result) == 1
        assert result[0]["period"] == "2024-01-15"

    @pytest.mark.asyncio
    async def test_get_weekly_trends(self, mock_surreal):
        service = TokenTrackingService(mock_surreal)
        mock_surreal._call.return_value = [{
            "result": [
                {
                    "week": 3,
                    "year": 2024,
                    "total_input_tokens": 1000,
                    "total_output_tokens": 2000,
                    "request_count": 10,
                }
            ]
        }]
        result = await service.get_weekly_trends(weeks=12)
        assert len(result) == 1
        assert result[0]["period"] == "2024-W03"

    @pytest.mark.asyncio
    async def test_get_monthly_trends(self, mock_surreal):
        service = TokenTrackingService(mock_surreal)
        mock_surreal._call.return_value = [{
            "result": [
                {
                    "month": 1,
                    "year": 2024,
                    "total_input_tokens": 1000,
                    "total_output_tokens": 2000,
                    "request_count": 10,
                }
            ]
        }]
        result = await service.get_monthly_trends(months=12)
        assert len(result) == 1
        assert result[0]["period"] == "2024-01"

    @pytest.mark.asyncio
    async def test_get_daily_trends_with_agent_id(self, mock_surreal):
        service = TokenTrackingService(mock_surreal)
        mock_surreal._call.return_value = [{"result": []}]
        result = await service.get_daily_trends(days=30, agent_id="agent-1")
        assert result == []
