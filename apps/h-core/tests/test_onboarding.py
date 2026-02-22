import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestOnboardingService:
    def _make_redis(self, stored: dict = None):
        stored = stored or {}
        client = AsyncMock()

        async def _get(key):
            val = stored.get(key)
            return val.encode() if isinstance(val, str) else val

        async def _set(key, value, ex=None, nx=False):
            if nx:
                if key in stored:
                    return False
                stored[key] = value
                return True
            stored[key] = value
            return True

        async def _delete(key):
            stored.pop(key, None)

        client.get = _get
        client.set = _set
        client.delete = _delete

        redis = MagicMock()
        redis.client = client
        redis.publish_event = AsyncMock()
        return redis

    @pytest.mark.asyncio
    async def test_new_user_is_not_onboarded(self):
        from src.features.home.onboarding.service import OnboardingService

        svc = OnboardingService(redis_client=self._make_redis())
        assert not await svc.is_onboarded("user_new")

    @pytest.mark.asyncio
    async def test_start_interview_returns_first_question(self):
        from src.features.home.onboarding.service import OnboardingService, INTERVIEW_QUESTIONS

        svc = OnboardingService(redis_client=self._make_redis())
        result = await svc.start_interview("user_1", "Alice")

        assert result["status"] == "started"
        assert result["question"] == INTERVIEW_QUESTIONS[0]["text"]
        assert result["step"] == 0

    @pytest.mark.asyncio
    async def test_already_onboarded_user_skips(self):
        from src.features.home.onboarding.service import OnboardingService

        stored = {"hairem:onboarded:user_done": "1"}
        svc = OnboardingService(redis_client=self._make_redis(stored))
        result = await svc.start_interview("user_done")

        assert result["status"] == "already_onboarded"

    @pytest.mark.asyncio
    async def test_submit_answer_advances_step(self):
        from src.features.home.onboarding.service import OnboardingService, INTERVIEW_QUESTIONS

        svc = OnboardingService(redis_client=self._make_redis())
        await svc.start_interview("user_2")
        result = await svc.submit_answer("user_2", "Alice")

        assert result["status"] == "in_progress"
        assert result["step"] == 1
        assert result["question"] == INTERVIEW_QUESTIONS[1]["text"]

    @pytest.mark.asyncio
    async def test_complete_interview_after_all_answers(self):
        from src.features.home.onboarding.service import OnboardingService, INTERVIEW_QUESTIONS

        svc = OnboardingService(redis_client=self._make_redis())
        await svc.start_interview("user_3")

        for _ in INTERVIEW_QUESTIONS[:-1]:
            await svc.submit_answer("user_3", "test_answer")

        result = await svc.submit_answer("user_3", "final_answer")
        assert result["status"] == "complete"
        assert "answers" in result

    @pytest.mark.asyncio
    async def test_user_is_marked_onboarded_after_completion(self):
        from src.features.home.onboarding.service import OnboardingService, INTERVIEW_QUESTIONS

        svc = OnboardingService(redis_client=self._make_redis())
        await svc.start_interview("user_4")

        for _ in INTERVIEW_QUESTIONS:
            await svc.submit_answer("user_4", "answer")

        assert await svc.is_onboarded("user_4")

    @pytest.mark.asyncio
    async def test_onboarding_complete_publishes_event(self):
        from src.features.home.onboarding.service import OnboardingService, INTERVIEW_QUESTIONS

        redis = self._make_redis()
        svc = OnboardingService(redis_client=redis)
        await svc.start_interview("user_5")

        for _ in INTERVIEW_QUESTIONS:
            await svc.submit_answer("user_5", "answer")

        redis.publish_event.assert_called_once()
        call_args = redis.publish_event.call_args[0]
        assert call_args[0] == "system_stream"
        assert call_args[1]["type"] == "system.onboarding_complete"

    @pytest.mark.asyncio
    async def test_answers_stored_in_result(self):
        from src.features.home.onboarding.service import OnboardingService, INTERVIEW_QUESTIONS

        svc = OnboardingService(redis_client=self._make_redis())
        await svc.start_interview("user_6")

        answers = ["Bob", "musique et tech", "bien", "seul"]
        for answer in answers:
            result = await svc.submit_answer("user_6", answer)

        assert result["status"] == "complete"
        assert result["answers"]["preferred_name"] == "Bob"
        assert result["answers"]["interests"] == "musique et tech"
