# Story 2-2: Retrieve Relevant Memories

**Status:** done

## Story

As an Agent,
I want to retrieve relevant memories,
So that I can recall past interactions that matter.

## Acceptance Criteria

1. [AC1] Given a query, when searching memories, then relevant memories are returned
2. [AC2] Given memories are retrieved, when ordered by relevance, then most relevant appear first
3. [AC3] Given no relevant memories, when searched, then empty result is returned

## Tasks / Subtasks

- [x] Task 1: Implement memory retrieval
- [x] Task 2: Add relevance scoring
- [x] Task 3: Implement ranking

## Dev Notes

- Memory retrieval via recall_memory function
- Relevance scoring based on recency and importance
- Implemented in apps/h-core/src/domain/memory.py

## Status: done
