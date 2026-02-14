# Story 9.3: Mobile Location

Status: completed

## Story

As a System,
I want mobile clients to report their location,
so that agents can be mobile.

## Acceptance Criteria

1. [AC1] Given mobile client sends location, when location is received, then agent's location is updated
2. [AC2] Given location update frequency is high, when processed, then throttling is applied
3. [AC3] Given mobile client disconnects, when last location exists, then last known location is preserved

## Tasks / Subtasks

- [x] Task 1: Implement mobile location API (AC: #1)
  - [x] Subtask 1.1: Create location update endpoint
  - [x] Subtask 1.2: Validate incoming location data
- [x] Task 2: Implement throttling (AC: #2)
  - [x] Subtask 2.1: Define throttle rules
  - [x] Subtask 2.2: Apply per client
- [x] Task 3: Implement disconnect handling (AC: #3)
  - [x] Subtask 3.1: Detect client disconnect
  - [x] Subtask 3.2: Preserve last known location

## Dev Notes

### References
- PRD: _bmad-output/planning-artifacts/prd.md (FR49)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### File List
- apps/h-core/src/features/home/spatial/mobile/__init__.py
- apps/h-core/src/features/home/spatial/mobile/models.py
- apps/h-core/src/features/home/spatial/mobile/service.py
- apps/h-core/src/main.py (modified)
