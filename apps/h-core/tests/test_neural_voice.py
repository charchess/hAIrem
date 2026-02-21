import pytest
from src.models.agent import AgentConfig


def _make_assignment():
    from src.services.audio.neural_voice import NeuralVoiceAssignment

    return NeuralVoiceAssignment()


def test_known_agents_have_distinct_voices():
    nva = _make_assignment()
    voices = {
        "lisa": nva.get_voice("lisa"),
        "renarde": nva.get_voice("renarde"),
        "electra": nva.get_voice("electra"),
    }
    assert len(set(voices.values())) == 3


def test_config_voice_id_overrides_default():
    nva = _make_assignment()
    result = nva.get_voice("lisa", config_voice_id="custom-voice-fr")
    assert result == "custom-voice-fr"


def test_unknown_agent_gets_default_voice():
    nva = _make_assignment()
    result = nva.get_voice("inconnu_agent_xyz")
    assert result == "FR-Default"


def test_agent_config_accepts_voice_id():
    config = AgentConfig(name="Lisa", role="companion", voice_id="FR-Lisa")
    assert config.voice_id == "FR-Lisa"


def test_agent_config_voice_id_defaults_to_none():
    config = AgentConfig(name="Lisa", role="companion")
    assert config.voice_id is None


def test_dieu_and_entropy_get_neutral_voice():
    nva = _make_assignment()
    assert nva.get_voice("dieu") == nva.get_voice("entropy")


def test_case_insensitive_lookup():
    nva = _make_assignment()
    assert nva.get_voice("LISA") == nva.get_voice("lisa")
    assert nva.get_voice("Renarde") == nva.get_voice("renarde")
