# Story 11-2: Modular Skill Packages

**Status:** backlog

## Story

As a User,
I want to install skill packages,
So that I can add new capabilities to agents easily.

## Acceptance Criteria

1. [AC1] Given a skill package exists, when installed, then it's available to agents
2. [AC2] Given a package has dependencies, when installed, then they're resolved automatically
3. [AC3] Given a package is uninstalled, when removed, then all related files are cleaned

## Tasks / Subtasks

- [ ] Task 1: Implement package manager
- [ ] Task 2: Add dependency resolution
- [ ] Task 3: Add cleanup on removal

## Dev Notes

- To be implemented in Sprint 23
- Package format: Python wheels or Docker images
- Dependency resolution via pip or docker-compose

## File List

- apps/h-core/src/skills/package_manager.py (to be created)

## Status: backlog
