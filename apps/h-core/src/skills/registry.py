import importlib
import inspect
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_SKILLS_ROOT = Path(__file__).parent


class SkillRegistry:
    def load(self, skill_name: str) -> dict[str, Callable]:
        skill_dir = _SKILLS_ROOT / skill_name
        if not skill_dir.is_dir():
            raise ValueError(f"Skill '{skill_name}' not found in {_SKILLS_ROOT}")

        module = importlib.import_module(f"src.skills.{skill_name}")
        tools: dict[str, Callable] = {}
        for attr_name, obj in inspect.getmembers(module, inspect.isfunction):
            if not attr_name.startswith("_"):
                tools[attr_name] = obj

        if not tools:
            logger.warning(f"SKILL_REGISTRY: No public functions found in skill '{skill_name}'")

        logger.info(f"SKILL_REGISTRY: Loaded {len(tools)} tools from '{skill_name}': {list(tools)}")
        return tools

    def get_metadata(self, skill_name: str) -> dict[str, Any]:
        skill_dir = _SKILLS_ROOT / skill_name
        if not skill_dir.is_dir():
            raise ValueError(f"Skill '{skill_name}' not found in {_SKILLS_ROOT}")

        yaml_path = skill_dir / "skill.yaml"
        if not yaml_path.exists():
            return {"name": skill_name, "access": "multiple", "version": "unknown", "description": "", "tools": []}

        with open(yaml_path) as f:
            data = yaml.safe_load(f) or {}

        data.setdefault("access", "multiple")
        return data

    def list_available(self) -> list[str]:
        return [d.name for d in _SKILLS_ROOT.iterdir() if d.is_dir() and (d / "__init__.py").exists()]

    def list_all_metadata(self) -> list[dict[str, Any]]:
        return [self.get_metadata(name) for name in self.list_available()]
