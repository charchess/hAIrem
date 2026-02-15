# Story 6.2: Per-User Memory

Status: done

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

### Implementation Plan

Story 6.2 was already fully implemented with:
- UserMemoryContext class for managing per-user memory context
- UserMemoryService for storing/retrieving memories with user association
- MemoryConsolidator updated to associate user_id with consolidated facts

### Debug Log

- 2026-02-14: Found bug in test `test_consolidate_uses_primary_user_id` - failed because `user_ids_in_batch` was a set (unordered), causing non-deterministic first user_id selection. Fixed by using list with seen_user_ids set for deduplication.

### Completion Notes

✅ Story implementation verified and bug fix applied
- Fixed MemoryConsolidator to preserve user_id insertion order (set → list)
- All 22 memory-related tests pass
- AC1, AC2, AC3 satisfied by existing implementation

## Change Log

- 2026-02-14: Fixed bug in MemoryConsolidator where user_ids_in_batch used set instead of list, causing non-deterministic primary_user_id selection. Changed to list with deduplication to preserve insertion order.
- 2026-02-14: Code Review - Fixed File List (removed surrealdb.py, agent.py - not modified in this session)

## File List

- apps/h-core/src/features/home/per_user_memory/__init__.py (new)
- apps/h-core/src/features/home/per_user_memory/service.py (new)
- apps/h-core/src/domain/memory.py (modified - bug fix: user_ids_in_batch set→list)
