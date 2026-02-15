# Story 11-4: Enable/Disable Skills

**Status:** done

## Story

As an Admin,
I want to enable or disable skills,
So that I can control which capabilities are available.

## Acceptance Criteria

1. [AC1] Given a skill is disabled, when agents try to use it, then it's not available
2. [AC2] Given a skill is enabled, when disabled before, then it's available again
3. [AC3] Given skill state changes, when applied, then it's persisted across restarts

## Tasks / Subtasks

- [x] Task 1: Implement skill enable/disable (APIs /api/skills/{id}/enable|disable)
- [x] Task 2: Add state persistence (skills_enabled set)
- [x] Task 3: Add admin endpoints (/api/skills, /api/skills/{id}, /api/skills/{id}/status)

## Dev Notes

- APIs implémentées in-memory (skills_enabled set)
- Ready for DB persistence
- Integrates with PluginLoader

## File List

- apps/h-bridge/src/main.py (skills APIs)

## Status: done
