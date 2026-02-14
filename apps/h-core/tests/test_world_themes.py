import pytest
from src.features.home.spatial.themes.models import (
    Theme,
    ThemeDecoration,
    ThemeMood,
    WorldThemeState,
    PREDEFINED_THEMES,
    NEUTRAL_THEME,
)
from src.features.home.spatial.themes.service import WorldThemeService


class TestThemeModels:
    def test_neutral_theme_is_default(self):
        assert NEUTRAL_THEME.is_default is True
        assert NEUTRAL_THEME.name == "neutral"
        assert NEUTRAL_THEME.mood.adjective == "neutral"

    def test_predefined_themes_exist(self):
        assert "neutral" in PREDEFINED_THEMES
        assert "christmas" in PREDEFINED_THEMES
        assert "halloween" in PREDEFINED_THEMES
        assert "spring" in PREDEFINED_THEMES
        assert "summer" in PREDEFINED_THEMES
        assert "autumn" in PREDEFINED_THEMES

    def test_christmas_theme_has_decorations(self):
        christmas = PREDEFINED_THEMES["christmas"]
        assert len(christmas.decorations) > 0
        assert christmas.mood.adjective == "festive"

    def test_theme_decoration_model(self):
        decoration = ThemeDecoration(
            item="christmas_tree",
            location="living_room",
            description="A festive tree"
        )
        assert decoration.item == "christmas_tree"
        assert decoration.location == "living_room"

    def test_world_theme_state_model(self):
        state = WorldThemeState(
            current_theme="christmas",
            active_agents=["agent-1", "agent-2"]
        )
        assert state.current_theme == "christmas"
        assert len(state.active_agents) == 2


class TestWorldThemeService:
    @pytest.fixture
    def theme_service(self):
        return WorldThemeService()

    @pytest.mark.asyncio
    async def test_initialize_sets_neutral_theme(self, theme_service):
        await theme_service.initialize()
        assert theme_service.get_current_theme().name == "neutral"

    def test_get_current_theme_returns_neutral_by_default(self, theme_service):
        theme = theme_service.get_current_theme()
        assert theme.name == "neutral"

    def test_get_theme_by_name_returns_theme(self, theme_service):
        theme = theme_service.get_theme_by_name("christmas")
        assert theme is not None
        assert theme.name == "christmas"

    def test_get_theme_by_name_returns_none_for_unknown(self, theme_service):
        theme = theme_service.get_theme_by_name("unknown_theme")
        assert theme is None

    def test_get_all_themes_returns_all_available(self, theme_service):
        themes = theme_service.get_all_themes()
        assert len(themes) > 0
        theme_names = [t.name for t in themes]
        assert "neutral" in theme_names
        assert "christmas" in theme_names

    @pytest.mark.asyncio
    async def test_set_theme_changes_current_theme(self, theme_service):
        await theme_service.initialize()
        result = await theme_service.set_theme("christmas")
        
        assert result is True
        assert theme_service.get_current_theme().name == "christmas"

    @pytest.mark.asyncio
    async def test_set_theme_notifies_callbacks(self, theme_service):
        await theme_service.initialize()
        
        notified_theme_name = None
        notified_theme = None
        
        async def callback(theme_name, theme):
            nonlocal notified_theme_name, notified_theme
            notified_theme_name = theme_name
            notified_theme = theme
        
        theme_service.register_theme_callback("agent-1", callback)
        await theme_service.set_theme("halloween")
        
        assert notified_theme_name == "halloween"
        assert notified_theme is not None
        assert notified_theme.name == "halloween"

    @pytest.mark.asyncio
    async def test_set_invalid_theme_returns_false(self, theme_service):
        result = await theme_service.set_theme("nonexistent_theme")
        assert result is False
        assert theme_service.get_current_theme().name == "neutral"

    @pytest.mark.asyncio
    async def test_clear_theme_reverts_to_neutral(self, theme_service):
        await theme_service.initialize()
        await theme_service.set_theme("christmas")
        
        await theme_service.clear_theme()
        
        assert theme_service.get_current_theme().name == "neutral"

    def test_unregister_theme_callback(self, theme_service):
        async def callback(theme_name, theme):
            pass
        
        theme_service.register_theme_callback("agent-1", callback)
        theme_service.unregister_theme_callback("agent-1")
        
        assert "agent-1" not in theme_service.get_theme_state().active_agents

    def test_get_theme_prompt_context_neutral(self, theme_service):
        context = theme_service.get_theme_prompt_context()
        assert "[World Theme] Current theme: Neutral" in context
        assert "neutral" in context.lower()

    def test_get_theme_prompt_context_with_decorations(self, theme_service):
        theme_service._current_theme = PREDEFINED_THEMES["christmas"]
        
        context = theme_service.get_theme_prompt_context()
        
        assert "[World Theme] Current theme: Christmas" in context
        assert "festive" in context

    def test_get_theme_state(self, theme_service):
        state = theme_service.get_theme_state()
        assert state.current_theme == "neutral"
        assert isinstance(state.active_agents, list)


class TestThemeIntegration:
    @pytest.mark.asyncio
    async def test_theme_change_during_conversation(self):
        service = WorldThemeService()
        await service.initialize()
        
        conversation_history = []
        
        async def mock_agent_response(theme_name, theme):
            conversation_history.append(theme_name)
        
        service.register_theme_callback("agent-1", mock_agent_response)
        
        await service.set_theme("christmas")
        assert len(conversation_history) == 1
        
        await service.set_theme("halloween")
        assert len(conversation_history) == 2
        
        assert conversation_history[0] == "christmas"
        assert conversation_history[1] == "halloween"
