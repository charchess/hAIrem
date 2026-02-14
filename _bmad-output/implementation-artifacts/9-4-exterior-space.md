# Story 9.4: Exterior Space

Status: done

## Story

As a System,
I want remote access to have "exterior" space concept,
so that agents know when user is outside.

## Acceptance Criteria

1. [AC1] Given user accesses via phone, when location is exterior, then "exterior" space is set
2. [AC2] Given user is in exterior, when agents respond, then context includes exterior theme
3. [AC3] Given user returns inside, when re-entering, then location updates to appropriate room

## Tasks / Subtasks

- [x] Task 1: Implement exterior detection (AC: #1)
  - [x] Subtask 1.1: Define exterior markers (GPS, network type, etc.)
  - [x] Subtask 1.2: Set exterior space when detected
- [x] Task 2: Implement exterior context (AC: #2)
  - [x] Subtask 2.1: Add exterior theme to agent context
  - [x] Subtask 2.2: Agents respond appropriately
- [x] Task 3: Implement re-entry handling (AC: #3)
  - [x] Subtask 3.1: Detect return inside
  - [x] Subtask 3.2: Update location to room

## Dev Notes

### References
- PRD: _bmad-output/planning-artifacts/prd.md (FR50)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### File List
- apps/h-core/src/features/home/spatial/exterior/models.py (new)
- apps/h-core/src/features/home/spatial/exterior/service.py (new)
- apps/h-core/src/features/home/spatial/exterior/__init__.py (new)
- apps/h-core/src/features/home/spatial/mobile/models.py (modified - added exterior fields)
- apps/h-core/src/features/home/spatial/mobile/service.py (modified - integrated exterior service)
- apps/h-core/src/features/home/spatial/__init__.py (modified - exports exterior service)
- apps/h-core/src/main.py (modified - initialized exterior service)
