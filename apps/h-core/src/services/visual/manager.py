import asyncio
import logging
import os
import shutil
from datetime import datetime
from typing import Any

from src.infrastructure.surrealdb import SurrealDbClient

logger = logging.getLogger(__name__)


class AssetManager:
    def __init__(self, db_client: SurrealDbClient, storage_path: str = "/media/generated"):
        self.db = db_client
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)

    async def save_asset(self, source_path: str, metadata: dict[str, Any]) -> tuple[str, str | None]:
        """
        Moves a generated file to persistent storage and indexes it in SurrealDB.

        Args:
            source_path: Local path to the generated image file.
            metadata: Dict containing prompt, embedding, agent_id, tags, etc.

        Returns:
            A tuple of (URI, record_id).
        """
        filename = os.path.basename(source_path)
        # Ensure filename is somewhat unique if needed, but here we assume it's already managed
        dest_path = os.path.join(self.storage_path, filename)

        # Move file asynchronously
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, shutil.move, source_path, dest_path)
            # Story 25.6: Ensure bridge can serve the file (chmod 644)
            os.chmod(dest_path, 0o644)
            logger.info(f"Asset moved to {dest_path} with 644 permissions")
        except Exception as e:
            logger.error(f"Failed to move asset from {source_path} to {dest_path}: {e}")
            raise

        # Index in DB
        asset_url = f"file://{dest_path}"

        asset_data = {
            "url": asset_url,
            "prompt": metadata.get("prompt", ""),
            "embedding": metadata.get("embedding", []),
            "agent_id": metadata.get("agent_id", "system"),
            "tags": metadata.get("tags", []),
            "reference_image_used": metadata.get("reference_image_used", ""),
        }

        asset_id = await self.db.save_asset_record(asset_data)
        if asset_id:
            logger.info(f"Asset indexed in SurrealDB: {asset_url} -> ID: {asset_id}")
        else:
            logger.warning(f"Asset index failed for {asset_url}")

        return asset_url, asset_id

    async def get_asset_by_prompt(self, embedding: list[float], limit: int = 5, threshold: float = 0.0) -> list[dict[str, Any]]:
        """
        Search for assets using vector similarity in SurrealDB.
        """
        if not embedding:
            return []

        # SurrealDB 2.x vector similarity query
        query = f"SELECT *, vector::similarity::cosine(embedding, {embedding}) AS score FROM visual_asset "
        if threshold > 0:
            query += f"WHERE vector::similarity::cosine(embedding, {embedding}) > {threshold} "
        query += f"ORDER BY score DESC LIMIT {limit};"
        
        try:
            res = await self.db._call("query", query)
            if res and isinstance(res, list) and len(res) > 0:
                result_list = res[0].get("result", []) if isinstance(res[0], dict) else res
                return result_list if isinstance(result_list, list) else []
            return []
        except Exception as e:
            logger.error(f"Failed to search assets by prompt: {e}")
            return []

    async def cleanup_assets(self, quota_bytes: int):
        """
        Garbage collection (LRU): removes oldest files when quota is reached.
        """
        try:
            loop = asyncio.get_running_loop()

            def get_files_with_stats():
                files_found = []
                for f in os.listdir(self.storage_path):
                    path = os.path.join(self.storage_path, f)
                    if os.path.isfile(path):
                        stats = os.stat(path)
                        files_found.append({"path": path, "size": stats.st_size, "atime": stats.st_atime})
                return files_found

            files = await loop.run_in_executor(None, get_files_with_stats)
            total_size = sum(f["size"] for f in files)

            if total_size <= quota_bytes:
                logger.info(f"Storage usage ({total_size} bytes) is within quota ({quota_bytes} bytes).")
                return

            logger.info(f"Quota exceeded ({total_size} > {quota_bytes}). Starting cleanup...")

            # Sort by last access time (oldest first)
            files.sort(key=lambda x: x["atime"])

            to_delete_size = total_size - quota_bytes
            deleted_count = 0
            deleted_size = 0

            for f in files:
                if deleted_size >= to_delete_size:
                    break

                try:
                    await loop.run_in_executor(None, os.remove, f["path"])

                    # Also remove from DB
                    asset_url = f"file://{f['path']}"
                    await self.db._call("query", f"DELETE visual_asset WHERE url = '{asset_url}';")

                    deleted_size += f["size"]
                    deleted_count += 1
                    logger.debug(f"Deleted asset: {f['path']}")
                except Exception as e:
                    logger.error(f"Failed to delete {f['path']}: {e}")

            logger.info(f"Cleanup completed: deleted {deleted_count} files, total {deleted_size} bytes.")

        except Exception as e:
            logger.error(f"Error during asset cleanup: {e}")
