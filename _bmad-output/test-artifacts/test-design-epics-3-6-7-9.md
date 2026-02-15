# Test Design: Couverture Tests pour Epics 3, 6, 7, 9

**Date:** 2026-02-15
**Author:** Charchess
**Status:** Draft

---

## Résumé Exécutif

**Problème信号的发现:** Le Scrum Master a signalé un défaut de couverture des tests pour les epics marqués "done". **DECOUVERTE CRITIQUE:** Les tests EXISTENT déjà! Le vrai problème est que ce sont des tests **ATDD** (Acceptance Test Driven Development) conçus pour échouer AVANT l'implémentation. Le code a été implémenté mais les tests n'ont JAMAIS été promus de "RED" à "GREEN".

**Scope:** Analyse de risque et stratégie de couverture pour Epic 3, 6, 7, 9

**Résumé des Risques:**

- Total risques identifiés: 12
- Risques haute priorité (≥6): 5
- Catégories critiques: SEC, BUS, TECH

**Résumé de Couverture:**

- Tests existants: ~25 fichiers de tests
- Status: ATDD (conçus pour échouer)
- Action requise: Promotion RED → GREEN
- Effort estimé: 3-5 jours de travail de validation

---

## Découverte: Tests Existants

| Epic | Fichiers de Tests Trouvés | Type | Status Actuel |
|------|--------------------------|------|---------------|
| **Epic 3** (Social Arbiter) | `tests/atdd/epic3-social-arbiter.spec.ts` | E2E/ATDD | RED (conçu pour échouer) |
| **Epic 6** (Multi-User) | `tests/atdd/epic6-multi-user.spec.ts` + `tests/api/epic6-multiuser-complete.spec.ts` | ATDD + API | RED |
| **Epic 7** (Administration) | `tests/atdd/epic7-admin.spec.ts` + `tests/api/admin-panel.spec.ts` + `tests/e2e/admin-panel.spec.ts` | ATDD + API + E2E | RED |
| **Epic 9** (Spatial) | `tests/atdd/epic9-spatial.spec.ts` + `tests/api/epic9-spatial-complete.spec.ts` | ATDD + API | RED |

---

## Not in Scope

| Item | Reasoning | Mitigation |
|------|-----------|------------|
| **Epic 14 Wakeword Test** (sensory_ears.spec.ts) | Problème已知 (Element #status-brain not found) | Fix séparé requis - voir document de Bob |
| **Unit Tests** | Pas de fichiers .test.ts trouvés | Couverture unitaire à évaluer séparément |
| **Performance/Load Testing** | NFRs pas dans le scope actuel | À traiter dans workflow NR |

---

## Risk Assessment

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
|---------|---------|------------|-------------|--------|-------|------------|-------|----------|
| R-001 | SEC | Epic 7 Admin: Accès non autorisé aux APIs d'administration | 2 | 3 | 6 | Tests d'auth existants + ajout tests RBAC | QA | Sprint actuel |
| R-002 | BUS | Epic 3: Mauvaise sélection d'agent导致错误响应 | 2 | 3 | 6 | Valider scoring algorithm + tests E2E multi-agents | QA | Sprint actuel |
| R-003 | TECH | Epic 6: Mémoire utilisateur non isolée导致混合数据 | 3 | 3 | 9 | Tests d'intégration specifically for isolation | QA/DEV | IMMEDIAT |
| R-004 | DATA | Epic 9: Données de localisation incorrectes导致错误的room assignment | 2 | 3 | 6 | Tests API de geofencing + validation coordinate | QA | Sprint actuel |
| R-005 | BUS | Epic 7: Configuration agent错误导致服务中断 | 2 | 2 | 4 | Tests API CRUD + validation schema | QA | Prochain sprint |

### Medium-Priority Risks (Score 3-4)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
|---------|---------|------------|-------------|--------|-------|------------|-------|
| R-006 | TECH | Epic 9: Thème spatial pas appliqué correctement | 2 | 2 | 4 | Tests UI validation + screenshot regression | DEV |
| R-007 | OPS | Epic 3: Turn-taking ne fonctionne pas导致响应延迟 | 1 | 2 | 2 | Monitor logs + tests timeout | DEV |
| R-008 | PERF | Epic 6: Voice recognition超时 | 2 | 2 | 4 | Tests performance + timeout configuration | QA |

### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
|---------|---------|------------|-------------|--------|-------|--------|
| R-009 | BUS | Epic 9: World theme偏好保存失败 | 1 | 1 | 1 | Monitor |
| R-010 | TECH | Epic 7: Logging insuffisant pour debugging | 1 | 1 | 1 | Monitor |
| R-011 | PERF | Epic 6: Évolution sociale grid lente | 1 | 2 | 2 | Monitor |

### Risk Category Legend

- **TECH**: Technical/Architecture (flaws, integration, scalability)
- **SEC**: Security (access controls, auth, data exposure)
- **PERF**: Performance (SLA violations, degradation, resource limits)
- **DATA**: Data Integrity (loss, corruption, inconsistency)
- **BUS**: Business Impact (UX harm, logic errors, revenue)
- **OPS**: Operations (deployment, config, monitoring)

---

## Entry Criteria

- [x] Requirements et assumptions documentés (tests-manquants-pour-TEA.md)
- [x] Code des epics implémenté et déployé en staging
- [x] Tests ATDD existants identifiés
- [x] Environment de test accessible

## Exit Criteria

- [ ] Tests ATDD promus de RED à GREEN (validés contre l'implémentation)
- [ ] Tous les tests P0 passent
- [ ] R-003 (isolation mémoire) traité en priorité
- [ ] Coverage acceptée par Tech Lead

---

## Test Coverage Plan

### Situation Actuelle vs. Requis

#### Epic 3: Social Arbiter (FR18-FR23)

| Requirement | Tests Existants | Test Level | Status | Action Requise |
|------------|-----------------|------------|--------|----------------|
| FR18: Agent selection | `epic3-social-arbiter.spec.ts` | E2E | RED | Promouvoir → GREEN |
| FR19: Interest scoring | `epic3-social-arbiter.spec.ts` | E2E | RED | Promouvoir → GREEN |
| FR20: Emotional context | `epic3-social-arbiter.spec.ts` | E2E | RED | Promouvoir → GREEN |
| FR21: Named agent priority | `epic3-social-arbiter.spec.ts` | E2E | RED | Promouvoir → GREEN |
| FR22: Turn-taking | `epic3-social-arbiter.spec.ts` | E2E | RED | Promouvoir → GREEN |
| FR23: Response suppression | `epic3-social-arbiter.spec.ts` | E2E | RED | Promouvoir → GREEN |

**Action:** Créer tests unitaires pour scoring algorithm + valider E2E

#### Epic 6: Multi-User & Social Grid (FR24-FR31)

| Requirement | Tests Existants | Test Level | Status | Action Requise |
|------------|-----------------|------------|--------|----------------|
| FR24: Voice recognition | `epic6-multi-user.spec.ts` + API | E2E + API | RED | Promouvoir + ajouter tests isolation |
| FR25: Per-user memory | `epic6-multi-user.spec.ts` + API | E2E + API | RED | **CRITICAL:** Tests isolation requis |
| FR26: Emotional history | `epic6-multi-user.spec.ts` + API | E2E + API | RED | Promouvoir |
| FR27: Agent-agent relationships | `epic6-multi-user.spec.ts` | E2E | RED | Promouvoir |
| FR28: Agent-user relationships | `epic6-multi-user.spec.ts` | E2E | RED | Promouvoir |
| FR29: Tone varies | `epic6-multi-user.spec.ts` | E2E | RED | Promouvoir |
| FR30: Evolving social grid | `epic6-multi-user.spec.ts` | E2E | RED | Promouvoir |

**Action:** **PRIORITÉ HAUTE** - Tests isolation mémoire (R-003, Score=9)

#### Epic 7: Administration (FR32-FR36)

| Requirement | Tests Existants | Test Level | Status | Action Requise |
|------------|-----------------|------------|--------|----------------|
| FR32: Token consumption | `admin-panel.spec.ts` | API+E2E | RED | Promouvoir |
| FR33: Enable/disable agents | `epic7-admin.spec.ts` | ATDD | RED | Promouvoir + tests API |
| FR34: Configure parameters | `epic7-admin.spec.ts` | ATDD | RED | Promouvoir |
| FR35: Add new agents | `epic7-admin.spec.ts` | ATDD | RED | Promouvoir + validation |
| FR36: LLM providers | `admin-panel.spec.ts` | API | RED | Promouvoir |

**Action:** Tests RBAC + validation schema

#### Epic 9: Spatial Presence (FR47-FR51)

| Requirement | Tests Existants | Test Level | Status | Action Requise |
|------------|-----------------|------------|--------|----------------|
| FR47: Room assignment | `epic9-spatial.spec.ts` + API | ATDD + API | RED | Promouvoir |
| FR48: Location tracking | `epic9-spatial.spec.ts` + API | ATDD + API | RED | Promouvoir |
| FR49: Mobile location | `epic9-spatial.spec.ts` | ATDD | RED | Promouvoir |
| FR50: Exterior space | `epic9-spatial.spec.ts` | ATDD | RED | Promouvoir |
| FR51: World themes | `epic9-spatial.spec.ts` | ATDD | RED | Promouvoir |

**Action:** Tests geofencing + validation coordinates

---

## Action: Promotion ATDD RED → GREEN

### Workflow Requis

1. **Pour chaque test ATDD existant:**
   - Exécuter le test contre l'implémentation réelle
   - Si FAIL: analyser si c'est un bug d'implémentation ou un test mal écrit
   - Si PASS: promouvoir le status → GREEN

2. **Si test échoue:**
   - Créer ticket bug si c'est un bug d'implémentation
   - Mettre à jour le test si c'est un problème de test (sélecteurs, timing, etc.)

3. **Tests manquants à ajouter:**
   - Tests d'isolation (R-003, priorité CRITICAL)
   - Tests unitaires pour scoring algorithms
   - Tests RBAC pour Admin (R-001)

---

## Resource Estimates

### Test Promotion Effort

| Epic | Tests Count | Hours/Test | Total Hours | Priority |
|------|-------------|------------|-------------|----------|
| Epic 3 | 15 | 0.5 | 7.5 | Haute |
| Epic 6 | 20 | 0.75 | 15.0 | CRITICAL |
| Epic 7 | 12 | 0.5 | 6.0 | Haute |
| Epic 9 | 15 | 0.5 | 7.5 | Moyenne |
| **Total** | **62** | **-** | **36.0** | **~5 jours** |

### Tests Unitaires à Créer

| Component | Tests | Hours | Owner |
|-----------|-------|------|-------|
| Scoring Engine (Epic 3) | 10 | 4 | DEV |
| Memory Isolation (Epic 6) | 8 | 3 | DEV |
| Admin RBAC (Epic 7) | 5 | 2 | DEV |

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: ≥95% (waivers required for failures)
- **P2/P3 pass rate**: ≥90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **Critical paths (Epic 6)**: ≥90% (isolation is critical)
- **Security (Epic 7)**: 100%
- **Business logic (Epic 3)**: ≥80%
- **Location services (Epic 9)**: ≥70%

### Non-Negotiable Requirements

- [ ] Epic 6 memory isolation validée (R-003, Score=9)
- [ ] Epic 7 RBAC tests passent
- [ ] Epic 3 agent selection validée
- [ ] Pas de régression sur fonctionnalités existantes

---

## Mitigation Plans

### R-003: Memory Isolation Failure (Score: 9) - CRITICAL

**Description:** Données utilisateur qui se mélangent entre sessions

**Mitigation Strategy:**
1. Créer tests d'intégration specifically pour isolation
2. Tester: User A login → opérations → logout → User B login → vérifier que données User A pas visibles
3. Tester: Accès concurrent à des données utilisateur

**Owner:** QA Lead + DEV
**Timeline:** 2026-02-16 (immédiat)
**Status:** **IN PROGRESS**
**Verification:** Tests isolation passent + code review

### R-001: Admin Access Control (Score: 6)

**Mitigation Strategy:**
1. Valider que les tests auth existants couvrent admin endpoints
2. Ajouter tests RBAC: utilisateur non-admin ne peut pas accéder /api/admin/*
3. Tester: JWT token avec rôle user vs admin

**Owner:** QA
**Timeline:** 2026-02-17
**Status:** Planned

---

## Assumptions and Dependencies

### Assumptions

1. Code des epics est fonctionnel et déployé en staging
2. Les tests ATDD sont syntaxiquement corrects (juste pas encore exécutés contre l'implémentation)
3. Environment de test avec seed data est disponible

### Dependencies

1. **sensory_ears.spec.ts fix** - Bloquant pour Epic 14 mais pas blocker pour 3,6,7,9
2. **Backend API opérationnel** - Requis pour exécuter tests API
3. **Seed data scripts** - Requis pour tests isolation

### Risks to Plan

- **Risk**: Tests ATDD écrits avec sélecteurs incorrects
  - **Impact**: Tests peuvent échouer même si feature fonctionne
  - **Contingency**: Mettre à jour sélecteurs, utiliser tests API comme fallback

---

## Interworking & Regression

| Service/Component | Impact | Regression Scope |
|-------------------|--------|-----------------|
| **Chat Engine** | Epic 3 modifie le flow de réponse | Tests e2e/chat-engine.spec.ts |
| **Memory Service** | Epic 6 change la isolation | Tests memory-api.spec.ts |
| **Auth Service** | Epic 7 ajout endpoints admin | Tests auth existants |
| **Location Service** | Epic 9 nouveau service | N/A - nouveau |

---

## Follow-on Workflows Recommandés

1. **Pour chaque epic:**
   - Exécuter ATDD tests existants
   - Analyser échecs
   - Mettre à jour tests ou créer tickets bug

2. **Workflow *automate* (optionnel):**
   - Si couverture insuffisante après promotion
   - Générer tests additionnels

3. **Workflow *test-review* (après fixes):**
   - Valider qualité des tests finaux

---

## Appendix

### Fichiers de Tests Existants

```
tests/atdd/epic3-social-arbiter.spec.ts        # E2E, ATDD
tests/atdd/epic6-multi-user.spec.ts            # E2E, ATDD
tests/api/epic6-multiuser-complete.spec.ts    # API, COMPLETE
tests/atdd/epic7-admin.spec.ts                 # E2E, ATDD
tests/api/admin-panel.spec.ts                  # API
tests/e2e/admin-panel.spec.ts                  # E2E
tests/atdd/epic9-spatial.spec.ts               # E2E, ATDD
tests/api/epic9-spatial-complete.spec.ts      # API, COMPLETE
```

### Knowledge Base References

- `risk-governance.md` - Risk classification framework
- `probability-impact.md` - Risk scoring methodology
- `test-levels-framework.md` - Test level selection
- `test-priorities-matrix.md` - P0-P3 prioritization
- `network-first.md` - Flakiness prevention

### Problème Connu: Wakeword Test

- **Fichier:** `tests/e2e/sensory_ears.spec.ts`
- **Problème:** Element `#status-brain` not found
- **Status:** CASSÉ - action requise séparément

---

**Generated by:** BMad TEA Agent - Test Architect Module
**Workflow:** `_bmad/tea/testarch/test-design`
**Version:** 4.0 (BMad v6)
