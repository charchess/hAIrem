# 📋 COVERAGE AUDIT - Tests & Validation Gaps

**Date:** 2026-02-14  
**Auteur:** Quinn (QA)  
**Pour:** TEA (Murat) - Master Test Architect  

---

## 1. ÉTAT ACTUEL DES TESTS

### 1.1 Résumé Exécutif

| Métrique | Valeur |
|----------|--------|
| **Tests E2E totaux** | 27 |
| **Tests passants** | 26/27 |
| **Tests échouants** | 1 (wakeword) |
| **Couverture UI** | ~60% |
| **Couverture API** | ~30% |
| **Couverture Backend** | ~20% |

### 1.2 Tests Existants

```
tests/e2e/
├── health.spec.ts                    # ✅ Smoke test (1 test)
├── dashboard.spec.ts                 # ✅ Navigation panels (3 tests)
├── chat-engine.spec.ts               # ✅ Chat send/receive (2 tests)
├── sensory_ears.spec.ts              # ⚠️ Audio (2 tests - 1 fail)
├── ui-validations.spec.ts            # ✅ UI interactions (11 tests)
├── visual_flow.spec.ts               # ✅ /imagine command (1 test)
├── visual_flow_clean.spec.ts         # ✅ Visual flow (1 test)
└── refresh-bug-fixes.spec.ts         # ✅ Bug fixes (3 tests)
```

---

## 2. TESTS MANQUANTS - PAR DOMAINE

### 2.1 ADMIN PANEL (Epic 17)

| Feature | Status | Priorité |
|---------|--------|----------|
| **Onglet System** - Status indicators | ✅ Testé | - |
| **Onglet LLM** - Provider/Model/URL | ❌ NOT TESTED | 🔴 P0 |
| **Onglet LLM** - Test Connection | ❌ NOT TESTED | 🔴 P0 |
| **Onglet LLM** - Save Config | ❌ NOT TESTED | 🔴 P0 |
| **Onglet Logs** - Affichage logs | ❌ NOT TESTED | 🟡 P1 |
| **Onglet Logs** - Pause/Clear | ❌ NOT TESTED | 🟡 P1 |
| **Onglet Agents** - Liste agents | ❌ NOT TESTED | 🔴 P0 |
| **Onglet Agents** - Config per agent | ❌ NOT TESTED | 🔴 P0 |
| **Onglet Agents** - Save override | ❌ NOT TESTED | 🔴 P0 |

**Éléments UI non testés:**
```html
<!-- LLM Tab -->
<select id="llm-provider-select">          <!-- NOT TESTED -->
<input id="llm-model-input">               <!-- NOT TESTED -->
<input id="llm-base-url-input">           <!-- NOT TESTED -->
<button id="llm-test-btn">                <!-- NOT TESTED -->
<button id="save-agent-override">         <!-- NOT TESTED -->

<!-- Logs Tab -->
<button id="pause-logs">                  <!-- NOT TESTED -->
<button id="clear-logs">                 <!-- NOT TESTED -->

<!-- Agents Tab -->
<div id="agent-cards-container">          <!-- NOT TESTED -->
<input id="agent-llm-model">             <!-- NOT TESTED -->
```

### 2.2 API ENDPOINTS

| Endpoint | Method | Status | Priorité |
|----------|--------|--------|----------|
| `/api/agents` | GET | ❌ NOT TESTED | 🔴 P0 |
| `/api/history` | GET | ❌ NOT TESTED | 🔴 P0 |
| `/api/admin/token-usage` | GET | ❌ NOT TESTED | 🟡 P1 |
| `/api/admin/token-cost-summary` | GET | ❌ NOT TESTED | 🟡 P1 |
| `/api/admin/agents` | GET | ❌ NOT TESTED | 🔴 P0 |
| `/api/admin/agents/{id}/status` | GET | ❌ NOT TESTED | 🟡 P1 |
| `/api/admin/agents/{id}/enable` | POST | ❌ NOT TESTED | 🔴 P0 |
| `/api/admin/agents/{id}/disable` | POST | ❌ NOT TESTED | 🔴 P0 |
| `/api/test/seed-graph` | POST | ❌ NOT TESTED | 🟢 P2 |
| `/api/test/reset-streams` | POST | ❌ NOT TESTED | 🟢 P2 |

### 2.3 CHAT & MESSAGING

| Scenario | Status | Priorité |
|----------|--------|----------|
| Envoi message → broadcast | ✅ Testé | - |
| Envoi message → agent spécifique | ✅ Testé | - |
| Commande `/imagine` | ✅ Testé | - |
| Commande `/outfit` | ❌ NOT TESTED | 🟡 P1 |
| Commande slash unknown | ❌ NOT TESTED | 🟢 P2 |
| Message vide | ❌ NOT TESTED | 🟡 P1 |
| Message très long | ❌ NOT TESTED | 🟢 P2 |
| Caractères spéciaux | ❌ NOT TESTED | 🟢 P2 |
| XSS attempt | ❌ NOT TESTED | 🟢 P2 |

### 2.4 WEBSOCKET

| Scenario | Status | Priorité |
|----------|--------|----------|
| Connexion WebSocket | ⚠️ Partiel | - |
| Reconnexion auto | ❌ NOT TESTED | 🔴 P0 |
| Déconnexion serveur | ❌ NOT TESTED | 🔴 P0 |
| Message corrompu | ❌ NOT TESTED | 🟢 P2 |
| Heartbeat/ping-pong | ❌ NOT TESTED | 🟡 P1 |

### 2.5 AUDIO / WAKEWORD (Epic 14)

| Scenario | Status | Priorité |
|----------|--------|----------|
| Wakeword binary stream | ❌ FAIL (element missing) | 🔴 P0 |
| TTS audio stream | ❌ NOT TESTED | 🔴 P0 |
| Whisper transcription | ❌ NOT TESTED | 🔴 P0 |
| Voice trigger button | ❌ NOT TESTED | 🟡 P1 |
| Audio playback | ❌ NOT TESTED | 🟡 P1 |

### 2.6 NAVIGATION & UI

| Scenario | Status | Priorité |
|----------|--------|----------|
| Ouverture Admin panel | ✅ Testé | - |
| Fermeture Admin (X) | ✅ Testé | - |
| Fermeture Admin (Echap) | ✅ Testé | - |
| Fermeture Admin (click outside) | ✅ Testé | - |
| Ouverture Crew panel | ✅ Testé | - |
| Fermeture Crew (X) | ✅ Testé | - |
| Fermeture Crew (Echap) | ✅ Testé | - |
| Fermeture Crew (click outside) | ✅ Testé | - |
| Log level select | ❌ NOT TESTED | 🟡 P1 |
| Suggestion menu | ❌ NOT TESTED | 🟡 P1 |

---

## 3. GAPS FONCTIONNELS

### 3.1 Epic 18 - UTS (Urge to Speak)

| Component | Status |
|-----------|--------|
| **Documentation** | ✅ Complète (`docs/architecture/10-social-arbiter.md`) |
| **Code SocialArbiter** | ✅ Existe (`src/features/home/social_arbiter/`) |
| **Intégration main.py** | ❌ NOT INTEGRATED |
| **Tests** | ❌ NOT TESTED |

**Tests requis:**
- ScoringEngine calcule les scores UTS correctement
- TurnManager gère la file d'attente
- ResponseSuppressor applique l'inhibition
- Routing basé sur UTS > 0.75

### 3.2 Epic 13 - Deep Cognition

| Component | Status |
|-----------|--------|
| Schema SurrealDB | ✅ Implementé |
| Graph edges (BELIEVES, ABOUT, CAUSED) | ✅ Implementé |
| Semantic search | ✅ Implementé |
| Semantic decay | ⚠️ Partiel |
| Consolidation | ✅ Implementé |
| Tests unitaires | ❌ NOT TESTED |
| Tests d'intégration | ❌ NOT TESTED |

### 3.3 Epic 14 - Sensory Layer

| Component | Status | Tests |
|-----------|--------|-------|
| Wakeword detection | ❌ BROKEN | ❌ |
| Whisper STT | ✅ Implementé | ❌ |
| TTS (Melo/OpenVoice) | ⚠️ Partiel | ❌ |
| Audio streaming | ⚠️ Partiel | ❌ |

---

## 4. GAPS TECHNIQUES

### 4.1 Tests Unitaires Python

```
apps/h-core/tests/
├── test_agent_creation.py          # ✅ Existe
├── test_agent_management.py        # ✅ Existe
├── test_per_user_memory.py         # ✅ Existe
├── test_social_grid.py            # ✅ Existe
├── test_quality_gates.py          # ✅ Existe
├── test_voice_recognition.py      # ✅ Existe
├── test_visual_dreamer.py         # ✅ Existe
└── test_social_arbiter.py         # ✅ Existe

# MANQUANTS:
- test_memory_consolidator.py
- test_routing.py
- test_plugin_loader.py
- test_llm_client.py
```

### 4.2 Tests d'Intégration

| Integration | Status |
|------------|--------|
| h-core ↔ Redis | ❌ NOT TESTED |
| h-core ↔ SurrealDB | ⚠️ Partiel |
| h-bridge ↔ h-core | ❌ NOT TESTED |
| h-bridge ↔ WebSocket | ❌ NOT TESTED |
| Agent ↔ LLM | ❌ NOT TESTED |

### 4.3 Performance Tests

| Scenario | Status |
|----------|--------|
| Load testing | ❌ NOT TESTED |
| Redis stream throughput | ❌ NOT TESTED |
| SurrealDB query performance | ❌ NOT TESTED |
| LLM response time | ❌ NOT TESTED |

---

## 5. RISQUES & RECOMMANDATIONS

### 5.1 Risks Identifiés

| Risk | Impact | Probability |
|------|--------|-------------|
| UTS non implémenté | 🔴 Critique | Haute |
| Wakeword cassé | 🔴 Critique | Haute |
| API non testée | 🟡 Moyen | Haute |
| Pas de regression suite | 🟡 Moyen | Moyenne |

### 5.2 Priorisation Recommandée

#### 🔴 P0 - Critique (à faire en premier)

1. **Fix wakeword test** - `#status-brain` element missing
2. **API tests** - /api/admin/* endpoints
3. **Admin Panel LLM tab** - Toutes les fonctionnalités
4. **WebSocket reconnection** - Scénarios de reconnexion

#### 🟡 P1 - Important

1. **Agent enable/disable** - API + UI
2. **Audio/TTS tests** - Epic 14
3. **Commandes slash** - /outfit, /imagine variants

#### 🟢 P2 - Nice to have

1. **Performance tests**
2. **Security tests** (XSS, injection)
3. **Edge cases** (long messages, special chars)

---

## 6. PLAN D'ACTION TEA

### Step 1: Fix Blocker
```
- Corriger wakeword test (status-brain element)
- Status: 🔴 BLOCKER
```

### Step 2: API Coverage
```
- Créer API test suite pour /api/admin/*
- Créer API test suite pour /api/agents, /api/history
- Status: 🔴 HIGH PRIORITY
```

### Step 3: Admin Panel
```
- Tester onglet LLM (provider, model, test, save)
- Tester onglet Agents (list, config, save)
- Status: 🔴 HIGH PRIORITY
```

### Step 4: Integration
```
- WebSocket reconnection tests
- Audio flow tests
- Status: 🟡 MEDIUM PRIORITY
```

### Step 5: Epic 18 UTS
```
- Si implémenté: tests scoring engine
- Si reporté: documenter comme "deferred"
- Status: 📌 DECISION NEEDED
```

---

## 7. ANNEXE: CHECKLIST COMPLÈTE

### ✅ Déjà Testé (26 tests)

- [x] Health smoke test
- [x] Dashboard navigation open/close
- [x] Admin panel elements
- [x] Crew panel open/close
- [x] Chat send to specific agent
- [x] Chat broadcast
- [x] Background presence
- [x] Avatar presence
- [x] Visual /imagine flow
- [x] Visual flow clean
- [x] Refresh no replay
- [x] Dieu not in dropdown
- [x] User message echo fix

### ❌ Non Testé

- [ ] LLM provider select
- [ ] LLM model input
- [ ] LLM test connection
- [ ] LLM save config
- [ ] Agent enable/disable API
- [ ] Agent override save
- [ ] WebSocket reconnection
- [ ] Wakeword detection
- [ ] TTS audio
- [ ] Whisper transcription
- [ ] /outfit command
- [ ] Log level change
- [ ] Token usage API
- [ ] All /api/admin/* endpoints

---

**Document généré par Quinn (QA)**  
**Pour assignment TEA - Coverage Audit**
