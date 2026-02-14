# User Story 13.2: L'Algorithme d'Oubli (Semantic Decay)

**ID:** 13.2  
**Epic:** 13 - La Mémoire de l'Équipage (Deep Cognitive Memory)  
**Status:** ready-for-dev  
**Priority:** High  
**Generated:** 2026-02-11

## 1. Description de la Story

**As an** Agent,  
**I want** my memories to fade over time if they are not reinforced,  
**So that** I maintain a natural and relevant cognitive load and avoid context saturation.

### Business Value
Le système hAIrem repose sur une "Mémoire Dynamique Pondérée". Sans mécanisme d'oubli, le graphe de connaissances devient trop dense, ce qui dilue la pertinence des agents et augmente inutilement le nombre de tokens injectés dans les prompts LLM.

---

## 2. Critères d'Acceptation (BDD)

### Scenario 1: Réduction de la force des souvenirs lors du cycle de sommeil
- **Given** un ensemble de relations `BELIEVES` dans SurrealDB avec des scores de `strength` variés (ex: 0.8, 0.5, 0.3).
- **When** la tâche de maintenance du cycle de sommeil (Sleep Cycle) est exécutée.
- **Then** le système doit appliquer une réduction exponentielle à chaque score `strength`.
- **And** le nouveau score doit être persisté en base de données.

### Scenario 2: Suppression automatique des souvenirs obsolètes
- **Given** une arête `BELIEVES` dont la force (`strength`) après decay tombe en dessous de 0.1.
- **When** le processus de consolidation se termine.
- **Then** cette arête doit être supprimée du graphe actif (ou déplacée vers une table d'archive `BELIEVES_ARCHIVE`).
- **And** le nœud `fact` associé doit être supprimé s'il n'est plus référencé par aucune autre arête.

### Scenario 3: Préservation des faits "immuables"
- **Given** un fait marqué avec une métadonnée `permanent: true`.
- **When** le cycle de sommeil s'exécute.
- **Then** sa `strength` ne doit pas être affectée par le decay.

---

## 3. Contexte Technique & Guardrails

### Architecture SurrealDB
- **Edges concernées :** `BELIEVES`.
- **Propriétés requises :** `strength` (float, 0.0 to 1.0), `last_reinforced` (datetime), `permanent` (boolean).
- **Query suggérée :** 
  ```surrealql
  UPDATE BELIEVES SET strength = strength * 0.9 WHERE permanent != true;
  ```
  *(Note : L'algorithme exact de decay peut être plus complexe, ex: basé sur le temps écoulé depuis `last_reinforced`).*

### Contraintes d'Implémentation
- **Composant :** Créer ou étendre `apps/h-core/memory/consolidator.py`.
- **Scheduling :** Le processus doit pouvoir être déclenché via une commande CLI ou un endpoint interne (ex: `/internal/memory/sleep-cycle`).
- **Logging :** Logger le nombre de faits "oubliés" à chaque cycle.

### Performance
- Le traitement doit être effectué par lots (batch processing) pour éviter de bloquer la base de données si le graphe contient des milliers d'arêtes.

---

## 4. Dépendances & Références
- **Dépend de :** Story 13.1 (Schéma de Graphe Subjectif).
- **Bloque :** Story 13.3 (Synthèse des conflits - nécessite une base de données propre).
- **Documents de référence :** `docs/architecture.md`, `docs/prd-v4.md`.

---

## 5. Instructions pour le Développeur
1. Vérifier que le schéma `BELIEVES` supporte bien le champ `strength`.
2. Implémenter la logique de decay dans un module de service dédié.
3. Créer un test unitaire simulant le passage du temps et vérifiant la suppression des faits sous le seuil de 0.1.
4. S'assurer que les faits liés à l'identité de l'agent (ex: "Je m'appelle Lisa") sont marqués comme `permanent: true`.

---
*Ultimate BMad Method STORY CONTEXT CREATED - Comprehensive developer guide created.*

## 6. Tasks & Subtasks

### Implementation Tasks
- [ ] **Task 1: Setup & Data Model Verification**
    - [ ] [1a] Verify `BELIEVES` schema in SurrealDB for `strength`, `last_reinforced`, and `permanent` fields.
    - [ ] [1b] Add any missing fields to the schema definition.
- [ ] **Task 2: Core Decay Logic**
    - [ ] [2a] Implement the exponential decay algorithm in `apps/h-core/memory/consolidator.py`.
    - [ ] [2b] Ensure the logic handles the `permanent: true` flag to skip decay.
- [ ] **Task 3: Cleanup & Archiving Logic**
    - [ ] [3a] Implement logic to identify and remove/archive edges with `strength < 0.1`.
    - [ ] [3b] Implement logic to remove orphaned `fact` nodes.
- [ ] **Task 4: Integration & Scheduling**
    - [ ] [4a] Create an internal API endpoint or command to trigger the Sleep Cycle.
    - [ ] [4b] Integrate logging for facts processed and removed.

### Testing Tasks
- [ ] [Test 1] Create unit tests for the decay formula (verify math).
- [ ] [Test 2] Integration test: Insert facts, run cycle, verify strength reduction.
- [ ] [Test 3] Edge case: Verify permanent facts remain at 1.0 strength.
- [ ] [Test 4] Cleanup test: Verify facts with strength 0.05 are removed.

## 7. Dev Agent Record

### Implementation Plan
- (To be filled by Dev Agent)

### Debug Log
- (To be filled by Dev Agent)

### Completion Notes
- (To be filled by Dev Agent)

## 8. File List
- (New or modified files)

## 9. Change Log
- 2026-02-11: Story created and initialized for development.

## 10. Status
Status: in-progress
