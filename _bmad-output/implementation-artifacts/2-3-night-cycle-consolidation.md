# Story 2-3: Night Cycle Consolidation

**Status:** done

## Story

As a System,
I want to consolidate memories during night cycle,
So that memories are organized and processed periodically.

## Acceptance Criteria

1. [AC1] Given the night cycle runs, when executed, then memories are consolidated
2. [AC2] Given consolidation runs, when complete, then similar memories are merged
3. [AC3] Given consolidation completes, when finished, then results are logged

## Tasks / Subtasks

- [x] Task 1: Implement night cycle scheduler
- [x] Task 2: Add memory consolidation logic
- [x] Task 3: Add logging

## Dev Notes

- Night cycle implemented in apps/h-core/src/domain/memory.py
- Consolidation via MemoryConsolidator class
- Scheduled via sleep cycle worker

## Status: done
