import asyncio
import os
import time
import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch


def _make_worker(storage_path, surreal=None, max_files=100, check_interval=1):
    from src.services.media_cleanup import MediaCleanupWorker

    if surreal is None:
        surreal = MagicMock()
        surreal._call = AsyncMock(return_value=[{"result": []}])

    return MediaCleanupWorker(
        storage_path=storage_path,
        surreal_client=surreal,
        max_files=max_files,
        check_interval_seconds=check_interval,
    ), surreal


@pytest.mark.asyncio
async def test_lru_removes_oldest_files_when_limit_reached():
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(110):
            path = os.path.join(tmp, f"asset_{i:03d}.png")
            with open(path, "w") as f:
                f.write("x")
            os.utime(path, (time.time() - (110 - i) * 10, time.time() - (110 - i) * 10))

        worker, _ = _make_worker(tmp, max_files=100)
        await worker.run_once()

        remaining = os.listdir(tmp)
        assert len(remaining) == 100


@pytest.mark.asyncio
async def test_lru_deletes_oldest_first():
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(105):
            path = os.path.join(tmp, f"asset_{i:03d}.png")
            with open(path, "w") as f:
                f.write("x")
            atime = time.time() - (105 - i) * 10
            os.utime(path, (atime, atime))

        worker, _ = _make_worker(tmp, max_files=100)
        await worker.run_once()

        remaining = set(os.listdir(tmp))
        for i in range(5):
            assert f"asset_{i:03d}.png" not in remaining


@pytest.mark.asyncio
async def test_no_deletion_when_under_limit():
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(50):
            path = os.path.join(tmp, f"asset_{i:03d}.png")
            with open(path, "w") as f:
                f.write("x")

        worker, _ = _make_worker(tmp, max_files=100)
        await worker.run_once()

        assert len(os.listdir(tmp)) == 50


@pytest.mark.asyncio
async def test_permanent_files_not_deleted():
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(110):
            path = os.path.join(tmp, f"asset_{i:03d}.png")
            with open(path, "w") as f:
                f.write("x")
            atime = time.time() - (110 - i) * 10
            os.utime(path, (atime, atime))

        perm_path = os.path.join(tmp, "asset_000.png")
        perm_url = f"file://{perm_path}"

        surreal = MagicMock()
        surreal._call = AsyncMock(return_value=[{"result": [{"url": perm_url}]}])

        worker, _ = _make_worker(tmp, surreal=surreal, max_files=100)
        await worker.run_once()

        assert os.path.exists(perm_path)


@pytest.mark.asyncio
async def test_cleanup_runs_periodically():
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(5):
            path = os.path.join(tmp, f"asset_{i}.png")
            with open(path, "w") as f:
                f.write("x")

        worker, _ = _make_worker(tmp, max_files=100, check_interval=0)
        worker.run_once = AsyncMock()

        task = asyncio.create_task(worker.run_loop())
        await asyncio.sleep(0.05)
        worker.stop()
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert worker.run_once.call_count >= 1
