# Story 3.5: Turn-Taking Management

Status: in-progress

## Story

As a Arbiter,
I want to manage turn-taking in conversations,
so that agents don't speak over each other.

## Acceptance Criteria

1. [AC1] Given multiple agents want to respond simultaneously, when turn-taking is enforced, then agents respond in sequence
2. [AC2] Given an agent is currently responding, when another agent tries to respond, then the second agent is queued or suppressed
3. [AC3] Given conversation flow, when turns are managed, then each turn has a defined timeout to prevent deadlocks

## Tasks / Subtasks

- [x] Task 1: Implement response queue (AC: #1, #2)
  - [x] Subtask 1.1: Create Redis-based response queue
  - [x] Subtask 1.2: Implement FIFO ordering for pending responses
- [x] Task 2: Implement turn state machine (AC: #2)
  - [x] Subtask 2.1: Define states: IDLE, RESPONDING, QUEUED
  - [x] Subtask 2.2: Handle state transitions
- [x] Task 3: Implement timeout handling (AC: #3)
  - [x] Subtask 3.1: Define turn timeout configuration
  - [x] Subtask 3.2: Implement timeout handler to release turn

## Dev Notes

### References
- Architecture: _bmad-output/planning-artifacts/architecture.md
- PRD: _bmad-output/planning-artifacts/prd.md (FR22)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md
- Redis: Using Redis Streams for queue management (per architecture)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### File List
- `apps/h-core/src/features/home/social_arbiter/turn_taking.py` - TurnManager, TurnState, TurnTimeoutConfig, QueuedResponse
- `apps/h-core/src/features/home/social_arbiter/__init__.py` - Updated exports
