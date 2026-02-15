# Story 13.4: Conflict Synthesis (Truth Resolution)

**Status:** done  
**Epic:** 13 - Deep Cognitive Architecture

## Story

**As a** System,
**I want** to detect when a new observation contradicts an old belief,
**so that** I can evolve my understanding rather than holding two opposing views.

## Acceptance Criteria

1. **Conflict Detection:**
   - During memory consolidation, before inserting a new fact, the system must check for semantic similarity (> 0.85) with existing facts about the same subject.

2. **Conflict Resolution Loop:**
   - If a potential conflict is detected, trigger an LLM "Resolution Prompt":
     - "Fact A: User likes tea (Strength 0.9)"
     - "Fact B: User says they hate tea now."
     - "Resolution: User changed their preference. Synthesize: User no longer likes tea."

3. **Graph Update:**
   - If resolution results in a "Override": weaken/delete old edge and create new synthesis.
   - If resolution results in a "Merge": update old edge metadata.

## Tasks / Subtasks

- [x] Implement `ConflictResolver` service in `apps/h-core/src/domain/memory.py` (AC: #2)
  - [x] Design the "Synthesis Prompt".
- [x] Integrate conflict check in `MemoryConsolidator.consolidate()` (AC: #1)
  - [x] Perform vector search for each new fact.
- [x] Implement `merge_or_override_fact()` in `SurrealDbClient` (AC: #3).

## Implementation Notes

- Implemented in `apps/h-core/src/domain/memory.py` - ConflictResolver class
- Uses LLM to synthesize conflicting facts
- Integrated into MemoryConsolidator.consolidate() via semantic_search()

## File List

- apps/h-core/src/domain/memory.py (ConflictResolver class)
- apps/h-core/src/infrastructure/surrealdb.py (merge_or_override_fact method)

## Status: done
