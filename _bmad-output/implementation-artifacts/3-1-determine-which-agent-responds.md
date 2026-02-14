# Story 3.1: Determine Which Agent Responds

Status: completed

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a System,
I want to determine which agent should respond to a message,
so that the most appropriate agent replies.

## Acceptance Criteria

1. [AC1] Given a user message arrives, when the arbiter processes it, then the most relevant agent is selected based on scoring
2. [AC2] Given multiple agents have similar scores, when there's a tie, then a deterministic tiebreaker is applied
3. [AC3] Given no agent meets minimum threshold, when arbiter evaluates, then a default agent is selected or message is rejected

## Tasks / Subtasks

- [x] Task 1: Implement agent scoring engine (AC: #1)
  - [x] Subtask 1.1: Define scoring algorithm based on relevance, interests, and emotional context
  - [x] Subtask 1.2: Create scoring input (user message, agent profiles)
  - [x] Subtask 1.3: Return ranked agent list
- [x] Task 2: Implement tiebreaker logic (AC: #2)
  - [x] Subtask 2.1: Define deterministic ordering (e.g., agent ID, last response time)
- [x] Task 3: Implement fallback behavior (AC: #3)
  - [x] Subtask 3.1: Define minimum threshold configuration
  - [x] Subtask 3.2: Define default agent selection logic

## Dev Notes

- Architecture follows feature-based organization under `src/features/home/social_arbiter/`
- Uses configurable scoring weights for relevance (0.5), interests (0.3), and emotional context (0.2)
- Minimum threshold default: 0.2, configurable
- Integration with Redis via ArbiterService for event publishing

### Project Structure Notes

- Created `src/features/home/social_arbiter/` directory per architecture
- Test file: `tests/test_social_arbiter.py`

### References

- Architecture: _bmad-output/planning-artifacts/architecture.md
- PRD: _bmad-output/planning-artifacts/prd.md (FR18-FR23)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

- apps/h-core/src/features/home/social_arbiter/__init__.py
- apps/h-core/src/features/home/social_arbiter/models.py
- apps/h-core/src/features/home/social_arbiter/scoring.py
- apps/h-core/src/features/home/social_arbiter/tiebreaker.py
- apps/h-core/src/features/home/social_arbiter/fallback.py
- apps/h-core/src/features/home/social_arbiter/arbiter.py
- apps/h-core/src/features/home/social_arbiter/service.py
- apps/h-core/tests/test_social_arbiter.py
