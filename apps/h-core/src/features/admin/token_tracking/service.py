import logging
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, List, Optional

from src.infrastructure.surrealdb import SurrealDbClient

from .models import AgentCostSummary, TimePeriodTrend, TokenUsage
from .pricing import calculate_cost, get_pricing
from .repository import TokenTrackingRepository

logger = logging.getLogger(__name__)

TokenUsageCallback = Callable[[TokenUsage], Awaitable[None]]


class TokenTrackingService:
    def __init__(self, surreal_client: Optional[SurrealDbClient] = None):
        self.surreal = surreal_client
        self.repository = TokenTrackingRepository(surreal_client)
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return

        await self.repository.setup_schema()
        self._initialized = True
        logger.info("Token tracking service initialized")

    async def record_token_usage(
        self,
        agent_id: str,
        input_tokens: int,
        output_tokens: int,
        model: str,
        provider: str,
    ) -> TokenUsage:
        usage = TokenUsage(
            agent_id=agent_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            provider=provider,
        )

        await self.repository.save_token_usage(usage)
        return usage

    async def get_agent_usage(
        self,
        agent_id: str,
        limit: int = 100,
    ) -> List[TokenUsage]:
        return await self.repository.get_usage_by_agent(agent_id, limit)

    async def get_all_usage(self, limit: int = 1000) -> List[TokenUsage]:
        return await self.repository.get_all_usage(limit)

    async def get_usage_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        agent_id: Optional[str] = None,
    ) -> List[TokenUsage]:
        return await self.repository.get_usage_by_time_range(start_time, end_time, agent_id)

    async def get_cost_summary_by_agent(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[dict[str, Any]]:
        summaries = await self.repository.get_cost_summary_by_agent(start_time, end_time)

        result = []
        for summary in summaries:
            usage_list = await self.repository.get_usage_by_time_range(
                start_time or datetime.min,
                end_time or datetime.max,
                summary.agent_id,
            )

            total_cost = 0.0
            for usage in usage_list:
                cost = calculate_cost(
                    usage.provider,
                    usage.model,
                    usage.input_tokens,
                    usage.output_tokens,
                )
                total_cost += cost

            summary.total_cost = total_cost
            result.append(summary.to_dict())

        return result

    async def get_daily_trends(
        self,
        days: int = 30,
        agent_id: Optional[str] = None,
    ) -> List[dict[str, Any]]:
        trends = await self.repository.get_daily_trends(days, agent_id)
        return await self._add_costs_to_trends(trends)

    async def get_weekly_trends(
        self,
        weeks: int = 12,
        agent_id: Optional[str] = None,
    ) -> List[dict[str, Any]]:
        trends = await self.repository.get_weekly_trends(weeks, agent_id)
        return await self._add_costs_to_trends(trends)

    async def get_monthly_trends(
        self,
        months: int = 12,
        agent_id: Optional[str] = None,
    ) -> List[dict[str, Any]]:
        trends = await self.repository.get_monthly_trends(months, agent_id)
        return await self._add_costs_to_trends(trends)

    async def _add_costs_to_trends(self, trends: List[TimePeriodTrend]) -> List[dict[str, Any]]:
        result = []
        for trend in trends:
            pricing = get_pricing("default", "default")
            cost = pricing.calculate_cost(trend.total_input_tokens, trend.total_output_tokens)
            trend.total_cost = cost
            result.append(trend.to_dict())
        return result
