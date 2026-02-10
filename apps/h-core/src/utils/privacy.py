import logging
import math
import re

logger = logging.getLogger(__name__)

class PrivacyFilter:
    """Utility to redact sensitive information from text."""

    REDACTION_STRING = "[REDACTED]"

    # Layer 1: Regex Patterns
    PATTERNS = [
        # Google API Keys
        (r'AIza[0-9A-Za-z-_]{35}', "API Key (Google)"),
        # OpenAI API Keys
        (r'sk-[a-zA-Z0-9]{20,}', "API Key (OpenAI)"),
        # IP Addresses (IPv4)
        (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', "IP Address"),
        # Generic Tokens/Keys
        (r'\b[a-zA-Z0-9]{32,}\b', "Generic Token")
    ]

    # Layer 2: Contextual Keywords
    CONTEXT_KEYWORDS = [
        "password", "mdp", "mot de passe", "secret", "token", "apikey", "api_key"
    ]

    def __init__(self, entropy_threshold: float = 3.8):
        self.entropy_threshold = entropy_threshold

    def calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not text:
            return 0.0
        
        # Count frequency of each character
        freq: dict[str, int] = {}
        for char in text:
            freq[char] = freq.get(char, 0) + 1
        
        # Calculate entropy
        probs = [count / len(text) for count in freq.values()]
        entropy = -sum(p * math.log2(p) for p in probs)
        return entropy

    def redact(self, text: str) -> tuple[str, list[str]]:
        """
        Scan and redact sensitive info.
        Returns (redacted_text, list_of_detected_types)
        """
        if not text:
            return text, []

        redacted_text = text
        detected_types = []

        # 1. Regex Redaction (Layer 1)
        for pattern, label in self.PATTERNS:
            matches = re.findall(pattern, redacted_text)
            if matches:
                redacted_text = re.sub(pattern, self.REDACTION_STRING, redacted_text)
                if label not in detected_types:
                    detected_types.append(label)

        # 2. Contextual Redaction (Layer 2)
        # Search for words following keywords: "password: value", "mdp = value"
        for kw in self.CONTEXT_KEYWORDS:
            # Matches keyword followed by optional symbols (: = ) and then a word
            # We use a non-greedy whitespace match and capture the next non-whitespace word
            ctx_pattern = rf'(?i)({kw})\s*[:=]\s*([^\s,;]+)'
            
            def replace_ctx(match):
                nonlocal detected_types
                if "Contextual Secret" not in detected_types:
                    detected_types.append("Contextual Secret")
                return f"{match.group(1)}: {self.REDACTION_STRING}"

            redacted_text = re.sub(ctx_pattern, replace_ctx, redacted_text)

        # 3. High Entropy Redaction (Layer 3)
        # Split into words and check entropy for words > 8 chars
        words = redacted_text.split()
        for word in words:
            # Skip if already redacted or too short
            if self.REDACTION_STRING in word or len(word) < 10:
                continue
            
            # If it looks like a hash or random string
            if self.calculate_entropy(word) > self.entropy_threshold:
                # Double check: does it contain mixed case and numbers/symbols?
                if any(c.isdigit() for c in word) or any(not c.isalnum() for c in word):
                    redacted_text = redacted_text.replace(word, self.REDACTION_STRING)
                    if "High Entropy String" not in detected_types:
                        detected_types.append("High Entropy String")

        return redacted_text, detected_types
