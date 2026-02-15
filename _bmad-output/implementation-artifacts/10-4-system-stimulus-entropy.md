# Story 10-4: System Stimulus/Entropy

**Status:** done

## Story

As an Agent,
I want to receive system stimuli,
So that I can act proactively without user input.

## Acceptance Criteria

1. [AC1] Given system stimuli exist, when generated, then agents can receive them
2. [AC2] Given stimuli trigger actions, when executed, then results are logged
3. [AC3] Given stimuli cause too many actions, when threshold reached, then rate limiting applies

## Tasks / Subtasks

- [x] Task 1: Implement stimulus configuration endpoint
- [x] Task 2: Add stimulus triggering endpoint
- [x] Task 3: Add rate limiting via max_stimuli_per_day

## Dev Notes

- System stimulus/entropy API implemented in apps/h-bridge/src/main.py
- Stimuli published to Redis for agent subscription
- Rate limiting via configuration

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stimulus/config` | GET | Get stimulus configuration |
| `/api/stimulus/config` | POST | Update stimulus configuration |
| `/api/stimulus/trigger` | POST | Manually trigger a stimulus |
| `/api/stimulus/history` | GET | Get stimulus history |

## File List

- apps/h-bridge/src/main.py (stimulus endpoints)

## Status: done
