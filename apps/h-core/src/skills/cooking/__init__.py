from __future__ import annotations


async def suggest_recipe(ingredients: list[str], **kwargs) -> str:
    joined = ", ".join(ingredients) if ingredients else "your ingredients"
    return (
        f"With {joined}, a stir-fry or salad works well. "
        "For a personalized recipe, ask your LLM directly with these ingredients."
    )


async def substitute_ingredient(ingredient: str, **kwargs) -> str:
    substitutions = {
        "butter": "olive oil or coconut oil",
        "eggs": "flax eggs (1 tbsp ground flax + 3 tbsp water)",
        "milk": "oat milk or almond milk",
        "flour": "almond flour or rice flour",
    }
    return substitutions.get(ingredient.lower(), f"No known substitution for {ingredient}")


async def set_timer(minutes: float, label: str = "cooking", ha_client=None, **kwargs) -> str:
    if ha_client is None:
        return f"[Simulation] Timer: {minutes} min for {label}. Connect Home Assistant to trigger a real timer."
    await ha_client.call_service(
        "timer", "start", {"entity_id": f"timer.{label.lower().replace(' ', '_')}", "duration": f"{int(minutes)}:00"}
    )
    return f"Timer started: {minutes} min for {label}"
