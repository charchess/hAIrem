# Story 11-3: Hotplug

**Status:** done

## Story

As a System,
I want to hotplug skills,
So that skills can be added without restarting the system.

## Acceptance Criteria

1. [AC1] Given a skill is hotplugged, when added, then it's available immediately
2. [AC2] Given hotplugging fails, when attempted, then system continues running
3. [AC3] Given a skill is removed via hotplug, when removed, then it's cleanly unloaded

## Tasks / Subtasks

- [x] Task 1: Implement hotplug detection (watchdog Observer)
- [x] Task 2: Add safe loading/unloading (AgentFileHandler)
- [x] Task 3: Add rollback on failure (error handling in _load_agent)

## Dev Notes

- Implemented via PluginLoader with watchdog observer
- on_modified/on_created triggers _load_agent
- Error handling prevents crashes

## File List

- apps/h-core/src/infrastructure/plugin_loader.py (EXISTS - Observer + AgentFileHandler)

## Status: done
