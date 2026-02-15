# Story 2-4: Memory Decay

**Status:** done

## Story

As an Agent,
I want memories to fade over time,
So that irrelevant memories don't clutter my context.

## Acceptance Criteria

1. [AC1] Given memories exist, when time passes, then their strength decreases
2. [AC2] Given a memory's strength is low, when threshold is reached, then it's removed
3. [AC3] Given permanent memories exist, when decay runs, then they're preserved

## Tasks / Subtasks

- [x] Task 1: Implement decay algorithm
- [x] Task 2: Add threshold cleanup
- [x] Task 3: Add permanent flag support

## Dev Notes

- Decay implemented in SurrealDB with exponential formula
- Threshold: strength < 0.1 triggers deletion
- Permanent facts preserved via permanent flag

## Status: done
