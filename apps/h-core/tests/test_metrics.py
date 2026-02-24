import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from prometheus_client import CollectorRegistry


def _fresh_registry():
    return CollectorRegistry()


class TestMetricsCollector:
    def test_record_surrealdb_call_observes_histogram(self):
        from src.infrastructure.metrics import MetricsCollector

        registry = _fresh_registry()
        col = MetricsCollector(registry=registry)
        col.record_surrealdb_call("query", 0.123)

        samples = {s.name: s.value for s in registry.collect() for s in s.samples}
        assert samples["surrealdb_call_duration_seconds_count"] == 1.0

    def test_record_surrealdb_call_labels_method(self):
        from src.infrastructure.metrics import MetricsCollector

        registry = _fresh_registry()
        col = MetricsCollector(registry=registry)
        col.record_surrealdb_call("query", 0.05)
        col.record_surrealdb_call("create", 0.10)

        samples = {(s.name, tuple(sorted(s.labels.items()))): s.value for m in registry.collect() for s in m.samples}
        count_query = samples.get(("surrealdb_call_duration_seconds_count", (("method", "query"),)), 0)
        count_create = samples.get(("surrealdb_call_duration_seconds_count", (("method", "create"),)), 0)
        assert count_query == 1.0
        assert count_create == 1.0

    def test_record_llm_completion_observes_histogram(self):
        from src.infrastructure.metrics import MetricsCollector

        registry = _fresh_registry()
        col = MetricsCollector(registry=registry)
        col.record_llm_completion("gpt-4o", 1.5)

        samples = {s.name: s.value for m in registry.collect() for s in m.samples}
        assert samples["llm_completion_duration_seconds_count"] == 1.0

    def test_record_tts_synthesis_observes_histogram(self):
        from src.infrastructure.metrics import MetricsCollector

        registry = _fresh_registry()
        col = MetricsCollector(registry=registry)
        col.record_tts_synthesis(0.42)

        samples = {s.name: s.value for m in registry.collect() for s in m.samples}
        assert samples["tts_synthesis_duration_seconds_count"] == 1.0

    def test_generate_prometheus_text_format(self):
        from src.infrastructure.metrics import MetricsCollector
        from prometheus_client import generate_latest

        registry = _fresh_registry()
        col = MetricsCollector(registry=registry)
        col.record_surrealdb_call("query", 0.1)
        col.record_llm_completion("gemini", 2.0)
        col.record_tts_synthesis(0.5)

        output = generate_latest(registry).decode()
        assert "surrealdb_call_duration_seconds" in output
        assert "llm_completion_duration_seconds" in output
        assert "tts_synthesis_duration_seconds" in output


class TestSurrealDbMetricsInstrumentation:
    @pytest.mark.asyncio
    async def test_call_records_latency(self):
        from src.infrastructure.metrics import MetricsCollector

        registry = _fresh_registry()
        col = MetricsCollector(registry=registry)

        mock_client = MagicMock()
        mock_client.query = AsyncMock(return_value=[{"result": []}])

        with patch("src.infrastructure.surrealdb.get_metrics_collector", return_value=col):
            from src.infrastructure.surrealdb import SurrealDbClient

            db = SurrealDbClient(url="ws://x", user="u", password="p")
            db.client = mock_client
            await db._call("query", "SELECT 1;")

        samples = {s.name: s.value for m in registry.collect() for s in m.samples}
        assert samples.get("surrealdb_call_duration_seconds_count", 0) == 1.0


class TestLlmMetricsInstrumentation:
    @pytest.mark.asyncio
    async def test_get_completion_records_latency(self):
        from src.infrastructure.metrics import MetricsCollector

        registry = _fresh_registry()
        col = MetricsCollector(registry=registry)

        with patch("src.infrastructure.llm.get_metrics_collector", return_value=col):
            with patch("src.infrastructure.llm.acompletion") as mock_acompletion:
                with patch("src.infrastructure.llm.LITELLM_AVAILABLE", True):
                    mock_resp = MagicMock()
                    mock_resp.choices = [MagicMock()]
                    mock_resp.choices[0].message.content = "hello"
                    mock_acompletion.return_value = mock_resp

                    from src.infrastructure.llm import LlmClient

                    llm = LlmClient()
                    llm.model = "gpt-4o"
                    llm._current_provider = {"model": "gpt-4o", "api_key": None, "base_url": None}
                    await llm.get_completion([{"role": "user", "content": "hi"}])

        samples = {s.name: s.value for m in registry.collect() for s in m.samples}
        assert samples.get("llm_completion_duration_seconds_count", 0) == 1.0


class TestTtsMetricsInstrumentation:
    @pytest.mark.asyncio
    async def test_synthesize_records_latency(self):
        from src.infrastructure.metrics import MetricsCollector

        registry = _fresh_registry()
        col = MetricsCollector(registry=registry)

        mock_primary = MagicMock()
        mock_primary.synthesize = AsyncMock(return_value=b"audio")
        mock_fallback = MagicMock()
        mock_redis = MagicMock()

        with patch("src.services.audio.tts_orchestrator.get_metrics_collector", return_value=col):
            from src.services.audio.tts_orchestrator import TtsOrchestrator

            orch = TtsOrchestrator(primary=mock_primary, fallback=mock_fallback, redis_client=mock_redis)
            await orch.synthesize("bonjour")

        samples = {s.name: s.value for m in registry.collect() for s in m.samples}
        assert samples.get("tts_synthesis_duration_seconds_count", 0) == 1.0
