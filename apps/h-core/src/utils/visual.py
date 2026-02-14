"""
Fallback utilities for visual agent functions
Provides minimal implementations when full visual module is not available
"""

import logging

logger = logging.getLogger(__name__)


def extract_poses(agent_data: dict) -> list:
    """Fallback implementation for pose extraction."""
    logger.warning("Using fallback pose extraction - returning empty list")
    return []


def pose_asset_exists(agent_id: str, pose_type: str) -> bool:
    """Fallback implementation for pose asset checking."""
    logger.warning(f"Using fallback pose asset check for {agent_id} - {pose_type}")
    return False


def save_agent_image(agent_id: str, image_data: bytes, pose_type: str) -> str:
    """Fallback implementation for image saving."""
    logger.warning(f"Using fallback image saving for {agent_id}")
    # Return a placeholder path
    return f"/tmp/{agent_id}_{pose_type}.png"


def count_pose_variations(agent_id: str) -> int:
    """Fallback implementation for pose variation counting."""
    logger.warning(f"Using fallback pose variation count for {agent_id}")
    return 1


# Additional fallback functions that might be needed
def get_agent_visual_config(agent_id: str) -> dict:
    """Get visual configuration for agent."""
    return {
        "agent_id": agent_id,
        "enabled": True,
        "fallback_mode": True
    }