# Story 7.4: Add New Agents

Status: done

## Story

As an Admin,
I want to add new agents to the system,
so that new personas can join.

## Acceptance Criteria

1. [AC1] Given admin adds new agent, when agent configuration is saved, then the agent is created
2. [AC2] Given new agent is created, when system runs, then agent is loaded and ready to interact
3. [AC3] Given agent folder structure is provided, when hotplug detects it, then agent loads without restart

## Tasks / Subtasks

- [x] Task 1: Implement agent creation API (AC: #1)
  - [x] Subtask 1.1: Define agent creation payload
  - [x] Subtask 1.2: Create agent in SurrealDB
- [x] Task 2: Implement agent loading (AC: #2)
  - [x] Subtask 2.1: Query agents on startup
  - [x] Subtask 2.2: Initialize agent with config
- [x] Task 3: Implement hotplug (AC: #3)
  - [x] Subtask 3.1: Watch for new agent folders
  - [x] Subtask 3.2: Load without restart

## Dev Notes

### References
- PRD: _bmad-output/planning-artifacts/prd.md (FR35)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md

## Dev Agent Record

### Agent Model Used

opencode/big-pickle

### Implementation Plan

Story 7.4 implementation includes:
- **AgentCreationPayload** model with validation
- **AgentCreationService** for create, list, get, delete operations
- **AgentCreationRepository** for SurrealDB persistence
- **PluginLoader** hotplug integration with folder watching
- Startup loading of enabled agents from DB
- Agent folder creation from manifest

### Completion Notes

✅ Story implementation verified complete
- All 16 agent creation tests pass
- AC1: Agent config saved creates agent (create_agent)
- AC2: Agent loads on startup (startup_load_enabled_agents)
- AC3: Hotplug loads without restart (PluginLoader + watcher)

## Change Log

- 2026-02-14: Implementation verified complete

## File List

- apps/h-core/src/features/admin/agent_creation/__init__.py
- apps/h-core/src/features/admin/agent_creation/models.py
- apps/h-core/src/features/admin/agent_creation/repository.py
- apps/h-core/src/features/admin/agent_creation/service.py
- apps/h-core/src/infrastructure/plugin_loader.py (modified)
- apps/h-core/src/main.py (modified)
