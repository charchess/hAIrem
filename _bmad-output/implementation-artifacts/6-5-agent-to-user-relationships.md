# Story 6.5: Agent-to-User Relationships

Status: completed

## Story

As a Agent,
I want to have dynamic relationships with users,
so that my interactions reflect how I feel about them.

## Acceptance Criteria

1. [AC1] Given an agent interacts with a user, when relationship evolves, then the agent's attitude is updated
2. [AC2] Given relationship exists, when agent responds to user, then discourse tone reflects the relationship
3. [AC3] Given relationship is very positive or negative, when appropriate, then agent may express preference to interact more/less

## Tasks / Subtasks

- [x] Task 1: Implement user-relationship tracking (AC: #1)
  - [x] Subtask 1.1: Define agent-user relationship data model
  - [x] Subtask 1.2: Update relationship based on interactions
- [x] Task 2: Implement relationship-based discourse (AC: #2)
  - [x] Subtask 2.1: Map relationship to tone modifiers
  - [x] Subtask 2.2: Apply in agent response generation
- [x] Task 3: Implement preference expression (AC: #3)
  - [x] Subtask 3.1: Define extreme relationship thresholds
  - [x] Subtask 3.2: Allow subtle expression of preference

## Dev Notes

### References
- PRD: _bmad-output/planning-artifacts/prd.md (FR29)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md
- Depends on: Story 6.1, 6.2
- Based on: Story 6.4 (agent_relationships module)

## Dev Agent Record

### Agent Model Used

opencode/big-pickle

### File List
- apps/h-core/src/features/home/user_relationships/__init__.py
- apps/h-core/src/features/home/user_relationships/models.py
- apps/h-core/src/features/home/user_relationships/repository.py
- apps/h-core/src/features/home/user_relationships/service.py
- apps/h-core/tests/test_user_relationships.py
