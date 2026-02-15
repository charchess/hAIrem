# Story 6.4: Agent-to-Agent Relationships

Status: done

## Story

As a Agent,
I want to have dynamic relationships with other agents,
so that my interactions reflect my feelings toward them.

## Acceptance Criteria

1. [AC1] Given agents interact, when interactions occur, then relationship score is updated based on interaction type
2. [AC2] Given relationship score exists, when agents communicate, then the tone reflects the relationship (positive/negative/neutral)
3. [AC3] Given relationships evolve, when thresholds are crossed, then relationship status changes (stranger -> acquaintance -> friend -> rival, etc.)

## Tasks / Subtasks

- [x] Task 1: Implement relationship tracking (AC: #1)
  - [x] Subtask 1.1: Define relationship data model (agent-agent pairs)
  - [x] Subtask 1.2: Implement score update based on interactions
- [x] Task 2: Implement relationship-based tone (AC: #2)
  - [x] Subtask 2.1: Map relationship score to tone modifiers
  - [x] Subtask 2.2: Apply tone in inter-agent communication
- [x] Task 3: Implement relationship evolution (AC: #3)
  - [x] Subtask 3.1: Define relationship thresholds and states
  - [x] Subtask 3.2: Update relationship state when thresholds crossed

## Dev Notes

### References
- PRD: _bmad-output/planning-artifacts/prd.md (FR28)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md

## Dev Agent Record

### Agent Model Used

opencode/big-pickle

### Implementation Plan

Story 6.4 implementation includes:
- **AgentRelationship** model with score, status, interaction_count
- **AgentRelationshipService** for score updates and status calculation
- **RelationshipRepository** for Redis-backed persistence
- **RelationshipStatus** enum: ENEMY (-100) → RIVAL → STRANGER → ACQUAINTANCE → FRIEND → ALLY (+100)
- **InteractionType** enum with score modifiers (HELPFUL +5, HURTFUL -10, etc.)
- **ToneModifier** system mapping relationship to ToneType (HOSTILE, COLD, NEUTRAL, WARM, FRIENDLY)

### Completion Notes

✅ Story implementation verified complete
- All 15 agent relationships tests pass
- AC1: Score updates based on interaction types (INTERACTION_SCORES)
- AC2: Tone reflects relationship (get_tone_modifier)
- AC3: Status changes at defined thresholds (RELATIONSHIP_THRESHOLDS)

## Change Log

- 2026-02-14: Implementation verified and marked complete

## File List

- apps/h-core/src/features/home/agent_relationships/__init__.py (new)
- apps/h-core/src/features/home/agent_relationships/models.py (new)
- apps/h-core/src/features/home/agent_relationships/service.py (new)
- apps/h-core/src/features/home/agent_relationships/repository.py (new)
