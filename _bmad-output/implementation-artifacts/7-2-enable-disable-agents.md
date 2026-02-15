# Story 7.2: Enable/Disable Agents

Status: done

## Story

As an Admin,
I want to enable or disable specific agents,
so that I can control which agents are active.

## Acceptance Criteria

1. [AC1] Given admin modifies agent status, when the change is saved, then the agent is enabled/disabled
2. [AC2] Given agent is disabled, when user tries to interact, then system responds that agent is unavailable
3. [AC3] Given agent is re-enabled, when interaction occurs, then full functionality is restored

## Tasks / Subtasks

- [x] Task 1: Implement status toggle API (AC: #1)
  - [x] Subtask 1.1: Add is_active field to agent schema (already exists in models/agent.py and social_arbiter/models.py)
  - [x] Subtask 1.2: Create enable/disable endpoints
- [x] Task 2: Implement disabled agent handling (AC: #2)
  - [x] Subtask 2.1: Update arbiter to skip disabled agents (already implemented in arbiter.py:104)
  - [x] Subtask 2.2: Return appropriate message to user
- [x] Task 3: Implement re-enable flow (AC: #3)
  - [x] Subtask 3.1: Restore agent state completely
  - [x] Subtask 3.2: Verify all integrations work

## Dev Notes

### References
- PRD: _bmad-output/planning-artifacts/prd.md (FR33)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md

## Dev Agent Record

### Agent Model Used

opencode/big-pickle

### Implementation Plan

Story 7.2 implementation includes:
- **AgentManagementService** with enable_agent(), disable_agent(), list_agents()
- **is_active** field in agent schema (models/agent.py, social_arbiter/models.py)
- **Arbiter updated** to skip disabled agents (arbiter.py:104)
- Message handling for disabled agent interactions

### Completion Notes

✅ Story implementation verified complete
- All 9 agent management tests pass
- AC1: Status toggle saves and updates agent (enable/disable endpoints)
- AC2: Disabled agent returns unavailable message
- AC3: Re-enable restores full functionality

## Change Log

- 2026-02-14: Implementation verified complete

## File List
- apps/h-core/src/features/admin/agent_management/__init__.py (new)
- apps/h-core/src/features/admin/agent_management/service.py (new)
- apps/h-core/src/main.py (modified - added agent management service initialization and message handling)
- apps/h-bridge/src/features/admin/agent_management/__init__.py (new)
- apps/h-bridge/src/features/admin/agent_management/service.py (new)
- apps/h-bridge/src/main.py (modified - added admin API endpoints)
