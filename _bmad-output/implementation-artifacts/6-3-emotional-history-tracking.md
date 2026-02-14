# Story 6.3: Emotional History Tracking

Status: completed

## Story

As a System,
I want to track emotional history per user,
so that I understand short-term context.

## Acceptance Criteria

1. [AC1] Given a user interacts, when emotional state is detected, then it's stored in short-term context
2. [AC2] Given emotional history exists, when next interaction occurs, then previous emotional state is loaded
3. [AC3] Given emotional history accumulates, when threshold is reached, then older emotions are summarized or archived

## Tasks / Subtasks

- [x] Task 1: Implement emotional state detection (AC: #1)
  - [x] Subtask 1.1: Detect emotion from user message (keyword-based or LLM)
  - [x] Subtask 1.2: Store emotional state with timestamp
- [x] Task 2: Implement emotional history loading (AC: #2)
  - [x] Subtask 2.1: Load recent emotional states per user
  - [x] Subtask 2.2: Include in conversation context
- [x] Task 3: Implement history management (AC: #3)
  - [x] Subtask 3.1: Define retention threshold
  - [x] Subtask 3.2: Implement summarization or archival

## Dev Notes

### References
- PRD: _bmad-output/planning-artifacts/prd.md (FR27)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### File List

- apps/h-core/src/features/home/emotional_history/__init__.py
- apps/h-core/src/features/home/emotional_history/models.py
- apps/h-core/src/features/home/emotional_history/repository.py
- apps/h-core/src/features/home/emotional_history/service.py
- apps/h-core/tests/test_emotional_history.py
