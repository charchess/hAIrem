# Story 9.5: World Themes

Status: completed

## Story

As a System,
I want world state to include themes,
so that agents can respond to seasonal/contextual changes.

## Acceptance Criteria

1. [AC1] Given theme is set, when agents respond, then theme context is included
2. [AC2] Given theme is changed, when saved, then active agents receive update
3. [AC3] Given no theme is set, when agents respond, then neutral theme is used

## Tasks / Subtask

- [x] Task 1: Implement theme system (AC: #1)
  - [x] Subtask 1.1: Define theme data model (name, decorations, mood)
  - [x] Subtask 1.2: Include theme in agent context
- [x] Task 2: Implement dynamic theme updates (AC: #2)
  - [x] Subtask 2.1: Push theme updates to agents
  - [x] Subtask 2.2: Handle in-flight conversations
- [x] Task 3: Implement default theme (AC: #3)
  - [x] Subtask 3.1: Define neutral theme
  - [x] Subtask 3.2: Fallback when no theme set

## Dev Notes

### References
- PRD: _bmad-output/planning-artifacts/prd.md (FR51)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md

## Dev Agent Record

### Agent Model Used

opencode/big-pickle

### File List

- apps/h-core/src/features/home/spatial/themes/models.py - Theme data models
- apps/h-core/src/features/home/spatial/themes/service.py - WorldThemeService
- apps/h-core/src/features/home/spatial/themes/__init__.py - Module exports
- apps/h-core/src/features/home/spatial/registry.py - SpatialRegistry
- apps/h-core/src/domain/agent.py - Agent integration for theme context
- apps/h-core/src/features/home/spatial/__init__.py - Updated exports
- apps/h-core/tests/test_world_themes.py - Tests
