# Story 11-2: Modular Skill Packages

**Status:** done

## Story

As a User,
I want to install skill packages,
So that I can add new capabilities to agents easily.

## Acceptance Criteria

1. [AC1] Given a skill package exists, when installed, then it's available to agents
2. [AC2] Given a package has dependencies, when installed, then they're resolved automatically
3. [AC3] Given a package is uninstalled, when removed, then all related files are cleaned

## Tasks / Subtasks

- [x] Task 1: Implement package manager (apps/h-core/src/skills/package_manager.py)
- [x] Task 2: Add dependency resolution (pip install)
- [x] Task 3: Add cleanup on removal

## Dev Notes

- Package manager implemented for Python wheels
- Install via pip --target
- Manifest.yaml for tracking
- Ready for integration with PluginLoader

## File List

- apps/h-core/src/skills/package_manager.py

## Status: done
