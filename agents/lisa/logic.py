import logging
from src.domain.agent import BaseAgent

logger = logging.getLogger(__name__)

class Agent(BaseAgent):
    """Custom logic for Lisa."""
    pass

async def get_inventory(ctx, args):
    door = await ctx.ha.get_state("binary_sensor.fridge_door")
    return f"Le frigo est {'ouvert' if door == 'on' else 'fermé'}."
