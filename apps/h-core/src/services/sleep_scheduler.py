import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class SleepScheduler:
    def __init__(
        self,
        consolidator: Any,
        redis_client: Any,
        inactivity_threshold_minutes: int | None = None,
        check_interval_seconds: int = 60,
    ):
        self.consolidator = consolidator
        self.redis = redis_client
        self.inactivity_threshold_minutes = (
            inactivity_threshold_minutes
            if inactivity_threshold_minutes is not None
            else int(os.getenv("SLEEP_INACTIVITY_THRESHOLD_MINUTES", "30"))
        )
        self.check_interval_seconds = check_interval_seconds
        self.last_activity: datetime = datetime.utcnow()
        self._last_cycle_run: datetime | None = None
        self._stop_event = asyncio.Event()

    def record_activity(self) -> None:
        self.last_activity = datetime.utcnow()

    async def _maybe_run_cycle(self) -> None:
        now = datetime.utcnow()
        threshold = timedelta(minutes=self.inactivity_threshold_minutes)
        idle_since = now - self.last_activity

        if threshold.total_seconds() > 0 and idle_since < threshold:
            return

        cooldown = max(threshold, timedelta(seconds=self.check_interval_seconds))
        if self._last_cycle_run and (now - self._last_cycle_run) < cooldown:
            return

        logger.info(f"SleepScheduler: {int(idle_since.total_seconds())}s idle — triggering sleep cycle.")
        await self._run_cycle()

    async def force_run(self) -> None:
        logger.info("SleepScheduler: forced run.")
        await self._run_cycle()

    async def _run_cycle(self) -> None:
        self._last_cycle_run = datetime.utcnow()
        try:
            learned = await self.consolidator.consolidate()
            await self.consolidator.apply_decay()
            logger.info(f"SleepScheduler: cycle complete — {learned} elements learned.")
        except Exception as e:
            logger.error(f"SleepScheduler: cycle failed — {e}")

    async def run_loop(self) -> None:
        logger.info("SleepScheduler: background loop started.")
        while not self._stop_event.is_set():
            try:
                await self._maybe_run_cycle()
            except Exception as e:
                logger.error(f"SleepScheduler: loop error — {e}")
            await asyncio.sleep(self.check_interval_seconds)

    def stop(self) -> None:
        self._stop_event.set()
