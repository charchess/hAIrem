# Story 11-1: Skills Separation

**Status:** done

## Story

As a Developer,
I want skills to be separated,
So that each skill is independent and can be managed separately.

## Acceptance Criteria

1. [AC1] Given skills exist, when loaded, then they're isolated from each other
2. [AC2] Given a skill has an error, when loaded, then other skills continue working
3. [AC3] Given skills are separated, when updating one, then others aren't affected

## Tasks / Subtasks

- [x] Task 1: Implement skill isolation (EXISTS - PluginLoader)
- [x] Task 2: Add error boundaries (EXISTS - PluginLoader)
- [x] Task 3: Add independent loading (EXISTS - PluginLoader)

## Dev Notes

- Already implemented via PluginLoader in apps/h-core/src/infrastructure/plugin_loader.py
- AgentRegistry manages isolated agent instances
- Each agent loads independently with error handling

## File List

- apps/h-core/src/infrastructure/plugin_loader.py (EXISTS)
- apps/h-bridge/src/main.py (skills API endpoints)

## Status: done
