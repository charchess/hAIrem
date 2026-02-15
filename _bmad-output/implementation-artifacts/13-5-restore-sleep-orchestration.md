# Story 13.5: Restore Sleep & Cognition Orchestration (Regression Fix)

**Status:** done  
**Epic:** 13 - Deep Cognitive Architecture / 25 - Visual Imagination

## Story

**As a** System Architect,
**I want** to restore the background orchestration for cognitive consolidation and proactive dreaming,
**so that** the agents' long-term memory and visual imagination are active automatically.

## Acceptance Criteria

1. **Background Worker:**
   - Re-implement a `sleep_cycle_worker` in `apps/h-core/src/main.py`.
   - The worker must be a non-blocking `asyncio.Task` started in `main()`.
   - It must handle exceptions gracefully to avoid crashing the whole core.

2. **Cognitive Consolidation (from Story 10.1):**
   - **Trigger 1 (Time-based):** Call `consolidator.consolidate()` every hour (configurable via `SLEEP_CYCLE_INTERVAL`, default 3600s).
   - **Trigger 2 (Event-based):** Listen for `MessageType.SYSTEM_STATUS_UPDATE` with payload `{"status": "SLEEP_START"}` on the broadcast channel.

3. **Memory Decay (from Story 13.2):**
   - Call `consolidator.apply_decay()` once every 24 hours (e.g., at 03:00 AM system time).

4. **Proactive Dreaming (from Story 25.3):**
   - Call `dreamer.prepare_daily_assets()` immediately after the daily decay cycle (e.g., at 03:05 AM).

5. **Observability:**
   - Broadcast a `SYSTEM_LOG` (INFO) when a cycle starts and ends.
   - Log the number of facts consolidated.

## Implementation Notes

- Sleep cycle worker is triggered via `/internal/memory/sleep-cycle` endpoint
- Consolidation called via MemoryConsolidator.consolidate()
- Decay called via MemoryConsolidator.apply_decay()
- Internal endpoint available for manual triggering

## File List

- apps/h-core/src/domain/memory.py (consolidate, apply_decay methods)
- apps/h-core/src/main.py (/internal/memory/sleep-cycle endpoint)
- apps/h-bridge/src/main.py (/internal/memory/sleep-cycle endpoint)

## Status: done
