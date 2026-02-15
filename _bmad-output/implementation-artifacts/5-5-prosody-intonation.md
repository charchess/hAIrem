# Story 5-5: Prosody and Intonation

**Status: completed**

## Story

As an Agent,
I want my voice to have proper prosody and intonation,
So that I sound natural.

## Acceptance Criteria

1. [AC1] Given text to be spoken, when TTS is generated, then prosody and intonation are applied
2. [AC2] Given speech, when generated, then it sounds natural
3. [AC3] Given questions vs statements, when synthesized, then intonation differs appropriately

## Tasks / Subtasks

- [x] Task 1: Create prosody service
- [x] Task 2: Implement intonation patterns
- [x] Task 3: Integrate with TTS

## Dev Notes

### Code Status
- Prosody service implemented
- Supports 5 intonation types: statement, question, exclamation, command, list
- Sentence type detection based on punctuation and question starters
- Supports 6 prosody styles: default, formal, casual, dramatic, monotone, expressive
- Integrated with TTS service

### Test File
tests/atdd/epic5-voice-modulation.spec.ts

## Dev Agent Record

### File List
- apps/h-bridge/src/services/prosody.py
- apps/h-bridge/src/handlers/tts.py (updated)
- apps/h-bridge/src/main.py (added prosody endpoints)

### Implementation Notes
- ProsodyConfig maps intonation types to pitch_modifier, rate_modifier, emphasis
- detect_sentence_type() analyzes text for question/statement/exclamation
- apply_prosody() applies prosody modifiers to voice params
- analyze_text_prosody() provides detailed prosody analysis
- API endpoints: GET/PUT /api/agents/{agent_id}/voice/prosody, POST /api/voice/analyze-prosody
