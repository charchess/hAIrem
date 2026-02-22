from __future__ import annotations


async def suggest_recipe(ingredients: list[str], **kwargs) -> str:
    return f"Based on {', '.join(ingredients)}, I suggest a simple stir-fry or salad."


async def substitute_ingredient(ingredient: str, **kwargs) -> str:
    substitutions = {
        "butter": "olive oil or coconut oil",
        "eggs": "flax eggs (1 tbsp ground flax + 3 tbsp water)",
        "milk": "oat milk or almond milk",
        "flour": "almond flour or rice flour",
    }
    return substitutions.get(ingredient.lower(), f"No known substitution for {ingredient}")


async def set_timer(minutes: float, label: str = "cooking", **kwargs) -> str:
    return f"Timer set: {minutes} min for {label}"
