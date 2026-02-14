# Test Design for QA: hAIrem V4.1 Stabilization

**Purpose:** Test execution recipe for QA team. Defines what to test, how to test it, and what QA needs from other teams.

**Date:** 2026-02-10
**Author:** Murat (Test Architect)
**Status:** Draft
**Project:** hairem

---

## Executive Summary

**Scope:** Implementation of critical tests for infrastructure and the top 10 orphan stories.

**Risk Summary:**
- Total Risks: 5
- Critical Categories: DATA (Memory), TECH (Bus).

**Coverage Summary:**
- P0 tests: ~15 (Redis, SurrealDB, Matrix)
- P1 tests: ~20 (Sensory, Proactivity, Vaults)
- P2 tests: ~10 (Sync, Onboarding)
- **Total**: ~45 tests (~2-3 weeks with 1 QA)

---

## Test Coverage Plan

### P0 (Critical)

| Test ID | Requirement | Test Level | Risk Link | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **P0-001** | Redis Streams ACK | API | R-02 | XADD -> XREADGROUP -> XACK |
| **P0-002** | SurrealDB SCHEMAFULL | API | R-01 | Test data validation rejection |
| **P0-003** | Matrix Init | API | R-01 | Validate initial graph links |

### P1 (High)

| Test ID | Requirement | Test Level | Risk Link | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **P1-001** | Sensory Pipeline | E2E | R-04 | Audio in -> Text -> Audio out |
| **P1-002** | Home Proactivity | API | R-03 | Stimuli trigger on World State |
| **P1-003** | Visual Vaults | API | R-01 | Persistence of named outfits |

---

## Execution Strategy

### Every PR: Playwright Tests (~5-10 min)
**All functional tests (P0, P1, P2)**
- Parallelized across 2 workers.
- Fast feedback on infrastructure and logic.

### Nightly: Full Regression (~30 min)
- Includes long-running E2E flows (Onboarding, Visual generation).

---

**Next Steps for QA Team:**
1. Use `/bmad:tea:automate` to generate P0 tests.
2. Complete `tests/support/helpers/redis-utils.ts`.