# Story 7.3: Configure Agent Parameters

Status: done

## Story

As an Admin,
I want to configure agent parameters and persona settings,
so that I can customize agent behavior.

## Acceptance Criteria

1. [AC1] Given admin accesses configuration, when parameters are modified, then agent behavior changes
2. [AC2] Given configuration is saved, when changes persist, then they survive system restart
3. [AC3] Given invalid configuration is provided, when saving, then validation errors are shown

## Tasks / Subtasks

- [x] Task 1: Implement parameter schema (AC: #1)
  - [x] Subtask 1.1: Define configurable parameters (temperature, max_tokens, system_prompt, etc.)
  - [x] Subtask 1.2: Add to agent config model
- [x] Task 2: Implement persistence (AC: #2)
  - [x] Subtask 2.1: Save to SurrealDB
  - [x] Subtask 2.2: Load on agent initialization
- [x] Task 3: Implement validation (AC: #3)
  - [x] Subtask 3.1: Define validation rules per parameter
  - [x] Subtask 3.2: Return clear error messages

## Dev Notes

### References
- PRD: _bmad-output/planning-artifacts/prd.md (FR34)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md

## Dev Agent Record

### Agent Model Used

opencode/big-pickle

### Implementation Plan

Story 7.3 implementation includes:
- **AgentConfigSchema** and **AgentParameters** models with validation
- **AgentConfigService** with validate_parameters(), save_config(), get_config()
- **AgentConfigRepository** for SurrealDB persistence
- Integration with **PluginLoader** for per-agent LLM config
- Validation rules for temperature, max_tokens, top_p, top_k, presence_penalty, frequency_penalty, context_window, model, base_url

### Debug Log

- 2026-02-14: Fixed `AgentConfigRepository.get_or_default()` to return DEFAULT_PARAMETERS instead of empty AgentParameters
- 2026-02-14: Fixed test mocking in test_per_agent_llm_config_loading and test_agent_config_no_override - added missing mock parameters and patched BaseAgent.start

### Completion Notes

✅ Story implementation verified and bugs fixed
- All 33 agent config tests pass
- AC1: Parameters modify agent behavior (via PluginLoader llm_config)
- AC2: Config persists to SurrealDB (AgentConfigRepository)
- AC3: Validation returns clear errors (validate_parameters)

## Change Log

- 2026-02-14: Fixed repository get_or_default to return DEFAULT_PARAMETERS
- 2026-02-14: Fixed test mocking issues

## File List

- apps/h-core/src/features/admin/agent_config/__init__.py (new)
- apps/h-core/src/features/admin/agent_config/models.py (new)
- apps/h-core/src/features/admin/agent_config/service.py (new)
- apps/h-core/src/features/admin/agent_config/repository.py (new)
- apps/h-core/tests/test_agent_config.py (modified - fixed mock issues)
