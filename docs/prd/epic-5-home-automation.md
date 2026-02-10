# Epic 5: Home Automation Bridge (Pluggable & Proactive)

**Goal:** Transform hAIrem into a living house OS by connecting Electra to Home Assistant via specialized logic and proactive event handling.

## Status
- [x] Story 5.1: Client Home Assistant (HA REST API Client)
- [x] Story 5.4: Custom Python Logic Loader (Pluggability Engine)
- [x] Story 5.5: Electra basic HA Tools (get_state, call_service)
- [ ] Story 5.6: Entity Discovery & Context Injection
- [ ] Story 5.7: Proactive HA Event Listeners
- [ ] Story 5.8: High-Level Automation Routines (Macros)

## User Stories

### Story 5.6: Entity Discovery & Context Injection
**As an** Agent (Electra),
**I want** to automatically know which devices are available in the house,
**So that** I don't have to ask the user for entity IDs.

**Acceptance Criteria:**
- [ ] Electra's logic fetches a list of entities from HA on startup.
- [ ] Logic filters entities based on a `ha_discovery` list in `expert.yaml`.
- [ ] Discovery results are injected into Electra's system prompt dynamically.

### Story 5.7: Proactive HA Event Listeners
**As a** User,
**I want** the agents to react automatically to house events (e.g. door opening),
**So that** the house feels alive without me initiating every conversation.

**Acceptance Criteria:**
- [ ] WebSocket listener implemented in `HaClient` or a dedicated service.
- [ ] HA events are routed to the Redis bus as `system.ha_event`.
- [ ] Agents can define "reaction rules" in their `logic.py`.

### Story 5.8: High-Level Automation Routines
**As a** User,
**I want** to trigger complex house states with a single command,
**So that** I can say "Electra, prepare the living room for a movie".

**Acceptance Criteria:**
- [ ] `logic.py` supports "Macro" tools that call multiple HA services in sequence.
- [ ] State validation: the agent verifies the final state before confirming.
