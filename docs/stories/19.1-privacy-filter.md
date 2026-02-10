# Story 19.1: Privacy Filter Integration

**Status:** Done
**Epic:** 19 - V3 Stabilization & Security

## Story
**As a** User,
**I want** my sensitive information (passwords, API keys) to be automatically redacted,
**so that** they are never stored in plain text in the system's long-term memory.

## Acceptance Criteria
1. **Middleware Integration:**
    - Update `main.py` (or the persistence layer) to pass all user messages through `PrivacyFilter.redact()` before calling `surreal_client.persist_message`.
2. **Log Scrubbing:**
    - Ensure that `SYSTEM_LOG` messages containing secrets are also filtered.
3. **Verification:**
    - Send a message containing a fake API key (ex: `AIza...`).
    - Verify in SurrealDB that the stored message contains `[REDACTED]`.

## Tasks
- [x] Import `PrivacyFilter` in `apps/h-core/src/main.py`.
- [x] Wrap persistence logic with redaction call.
- [x] Add unit test verifying end-to-end redaction in the DB.

---

# Story 19.2: Sleep Cycle Activation

**Status:** Done
**Epic:** 19 - V3 Stabilization & Security

## Story
**As a** System,
**I want** the memory consolidation to run automatically in the background,
**so that** I don't have to trigger it manually to learn new things.

## Acceptance Criteria
1. **Background Task:**
    - Instantiate and start the `MemoryConsolidator` loop in `main.py` during startup.
2. **Configurable Interval:**
    - Use `SLEEP_CYCLE_INTERVAL` (env var) to control frequency (default: 1 hour).
3. **Observability:**
    - Broadcast a `system.log` when a cycle starts and ends.

## Tasks
- [x] Initialize `MemoryConsolidator` in `startup_event` of `main.py`.
- [x] Create an async loop task that calls `consolidator.consolidate()`.
- [x] Verify logs show "Sleep Cycle complete".

---

# Story 19.3: UI Message Sanitization

**Status:** Done
**Epic:** 19 - V3 Stabilization & Security

## Story
**As a** User,
**I want** a clean chat history,
**so that** technical tags like `[pose:X]` don't clutter the dialogue once they've been processed.

## Acceptance Criteria
1. **Final Text Cleanup:**
    - Update `renderer.js` to ensure the final message added to history is the `cleanedText` (tags removed).
2. **Consistency:**
    - Ensure this applies to both static history load and live streaming chunks.

## Tasks
- [x] Refactor `addMessageToHistory` and `handleChunk` in `renderer.js`.

## Dev Agent Record
### Agent Model Used
Gemini 2.0 Flash

### Debug Log References
- `apps/h-core/tests/test_privacy_integration.py` passed.
- `apps/h-core/tests/test_sleep_cycle_integration.py` passed.
- Regression suite (17 tests) passed.

### Completion Notes List
- Integrated `PrivacyFilter` in `main.py` to redact secrets from `messages` and `system.log`.
- Activated `MemoryConsolidator` as a background task in `main.py`.
- Enhanced `renderer.js` to proactively hide technical tags `[pose:...]` during streaming and in history.
- Refactored `main.py` to support float values for `SLEEP_CYCLE_INTERVAL`.
- Updated `test_memory.py` to align with the new graph-based memory implementation.

### File List
- `apps/h-core/src/main.py`
- `apps/a2ui/js/renderer.js`
- `apps/h-core/tests/test_privacy_integration.py`
- `apps/h-core/tests/test_sleep_cycle_integration.py`
- `apps/h-core/tests/test_memory.py`

### Change Log
| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 2026-01-26 | 1.0 | Initial implementation of V3 Stabilization features | James (Dev) |

## QA Results

### Review Date: 2026-01-26
### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment
Implémentation exemplaire des corrections critiques. L'intégration du `PrivacyFilter` dans le flux de persistance comble une faille de sécurité majeure. L'activation du `MemoryConsolidator` en tâche de fond rend le système enfin autonome cognitivement. Côté UI, la gestion proactive des tags partiels pendant le streaming est une attention aux détails qui améliore grandement l'immersion.

### Compliance Check
- Coding Standards: [✓] Découplage respecté, utilisation de tâches asynchrones pour les boucles de fond.
- Project Structure: [✓] Alignement avec les modèles HLink.
- Testing Strategy: [✓] Tests d'intégration robustes couvrant les secrets et les cycles de sommeil.
- All ACs Met: [✓]

### Gate Status
Gate: PASS → docs/qa/gates/19.stabilization-v3.yml
Risk profile: Low (Stabilization successful)
NFR assessment: PASS (Security & Reliability enhanced)

### Recommended Status
**Status:** Done
