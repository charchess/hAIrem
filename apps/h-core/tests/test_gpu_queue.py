import asyncio
import pytest
from src.services.visual.gpu_queue import GPUQueue, get_gpu_queue


@pytest.mark.asyncio
async def test_gpu_queue_submit_returns_result():
    queue = GPUQueue()
    queue.start()

    async def my_task():
        return "rendered"

    result = await queue.submit(my_task)
    assert result == "rendered"
    await queue.stop()


@pytest.mark.asyncio
async def test_gpu_queue_start_creates_worker():
    queue = GPUQueue()
    assert queue._worker_task is None
    queue.start()
    assert queue._worker_task is not None
    assert queue._running is True
    await queue.stop()


@pytest.mark.asyncio
async def test_gpu_queue_stop_cancels_worker():
    queue = GPUQueue()
    queue.start()
    await queue.stop()
    assert queue._running is False


@pytest.mark.asyncio
async def test_gpu_queue_submit_auto_starts():
    queue = GPUQueue()
    assert not queue._running

    async def simple():
        return "auto"

    result = await queue.submit(simple)
    assert result == "auto"
    await queue.stop()


@pytest.mark.asyncio
async def test_gpu_queue_submit_propagates_exception():
    queue = GPUQueue()
    queue.start()

    async def failing_task():
        raise ValueError("GPU exploded")

    with pytest.raises(ValueError, match="GPU exploded"):
        await queue.submit(failing_task)

    await queue.stop()


@pytest.mark.asyncio
async def test_gpu_queue_sequential_tasks():
    queue = GPUQueue()
    queue.start()
    results = []

    for i in range(3):
        val = i

        async def task(v=val):
            return f"result_{v}"

        results.append(await queue.submit(task))

    assert results == ["result_0", "result_1", "result_2"]
    await queue.stop()


@pytest.mark.asyncio
async def test_get_gpu_queue_returns_singleton():
    import src.services.visual.gpu_queue as gq

    gq._GLOBAL_GPU_QUEUE = None

    q1 = get_gpu_queue()
    q2 = get_gpu_queue()
    assert q1 is q2

    await q1.stop()
    gq._GLOBAL_GPU_QUEUE = None
