# Story 5-2: Synthesized Voice Output

**Status:** done

## Story

As a User,
I want to hear agent responses as speech,
So that I can interact using voice only.

## Acceptance Criteria

1. [AC1] Given an agent responds, when text is generated, then it's converted to speech
2. [AC2] Given speech is generated, when ready, then it's played to the user
3. [AC3] Given playback fails, when attempted, then fallback to text is provided

## Tasks / Subtasks

- [x] Task 1: Implement text-to-speech conversion
- [x] Task 2: Add audio playback
- [x] Task 3: Add fallback handling

## Dev Notes

- TTS via Web Speech API (speechSynthesis)
- Audio playback in browser
- Fallback to text display

## Status: done
