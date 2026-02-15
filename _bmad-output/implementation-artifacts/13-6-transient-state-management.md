# Story 13.6: Transient State Management (Self-Awareness)

**Status:** done  
**Epic:** 13 - Deep Cognitive Architecture

## Story

**As a** System,
**I want** to manage the agents' transient states (outfit, location) as objective facts in the graph,
**so that** any agent (or the user) can query the current state while ensuring that old states are automatically invalidated.

## Acceptance Criteria

1. **State Uniqueness (Constraint):**
   - For relations of type `WEARS` and `IS_IN`, an agent can have only ONE active outgoing edge at a time.

2. **Automatic Invalidation:**
   - When a new `WEARS` relation is created (e.g., via `/outfit`), any existing `WEARS` edge from that agent must be deleted (or archived).
   - Same logic applies to `IS_IN` for locations.

3. **Graph Storage:**
   - Store the outfit description and location name as nodes, linked via the agent's ID.
   - Example: `RELATE agent:lisa->WEARS->outfit:red_dress SET timestamp=time::now()`.

4. **Introspection Tool:**
   - The `recall_memory` tool (or a new internal tool) must be able to prioritize these "Live Facts" when an agent wonders about their current state.

5. **Real-time Notification:**
   - When the state changes, a system message is sent to the specific agent: `[SYSTEM] Your state updated: You are now wearing [Description] in [Location].`

## Implementation Notes

- WEARS relation handled in visual vault service
- IS_IN relation handled in spatial location service
- State uniqueness via delete-before-relate pattern in SurrealDB

## File List

- apps/h-core/src/services/visual/vault.py (WEARS relations)
- apps/h-core/src/features/home/spatial/location/service.py (IS_IN relations)

## Status: done
