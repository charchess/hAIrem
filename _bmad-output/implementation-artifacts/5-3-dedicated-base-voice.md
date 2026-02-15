# Story 5-3: Dedicated Base Voice

**Status: completed**

## Story

As an Agent,
I want a dedicated base voice,
So that each agent has a unique vocal identity.

## Acceptance Criteria

1. [AC1] Given an agent is configured, when voice synthesis is requested, then the agent's dedicated voice is used
2. [AC2] Given an agent's voice profile, when set, then it's consistent across interactions
3. [AC3] Given multiple agents, when they speak, then each has a distinct voice

## Tasks / Subtasks

- [x] Task 1: Create voice profile system
- [x] Task 2: Implement voice profiles per agent
- [x] Task 3: Integrate with TTS service

## Dev Notes

### Code Status
- Voice profile system implemented with default profiles for amalia, marcus, elena
- Supports custom voice profiles per agent
- Integrated with TTS service

### Test File
tests/atdd/epic5-voice-modulation.spec.ts

## Dev Agent Record

### File List
- apps/h-bridge/src/services/voice.py
- apps/h-bridge/src/handlers/tts.py (updated)
- apps/h-bridge/src/main.py (added voice API endpoints)

### Implementation Notes
- Created VoiceProfile dataclass with pitch, rate, volume, language, gender
- DEFAULT_VOICES provides default profiles for amalia, marcus, elena, default
- VoiceProfileService manages profiles and applies them to TTS params
- API endpoints: GET/PUT /api/agents/{agent_id}/voice
