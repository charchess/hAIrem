# Story 3.6: Suppress Low-Priority Responses

Status: in-progress

## Story

As a Arbiter,
I want to suppress or delay low-priority responses,
so that only relevant responses are sent.

## Acceptance Criteria

1. [AC1] Given an agent has low relevance score, when the arbiter evaluates, then the response is suppressed if below minimum threshold
2. [AC2] Given a response is suppressed, when conditions change, then the response can be re-evaluated later (delay mechanism)
3. [AC3] Given suppression logging, when response is suppressed, then the reason is logged for debugging

## Tasks / Subtasks

- [x] Task 1: Implement suppression threshold (AC: #1)
  - [x] Subtask 1.1: Define minimum score threshold configuration
  - [x] Subtask 1.2: Implement score-based filtering before response
- [x] Task 2: Implement delayed re-evaluation (AC: #2)
  - [x] Subtask 2.1: Create delayed queue for suppressed responses
  - [x] Subtask 2.2: Implement re-evaluation trigger (time-based or context-based)
- [x] Task 3: Implement suppression logging (AC: #3)
  - [x] Subtask 3.1: Log suppressed responses with reason
  - [x] Subtask 3.2: Expose suppression stats via API

## Dev Notes

### References
- Architecture: _bmad-output/planning-artifacts/architecture.md
- PRD: _bmad-output/planning-artifacts/prd.md (FR23)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### File List

- `apps/h-core/src/features/home/social_arbiter/suppression.py` - NEW: Suppression config, suppressor, logging
- `apps/h-core/src/features/home/social_arbiter/arbiter.py` - UPDATED: Integration of suppression
- `apps/h-core/src/features/home/social_arbiter/__init__.py` - UPDATED: Export new components
- `apps/h-core/tests/test_social_arbiter.py` - UPDATED: Added suppression tests
