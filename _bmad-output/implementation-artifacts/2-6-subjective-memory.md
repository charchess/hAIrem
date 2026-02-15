# Story 2-6: Subjective Memory

**Status:** done

## Story

As an Agent,
I want my own subjective memories,
So that my beliefs are distinct from other agents.

## Acceptance Criteria

1. [AC1] Given an agent stores a memory, when saved, then it's linked to that agent
2. [AC2] Given an agent recalls memories, when queried, then only their memories are returned
3. [AC3] Given universal memories exist, when any agent queries, then they're accessible

## Tasks / Subtasks

- [x] Task 1: Implement agent-specific memory storage
- [x] Task 2: Add subjective retrieval
- [x] Task 3: Add universal facts support

## Dev Notes

- Subjective memory via BELIEVES edges in SurrealDB
- Agent-specific retrieval via semantic_search(agent_id)
- Universal facts via agent:system

## Status: done
