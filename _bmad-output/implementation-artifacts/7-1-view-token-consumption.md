# Story 7.1: View Token Consumption

Status: implemented

## Story

As an Admin,
I want to view token consumption per agent,
so that I can monitor costs.

## Acceptance Criteria

1. [AC1] Given admin accesses dashboard, when consumption is requested, then token usage per agent is displayed
2. [AC2] Given consumption data exists, when displayed, then costs are calculated based on provider pricing
3. [AC3] Given historical data exists, when requested, then trends are shown (daily, weekly, monthly)

## Tasks / Subtasks

- [x] Task 1: Implement token tracking (AC: #1)
  - [x] Subtask 1.1: Track tokens per request (input + output)
  - [x] Subtask 1.2: Store in SurrealDB with agent_id, timestamp
- [x] Task 2: Implement cost calculation (AC: #2)
  - [x] Subtask 2.1: Define provider pricing model
  - [x] Subtask 2.2: Calculate cost per agent
- [x] Task 3: Implement historical trends (AC: #3)
  - [x] Subtask 3.1: Aggregate by time period
  - [x] Subtask 3.2: Display trends in UI

## Dev Notes

### References
- PRD: _bmad-output/planning-artifacts/prd.md (FR32)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md

## Dev Agent Record

### Agent Model Used

opencode/big-pickle

### File List

- apps/h-core/src/features/admin/token_tracking/models.py
- apps/h-core/src/features/admin/token_tracking/pricing.py
- apps/h-core/src/features/admin/token_tracking/repository.py
- apps/h-core/src/features/admin/token_tracking/service.py
- apps/h-core/src/features/admin/token_tracking/__init__.py
- apps/h-core/src/infrastructure/llm.py (modified)
- apps/h-core/src/domain/agent.py (modified)
- apps/h-core/src/infrastructure/plugin_loader.py (modified)
- apps/h-core/src/main.py (modified)
- apps/h-bridge/src/main.py (modified)
