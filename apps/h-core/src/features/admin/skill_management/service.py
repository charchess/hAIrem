import logging
from datetime import datetime
from typing import Any, Optional

from src.skills.registry import SkillRegistry

logger = logging.getLogger(__name__)

_registry = SkillRegistry()


class SkillGrantService:
    def __init__(self, surreal_client=None):
        self.surreal = surreal_client

    async def _upsert(self, persona_id: str, skill_name: str, active: bool, access_mode: str):
        record_id = f"skill_grants:`{persona_id}_{skill_name}`"
        q = """
        INSERT INTO skill_grants {
            id: $id,
            persona_id: $persona,
            skill_name: $skill,
            active: $active,
            access_mode: $access,
            granted_at: time::now()
        } ON DUPLICATE KEY UPDATE
            active = $active,
            access_mode = $access;
        """
        params = {
            "id": record_id,
            "persona": persona_id,
            "skill": skill_name,
            "active": active,
            "access": access_mode,
        }
        if self.surreal:
            await self.surreal._call("query", q, params)

    async def is_active(self, persona_id: str, skill_name: str) -> bool:
        if not self.surreal:
            return True

        try:
            res = await self.surreal._call(
                "query",
                f"SELECT active FROM skill_grants WHERE persona_id = '{persona_id}' AND skill_name = '{skill_name}' LIMIT 1;",
            )
            if res and isinstance(res, list) and len(res) > 0:
                rows = res[0].get("result", []) if isinstance(res[0], dict) else []
                if rows:
                    return bool(rows[0].get("active", True))
        except Exception as e:
            logger.error(f"SKILL_GRANT: is_active check failed: {e}")

        return True

    async def grant(self, persona_id: str, skill_name: str) -> dict[str, Any]:
        try:
            metadata = _registry.get_metadata(skill_name)
        except ValueError:
            return {"success": False, "error": f"Skill '{skill_name}' not found"}

        access_mode = metadata.get("access", "multiple")

        if access_mode == "unique" and self.surreal:
            res = await self.surreal._call(
                "query",
                f"SELECT persona_id FROM skill_grants WHERE skill_name = '{skill_name}' AND active = true AND persona_id != '{persona_id}';",
            )
            if res and isinstance(res, list) and len(res) > 0:
                rows = res[0].get("result", []) if isinstance(res[0], dict) else []
                if rows:
                    holder = rows[0].get("persona_id", "unknown")
                    return {
                        "success": False,
                        "error": f"Skill '{skill_name}' is unique and already granted to '{holder}'",
                    }

        await self._upsert(persona_id, skill_name, active=True, access_mode=access_mode)
        logger.info(f"SKILL_GRANT: Granted '{skill_name}' to '{persona_id}' (access={access_mode})")
        return {"success": True, "persona_id": persona_id, "skill_name": skill_name, "active": True}

    async def revoke(self, persona_id: str, skill_name: str) -> dict[str, Any]:
        try:
            metadata = _registry.get_metadata(skill_name)
        except ValueError:
            return {"success": False, "error": f"Skill '{skill_name}' not found"}

        access_mode = metadata.get("access", "multiple")
        await self._upsert(persona_id, skill_name, active=False, access_mode=access_mode)
        logger.info(f"SKILL_GRANT: Revoked '{skill_name}' from '{persona_id}'")
        return {"success": True, "persona_id": persona_id, "skill_name": skill_name, "active": False}

    async def list_grants(self) -> list[dict[str, Any]]:
        if not self.surreal:
            return []
        try:
            res = await self.surreal._call("query", "SELECT * FROM skill_grants ORDER BY persona_id, skill_name;")
            if res and isinstance(res, list) and len(res) > 0:
                return res[0].get("result", []) if isinstance(res[0], dict) else []
        except Exception as e:
            logger.error(f"SKILL_GRANT: list_grants failed: {e}")
        return []

    async def list_persona_skills(self, persona_id: str) -> list[dict[str, Any]]:
        if not self.surreal:
            return []
        try:
            res = await self.surreal._call("query", f"SELECT * FROM skill_grants WHERE persona_id = '{persona_id}';")
            if res and isinstance(res, list) and len(res) > 0:
                return res[0].get("result", []) if isinstance(res[0], dict) else []
        except Exception as e:
            logger.error(f"SKILL_GRANT: list_persona_skills failed: {e}")
        return []


class SkillManagementService:
    def __init__(self, grant_service: SkillGrantService):
        self.grants = grant_service

    async def list_skills(self) -> list[dict[str, Any]]:
        all_grants = await self.grants.list_grants()
        active_grants: dict[str, list[str]] = {}
        for g in all_grants:
            if g.get("active"):
                sn = g["skill_name"]
                active_grants.setdefault(sn, []).append(g["persona_id"])

        result = []
        for meta in _registry.list_all_metadata():
            skill_name = meta["name"]
            result.append(
                {
                    "skill_name": skill_name,
                    "version": meta.get("version", "unknown"),
                    "access": meta.get("access", "multiple"),
                    "description": meta.get("description", ""),
                    "tools": [t["name"] for t in meta.get("tools", [])],
                    "active_for": active_grants.get(skill_name, []),
                    "available": True,
                }
            )
        return result

    async def grant(self, persona_id: str, skill_name: str) -> dict[str, Any]:
        return await self.grants.grant(persona_id, skill_name)

    async def revoke(self, persona_id: str, skill_name: str) -> dict[str, Any]:
        return await self.grants.revoke(persona_id, skill_name)

    async def list_persona_skills(self, persona_id: str) -> list[dict[str, Any]]:
        return await self.grants.list_persona_skills(persona_id)
