# Story 6.6: Tone Varies, Quality Constant

Status: completed

## Story

As a System,
I want relationship to affect tone but NOT service quality,
so that all users receive equal service.

## Acceptance Criteria

1. [AC1] Given an agent has poor relationship with user, when the user requests service, then tone may vary but quality remains constant
2. [AC2] Given critical requests (safety, information), when processed, then quality takes absolute priority over tone
3. [AC3] Given relationship affects tone, when implemented, then the tone variation is subtle and not offensive

## Tasks / Subtasks

- [x] Task 1: Implement quality gates (AC: #1, #2)
  - [x] Subtask 1.1: Define critical request types
  - [x] Subtask 1.2: Enforce quality priority regardless of tone
- [x] Task 2: Implement bounded tone variation (AC: #3)
  - [x] Subtask 2.1: Define acceptable tone range
  - [x] Subtask 2.2: Clamp tone variations to acceptable bounds
- [x] Task 3: Implement validation (AC: #2)
  - [x] Subtask 3.1: Test quality on all request types
  - [x] Subtask 3.2: Ensure no degradation on critical requests

## Dev Notes

### References
- PRD: _bmad-output/planning-artifacts/prd.md (FR30)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md

## Dev Agent Record

### Agent Model Used

opencode/big-pickle

### File List
- apps/h-core/src/features/home/quality_gates/__init__.py
- apps/h-core/src/features/home/quality_gates/models.py
- apps/h-core/src/features/home/quality_gates/service.py
- apps/h-core/tests/test_quality_gates.py
