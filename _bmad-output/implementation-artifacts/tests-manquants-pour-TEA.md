# Tests Manquants - Documentation pour TEA

**Date:** 2026-02-15  
**Auteur:** Bob (Scrum Master)  
**Objectif:** Identifier les tests manquants pour les epics marqués "done" mais sans couverture

---

## Résumé Exécutif

Les epics suivants sont marqués comme "complétés" mais n'ont **aucune couverture de tests** :
- Epic 3 (Social Arbiter)
- Epic 6 (Multi-User & Social Grid)
- Epic 7 (Administration)
- Epic 9 (Spatial Presence)

**Action requise:** Générer les tests avant release.

---

## Epic 3: Social Arbiter

**Status:** Code fait, Tests manquants  
**Fichiers créés:** 8 fichiers dans `apps/h-core/src/features/home/social_arbiter/`

### Requirements non testés (FR18-FR23)

| FR | Requirement | Status Tests |
|----|-------------|--------------|
| FR18 | Determine which agent responds | ❌ AUCUN |
| FR19 | Interest-based scoring | ❌ AUCUN |
| FR20 | Emotional context evaluation | ❌ AUCUN |
| FR21 | Named agent priority | ❌ AUCUN |
| FR22 | Turn-taking management | ❌ AUCUN |
| FR23 | Suppress low-priority responses | ❌ AUCUN |

### Tests à générer

1. **Test unitaire:** Scoring engine (relevance, interests, emotional context)
2. **Test unitaire:** Tiebreaker logic
3. **Test unitaire:** Fallback behavior
4. **Test d'intégration:** Arbiter end-to-end (message → agent selection)
5. **Test E2E:** Multi-agent conversation flow

### Fichiers de test existants
- `apps/h-core/tests/test_social_arbiter.py` (à vérifier si implémenté)

---

## Epic 6: Multi-User & Social Grid

**Status:** Code fait, Tests manquants  
**Fichiers créés:** 7 fichiers dans `apps/h-core/src/features/home/`

### Requirements non testés (FR24-FR31)

| FR | Requirement | Status Tests |
|----|-------------|--------------|
| FR24 | Voice recognition | ❌ AUCUN |
| FR25 | Per-user memory | ❌ AUCUN |
| FR26 | Emotional history tracking | ❌ AUCUN |
| FR27 | Agent-to-agent relationships | ❌ AUCUN |
| FR28 | Agent-to-user relationships | ❌ AUCUN |
| FR29 | Tone varies, quality constant | ❌ AUCUN |
| FR30 | Evolving social grid | ❌ AUCUN |

### Tests à générer

**Voice Recognition (FR24):**
1. Test: Voice embedding extraction
2. Test: Voice matching algorithm
3. Test: Fallback handling (unknown voice)

**Per-User Memory (FR25):**
1. Test: Mémoire séparée par utilisateur
2. Test: Récupération par utilisateur
3. Test: Isolation mémoire inter-utilisateurs

**Emotional History (FR26):**
1. Test: Tracking émotionnel par utilisateur
2. Test: Context émotionnel dans les réponses

**Relationships (FR27-FR28):**
1. Test: Création relations agent-agent
2. Test: Évolution relations dans le temps
3. Test: Impact du ton dans les réponses

**Social Grid (FR30):**
1. Test: Évolution de la grille sociale
2. Test: Seuils de relation

---

## Epic 7: Administration

**Status:** Code fait, Tests manquants  
**Fichiers créés:** 5 stories d'implémentation

### Requirements non testés (FR32-FR36)

| FR | Requirement | Status Tests |
|----|-------------|--------------|
| FR32 | View token consumption | ❌ AUCUN |
| FR33 | Enable/disable agents | ⚠️ PARTIEL (UI exists, API test missing) |
| FR34 | Configure agent parameters | ❌ AUCUN |
| FR35 | Add new agents | ⚠️ PARTIEL (UI exists, API test missing) |
| FR36 | Configure LLM providers | ❌ AUCUN |

### Tests à générer

**API Tests requis:**
1. `GET /api/admin/token-usage` - Affichage consommation tokens
2. `POST /api/admin/agents/{id}/enable` - Activer agent
3. `POST /api/admin/agents/{id}/disable` - Désactiver agent
4. `PUT /api/admin/agents/{id}/parameters` - Configurer paramètres
5. `POST /api/admin/agents` - Ajouter nouvel agent
6. `PUT /api/admin/agents/{id}/provider` - Configurer LLM provider

---

## Epic 9: Spatial Presence

**Status:** Code fait, Tests manquants  
**Fichiers créés:** ~50 fichiers dans `apps/h-core/src/features/home/spatial/`

### Requirements non testés (FR47-FR51)

| FR | Requirement | Status Tests |
|----|-------------|--------------|
| FR47 | Room assignment | ❌ AUCUN |
| FR48 | Location tracking | ❌ AUCUN |
| FR49 | Mobile location | ❌ AUCUN |
| FR50 | Exterior space | ❌ AUCUN |
| FR51 | World themes | ❌ AUCUN |

### Tests à générer

**Room Assignment (FR47):**
1. Test: Création room
2. Test: Assignation agent → room
3. Test: Query room info
4. Test: Mise à jour assignment

**Location Tracking (FR48):**
1. Test: Mise à jour location
2. Test: Historique location
3. Test: Confidence level

**Mobile Location (FR49):**
1. Test: API location mobile
2. Test: Throttling
3. Test: Last known location preservation

**Exterior Space (FR50):**
1. Test: Détection exterior (GPS, network)
2. Test: Context exterior dans agent response
3. Test: Re-entry detection

**World Themes (FR51):**
1. Test: Theme context dans agent response
2. Test: Dynamic theme update
3. Test: Default/neutral theme fallback

---

## Problèmes Connus

### Wakeword Test (Epic 14)
- **Fichier:** `sensory_ears.spec.ts`
- **Problème:** Element `#status-brain` not found
- **Status:** CASSÉ - Bloquant pour release

---

## Métriques Actuelles

| Métrique | Cible | Actuel | Status |
|----------|-------|--------|--------|
| P0 Coverage | 100% | <15% | ❌ |
| P1 Coverage | 80% | ~30% | ❌ |
| Overall Coverage | 90% | ~20% | ❌ |

---

## Prochaines Étapes

1. **Fixer wakeword test** (Epic 14) - PRIORITÉ HAUTE
2. **Générer tests Epic 3** - Required for MVP
3. **Générer tests Epic 7** - Admin API
4. **Générer tests Epic 6** - Multi-User
5. **Générer tests Epic 9** - Spatial

---

*Document généré lors de la rétrospective Epic 9*
*Pour TEA/Quinn: Prioriser par ordre de dépendance*
