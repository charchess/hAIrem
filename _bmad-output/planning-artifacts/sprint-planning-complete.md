# 🏃 Sprint Planning - hAIrem

**Document généré:** 2026-02-15  
**Scrum Master:** Bob  
**Projet:** hAIrem

---

## 📊 Vue d'Ensemble des Epics

| Epic | Phase | Nom | Stories | Status Actuel | Tests |
|------|-------|-----|---------|---------------|-------|
| **1** | MVP | Core Chat | 4 | ✅ DONE | - |
| **2** | MVP | Memory | 7 | ✅ DONE | - |
| **3** | MVP | Social Arbiter | 6 | ✅ DONE | 13/21 (62%) |
| **4** | MVP | Inter-Agent | 5 | ✅ DONE | - |
| **5** | Growth | Voice | 5 | 🔄 PARTIAL | 11/13 (85%) |
| **6** | Growth | Multi-User | 8 | ✅ DONE | 6/6 (100%) |
| **7** | Growth | Administration | 5 | ✅ DONE | 13/14 (93%) |
| **8** | Growth | Visual | 5 | ✅ DONE | 48/49 (98%) |
| **9** | Growth | Spatial | 5 | ✅ DONE | 20/20 (100%) |
| **10** | Vision | Proactivity | 5 | ⏳ BACKLOG | - |
| **11** | Vision | Skills | 4 | ⏳ BACKLOG | - |

---

## 🎯 Répartition par Sprint

### Sprint 21: Finaliser Voice (Epic 5)

**Phase:** Growth  
**Objectif:** Compléter Voice Modulation et Prosody

| Story | Description | Status | Code | Tests Est. |
|-------|-------------|--------|------|------------|
| 5-1 | Microphone Input | ✅ DONE | EXISTS | - |
| 5-2 | Synthesized Voice Output | ✅ DONE | EXISTS | - |
| 5-3 | Dedicated Base Voice | 🔄 PARTIAL | Partial | 3 |
| 5-4 | Voice Modulation | ❌ TODO | NEW | 5 |
| 5-5 | Prosody/Intonation | ❌ TODO | NEW | 5 |

**Tests estimés:** ~13  
**Dependencies:** Epic 3 (Social Arbiter)

---

### Sprint 22: Proactivity (Epic 10)

**Phase:** Vision  
**Objectif:** Implémenter events et calendar

| Story | Description | Status | Code | Tests Est. |
|-------|-------------|--------|------|------------|
| 10-1 | Event Subscriptions | ⏳ BACKLOG | Partial | 4 |
| 10-2 | Hardware Events | ⏳ BACKLOG | Partial | 4 |
| 10-3 | Calendar Events | ⏳ BACKLOG | NEW | 4 |
| 10-4 | System Stimulus/Entropy | ⏳ BACKLOG | NEW | 4 |
| 10-5 | Night Mode | ✅ DONE | EXISTS | - |

**Tests estimés:** ~16  
**Dependencies:** Epic 4 (Inter-Agent)

---

### Sprint 23: Skills & Hotplug (Epic 11)

**Phase:** Vision  
**Objectif:** Finaliser modularité et hotplug

| Story | Description | Status | Code | Tests Est. |
|-------|-------------|--------|------|------------|
| 11-1 | Skills Separation | ⏳ BACKLOG | Partial | 3 |
| 11-2 | Modular Skill Packages | ⏳ BACKLOG | Partial | 3 |
| 11-3 | Hotplug | ⏳ BACKLOG | Partial | 4 |
| 11-4 | Enable/Disable Skills | ⏳ BACKLOG | NEW | 4 |

**Tests estimés:** ~14  
**Dependencies:** -

---

### Sprint 24: Tests d'Intégration E2E

**Phase:** Integration  
**Objectif:** Tests end-to-end pour tous les epics

| Tâche | Description | Tests Est. |
|--------|-------------|------------|
| E2E Epic 3 | Tests UI Social Arbiter | 8 |
| E2E Epic 5 | Tests Voice E2E | 8 |
| E2E Epic 10 | Tests Proactivity E2E | 8 |
| E2E Epic 11 | Tests Skills E2E | 6 |
| Integration | Tests across epics | 10 |

**Tests estimés:** ~40

---

### Sprint 25: Performance & Optimisation

**Phase:** Optimisation  
**Objectif:** Performance et security review

| Tâche | Description |
|--------|-------------|
| Performance | Latence chat/voice |
| Caching | Optimisation Redis |
| Load Testing | Stress tests |
| Security Audit | RBAC review |

---

## 📈 Résumé Global

| Sprint | Focus | Stories | Tests Est. |
|--------|-------|---------|------------|
| **21** | Voice (Epic 5) | 3 | ~13 |
| **22** | Proactivity (Epic 10) | 4 | ~16 |
| **23** | Skills (Epic 11) | 4 | ~14 |
| **24** | Integration E2E | 5 | ~40 |
| **25** | Performance | 4 | ~10 |

**Total:** 5 Sprints, ~93 Tests estimés

---

## 🔗 Dépendances entre Epics

```
Epic 1 (Core) ─────┬─> Epic 3 (Arbiter) ──> Epic 5 (Voice)
Epic 2 (Memory) ────┤        │
Epic 4 (Inter-Agent)─┴───────┴─> Epic 10 (Proactivity)
                                           │
Epic 6 (Multi-User) ───────────────────────┤
Epic 7 (Admin) ────────────────────────────┤
Epic 8 (Visual) ─────────────────────────────┤
Epic 9 (Spatial) ───────────────────────────┘
```

---

## ✅ Definition of Done

Pour qu'une story soit considérée comme DONE:
1. Code implémenté
2. Tests unitaires passent
3. Tests d'intégration passent
4. Code review passé
5. Documentation mise à jour

---

## 📋 Prochaines Étapes

| Action | Responsable |
|--------|-------------|
| Valider ce planning | Charchess |
| Commencer Sprint 21 | Dev Agent |
| Créer stories pour Epic 10, 11 | Scrum Master |

---

**Date de début Sprint 21:** 2026-02-15  
**Durée:** 2 semaines (variable selon avancement)

---

## Questions en Attente

1. Priorité entre Epic 10 et Epic 11 ?
2. Budget tests acceptable ?
3. Ressources suffisantes ?

