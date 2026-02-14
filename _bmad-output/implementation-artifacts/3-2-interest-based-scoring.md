# Story 3.2: Interest-Based Scoring

Status: in-progress

## Story

As a Arbiter,
I want to score agents based on their interests and relevance,
so that the best agent is chosen.

## Acceptance Criteria

1. [AC1] Given a user message, when scoring agents, then each agent gets a score based on topic relevance
2. [AC2] Given each agent has defined interests (skills, domains), when message is analyzed, then matching interests boost the score
3. [AC3] Given the agent with highest score is prioritized, when scores are computed, then agents are ranked by score descending

## Tasks / Subtasks

- [x] Task 1: Define agent interest profile structure (AC: #1)
  - [x] Subtask 1.1: Create data model for agent interests (topics, skills, domains)
  - [x] Subtask 1.2: Load agent profiles from SurrealDB
- [x] Task 2: Implement topic relevance scoring (AC: #2)
  - [x] Subtask 2.1: Implement keyword/topic extraction from user message
  - [x] Subtask 2.2: Calculate match score between message topics and agent interests
  - [x] Subtask 2.3: Apply interest weight multiplier
- [x] Task 3: Return ranked agent list (AC: #3)
  - [x] Subtask 3.1: Sort agents by score descending
  - [x] Subtask 3.2: Return top candidate

## Dev Notes

### References
- Architecture: _bmad-output/planning-artifacts/architecture.md
- PRD: _bmad-output/planning-artifacts/prd.md (FR19)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md
- Depends on: Story 3.1

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### File List

- `apps/h-core/src/features/home/social_arbiter/topic_extraction.py` (NEW)
- `apps/h-core/src/features/home/social_arbiter/repository.py` (NEW)
- `apps/h-core/src/features/home/social_arbiter/models.py` (UPDATED)
- `apps/h-core/src/features/home/social_arbiter/scoring.py` (UPDATED)
- `apps/h-core/src/features/home/social_arbiter/service.py` (UPDATED)
