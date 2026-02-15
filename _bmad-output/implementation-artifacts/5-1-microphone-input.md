# Story 5-1: Microphone Input

**Status:** done

## Story

As a User,
I want to speak to agents via microphone,
So that I can interact using voice.

## Acceptance Criteria

1. [AC1] Given microphone access, when user speaks, then audio is captured
2. [AC2] Given audio is captured, when processed, then it's converted to text
3. [AC3] Given voice input fails, when attempted, then error is handled gracefully

## Tasks / Subtasks

- [x] Task 1: Implement microphone capture
- [x] Task 2: Add speech-to-text conversion
- [x] Task 3: Add error handling

## Dev Notes

- Microphone input via Web Audio API
- Speech-to-text via browser SpeechRecognition
- Error handling for permission denied

## Status: done
