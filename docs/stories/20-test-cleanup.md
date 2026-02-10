# Story 20.1: Signature Alignment (BaseAgent & SurrealDB)

**Status:** Done
**Epic:** 20 - Test Infrastructure Cleanup

## Story
**As a** Developer,
**I want** all unit tests to use the correct class signatures,
**so that** I can run the test suite without getting TypeErrors.

## Acceptance Criteria
1. **BaseAgent Fix:**
    - Update all tests in `test_generic_agent.py` and `test_agent_config.py` to provide a mock `llm_client` to the `BaseAgent` constructor.
2. **SurrealDB Fix:**
    - Update `test_surrealdb.py` to provide `url`, `user`, and `password` to the `SurrealDbClient` constructor.
3. **Mocks:**
    - Ensure all mocks correctly reflect the new asynchronous nature of these clients.

## Tasks
- [x] Refactor `apps/h-core/tests/test_generic_agent.py`.
- [x] Refactor `apps/h-core/tests/test_surrealdb.py`.
- [x] Refactor `apps/h-core/tests/test_agent_config.py`.

---

# Story 20.2: Logging & Formatting Cleanup

**Status:** Done
**Epic:** 20 - Test Infrastructure Cleanup

## Story
**As a** Developer,
**I want** the logging tests to match the new H-Link message format,
**so that** I can verify our observability pipeline accurately.

## Acceptance Criteria
1. **Log Format:**
    - Update `test_logging.py` to expect the `[LEVEL]` prefix in the payload content.
2. **Mock String Handling:**
    - Fix `test_polish_v2.py` where a `MagicMock` is passed to the `PrivacyFilter` instead of a string (causing Regex errors).

## Tasks
- [x] Update `apps/h-core/tests/test_logging.py`.
- [x] Fix string handling in `apps/h-core/tests/test_polish_v2.py`.

---

# Story 20.3: Dead Test Removal & Standardization

**Status:** Done
**Epic:** 20 - Test Infrastructure Cleanup

## Story
**As a** System Architect,
**I want** to remove tests that are no longer relevant and standardize the test execution environment,
**so that** the test suite remains fast and maintainable.

## Acceptance Criteria
1. **Audit & Removal:**
    - Remove `test_expert_ha_logic.py` and `test_ha_client.py` if they refer to non-existent modules or if their logic is already covered by `master_regression_v3.py`.
2. **PYTHONPATH Support:**
    - Ensure a simple `pytest` at the root works by ensuring all internal imports in tests are absolute (`from src.infrastructure...`).

## Tasks
- [x] Audit and potentially delete obsolete HA tests.
    - *Note:* Fixed and kept them as they provide valuable unit-level validation.
- [x] Standardize imports across all files in `apps/h-core/tests/`.

## Dev Agent Record
### Agent Model Used
Gemini 2.0 Flash

### Debug Log References
- `pytest apps/h-core/tests/` passed (47/47).
- `scripts/master_regression_v3.py` passed (Routing & Agent Loading).

### Completion Notes List
- Refactored `BaseAgent` and `SurrealDbClient` initializations across all legacy tests.
- Fixed `IndentationError` and `TypeError` in `test_polish_v2.py`.
- Updated `test_logging.py` to match new log prefixing.
- Validated `Electra` (formerly expert-domotique) logic and tools.
- Ensured 100% Green status for the core test suite.

### File List
- `apps/h-core/tests/test_generic_agent.py`
- `apps/h-core/tests/test_surrealdb.py`
- `apps/h-core/tests/test_agent_config.py`
- `apps/h-core/tests/test_agent_context.py`
- `apps/h-core/tests/test_logging.py`
- `apps/h-core/tests/test_polish_v2.py`
- `apps/h-core/tests/test_ha_client.py`
- `apps/h-core/tests/test_expert_ha_logic.py`
- `apps/h-core/tests/test_memory.py`

### Change Log
| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 2026-01-26 | 1.0 | Full cleanup of legacy unit tests | James (Dev) |

## QA Results

### Review Date: 2026-01-26
### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment
Excellent travail de nettoyage. Le passage de 13 échecs à 47 succès (100% Green) rétablit la confiance dans notre outil de validation. Les corrections sur les types de données (LogRecord) et les signatures de constructeurs alignent parfaitement les tests sur l'architecture V3.

### Compliance Check
- Coding Standards: [✓] PYTHONPATH standardisé.
- Project Structure: [✓]
- Testing Strategy: [✓] Suite complète exécutée et validée.
- All ACs Met: [✓]

### Gate Status
Gate: PASS → docs/qa/gates/20.test-cleanup.yml
Risk profile: Low (Dette résorbée)
NFR assessment: PASS (Testability & Maintainability)

### Recommended Status
**Status:** Done
