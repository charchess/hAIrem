import logging
from typing import Any, Optional
from src.infrastructure.surrealdb import SurrealDbClient

logger = logging.getLogger(__name__)

class VaultService:
    def __init__(self, db_client: SurrealDbClient):
        self.db = db_client

    async def save_item(self, agent_id: str, name: str, uri: str, prompt: str, category: str = "general", asset_id: str = None):
        """Saves a named asset to the vault."""
        logger.info(f"VAULT: Saving '{name}' for {agent_id} (Category: {category}, URI: {uri}, ID: {asset_id})")
        
        if not asset_id:
            # Last resort lookup
            q = "SELECT id FROM visual_asset WHERE url = $uri LIMIT 1;"
            res = await self.db._call('query', q, {"uri": uri})
            if isinstance(res, list) and len(res) > 0:
                first_stmt = res[0]
                results = first_stmt if isinstance(first_stmt, list) else first_stmt.get("result", [])
                if results and len(results) > 0:
                    asset_id = str(results[0].get("id"))
        
        if not asset_id:
            logger.warning(f"VAULT: Could not resolve record ID for URI: {uri}")
            return None
            
        # Story 25.7: Use INSERT ON DUPLICATE KEY UPDATE for robust upsert on unique index
        q = """
        INSERT INTO vault {
            agent_id: $agent, 
            name: $name, 
            asset_id: type::record($asset), 
            uri: $uri, 
            prompt: $prompt,
            category: $category,
            timestamp: time::now()
        } ON DUPLICATE KEY UPDATE 
            asset_id = type::record($asset),
            uri = $uri,
            prompt = $prompt,
            category = $category,
            timestamp = time::now();
        """
        params = {
            "agent": agent_id,
            "name": name,
            "asset": asset_id,
            "uri": uri,
            "prompt": prompt,
            "category": category
        }
        
        res = await self.db._call('query', q, params)
        logger.info(f"VAULT_UPSERT_RES: {res}")
        
        if isinstance(res, list) and len(res) > 0:
             # Check for error in response if client doesn't raise
             first = res[0]
             if isinstance(first, dict) and first.get("status") == "ERR":
                 logger.error(f"VAULT_UPSERT_ERR: {first}")
                 return None

        logger.info(f"VAULT: Successfully upserted '{name}' for {agent_id}")
        return asset_id

    async def get_item(self, agent_id: str, name: str, category: Optional[str] = None) -> Optional[dict[str, Any]]:
        """
        Retrieves a vault item by name for a specific agent.
        """
        name = name.strip().lower().replace(" ", "_").replace("'", "\\'")
        aid = f"subject:`{agent_id.lower().replace(' ', '_')}`"
        
        # Fetch with asset details joined
        query = f"SELECT *, asset_id.* as asset FROM vault WHERE agent_id = {aid} AND name = '{name}'"
        if category:
            query += f" AND category = '{category}'"
        query += " LIMIT 1;"
        
        try:
            res = await self.db._call("query", query)
            if res and isinstance(res, list) and len(res) > 0:
                result_list = res[0].get("result", []) if isinstance(res[0], dict) else res
                if result_list and isinstance(result_list, list) and len(result_list) > 0:
                    return result_list[0]
            return None
        except Exception as e:
            logger.error(f"VAULT_ERROR: Failed to get item '{name}': {e}")
            return None

    async def list_items(self, agent_id: str, category: Optional[str] = None) -> list[dict[str, Any]]:
        """
        Lists all vault items for an agent.
        """
        aid = f"subject:`{agent_id.lower().replace(' ', '_')}`"
        query = f"SELECT *, asset_id.* as asset FROM vault WHERE agent_id = {aid}"
        if category:
            query += f" AND category = '{category}'"
        
        try:
            res = await self.db._call("query", query)
            if res and isinstance(res, list) and len(res) > 0:
                result_list = res[0].get("result", []) if isinstance(res[0], dict) else res
                return result_list if isinstance(result_list, list) else []
            return []
        except Exception as e:
            logger.error(f"VAULT_ERROR: Failed to list items for {agent_id}: {e}")
            return []
