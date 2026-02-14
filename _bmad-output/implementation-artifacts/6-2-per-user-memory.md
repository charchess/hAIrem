# Story 6.2: Per-User Memory

Status: ready-for-dev

## Story

As a Agent,
I want to have separate memories for each user,
so that I remember interactions with each person differently.

## Acceptance Criteria

1. [AC1] Given an agent interacts with multiple users, when memories are stored, then each user's memories are separate
2. [AC2] Given memories are stored per user, when retrieval happens, then memories are filtered by the current user
3. [AC3] Given user switches, when context changes, then agent switches to the new user's memory context

## Tasks / Subtasks

- [x] Task 1: Implement user-memory linking (AC: #1)
  - [x] Subtask 1.1: Update memory schema to include user_id field
  - [x] Subtask 1.2: Implement memory creation with user association
- [x] Task 2: Implement user-filtered retrieval (AC: #2)
  - [x] Subtask 2.1: Update recall to filter by user_id
  - [x] Subtask 2.2: Include user context in memory prompts
- [x] Task 3: Implement context switching (AC: #3)
  - [x] Subtask 3.1: Detect user change in session
  - [x] Subtask 3.2: Switch memory context accordingly

## Dev Notes

### References
- PRD: _bmad-output/planning-artifacts/prd.md (FR25, FR26)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md
- Depends on: Story 6.1 (Voice Recognition)

## Dev Agent Record

### Agent Model Used

opencode/big-pickle

### File List

- apps/h-core/src/features/home/per_user_memory/__init__.py (new)
- apps/h-core/src/features/home/per_user_memory/service.py (new)
- apps/h-core/src/infrastructure/surrealdb.py (modified)
- apps/h-core/src/domain/agent.py (modified)
- apps/h-core/src/domain/memory.py (modified)
