# Story 9.2: Location Tracking

Status: done

## Story

As a System,
I want to track which location each agent is present in,
so that I know where agents are.

## Acceptance Criteria

1. [AC1] Given location updates, when agent moves, then location is updated and persisted
2. [AC2] Given location history exists, when queried, then recent locations are returned
3. [AC3] Given location is ambiguous, when tracked, then confidence level is included

## Tasks / Subtasks

- [x] Task 1: Implement location tracking (AC: #1)
  - [x] Subtask 1.1: Create location history table
  - [x] Subtask 1.2: Update on movement
- [x] Task 2: Implement location query (AC: #2)
  - [x] Subtask 2.1: Query current location
  - [x] Subtask 2.2: Return location history
- [x] Task 3: Implement confidence tracking (AC: #3)
  - [x] Subtask 3.1: Define confidence model
  - [x] Subtask 3.2: Include in location data

## Dev Notes

### References
- PRD: _bmad-output/planning-artifacts/prd.md (FR48)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md
- Depends on: Story 9.1

## Dev Agent Record

### Agent Model Used

opencode/big-pickle

### File List
- apps/h-core/src/features/home/spatial/location/models.py
- apps/h-core/src/features/home/spatial/location/repository.py
- apps/h-core/src/features/home/spatial/location/service.py
- apps/h-core/src/features/home/spatial/location/__init__.py
- apps/h-core/src/features/home/spatial/__init__.py (updated)
