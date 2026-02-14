# Story 3.3: Emotional Context Evaluation

Status: in-progress

## Story

As a Arbiter,
I want to evaluate the emotional context of interactions,
so that responses are emotionally appropriate.

## Acceptance Criteria

1. [AC1] Given a user message with emotional content, when the arbiter analyzes it, then the emotional tone is detected
2. [AC2] Given emotional tone is detected, when scoring agents, then agents with matching emotional capacity get a boost
3. [AC3] Given emotional context is evaluated, when selecting agent, then selected agent's emotional state is updated based on interaction

## Tasks / Subtasks

- [x] Task 1: Implement emotional tone detection (AC: #1)
  - [x] Subtask 1.1: Define emotion categories (happy, sad, angry, excited, etc.)
  - [x] Subtask 1.2: Implement emotion extraction from user message (keyword-based or LLM)
- [x] Task 2: Implement emotional scoring (AC: #2)
  - [x] Subtask 2.1: Define agent emotional capabilities
  - [x] Subtask 2.2: Apply emotional match bonus to scoring
- [x] Task 3: Update agent emotional state (AC: #3)
  - [x] Subtask 3.1: Update agent emotional state in memory
  - [x] Subtask 3.2: Track emotional history for context

## Dev Notes

### References
- Architecture: _bmad-output/planning-artifacts/architecture.md
- PRD: _bmad-output/planning-artifacts/prd.md (FR20)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md
- Depends on: Stories 3.1, 3.2

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### File List
- apps/h-core/src/features/home/social_arbiter/emotion_detection.py (new)
- apps/h-core/src/features/home/social_arbiter/models.py (updated)
- apps/h-core/src/features/home/social_arbiter/scoring.py (updated)
- apps/h-core/src/features/home/social_arbiter/arbiter.py (updated)
- apps/h-core/src/features/home/social_arbiter/service.py (updated)
- apps/h-core/src/features/home/social_arbiter/repository.py (updated)
- apps/h-core/src/features/home/social_arbiter/__init__.py (updated)
