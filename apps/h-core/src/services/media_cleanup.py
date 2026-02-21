import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_PERMANENT_QUERY = "SELECT url FROM visual_asset WHERE tags CONTAINS 'permanent';"


class MediaCleanupWorker:
    def __init__(
        self,
        storage_path: str,
        surreal_client: Any,
        max_files: int = 100,
        check_interval_seconds: int = 21600,
    ):
        self.storage_path = storage_path
        self.surreal = surreal_client
        self.max_files = max_files
        self.check_interval_seconds = check_interval_seconds
        self._stop_event = asyncio.Event()

    async def _get_permanent_urls(self) -> set[str]:
        if not self.surreal:
            return set()
        try:
            res = await self.surreal._call("query", _PERMANENT_QUERY)
            if res and isinstance(res, list) and len(res) > 0:
                records = res[0].get("result", []) if isinstance(res[0], dict) else []
                return {r["url"] for r in records if "url" in r}
        except Exception as e:
            logger.error(f"MediaCleanupWorker: permanent URL query failed — {e}")
        return set()

    async def run_once(self) -> None:
        try:
            loop = asyncio.get_running_loop()

            def _scan():
                entries = []
                for name in os.listdir(self.storage_path):
                    path = os.path.join(self.storage_path, name)
                    if os.path.isfile(path):
                        st = os.stat(path)
                        entries.append({"path": path, "atime": st.st_atime})
                return entries

            files = await loop.run_in_executor(None, _scan)

            if len(files) <= self.max_files:
                return

            permanent_urls = await self._get_permanent_urls()

            files.sort(key=lambda x: x["atime"])

            to_delete = len(files) - self.max_files
            deleted = 0

            for entry in files:
                if deleted >= to_delete:
                    break
                url = f"file://{entry['path']}"
                if url in permanent_urls:
                    continue
                try:
                    await loop.run_in_executor(None, os.remove, entry["path"])
                    deleted += 1
                    logger.debug(f"MediaCleanupWorker: deleted {entry['path']}")
                except Exception as e:
                    logger.error(f"MediaCleanupWorker: delete failed — {entry['path']}: {e}")

            logger.info(f"MediaCleanupWorker: cleanup done — {deleted} files removed.")

        except Exception as e:
            logger.error(f"MediaCleanupWorker: run_once error — {e}")

    async def run_loop(self) -> None:
        logger.info("MediaCleanupWorker: background loop started.")
        while not self._stop_event.is_set():
            await self.run_once()
            await asyncio.sleep(self.check_interval_seconds)

    def stop(self) -> None:
        self._stop_event.set()
