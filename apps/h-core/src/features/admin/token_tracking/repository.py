import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional

from src.infrastructure.surrealdb import SurrealDbClient

from .models import AgentCostSummary, TimePeriodTrend, TokenUsage

logger = logging.getLogger(__name__)


class TokenTrackingRepository:
    def __init__(self, surreal_client: Optional[SurrealDbClient]):
        self.surreal = surreal_client

    async def setup_schema(self):
        if not self.surreal or not self.surreal.client:
            logger.warning("SurrealDB client not available for token tracking schema setup")
            return

        try:
            schema_queries = """
            DEFINE TABLE IF NOT EXISTS token_usage SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS agent_id ON TABLE token_usage TYPE string;
            DEFINE FIELD IF NOT EXISTS input_tokens ON TABLE token_usage TYPE int;
            DEFINE FIELD IF NOT EXISTS output_tokens ON TABLE token_usage TYPE int;
            DEFINE FIELD IF NOT EXISTS model ON TABLE token_usage TYPE string;
            DEFINE FIELD IF NOT EXISTS provider ON TABLE token_usage TYPE string;
            DEFINE FIELD IF NOT EXISTS timestamp ON TABLE token_usage TYPE datetime DEFAULT time::now();
            DEFINE INDEX IF NOT EXISTS token_usage_agent ON TABLE token_usage FIELDS agent_id;
            DEFINE INDEX IF NOT EXISTS token_usage_timestamp ON TABLE token_usage FIELDS timestamp;
            """
            await self.surreal._call("query", schema_queries)
            logger.info("Token tracking schema setup completed")
        except Exception as e:
            logger.error(f"Failed to setup token tracking schema: {e}")

    async def save_token_usage(self, usage: TokenUsage) -> bool:
        if not self.surreal or not self.surreal.client:
            logger.warning("SurrealDB not available, skipping token usage save")
            return False

        try:
            data = usage.to_dict()
            result = await self.surreal._call("create", "token_usage", data)
            return result is not None
        except Exception as e:
            logger.error(f"Failed to save token usage: {e}")
            return False

    async def get_all_usage(self, limit: int = 1000) -> List[TokenUsage]:
        if not self.surreal or not self.surreal.client:
            return []

        try:
            query = f"SELECT * FROM token_usage ORDER BY timestamp DESC LIMIT {limit};"
            result = await self.surreal._call("query", query)
            if result and isinstance(result, list) and len(result) > 0:
                usage_data = result[0].get("result", [])
                return [TokenUsage.from_dict(u) for u in usage_data]
        except Exception as e:
            logger.error(f"Failed to get token usage: {e}")
        return []

    async def get_usage_by_agent(self, agent_id: str, limit: int = 100) -> List[TokenUsage]:
        if not self.surreal or not self.surreal.client:
            return []

        try:
            query = f"SELECT * FROM token_usage WHERE agent_id = '{agent_id}' ORDER BY timestamp DESC LIMIT {limit};"
            result = await self.surreal._call("query", query)
            if result and isinstance(result, list) and len(result) > 0:
                usage_data = result[0].get("result", [])
                return [TokenUsage.from_dict(u) for u in usage_data]
        except Exception as e:
            logger.error(f"Failed to get token usage by agent: {e}")
        return []

    async def get_usage_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        agent_id: Optional[str] = None,
    ) -> List[TokenUsage]:
        if not self.surreal or not self.surreal.client:
            return []

        try:
            start_str = start_time.isoformat()
            end_str = end_time.isoformat()

            if agent_id:
                query = f"SELECT * FROM token_usage WHERE agent_id = '{agent_id}' AND timestamp >= '{start_str}' AND timestamp <= '{end_str}' ORDER BY timestamp DESC;"
            else:
                query = f"SELECT * FROM token_usage WHERE timestamp >= '{start_str}' AND timestamp <= '{end_str}' ORDER BY timestamp DESC;"

            result = await self.surreal._call("query", query)
            if result and isinstance(result, list) and len(result) > 0:
                usage_data = result[0].get("result", [])
                return [TokenUsage.from_dict(u) for u in usage_data]
        except Exception as e:
            logger.error(f"Failed to get token usage by time range: {e}")
        return []

    async def get_cost_summary_by_agent(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[AgentCostSummary]:
        if not self.surreal or not self.surreal.client:
            return []

        try:
            if start_time and end_time:
                start_str = start_time.isoformat()
                end_str = end_time.isoformat()
                query = f"""
                SELECT
                    agent_id,
                    math::sum(input_tokens) AS total_input_tokens,
                    math::sum(output_tokens) AS total_output_tokens,
                    count() AS request_count
                FROM token_usage
                WHERE timestamp >= '{start_str}' AND timestamp <= '{end_str}'
                GROUP BY agent_id
                """
            else:
                query = """
                SELECT
                    agent_id,
                    math::sum(input_tokens) AS total_input_tokens,
                    math::sum(output_tokens) AS total_output_tokens,
                    count() AS request_count
                FROM token_usage
                GROUP BY agent_id
                """

            result = await self.surreal._call("query", query)
            if result and isinstance(result, list) and len(result) > 0:
                summary_data = result[0].get("result", [])
                return [AgentCostSummary(
                    agent_id=s.get("agent_id", ""),
                    total_input_tokens=s.get("total_input_tokens", 0),
                    total_output_tokens=s.get("total_output_tokens", 0),
                    request_count=s.get("request_count", 0),
                ) for s in summary_data]
        except Exception as e:
            logger.error(f"Failed to get cost summary by agent: {e}")
        return []

    async def get_daily_trends(
        self,
        days: int = 30,
        agent_id: Optional[str] = None,
    ) -> List[TimePeriodTrend]:
        return await self._get_time_period_trends("day", days, agent_id)

    async def get_weekly_trends(
        self,
        weeks: int = 12,
        agent_id: Optional[str] = None,
    ) -> List[TimePeriodTrend]:
        return await self._get_time_period_trends("week", weeks, agent_id)

    async def get_monthly_trends(
        self,
        months: int = 12,
        agent_id: Optional[str] = None,
    ) -> List[TimePeriodTrend]:
        return await self._get_time_period_trends("month", months, agent_id)

    async def _get_time_period_trends(
        self,
        period: str,
        count: int,
        agent_id: Optional[str] = None,
    ) -> List[TimePeriodTrend]:
        if not self.surreal or not self.surreal.client:
            return []

        try:
            if agent_id:
                if period == "day":
                    query = f"""
                    SELECT
                        time::day(timestamp) AS day,
                        time::month(timestamp) AS month,
                        time::year(timestamp) AS year,
                        math::sum(input_tokens) AS total_input_tokens,
                        math::sum(output_tokens) AS total_output_tokens,
                        count() AS request_count
                    FROM token_usage
                    WHERE agent_id = '{agent_id}'
                    GROUP BY time::day(timestamp), time::month(timestamp), time::year(timestamp)
                    ORDER BY year DESC, month DESC, day DESC
                    LIMIT {count}
                    """
                elif period == "week":
                    query = f"""
                    SELECT
                        time::week(timestamp) AS week,
                        time::year(timestamp) AS year,
                        math::sum(input_tokens) AS total_input_tokens,
                        math::sum(output_tokens) AS total_output_tokens,
                        count() AS request_count
                    FROM token_usage
                    WHERE agent_id = '{agent_id}'
                    GROUP BY time::week(timestamp), time::year(timestamp)
                    ORDER BY year DESC, week DESC
                    LIMIT {count}
                    """
                else:
                    query = f"""
                    SELECT
                        time::month(timestamp) AS month,
                        time::year(timestamp) AS year,
                        math::sum(input_tokens) AS total_input_tokens,
                        math::sum(output_tokens) AS total_output_tokens,
                        count() AS request_count
                    FROM token_usage
                    WHERE agent_id = '{agent_id}'
                    GROUP BY time::month(timestamp), time::year(timestamp)
                    ORDER BY year DESC, month DESC
                    LIMIT {count}
                    """
            else:
                if period == "day":
                    query = f"""
                    SELECT
                        time::day(timestamp) AS day,
                        time::month(timestamp) AS month,
                        time::year(timestamp) AS year,
                        math::sum(input_tokens) AS total_input_tokens,
                        math::sum(output_tokens) AS total_output_tokens,
                        count() AS request_count
                    FROM token_usage
                    GROUP BY time::day(timestamp), time::month(timestamp), time::year(timestamp)
                    ORDER BY year DESC, month DESC, day DESC
                    LIMIT {count}
                    """
                elif period == "week":
                    query = f"""
                    SELECT
                        time::week(timestamp) AS week,
                        time::year(timestamp) AS year,
                        math::sum(input_tokens) AS total_input_tokens,
                        math::sum(output_tokens) AS total_output_tokens,
                        count() AS request_count
                    FROM token_usage
                    GROUP BY time::week(timestamp), time::year(timestamp)
                    ORDER BY year DESC, week DESC
                    LIMIT {count}
                    """
                else:
                    query = f"""
                    SELECT
                        time::month(timestamp) AS month,
                        time::year(timestamp) AS year,
                        math::sum(input_tokens) AS total_input_tokens,
                        math::sum(output_tokens) AS total_output_tokens,
                        count() AS request_count
                    FROM token_usage
                    GROUP BY time::month(timestamp), time::year(timestamp)
                    ORDER BY year DESC, month DESC
                    LIMIT {count}
                    """

            result = await self.surreal._call("query", query)
            if result and isinstance(result, list) and len(result) > 0:
                trend_data = result[0].get("result", [])
                trends = []
                for t in trend_data:
                    if period == "day":
                        day = t.get("day", 0)
                        month = t.get("month", 0)
                        year = t.get("year", 0)
                        period_str = f"{year}-{month:02d}-{day:02d}"
                    elif period == "week":
                        week = t.get("week", 0)
                        year = t.get("year", 0)
                        period_str = f"{year}-W{week:02d}"
                    else:
                        month = t.get("month", 0)
                        year = t.get("year", 0)
                        period_str = f"{year}-{month:02d}"
                    trends.append(TimePeriodTrend(
                        period=period_str,
                        total_input_tokens=t.get("total_input_tokens", 0),
                        total_output_tokens=t.get("total_output_tokens", 0),
                        request_count=t.get("request_count", 0),
                    ))
                return trends
        except Exception as e:
            logger.error(f"Failed to get {period}ly trends: {e}")
        return []
