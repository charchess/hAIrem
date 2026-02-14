import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


class NameExtractor:
    def __init__(self):
        self._name_patterns = [
            re.compile(r'^(\w+),?\s+(?:tu|pourrais|peux|peut|pourrait|voudrais|voudrait|dis|dites|raconte)', re.IGNORECASE),
            re.compile(r'@(\w+)', re.IGNORECASE),
            re.compile(r'^(\w+)\s*:', re.IGNORECASE),
            re.compile(r'(?:dis-|dit-|raconte-|demande-|要求|告诉)(\s*)(\w+)', re.IGNORECASE),
            re.compile(r'^(?:bonjour|salut|hey|hello|hi)\s+(\w+)', re.IGNORECASE),
            re.compile(r'^(?:dis|dit)\s+(\w+)', re.IGNORECASE),
        ]

    def extract_name_from_message(self, message: str) -> str | None:
        message_stripped = message.strip()
        
        for pattern in self._name_patterns:
            match = pattern.match(message_stripped)
            if match:
                name = match.group(1) if match.lastindex >= 1 else match.group(2)
                if name:
                    cleaned_name = re.sub(r'[,\.\!\?\;]+$', '', name)
                    return cleaned_name.strip()
        
        first_word = message_stripped.split()[0] if message_stripped.split() else None
        if first_word and first_word[0].isupper() and len(first_word) > 1:
            if len(message_stripped.split()) > 1:
                cleaned_first = re.sub(r'[,\.\!\?\;]+$', '', first_word)
                return cleaned_first
        
        return None

    def find_agent_by_name(
        self,
        name: str,
        agents: dict[str, Any],
    ) -> tuple[str | None, bool]:
        name_lower = name.lower()
        
        if len(name_lower) <= 2:
            return None, False
        
        for agent_id, agent in agents.items():
            if not agent.is_active:
                continue
            
            if agent.name.lower() == name_lower:
                return agent_id, True
            
            if hasattr(agent, 'nickname') and agent.nickname:
                if agent.nickname.lower() == name_lower:
                    return agent_id, True
            
            if agent.name.lower().startswith(name_lower):
                return agent_id, True
            
            if name_lower in agent.name.lower():
                return agent_id, True
        
        for agent_id, agent in agents.items():
            if not agent.is_active:
                continue
            
            name_parts = name_lower.split()
            agent_name_parts = agent.name.lower().split()
            
            if any(part in agent_name_parts for part in name_parts if len(part) > 2):
                return agent_id, True
        
        return None, False
