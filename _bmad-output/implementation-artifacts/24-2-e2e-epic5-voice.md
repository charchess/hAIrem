# Story 24-2: E2E Epic 5 - Voice Tests

**Status:** done

## Story

As a QA Engineer,
I want end-to-end tests for Epic 5 Voice,
So that voice input/output works end-to-end.

## Acceptance Criteria

1. [AC1] Given microphone input, when speaking, then STT converts to text
2. [AC2] Given agent responds, when TTS, then audio plays
3. [AC3] Given voice modulation, when emotion set, then voice changes
4. [AC4] Given prosody, when style applied, then intonation varies

## Tasks / Subtasks

- [ ] Task 1: Create Playwright E2E tests for voice flow
- [ ] Task 2: Test STT → TTS pipeline
- [ ] Task 3: Test emotion/prosody modulation
- [ ] Task 4: Test browser compatibility

## Dev Notes

- Use Playwright with audio context
- Mock STT/TTS if needed
- ~8 tests estimated

## File List

- tests/e2e/epic5-voice.spec.ts

## Status: backlog