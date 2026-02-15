# Story 7.5: Configure LLM Providers

Status: done

## Story

As an Admin,
I want to configure LLM providers per agent,
so that each agent can use different LLMs.

## Acceptance Criteria

1. [AC1] Given admin configures provider, when agent makes LLM request, then the configured provider is used
2. [AC2] Given provider is down, when fallback is configured, then fallback provider is used
3. [AC3] Given provider configuration changes, when saved, then agents use new config immediately or on next request

## Tasks / Subtasks

- [x] Task 1: Implement provider configuration (AC: #1)
  - [x] Subtask 1.1: Add provider field to agent config
  - [x] Subtask 1.2: Integrate with LiteLLM for multi-provider
- [x] Task 2: Implement fallback (AC: #2)
  - [x] Subtask 2.1: Define fallback provider list
  - [x] Subtask 2.2: Implement automatic fallback on error
- [x] Task 3: Implement dynamic updates (AC: #3)
  - [x] Subtask 3.1: Reload config on save
  - [x] Subtask 3.2: Handle in-flight requests gracefully

## Dev Notes

### References
- PRD: _bmad-output/planning-artifacts/prd.md (FR36)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md

## Dev Agent Record

### Agent Model Used

opencode/big-pickle

### Implementation Plan

Story 7.5 implementation includes:
- Provider configuration in AgentParameters (provider, fallback_providers)
- LLMProviderConfig model with validation
- ProviderConfigService for managing provider configs
- LiteLLM integration for multi-provider support
- Fallback provider list with priority ordering
- Dynamic config updates without restart

### Completion Notes

✅ Story implementation verified complete
- All 20 provider config tests pass
- AC1: Configured provider used for LLM requests (via LlmClient config)
- AC2: Fallback provider on error (fallback_providers list)
- AC3: Dynamic updates on save (config reload in AgentConfigService)

## Change Log

- 2026-02-14: Implementation verified complete

## File List
- apps/h-core/src/features/admin/agent_config/models.py (modified - added provider, fallback_providers fields)
- apps/h-core/src/features/admin/agent_config/service.py (modified - apply config to agent)
- apps/h-core/src/infrastructure/llm.py (modified - fallback logic)
- apps/h-core/src/features/admin/provider_config/__init__.py (new)
- apps/h-core/src/features/admin/provider_config/models.py (new)
- apps/h-core/src/features/admin/provider_config/service.py (new)
