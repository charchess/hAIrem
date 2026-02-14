from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class ThemeDecoration(BaseModel):
    item: str = Field(..., description="Decoration item name")
    location: Optional[str] = Field(None, description="Where to place the decoration")
    description: str = Field(..., description="Description of decoration")


class ThemeMood(BaseModel):
    adjective: str = Field(..., description="Mood adjective (e.g., cozy, festive)")
    description: str = Field(..., description="Additional mood context")


class Theme(BaseModel):
    name: str = Field(..., description="Theme name (e.g., christmas, halloween, neutral)")
    display_name: str = Field(..., description="Display name for UI")
    decorations: list[ThemeDecoration] = Field(default_factory=list, description="Theme decorations")
    mood: ThemeMood = Field(..., description="Theme mood")
    is_default: bool = Field(default=False, description="Whether this is the default theme")
    active: bool = Field(default=True, description="Whether theme is currently active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


class WorldThemeState(BaseModel):
    current_theme: Optional[str] = Field(None, description="Currently active theme name")
    active_agents: list[str] = Field(default_factory=list, description="List of agents that received theme update")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


NEUTRAL_THEME = Theme(
    name="neutral",
    display_name="Neutral",
    decorations=[],
        mood=ThemeMood(
        adjective="neutral",
        description="Standard everyday mood without special context"
    ),
    is_default=True,
    active=True,
)


PREDEFINED_THEMES: dict[str, Theme] = {
    "neutral": Theme(
        name="neutral",
        display_name="Neutral",
        decorations=[],
        mood=ThemeMood(
            adjective="neutral",
            description="Standard everyday mood without special context"
        ),
        is_default=True,
        active=True,
    ),
    "christmas": Theme(
        name="christmas",
        display_name="Christmas",
        decorations=[
            ThemeDecoration(item="christmas_tree", location="living_room", description="Christmas tree with lights and ornaments"),
            ThemeDecoration(item="wreath", location="front_door", description="Festive door wreath"),
            ThemeDecoration(item="string_lights", location="mantle", description="String lights across mantle"),
            ThemeDecoration(item="stockings", location="fireplace", description="Stockings hung by the fireplace"),
        ],
        mood=ThemeMood(
            adjective="festive",
            description="Holiday spirit, cozy, gift-giving season"
        ),
        active=False,
    ),
    "halloween": Theme(
        name="halloween",
        display_name="Halloween",
        decorations=[
            ThemeDecoration(item="pumpkin", location="porch", description="Jack-o-lantern pumpkin"),
            ThemeDecoration(item="spider_web", location="front_entry", description="Cobweb decorations"),
            ThemeDecoration(item="ghost", location="hallway", description="Hanging ghost decorations"),
        ],
        mood=ThemeMood(
            adjective="spooky",
            description="Spooky, playful, costume-ready atmosphere"
        ),
        active=False,
    ),
    "spring": Theme(
        name="spring",
        display_name="Spring",
        decorations=[
            ThemeDecoration(item="flower_arrangement", location="living_room", description="Fresh spring flowers"),
            ThemeDecoration(item="pastel_bunting", location="garden", description="Pastel colored bunting"),
        ],
        mood=ThemeMood(
            adjective="fresh",
            description="Renewal, blooming flowers, lighter atmosphere"
        ),
        active=False,
    ),
    "summer": Theme(
        name="summer",
        display_name="Summer",
        decorations=[
            ThemeDecoration(item="sunflower", location="garden", description="Sunflower arrangements"),
            ThemeDecoration(item="beach_decor", location="living_room", description="Beach and ocean themed decor"),
        ],
        mood=ThemeMood(
            adjective="vibrant",
            description="Warm, energetic, vacation vibes"
        ),
        active=False,
    ),
    "autumn": Theme(
        name="autumn",
        display_name="Autumn",
        decorations=[
            ThemeDecoration(item="pumpkin_arrangement", location="entrance", description="Pumpkin and gourds"),
            ThemeDecoration(item="fall_leaves", location="mantle", description="Fall leaf arrangements"),
            ThemeDecoration(item="candle", location="table", description="Scented candles with warm fragrances"),
        ],
        mood=ThemeMood(
            adjective="cozy",
            description="Harvest, warmth, comfort, falling leaves"
        ),
        active=False,
    ),
}
