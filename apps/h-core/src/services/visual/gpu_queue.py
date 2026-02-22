from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


class GPUQueue:
    def __init__(self, max_size: int = 10):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._worker_task: asyncio.Task | None = None
        self._running = False

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._worker())
            logger.info("GPUQueue: worker started")

    async def stop(self) -> None:
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("GPUQueue: stopped")

    async def submit(self, coro_factory: Callable[[], Coroutine[Any, Any, str]]) -> str:
        if not self._running:
            self.start()
        future: asyncio.Future[str] = asyncio.get_running_loop().create_future()
        await self._queue.put((coro_factory, future))
        return await future

    async def _worker(self) -> None:
        while self._running:
            try:
                coro_factory, future = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                try:
                    result = await coro_factory()
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)
                finally:
                    self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"GPUQueue: worker error — {e}")


_GLOBAL_GPU_QUEUE: GPUQueue | None = None


def get_gpu_queue() -> GPUQueue:
    global _GLOBAL_GPU_QUEUE
    if _GLOBAL_GPU_QUEUE is None:
        _GLOBAL_GPU_QUEUE = GPUQueue()
        _GLOBAL_GPU_QUEUE.start()
    return _GLOBAL_GPU_QUEUE
