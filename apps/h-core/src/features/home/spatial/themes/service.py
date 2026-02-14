import logging
from typing import Optional, Callable, Awaitable
from datetime import datetime

from src.features.home.spatial.themes.models import (
    Theme,
    WorldThemeState,
    PREDEFINED_THEMES,
    NEUTRAL_THEME,
)

logger = logging.getLogger(__name__)


class ThemeUpdateCallback:
    def __init__(self, callback: Callable[[str, Theme], Awaitable[None]]):
        self.callback = callback
        self.agent_id: Optional[str] = None


class WorldThemeService:
    def __init__(self):
        self._current_theme: Theme = NEUTRAL_THEME
        self._theme_state = WorldThemeState(
            current_theme="neutral",
            active_agents=[],
        )
        self._theme_callbacks: list[ThemeUpdateCallback] = []
        self._custom_themes: dict[str, Theme] = {}

    async def initialize(self):
        logger.info("WorldThemeService: Initializing with neutral theme")
        await self._notify_all_agents()

    def get_current_theme(self) -> Theme:
        return self._current_theme

    def get_theme_by_name(self, name: str) -> Optional[Theme]:
        if name in self._custom_themes:
            return self._custom_themes[name]
        return PREDEFINED_THEMES.get(name)

    def get_all_themes(self) -> list[Theme]:
        all_themes = list(PREDEFINED_THEMES.values())
        all_themes.extend(self._custom_themes.values())
        return all_themes

    async def set_theme(self, theme_name: str) -> bool:
        theme = self.get_theme_by_name(theme_name)
        if not theme:
            logger.warning(f"WorldThemeService: Theme '{theme_name}' not found")
            return False

        old_theme_name = self._current_theme.name
        self._current_theme = theme
        self._theme_state.current_theme = theme_name
        self._theme_state.last_updated = datetime.utcnow()

        logger.info(f"WorldThemeService: Theme changed from '{old_theme_name}' to '{theme_name}'")

        await self._notify_all_agents()
        return True

    async def clear_theme(self):
        logger.info("WorldThemeService: Clearing theme, reverting to neutral")
        await self.set_theme("neutral")

    def register_theme_callback(
        self, agent_id: str, callback: Callable[[str, Theme], Awaitable[None]]
    ):
        callback_obj = ThemeUpdateCallback(callback)
        callback_obj.agent_id = agent_id
        self._theme_callbacks.append(callback_obj)
        logger.info(f"WorldThemeService: Registered theme callback for agent '{agent_id}'")

        if agent_id not in self._theme_state.active_agents:
            self._theme_state.active_agents.append(agent_id)

    def unregister_theme_callback(self, agent_id: str):
        self._theme_callbacks = [
            cb for cb in self._theme_callbacks if cb.agent_id != agent_id
        ]
        self._theme_state.active_agents = [
            a for a in self._theme_state.active_agents if a != agent_id
        ]
        logger.info(f"WorldThemeService: Unregistered theme callback for agent '{agent_id}'")

    async def _notify_all_agents(self):
        for callback_obj in self._theme_callbacks:
            try:
                await callback_obj.callback(
                    self._theme_state.current_theme, self._current_theme
                )
            except Exception as e:
                logger.error(
                    f"WorldThemeService: Error notifying agent '{callback_obj.agent_id}': {e}"
                )

    def get_theme_prompt_context(self) -> str:
        theme = self._current_theme
        context_parts = [
            f"[World Theme] Current theme: {theme.display_name}",
            f"[World Mood] The atmosphere is {theme.mood.adjective}: {theme.mood.description}",
        ]

        if theme.decorations:
            decoration_list = [
                f"{d.item} in {d.location}" for d in theme.decorations
            ]
            context_parts.append(
                f"[Decorations] {', '.join(decoration_list)}"
            )

        return " ".join(context_parts)

    def get_theme_state(self) -> WorldThemeState:
        return self._theme_state
