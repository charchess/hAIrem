# Story 1-3: Plugin Loader

**Status:** done

## Story

As a Developer,
I want a plugin loader system,
So that agents can be dynamically loaded and reloaded.

## Acceptance Criteria

1. [AC1] Given a plugin directory, when the system starts, then all valid plugins are loaded
2. [AC2] Given a new plugin is added, when detected, then it's loaded without restart
3. [AC3] Given a plugin has an error, when loading, then it's logged and skipped gracefully

## Tasks / Subtasks

- [x] Task 1: Implement plugin discovery
- [x] Task 2: Create plugin interface/contract
- [x] Task 3: Implement hot-reload capability
- [x] Task 4: Add error handling

## Dev Notes

- Plugin loader in apps/h-core/src/plugins/
- Dynamic agent loading implemented
- Hot-reload supported

## Status: done
