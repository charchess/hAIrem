# Story 10-5: Night Mode

**Status:** done

## Story

As a System,
I want to enter night mode,
So that the system reduces activity during sleep hours.

## Acceptance Criteria

1. [AC1] Given night mode is triggered, when executed, then system activity is reduced
2. [AC2] Given night mode is active, when urgent events occur, then they're still processed
3. [AC3] Given morning arrives, when night mode ends, then normal activity resumes

## Tasks / Subtasks

- [x] Task 1: Implement night mode activation
- [x] Task 2: Add urgent event handling
- [x] Task 3: Add morning wake-up

## Dev Notes

- Night mode via sleep cycle worker
- Reduced activity during night hours
- Emergency events still processed

## File List

- apps/h-core/src/domain/memory.py (sleep_cycle_worker)

## Status: done
