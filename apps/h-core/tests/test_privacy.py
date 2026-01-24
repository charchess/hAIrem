import pytest
from src.utils.privacy import PrivacyFilter

def test_privacy_regex_redaction():
    pf = PrivacyFilter()
    
    # 1. Google API Key
    text = "My key is AIzaSyAYZ8kJfPGg8Kqj5auPvT5qFeMeEvwffqo"
    redacted, detected = pf.redact(text)
    assert "[REDACTED]" in redacted
    assert "AIza" not in redacted
    assert "API Key (Google)" in detected

    # 2. IP Address
    text = "Connect to 192.168.1.100"
    redacted, detected = pf.redact(text)
    assert "192.168.1.100" not in redacted
    assert "[REDACTED]" in redacted
    assert "IP Address" in detected

def test_privacy_contextual_redaction():
    pf = PrivacyFilter()
    
    # 1. Password keyword
    text = "My password: hunter2"
    redacted, detected = pf.redact(text)
    assert "hunter2" not in redacted
    assert "[REDACTED]" in redacted
    assert "Contextual Secret" in detected

    # 2. Mixed keywords
    text = "mdp = super-secret-123"
    redacted, detected = pf.redact(text)
    assert "super-secret-123" not in redacted
    assert "Contextual Secret" in detected

def test_privacy_entropy_redaction():
    pf = PrivacyFilter(entropy_threshold=3.5)
    
    # High entropy random string (often a secret)
    text = "Use this string: 8fG29!Lp0Z99xYz"
    redacted, detected = pf.redact(text)
    assert "8fG29!Lp0Z99xYz" not in redacted
    assert "High Entropy String" in detected

    # Low entropy normal word should NOT be redacted
    text = "Hello world this is beautiful"
    redacted, detected = pf.redact(text)
    assert redacted == text
    assert len(detected) == 0

def test_privacy_no_redaction():
    pf = PrivacyFilter()
    text = "This is a normal message without any secrets."
    redacted, detected = pf.redact(text)
    assert redacted == text
    assert len(detected) == 0
