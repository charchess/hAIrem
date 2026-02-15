# Story 11-3: Hotplug

**Status:** backlog

## Story

As a System,
I want to hotplug skills,
So that skills can be added without restarting the system.

## Acceptance Criteria

1. [AC1] Given a skill is hotplugged, when added, then it's available immediately
2. [AC2] Given hotplugging fails, when attempted, then system continues running
3. [AC3] Given a skill is removed via hotplug, when removed, then it's cleanly unloaded

## Tasks / Subtasks

- [ ] Task 1: Implement hotplug detection
- [ ] Task 2: Add safe loading/unloading
- [ ] Task 3: Add rollback on failure

## Dev Notes

- To be implemented in Sprint 23
- File system watcher for skill directory
- Graceful loading/unloading with rollback

## File List

- apps/h-core/src/skills/hotplug.py (to be created)

## Status: backlog
