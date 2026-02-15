# Story 11-4: Enable/Disable Skills

**Status:** backlog

## Story

As an Admin,
I want to enable or disable skills,
So that I can control which capabilities are available.

## Acceptance Criteria

1. [AC1] Given a skill is disabled, when agents try to use it, then it's not available
2. [AC2] Given a skill is enabled, when disabled before, then it's available again
3. [AC3] Given skill state changes, when applied, then it's persisted across restarts

## Tasks / Subtasks

- [ ] Task 1: Implement skill enable/disable
- [ ] Task 2: Add state persistence
- [ ] Task 3: Add admin UI

## Dev Notes

- To be implemented in Sprint 23
- Skill state stored in database
- Admin API: PUT /api/skills/{skill_id}/enable

## File List

- apps/h-bridge/src/main.py (add endpoints)
- apps/h-core/src/skills/repository.py (add state management)

## Status: backlog
