# Story 18.4: Flux de Discussion Inter-Agents

Status: ready-for-dev

## Story

As a User,
I want to watch my agents discuss among themselves organically without intervention,
so that the home feels like a living environment with autonomous social dynamics.

## Acceptance Criteria

1. [AC1] Given an initial user interaction or a system trigger, when an agent responds, then other agents can choose to react to that response.
2. [AC2] Given a multi-agent exchange, then the Social Arbiter manages the discussion budget (max 5 turns) to prevent infinite loops.
3. [AC3] Given an ongoing discussion, then the visual focus (Glow/Rim Light) correctly follows the active speaker in the conversation.
4. [AC4] Given the agents are discussing, then their memories of the conversation are correctly persisted for each participant.

## Tasks / Subtasks

- [x] Task 1: Refine Inter-Agent Routing (AC: #1, #2)
  - [x] Subtask 1.1: Ensure `HaremOrchestrator` correctly routes agent-to-agent messages through the arbiter (Moved logic before target==user check)
  - [ ] Subtask 1.2: Implement logic to decrease "interest score" over turns to naturally end conversations
- [x] Task 2: Conversation Persistence (AC: #4)
  - [x] Subtask 2.1: Verify that `on_message` in `BaseAgent` correctly appends messages from other agents to local history
  - [x] Subtask 2.2: Ensure `MemoryConsolidator` links these inter-agent facts in the graph (Verified: Sleep cycle extracts from all history)
- [ ] Task 3: Integration and E2E (AC: #3)
  - [ ] Subtask 3.1: Create an E2E test for a 3-turn multi-agent exchange (In progress: debugging timing issues)
  - [ ] Subtask 3.2: Verify visual feedback follows the speaking chain

## Dev Notes

- Component: `apps/h-core/src/main.py`, `apps/h-core/src/features/home/social_arbiter/`
- Constraint: Maintain the `target == "user"` check to avoid UI echoing, but allow agents to see the content.
- Pattern: "Social Working Memory" (SWM) - agents need to know what was just said even if not addressed to them.

### References

- [Source: apps/h-core/src/main.py#handle_message]
- [Source: docs/stories/18.4-inter-agent-discussion.md]

## Dev Agent Record

### Agent Model Used

gemini-3-flash-preview

### File List

- `apps/h-core/src/main.py`
- `apps/h-core/src/domain/agent.py`
- `tests/e2e/multi-agent-flow.spec.ts`
