# Story 6.7: Evolving Social Grid

Status: completed

## Story

As a System,
I want the social grid to evolve over time,
so that relationships change based on interactions.

## Acceptance Criteria

1. [AC1] Given interactions occur, when relationship thresholds are crossed, then relationships evolve
2. [AC2] Given social grid evolves, when significant changes happen, then appropriate agents/users are notified
3. [AC3] Given social grid is stored, when system restarts, then the grid persists

## Tasks / Subtasks

- [x] Task 1: Implement threshold-based evolution (AC: #1)
  - [x] Subtask 1.1: Define relationship thresholds (already in user_relationships and agent_relationships)
  - [x] Subtask 1.2: Check thresholds after each interaction (handled by existing services)
  - [x] Subtask 1.3: Update relationship state (handled by existing services)
- [x] Task 2: Implement change notifications (AC: #2)
  - [x] Subtask 2.1: Detect significant relationship changes
  - [x] Subtask 2.2: Notify affected agents
- [x] Task 3: Implement grid persistence (AC: #3)
  - [x] Subtask 3.1: Store social grid in SurrealDB
  - [x] Subtask 3.2: Load on system startup

## Dev Notes

### References
- PRD: _bmad-output/planning-artifacts/prd.md (FR31)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md

## Dev Agent Record

### Agent Model Used

opencode/big-pickle

### File List
- apps/h-core/src/features/home/social_grid/__init__.py
- apps/h-core/src/features/home/social_grid/models.py
- apps/h-core/src/features/home/social_grid/repository.py
- apps/h-core/src/features/home/social_grid/service.py
- apps/h-core/src/features/home/social_grid/service_utils.py
