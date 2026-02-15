# User Story 13.2: L'Algorithme d'Oubli (Semantic Decay)

**ID:** 13.2  
**Epic:** 13 - La Mémoire de l'Équipage (Deep Cognitive Memory)  
**Status:** done  
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
- [x] **Task 1: Setup & Data Model Verification**
    - [x] [1a] Verify `BELIEVES` schema in SurrealDB for `strength`, `last_reinforced`, and `permanent` fields.
    - [x] [1b] Add any missing fields to the schema definition.
- [x] **Task 2: Core Decay Logic**
    - [x] [2a] Implement the exponential decay algorithm in `apps/h-core/memory/consolidator.py`.
    - [x] [2b] Ensure the logic handles the `permanent: true` flag to skip decay.
- [x] **Task 3: Cleanup & Archiving Logic**
    - [x] [3a] Implement logic to identify and remove/archive edges with `strength < 0.1`.
    - [x] [3b] Implement logic to remove orphaned `fact` nodes.
- [x] **Task 4: Integration & Scheduling**
    - [x] [4a] Create an internal API endpoint or command to trigger the Sleep Cycle.
    - [x] [4b] Integrate logging for facts processed and removed.

### Testing Tasks
- [x] [Test 1] Create unit tests for the decay formula (verify math).
- [x] [Test 2] Integration test: Insert facts, run cycle, verify strength reduction.
- [x] [Test 3] Edge case: Verify permanent facts remain at 1.0 strength.
- [x] [Test 4] Cleanup test: Verify facts with strength 0.05 are removed.

## 7. Dev Agent Record

### Implementation Plan
- Extended SurrealDB schema with `permanent` and `last_reinforced` fields on BELIEVES edge
- Updated `apply_decay_to_all_memories()` to skip permanent facts
- Added `cleanup_orphaned_facts()` method to remove unreferenced fact nodes
- Created internal API endpoint `/internal/memory/sleep-cycle` for triggering decay
- Integrated cleanup call in MemoryConsolidator.apply_decay()

### Debug Log
- 2026-02-15: Initial implementation of Story 13.2
- Added permanent field to BELIEVES schema in h-core and h-bridge SurrealDB clients
- Updated decay queries to exclude permanent facts (WHERE permanent != true)
- Added cleanup_orphaned_facts() to both h-core and h-bridge
- 2026-02-15: Code review fixes - unified decay formula to use last_reinforced field in both h-core and h-bridge

### Completion Notes
✅ Story 13.2 implementation complete:
- AC1: Decay applied via exponential formula (strength * pow(decay_rate, time_diff))
- AC2: Memories with strength < 0.1 are automatically deleted
- AC3: Permanent facts (permanent: true) are preserved during decay
- AC4: Orphaned fact nodes are cleaned up after decay
- All 12 tests pass (memory + graph_memory test suites)

## 8. File List

Modified files:
- apps/h-core/src/infrastructure/surrealdb.py (added permanent field, updated decay logic, added cleanup_orphaned_facts)
- apps/h-core/src/domain/memory.py (updated apply_decay to call cleanup)
- apps/h-bridge/src/infrastructure/surrealdb.py (added permanent field support, added cleanup_orphaned_facts)
- apps/h-bridge/src/main.py (added /internal/memory/sleep-cycle endpoint)
- apps/h-core/tests/test_memory.py (added decay tests)
- apps/h-core/tests/test_graph_memory.py (added decay and cleanup tests)

## 9. Change Log
- 2026-02-11: Story created and initialized for development.
- 2026-02-15: Implemented semantic decay with permanent flag support
- 2026-02-15: Added cleanup for orphaned fact nodes
- 2026-02-15: Created internal API endpoint for sleep cycle
- 2026-02-15: Added comprehensive unit tests (12 tests passing)

## 10. Status
Status: done
