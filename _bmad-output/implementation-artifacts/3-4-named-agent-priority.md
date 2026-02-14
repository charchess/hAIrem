# Story 3.4: Named Agent Priority

Status: in-progress

## Story

As a System,
I want named agents to get priority,
so that when a user says "Lisa, tell me...", Lisa responds.

## Acceptance Criteria

1. [AC1] Given a user explicitly names an agent in the message, when the message is processed, then that agent gets priority
2. [AC2] Given a named agent is prioritized, when scoring is computed, then the named agent's score is boosted above all others
3. [AC3] Given a named agent is not found in the system, when processing, then the message is handled as if no name was mentioned

## Tasks / Subtasks

- [x] Task 1: Implement name detection (AC: #1)
  - [x] Subtask 1.1: Parse user message for agent name mentions
  - [x] Subtask 1.2: Handle variations (full name, nickname, partial match)
- [x] Task 2: Implement priority boost (AC: #2)
  - [x] Subtask 2.1: Apply maximum priority score to named agent
  - [x] Subtask 2.2: Skip other agents if named agent meets minimum threshold
- [x] Task 3: Handle unknown agent name (AC: #3)
  - [x] Subtask 3.1: Log warning for unknown name
  - [x] Subtask 3.2: Fallback to standard scoring

## Dev Notes

### References
- Architecture: _bmad-output/planning-artifacts/architecture.md
- PRD: _bmad-output/planning-artifacts/prd.md (FR21)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md
- Depends on: Stories 3.1, 3.2

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### File List

- `apps/h-core/src/features/home/social_arbiter/name_detection.py` - New file for name extraction
- `apps/h-core/src/features/home/social_arbiter/arbiter.py` - Updated to integrate name detection
- `apps/h-core/src/features/home/social_arbiter/__init__.py` - Updated to export NameExtractor
- `apps/h-core/tests/test_social_arbiter.py` - Added tests for name extraction and priority

### Implementation Details

Created `NameExtractor` class with support for:
- Pattern: "Name, verb..." (e.g., "Lisa, tu peux me dire...")
- Pattern: "@Name" (e.g., "@Marie dis-moi")
- Pattern: "Name:" (e.g., "Paul: raconte")
- Pattern: "Bonjour/Hey/Salut Name" (e.g., "Bonjour Lisa", "Hey Marie")
- Pattern: "Dis/Dit Name" (e.g., "Dis Paul")
- Partial name matching (e.g., "Lis" matches "Lisa")
- Short names (<=2 chars) filtered out

The `SocialArbiter.determine_responder()` method now:
1. First checks explicit `mentioned_agents` parameter (Stories 3.1-3.3)
2. Then detects names from message content (this story)
3. Falls back to standard scoring if no match found

When an unknown name is detected, a warning is logged and the message is processed using standard scoring.