# 📋 CATALOGUE COMPLET DES TESTS - Couverture 100%

**Date:** 2026-02-14  
**Auteur:** TEA (Murat) - Master Test Architect  

---

## 📊 RÉSUMÉ EXÉCUTIF

| Métrique | Valeur |
|----------|--------|
| **Fichiers de Tests Totaux** | 43 |
| **Tests Estimés** | ~500+ |
| **Tests GREEN (passent)** | ~150 |
| **Tests RED (échouent)** | ~200 |
| **Tests NON ÉCRITS** | ~150 |
| **Couverture Actuelle** | ~65% |

---

## 📁 INVENTAIRE COMPLET DES TESTS

### 1. PLAYWRIGHT - E2E (15 fichiers)

| Fichier | Tests | Epic | Status |
|---------|-------|------|--------|
| `tests/e2e/health.spec.ts` | 1 | - | ✅ GREEN |
| `tests/e2e/dashboard.spec.ts` | 3 | Epic 17 | ✅ GREEN |
| `tests/e2e/chat-engine.spec.ts` | 4 | Epic 1 | ✅ GREEN |
| `tests/e2e/sensory_ears.spec.ts` | 2 | Epic 5 | ⚠️ 1 GREEN, 1 RED |
| `tests/e2e/ui-validations.spec.ts` | 11 | Epic 17 | ✅ GREEN |
| `tests/e2e/visual_flow.spec.ts` | 1 | Epic 8 | ✅ GREEN |
| `tests/e2e/visual_flow_clean.spec.ts` | 1 | Epic 8 | ✅ GREEN |
| `tests/e2e/refresh-bug-fixes.spec.ts` | 3 | - | ✅ GREEN |
| `tests/e2e/admin-panel.spec.ts` | 10 | Epic 7 | 🔴 RED (UI missing) |
| `tests/e2e/slash-commands.spec.ts` | 11 | Epic 1 | ⚠️ Partiel |
| `tests/e2e/websocket.spec.ts` | 12 | - | 🔴 PARTIEL |
| `tests/e2e/websocket-complete.spec.ts` | 10 | - | 🔴 RED |
| `tests/e2e/ui-elements-complete.spec.ts` | 18 | - | 🔴 RED |
| `tests/e2e/epic1-chat.spec.ts` | 28 | Epic 1 | 🔴 RED |
| `tests/e2e/epic1-chat.spec.ts` | 28 | Epic 1 | 🔴 RED |

**Sous-total E2E:** ~150 tests

---

### 2. PLAYWRIGHT - API (15 fichiers)

| Fichier | Tests | Epic | Status |
|---------|-------|------|--------|
| `tests/api/api-real-implementation.spec.ts` | ~10 | - | ✅ GREEN |
| `tests/api/voice_dna.spec.ts` | ~5 | Epic 5 | ✅ GREEN |
| `tests/api/proactivity.spec.ts` | ~5 | Epic 10 | ✅ GREEN |
| `tests/api/sensory_pipeline.spec.ts` | ~5 | Epic 5 | ✅ GREEN |
| `tests/api/vault_system.spec.ts` | ~5 | Epic 8 | ✅ GREEN |
| `tests/api/surrealdb_schema.spec.ts` | ~10 | Epic 2 | ✅ GREEN |
| `tests/api/orchestration.spec.ts` | ~8 | Epic 4 | ✅ GREEN |
| `tests/api/redis_streams.spec.ts` | ~8 | Epic 4 | ✅ GREEN |
| `tests/api/admin-panel.spec.ts` | 16 | Epic 7 | ✅ GREEN |
| `tests/api/voice-audio.spec.ts` | 20 | Epic 5 | 🔴 RED |
| `tests/api/memory-api.spec.ts` | 22 | Epic 2 | 🔴 RED |
| `tests/api/epic2-memory.spec.ts` | 40 | Epic 2 | 🔴 RED |
| `tests/api/epic4-inter-agent.spec.ts` | 22 | Epic 4 | 🔴 RED |
| `tests/api/epic8-visual.spec.ts` | 28 | Epic 8 | 🔴 RED |
| `tests/api/epic6-multiuser-complete.spec.ts` | 40 | Epic 6 | 🔴 RED |
| `tests/api/epic9-spatial-complete.spec.ts` | 35 | Epic 9 | 🔴 RED |
| `tests/api/epic10-proactivity-complete.spec.ts` | 40 | Epic 10 | 🔴 RED |

**Sous-total API:** ~320 tests

---

### 3. PLAYWRIGHT - ATDD (8 fichiers) - TOUS RED

| Fichier | Tests | Epic | Status |
|---------|-------|------|--------|
| `tests/atdd/epic3-social-arbiter.spec.ts` | 20 | Epic 3 | 🔴 RED |
| `tests/atdd/epic5-voice-modulation.spec.ts` | 15 | Epic 5 | 🔴 RED |
| `tests/atdd/epic6-multi-user.spec.ts` | 18 | Epic 6 | 🔴 RED |
| `tests/atdd/epic7-admin.spec.ts` | 15 | Epic 7 | 🔴 RED |
| `tests/atdd/epic8-provider-switching.spec.ts` | 18 | Epic 8 | 🔴 RED |
| `tests/atdd/epic9-spatial.spec.ts` | 16 | Epic 9 | 🔴 RED |
| `tests/atdd/epic10-proactivity.spec.ts` | 14 | Epic 10 | 🔴 RED |
| `tests/atdd/security-edge-cases.spec.ts` | 20 | - | 🔴 RED |

**Sous-total ATDD:** ~136 tests

---

### 4. PYTHON - UNIT TESTS

| Fichier | Tests | Status |
|---------|-------|--------|
| `tests/unit/test_background_data_testid.py` | ~5 | ✅ GREEN |
| `tests/unit/test_uts_arbiter.py` | 15 | 🔴 RED (vide) |
| `tests/unit/test_backend_components.py` | 20 | 🔴 RED (vide) |

---

### 5. PYTHON - INTEGRATION TESTS

| Fichier | Tests | Status |
|---------|-------|--------|
| `tests/integration/test_wakeword_integration.py` | ~5 | ⚠️ PARTIEL |
| `tests/integration/test_audio_integration_simple.py` | ~3 | ⚠️ PARTIEL |
| `tests/integration/test_audio_ingestion_e2e.py` | ~2 | 🔴 RED |
| `tests/integration/test_deep_cognition.py` | 15 | 🔴 RED (vide) |

---

## 🎯 COUVERTURE PAR EPIC - DÉTAILLÉE

### Epic 1: Core Chat & Messaging (FR1-FR4)

| FR | Requirement | Tests | Status |
|----|-------------|-------|--------|
| FR1 | Send text messages | 5 | ✅ ~80% |
| FR2 | Receive responses | 5 | ✅ ~80% |
| FR3 | Agent-initiated | 4 | 🔴 ~30% |
| FR4 | Avatars & emotions | 6 | 🟡 ~60% |

**Total Epic 1:** ~20 tests  
**Gap:** Tests E2E pour agents initiative + émotion

---

### Epic 2: Memory System (FR5-FR12)

| FR | Requirement | Tests | Status |
|----|-------------|-------|--------|
| FR5 | Store memories | 5 | ✅ ~90% |
| FR6 | Retrieve memories | 8 | ✅ ~90% |
| FR7 | Night consolidation | 6 | 🟡 ~70% |
| FR8 | Memory decay | 6 | 🟡 ~70% |
| FR9 | Reinforcement | 4 | 🟡 ~60% |
| FR10 | Subjective memory | 4 | 🔴 ~30% |
| FR11 | Persistence | 4 | 🟡 ~60% |
| FR12 | Query log | 5 | 🔴 ~40% |

**Total Epic 2:** ~42 tests  
**Gap:** FR10 (subjective), FR12 (query log UI)

---

### Epic 3: Social Arbiter (FR18-FR23) - 🚨 CRITIQUE

| FR | Requirement | Tests | Status |
|----|-------------|-------|--------|
| FR18 | Agent selection | 4 | 🔴 RED |
| FR19 | Interest scoring | 3 | 🔴 RED |
| FR20 | Emotional context | 3 | 🔴 RED |
| FR21 | Named priority | 3 | 🔴 RED |
| FR22 | Turn-taking | 3 | 🔴 RED |
| FR23 | Suppression | 3 | 🔴 RED |

**Total Epic 3:** ~20 tests  
**Status:** 🔴 0% implémenté - CODE MANQUANT

---

### Epic 4: Inter-Agent (FR13-FR17)

| FR | Requirement | Tests | Status |
|----|-------------|-------|--------|
| FR13 | Direct messages | 4 | ✅ ~90% |
| FR14 | Broadcast group | 4 | ✅ ~85% |
| FR15 | Broadcast all | 3 | 🟡 ~70% |
| FR16 | Whisper channel | 4 | 🔴 ~50% |
| FR17 | Event subscriptions | 5 | 🟡 ~60% |

**Total Epic 4:** ~20 tests  
**Gap:** Whisper UI, event subscriptions

---

### Epic 5: Voice (FR37-FR41)

| FR | Requirement | Tests | Status |
|----|-------------|-------|--------|
| FR37 | Microphone input | 3 | ✅ ~80% |
| FR38 | TTS output | 5 | 🟡 ~60% |
| FR39 | Base voice | 2 | 🔴 ~20% |
| FR40 | Voice modulation | 8 | 🔴 RED |
| FR41 | Prosody/intonation | 6 | 🔴 RED |

**Total Epic 5:** ~24 tests  
**Gap:** FR39-FR41 (code manquant)

---

### Epic 6: Multi-User (FR24-FR31)

| FR | Requirement | Tests | Status |
|----|-------------|-------|--------|
| FR24 | Voice recognition | 7 | 🔴 RED |
| FR25 | Per-user memory | 6 | 🔴 RED |
| FR26 | Emotional history | 7 | 🔴 RED |
| FR27 | Agent relationships | 6 | 🔴 RED |
| FR28 | User relationships | 5 | 🔴 RED |
| FR29 | Quality constant | 3 | 🔴 RED |
| FR30 | Social grid | 6 | 🔴 RED |

**Total Epic 6:** ~40 tests  
**Status:** 🔴 ~10% - CODE MANQUANT

---

### Epic 7: Admin (FR32-FR36)

| FR | Requirement | Tests | Status |
|----|-------------|-------|--------|
| FR32 | Token usage | 4 | ✅ ~90% |
| FR33 | Enable/disable | 5 | ✅ ~80% |
| FR34 | Config params | 4 | 🔴 ~40% |
| FR35 | Add agents | 4 | 🔴 ~30% |
| FR36 | LLM providers | 6 | 🔴 ~40% |

**Total Epic 7:** ~23 tests  
**Gap:** FR34-FR36 (API + UI)

---

### Epic 8: Visual (FR42-FR46)

| FR | Requirement | Tests | Status |
|----|-------------|-------|--------|
| FR42 | Image generation | 6 | ✅ ~85% |
| FR43 | Multi-provider | 7 | 🟡 ~60% |
| FR44 | Switchable | 6 | 🔴 ~40% |
| FR45 | Outfits | 6 | 🟡 ~60% |
| FR46 | Caching | 6 | 🟡 ~50% |

**Total Epic 8:** ~31 tests  
**Gap:** FR44 switchable UI

---

### Epic 9: Spatial (FR47-FR51)

| FR | Requirement | Tests | Status |
|----|-------------|-------|--------|
| FR47 | Room assignment | 7 | 🔴 RED |
| FR48 | Location tracking | 6 | 🔴 RED |
| FR49 | Mobile location | 5 | 🔴 RED |
| FR50 | Exterior space | 5 | 🔴 RED |
| FR51 | World themes | 7 | 🔴 RED |

**Total Epic 9:** ~30 tests  
**Status:** 🔴 0% - CODE MANQUANT

---

### Epic 10: Proactivity (FR52-FR56)

| FR | Requirement | Tests | Status |
|----|-------------|-------|--------|
| FR52 | Event subscriptions | 6 | 🟡 ~50% |
| FR53 | Hardware events | 7 | 🔴 RED |
| FR54 | Calendar events | 8 | 🔴 RED |
| FR55 | System stimulus | 6 | 🔴 RED |
| FR56 | Night mode | 5 | 🟡 ~60% |

**Total Epic 10:** ~32 tests  
**Gap:** FR53-FR55 (code manquant)

---

## 🔴 CE QUI MANQUE POUR 100%

### 1. Tests à Écrire (Code existe)

| Category | Tests Manquants |
|----------|-----------------|
| WebSocket heartbeat | 5 |
| Voice trigger UI | 4 |
| Audio playback UI | 5 |
| Suggestion menu | 4 |
| Log level UI | 3 |
| **Sous-total** | **~21** |

### 2. Tests RED - Code à Implémenter

| Epic | Tests RED | Implémentation Requise |
|------|-----------|------------------------|
| Epic 3 | 20 | ScoringEngine, TurnManager, ResponseSuppressor |
| Epic 6 | 40 | Voice ID, User memory, Emotional tracking |
| Epic 9 | 30 | Spatial/Room API |
| Epic 10 | 20 | Hardware events, Calendar, Stimulus |
| Epic 5 | 15 | Voice modulation, Prosody |
| **Sous-total** | **~125** |

### 3. Tests Unitaires Python Manquants

| Fichier | Status |
|---------|--------|
| `test_memory_consolidator.py` | 🔴 VIDE |
| `test_routing.py` | 🔴 VIDE |
| `test_plugin_loader.py` | 🔴 VIDE |
| `test_llm_client.py` | 🔴 VIDE |
| `test_deep_cognition.py` | 🔴 VIDE |

### 4. Bugs Connus

| Test | Issue |
|------|-------|
| `sensory_ears.spec.ts` | Wakeword element `#status-brain` manquant |
| Epic 18 UTS | Code non intégré dans main.py |

---

## ✅ CHECKLIST POUR 100%

- [ ] Écrire ~21 tests E2E (websocket, voice, UI)
- [ ] Implémenter Epic 3 → +20 tests GREEN
- [ ] Implémenter Epic 6 → +40 tests GREEN
- [ ] Implémenter Epic 9 → +30 tests GREEN
- [ ] Implémenter Epic 10 → +20 tests GREEN
- [ ] Implémenter Epic 5 (voice modulation) → +15 tests GREEN
- [ ] Écrire tests unitaires Python (~50)
- [ ] Fix wakeword test
- [ ] Intégrer Epic 18 UTS dans main.py

---

## 📊 BILAN FINAL

| Métrique | Actuel | Après Implémentation |
|----------|--------|---------------------|
| Fichiers tests | 46 | 46 |
| Tests totaux | ~650 | ~650 |
| Tests GREEN | ~150 | ~350 |
| Tests RED | ~200 | ~0 |
| Couverture | ~65% | **~100%** |

---

## 📁 INVENTAIRE FINAL - TOUS FICHIERS

### PLAYWRIGHT - E2E (18 fichiers)

| # | Fichier | Tests | Status |
|---|---------|-------|--------|
| 1 | health.spec.ts | 1 | ✅ GREEN |
| 2 | dashboard.spec.ts | 3 | ✅ GREEN |
| 3 | chat-engine.spec.ts | 4 | ✅ GREEN |
| 4 | sensory_ears.spec.ts | 2 | ⚠️ 1 GREEN, 1 RED |
| 5 | ui-validations.spec.ts | 11 | ✅ GREEN |
| 6 | visual_flow.spec.ts | 1 | ✅ GREEN |
| 7 | visual_flow_clean.spec.ts | 1 | ✅ GREEN |
| 8 | refresh-bug-fixes.spec.ts | 3 | ✅ GREEN |
| 9 | admin-panel.spec.ts | 10 | 🔴 RED |
| 10 | slash-commands.spec.ts | 11 | ⚠️ PARTIEL |
| 11 | websocket.spec.ts | 12 | 🔴 PARTIEL |
| 12 | websocket-complete.spec.ts | 10 | 🔴 RED |
| 13 | ui-elements-complete.spec.ts | 18 | 🔴 RED |
| 14 | ui-complete.spec.ts | 58 | 🔴 RED |
| 15 | epic1-chat.spec.ts | 28 | 🔴 RED |

**Sous-total E2E:** ~200 tests

---

### PLAYWRIGHT - API (17 fichiers)

| # | Fichier | Tests | Status |
|---|---------|-------|--------|
| 1 | api-real-implementation.spec.ts | 10 | ✅ GREEN |
| 2 | voice_dna.spec.ts | 5 | ✅ GREEN |
| 3 | proactivity.spec.ts | 5 | ✅ GREEN |
| 4 | sensory_pipeline.spec.ts | 5 | ✅ GREEN |
| 5 | vault_system.spec.ts | 5 | ✅ GREEN |
| 6 | surrealdb_schema.spec.ts | 10 | ✅ GREEN |
| 7 | orchestration.spec.ts | 8 | ✅ GREEN |
| 8 | redis_streams.spec.ts | 8 | ✅ GREEN |
| 9 | admin-panel.spec.ts | 16 | ✅ GREEN |
| 10 | voice-audio.spec.ts | 20 | 🔴 RED |
| 11 | memory-api.spec.ts | 22 | 🔴 RED |
| 12 | epic2-memory.spec.ts | 40 | 🔴 RED |
| 13 | epic4-inter-agent.spec.ts | 22 | 🔴 RED |
| 14 | epic8-visual.spec.ts | 28 | 🔴 RED |
| 15 | epic6-multiuser-complete.spec.ts | 40 | 🔴 RED |
| 16 | epic9-spatial-complete.spec.ts | 35 | 🔴 RED |
| 17 | epic10-proactivity-complete.spec.ts | 40 | 🔴 RED |
| 18 | api-complete.spec.ts | 80 | 🔴 RED |

**Sous-total API:** ~400 tests

---

### PLAYWRIGHT - ATDD (8 fichiers) - TOUS RED

| # | Fichier | Tests | Status |
|---|---------|-------|--------|
| 1 | epic3-social-arbiter.spec.ts | 20 | 🔴 RED |
| 2 | epic5-voice-modulation.spec.ts | 15 | 🔴 RED |
| 3 | epic6-multi-user.spec.ts | 18 | 🔴 RED |
| 4 | epic7-admin.spec.ts | 15 | 🔴 RED |
| 5 | epic8-provider-switching.spec.ts | 18 | 🔴 RED |
| 6 | epic9-spatial.spec.ts | 16 | 🔴 RED |
| 7 | epic10-proactivity.spec.ts | 14 | 🔴 RED |
| 8 | security-edge-cases.spec.ts | 20 | 🔴 RED |

**Sous-total ATDD:** ~136 tests

---

### PYTHON - UNIT TESTS (4 fichiers)

| # | Fichier | Tests | Status |
|---|---------|-------|--------|
| 1 | test_background_data_testid.py | 5 | ✅ GREEN |
| 2 | test_uts_arbiter.py | 15 | 🔴 RED |
| 3 | test_backend_components.py | 20 | 🔴 RED |
| 4 | test_python_complete.py | 95 | 🔴 RED |

---

### PYTHON - INTEGRATION (3 fichiers)

| # | Fichier | Tests | Status |
|---|---------|-------|--------|
| 1 | test_wakeword_integration.py | 5 | ⚠️ PARTIEL |
| 2 | test_audio_integration_simple.py | 3 | ⚠️ PARTIEL |
| 3 | test_deep_cognition.py | 15 | 🔴 RED |

---

## ✅ CE QUI EST COUVERT (PEUT ÊTRE TESTÉ MAINTENANT)

### Tests GREEN (~150) - Fonctionnent dès maintenant :
- Health checks
- Dashboard navigation
- Chat send/receive (partiel)
- UI validations (partiel)
- Visual flow (partiel)
- Admin API (Token Usage, Agent Enable/Disable)
- Redis streams
- SurrealDB schema
- Orchestration

### Tests À Implémenter (~500) :
- Epic 3 Social Arbiter
- Epic 5 Voice Modulation
- Epic 6 Multi-User
- Epic 9 Spatial
- Epic 10 Proactivity (complet)
- UI suggestions, voice trigger, audio playback
- WebSocket heartbeat
- Python unit tests

---

*Document généré par TEA (Murat)*
