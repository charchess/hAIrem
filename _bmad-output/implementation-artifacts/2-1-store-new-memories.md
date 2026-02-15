# Story 2-1: Store New Memories

**Status:** done

## Story

As an Agent,
I want to store new memories,
So that I can remember interactions for future reference.

## Acceptance Criteria

1. [AC1] Given a new interaction, when it occurs, then it's stored in memory
2. [AC2] Given a memory is stored, when queried, then it can be retrieved
3. [AC3] Given the system restarts, when memories are stored, then they persist

## Tasks / Subtasks

- [x] Task 1: Implement memory storage interface
- [x] Task 2: Connect to database
- [x] Task 3: Add persistence layer

## Dev Notes

- Memory storage implemented in apps/h-core/src/domain/memory.py
- Redis-based storage for fast access
- Persistence via database

## Status: done
