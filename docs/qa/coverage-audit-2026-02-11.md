# QA Coverage Audit - 2026-02-11

**Auditor:** Quinn (QA Agent)
**Date:** Feb 11, 2026
**Context:** Post-Sprint 9 (Sensory Layer Implementation)

This document provides a transparent assessment of the project's test coverage and functional stability.

---

## 🟢 Green Zone: Solid & Verified
*Components with recent code activity, active tests, and verified integration.*

### 1. Sensory Layer (Epic 14)
*   **Audio Ingestion:** ✅ (WebRTC capture -> Backend)
*   **Wake Word:** ✅ (Local detection with fallback)
*   **Whisper STT:** ✅ (Local streaming transcription)
*   **Neural TTS:** ✅ (MeloTTS architecture + Fallbacks)
*   **Confidence:** High. Code is fresh and 100% covered by unit/integration tests.

### 2. Core Infrastructure
*   **WebSocket Bridge:** ✅ (Verified message routing)
*   **Redis Streams:** ✅ (Verified event bus logic)
*   **SurrealDB Connection:** ✅ (Verified client & graph queries)
*   **Docker Configuration:** ✅ (Build verified, dependencies updated)
*   **Confidence:** High. These are the rails the system runs on.

### 3. Cognitive Core (Epic 13 partial)
*   **Subjective Retrieval:** ✅ (Graph traversal per agent)
*   **Seeding API:** ✅ (Data injection)
*   **Confidence:** Medium-High. Logic is verified, but dataset is small.

---

## 🟡 Grey Zone: Uncertain / Risk Area
*Components present in codebase but lacking recent tests or verification.*

### 1. Visual Imagination (Epic 25)
*   **Status:** Code exists (`apps/h-bridge/src/services/*`?) but `tests/test_visual_variety.py` was broken and removed.
*   **Risk:** Generation of images via NanoBanana/Local providers might be broken due to API changes or dependency drift.
*   **Action Required:** Re-implement `test_visual_variety.py` properly.

### 2. Home Assistant Integration (Epic 5)
*   **Status:** Many stories (`5.1` to `5.7`) imply deep HA integration. No recent tests ran on this.
*   **Risk:** Connection to HA, entity discovery, and action loop might be regressed.
*   **Action Required:** Manual E2E test with a live HA instance.

### 3. Avatar Expressions (Epic 11)
*   **Status:** `chat-to-pose` logic exists, but no specific test verified that "happy" text triggers "happy" pose file load.
*   **Risk:** Visual feedback might be disconnected from chat intent.

### 4. Advanced Social Synergy (Epic 18)
*   **Status:** `UTS Algorithm` (Turn taking) stories exist.
*   **Risk:** Multi-agent conversation flow hasn't been stress-tested recently.

---

## 🔴 Red Zone: Dead or Obsolete
*Code or Stories that seem abandoned or replaced.*

*   **Legacy Celery Workers:** References to Celery in older stories (`5.2`). Architecture has moved to Redis Streams. Old worker code should be purged if still present.
*   **Legacy UI Tests:** Old Selenium/E2E tests that might still be looking for V1 UI elements (we fixed the critical ones, but deep UI testing is sparse).

---

## 📋 Recommendations for Next QA Sprint

1.  **Prioritize Epic 25 Recovery:** Write a functional test for the Image Generation pipeline. It's a "Wow" feature that shouldn't be left rotting.
2.  **Mock HA Interface:** Create a mock Home Assistant server to test Epic 5 logic without needing a real instance.
3.  **Visual Regression Testing:** Implement snapshot testing for the Avatar canvas (verify poses change).

---

**Summary:** The **Brain** and **Ears/Mouth** are healthy. The **Eyes** (Vision/Generation) and **Hands** (Home Assistant) are currently unverified.
