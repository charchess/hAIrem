# Story 11-1: Skills Separation

**Status:** backlog

## Story

As a Developer,
I want skills to be separated,
So that each skill is independent and can be managed separately.

## Acceptance Criteria

1. [AC1] Given skills exist, when loaded, then they're isolated from each other
2. [AC2] Given a skill has an error, when loaded, then other skills continue working
3. [AC3] Given skills are separated, when updating one, then others aren't affected

## Tasks / Subtasks

- [ ] Task 1: Implement skill isolation
- [ ] Task 2: Add error boundaries
- [ ] Task 3: Add independent loading

## Dev Notes

- To be implemented in Sprint 23
- Skill isolation via separate processes/containers
- Error boundaries prevent cascade failures

## File List

- apps/h-core/src/skills/ (to be restructured)

## Status: backlog
