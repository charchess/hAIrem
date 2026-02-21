import os
import yaml
import logging

logger = logging.getLogger(__name__)

# Constants for paths
CONFIG_DIR = os.getenv("VISUAL_CONFIG_DIR", "/app/config/visual")
AGENTS_DIR = os.getenv("AGENTS_DIR", "/app/agents")


class VisualBible:
    def __init__(self):
        self.poses = {}
        self.attitudes = {}
        self.style = {}
        self.personas = {}
        self.themes = {}
        self.current_theme_name = "Default"
        self.load_all()

    def _safe_load(self, path, default=None):
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return yaml.safe_load(f) or (default if default is not None else {})
            except Exception as e:
                logger.error(f"BIBLE: Error loading {path}: {e}")
        return default if default is not None else {}

    def set_theme(self, theme_name: str):
        """Sets the active theme for prompt generation."""
        self.current_theme_name = theme_name
        logger.info(f"BIBLE: Theme set to '{theme_name}'")

    def load_all(self):
        # Allow override from env for testing
        config_dir = os.getenv("VISUAL_CONFIG_DIR", CONFIG_DIR)
        agents_dir = os.getenv("AGENTS_DIR", AGENTS_DIR)

        # 1. Load Poses
        self.poses = self._safe_load(os.path.join(config_dir, "POSES.yaml"))

        # 2. Load Attitudes
        self.attitudes = self._safe_load(os.path.join(config_dir, "ATTITUDES.yaml"))

        # 3. Load Global Style
        self.style = self._safe_load(os.path.join(config_dir, "STYLE_GLOBAL.yaml"))

        # 4. Load Themes
        theme_path = os.path.join(config_dir, "THEMES.yaml")
        if os.path.exists(theme_path):
            self.themes = self._safe_load(theme_path)

        # 5. Load Personas from agent folders
        if os.path.exists(agents_dir):
            for agent_id in os.listdir(agents_dir):
                agent_dir_path = os.path.join(agents_dir, agent_id)
                if not os.path.isdir(agent_dir_path):
                    continue

                persona_path = os.path.join(agent_dir_path, "persona.yaml")
                if os.path.exists(persona_path):
                    data = self._safe_load(persona_path)
                    # Store absolute path to agent dir for reference resolution
                    data["_base_path"] = agent_dir_path
                    self.personas[agent_id.lower()] = data

        logger.info(
            f"BIBLE: Loaded {len(self.poses)} poses, {len(self.attitudes)} attitudes, {len(self.personas)} personas, {len(self.themes)} themes."
        )

    def get_persona_data(self, agent_id):
        return self.personas.get(agent_id.lower(), {})

    def get_reference_images(self, agent_id):
        persona = self.get_persona_data(agent_id)
        base_path = persona.get("_base_path")
        sheets = persona.get("reference_sheets", [])

        if not base_path or not sheets:
            return []

        resolved = []
        for s in sheets:
            abs_path = os.path.join(base_path, s)
            if os.path.exists(abs_path):
                resolved.append(abs_path)
        return resolved

    def get_prompt_parts(self, agent_id, pose_key="neutral", attitude_key="standing"):
        persona = self.get_persona_data(agent_id)

        # Base parts
        base_style = self.style.get("character_style") or self.style.get("global_style", "")
        engine = self.style.get("engine_directives", "")
        post = self.style.get("post_process_constraints", "")

        # Apply theme overrides if any
        active_theme = self.themes.get(self.current_theme_name, {})
        if active_theme:
            if active_theme.get("character_style_suffix"):
                base_style = f"{base_style}, {active_theme['character_style_suffix']}"
            if active_theme.get("engine_directives_suffix"):
                engine = f"{engine}, {active_theme['engine_directives_suffix']}"

        res = {
            "character_desc": persona.get("description", f"A character named {agent_id}"),
            "pose_desc": self.poses.get(pose_key, self.poses.get("neutral", "")),
            "attitude_desc": self.attitudes.get(attitude_key, self.attitudes.get("standing", "")),
            "global_style": base_style,
            "engine_directives": engine,
            "post_process": post,
        }
        return res


bible = VisualBible()


def build_prompt(agent_id, description="", pose="neutral", attitude="standing", outfit=None, location=None, **kwargs):
    # Hot reload for live config changes
    bible.load_all()

    is_system = agent_id.lower() == "system"
    style_cfg = bible.style
    active_theme = bible.themes.get(bible.current_theme_name, {})

    if is_system:
        base_style = style_cfg.get("background_style") or style_cfg.get("global_style", "")
        engine = style_cfg.get("engine_directives", "")
        suffix = style_cfg.get("background_suffix", "")

        if active_theme:
            if active_theme.get("background_style_suffix"):
                base_style = f"{base_style}, {active_theme['background_style_suffix']}"

        return f"{description}, {base_style}, {suffix}, {engine}"

    parts = bible.get_prompt_parts(agent_id, pose, attitude)
    outfit_part = f"Wearing {outfit}." if outfit else ""
    location_part = f"Located in {location}." if location else ""
    action_part = f"Action: {description}." if description else ""

    prompt = (
        f"{parts['character_desc']} {outfit_part} {location_part} {action_part} "
        f"{parts['pose_desc']} {parts['attitude_desc']} "
        f"{parts['global_style']} {parts['engine_directives']}. "
        f"{parts['post_process']}"
    )
    return prompt
