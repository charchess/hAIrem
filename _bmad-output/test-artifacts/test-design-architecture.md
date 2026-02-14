# Test Design for Architecture: hAIrem V4.1 Stabilization

**Purpose:** Architectural concerns, testability gaps, and NFR requirements for review by Architecture/Dev teams. Serves as a contract between QA and Engineering on what must be addressed before test development begins.

**Date:** 2026-02-10
**Author:** Murat (Test Architect)
**Status:** Architecture Review Pending
**Project:** hairem
**PRD Reference:** docs/prd.md
**ADR Reference:** _bmad-output/planning-artifacts/architecture.md

---

## Executive Summary

**Scope:** Stabilization of the core infrastructure (Redis Streams, SurrealDB SCHEMAFULL) and validation of V4.1 features (Sensory, Home, Visual).

**Business Context** (from PRD):
- **Impact:** Eliminating 'Deep Corruption' and enabling 'Deep Presence'.
- **Problem:** Data loss via volatile Pub/Sub and inconsistent graph memory.
- **GA Launch:** March 2026.

**Architecture** (from ADR):
- **Key Decision 1:** SurrealDB 2.7 in SCHEMAFULL mode.
- **Key Decision 2:** Redis 8.6 with Streams for stimuli persistence.
- **Key Decision 3:** H-Core Orchestrator refactored into a class lifecycle.

**Risk Summary:**
- **Total risks**: 5
- **High-priority (≥6)**: 2 (Data Corruption, Stimuli Loss)
- **Test effort**: ~40-60 tests (~3-5 weeks for 1 QA)

---

## Quick Guide

### 🚨 BLOCKERS - Team Must Decide

1. **B-01: Redis Streams Helper** - Architecture must provide a way to inspect Streams length and ACK status for testing (recommended owner: Amelia/Dev)
2. **B-02: Seeding API** - Need an endpoint to inject specific agent relationships into SurrealDB instantly (recommended owner: Amelia/Dev)

---

## For Architects and Devs - Open Topics 👷

### Risk Assessment

| Risk ID | Category | Description | Prob | Imp | Score | Mitigation | Owner | Timeline |
| --- | --- | --- | :---: | :---: | :---: | --- | --- | --- |
| **R-01** | **DATA** | Corruption de la Mémoire MDP | 2 | 3 | **6** | SCHEMAFULL + Valid. Pydantic | Amelia | Sprint 1 |
| **R-02** | **TECH** | Perte de Stimuli (ACK failure) | 3 | 2 | **6** | Redis Streams + Integration Tests | Amelia | Sprint 1 |

---

### Testability Concerns and Architectural Gaps

#### 1. Blockers to Fast Feedback
- **No API for test data seeding** -> Cannot parallelize graph tests -> Provide `/api/test/seed-graph` endpoint (Backend, Sprint 0)

#### 2. Architectural Improvements Needed
1. **Log Observability**
   - **Current problem**: Logs are broadcast via Pub/Sub (volatile).
   - **Required change**: Expose a retrieval endpoint for historical logs in testing.

---

**Next Steps for Architecture Team:**
1. Review blockers (B-01, B-02).
2. Implement seeding API for graph tests.