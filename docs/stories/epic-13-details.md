# Story 13.1: Graph Schema Implementation

**Status:** Draft
**Epic:** 13 - Deep Cognitive Architecture

## Story
**As a** System Architect,
**I want** to implement a true Graph database schema in SurrealDB,
**so that** memories are not just isolated documents but connected nodes representing the richness of a mental model.

## Acceptance Criteria
1. **Schema Definition:**
    - Define Node Tables: `fact`, `subject` (user/agent), `concept`.
    - Define Edge Tables: `BELIEVES` (Agent->Fact), `ABOUT` (Fact->Subject/Concept), `CAUSED` (Fact->Fact).
2. **Migration:**
    - Create a script to migrate existing "flat" memories into this new graph structure (best effort).
3. **Insertion Logic:**
    - Update `MemoryConsolidator` to generate Graph insertions (RELATE statements) instead of simple INSERTs.
    - Example: `RELATE agent:lisa->BELIEVES->fact:uuid SET confidence=0.9`.

## Tasks
- [ ] Create `apps/h-core/src/infrastructure/graph_schema.surql`
- [ ] Implement `insert_graph_memory(fact_data)` in `SurrealDbClient`.
- [ ] Update `MemoryConsolidator` prompt to output relations.

## Dev Notes
- SurrealDB allows "schemaless" but we want `SCHEMAFULL` for edges to ensure data integrity.
- Edge `BELIEVES` should carry metadata: `confidence`, `decay_factor`, `last_accessed`.

---

# Story 13.2: The Decay Algorithm

**Status:** Draft
**Epic:** 13 - Deep Cognitive Architecture

## Story
**As a** Product Owner,
**I want** unused memories to slowly fade away (lower confidence),
**so that** the agents focus on relevant, recent, or reinforced information, simulating a living memory.

## Acceptance Criteria
1. **Decay Field:** Every `BELIEVES` edge has a `last_accessed` timestamp and a `strength` (0.0-1.0).
2. **Background Process:** A "Dreaming" process runs nightly (or via API).
3. **The Algorithm:**
    - For each memory not accessed in X days, reduce `strength` by Y%.
    - If `strength` < 0.1, archive/delete the edge (Forgetting).
4. **Reinforcement:** When a memory is recalled via RAG, reset `last_accessed` and boost `strength`.

## Tasks
- [ ] Implement `apply_decay()` in `MemoryConsolidator`.
- [ ] Add `update_access_time(fact_id)` in `SurrealDbClient`.
- [ ] Connect RAG retrieval to the reinforcement logic.

---

# Story 13.3: Subjective Retrieval

**Status:** Draft
**Epic:** 13 - Deep Cognitive Architecture

## Story
**As an** Agent,
**I want** to recall memories that *I* believe in,
**so that** my personality and bias remain consistent (e.g., Lisa might hate the rain, while Electra loves it).

## Acceptance Criteria
1. **Contextual Query:** `recall_memory` must filter edges starting from the current agent's ID.
    - Query: `SELECT ->BELIEVES[WHERE strength > 0.3]->fact FROM agent:current_agent`
2. **Shared vs Private:** Some facts are "Universal" (everyone believes them), others are "Subjective".
    - Universal facts can be linked to a generic `agent:system`.
3. **Tool Update:** Update `recall_memory` tool to implicitly use the executing agent's ID.

## Tasks
- [ ] Modify `SurrealDbClient.semantic_search` to accept an `agent_id` filter.
- [ ] Update `BaseAgent.recall_memory` to pass `self.config.name`.

---

# Story 13.4: Conflict Synthesis

**Status:** Draft
**Epic:** 13 - Deep Cognitive Architecture

## Story
**As a** System,
**I want** to detect when a new observation contradicts an old belief,
**so that** I can evolve my understanding rather than holding two opposing views.

## Acceptance Criteria
1. **Conflict Detection:** When inserting a new fact, check for semantic similarity > 0.85 with existing facts about the same subject.
2. **LLM Synthesis:** If conflict detected, ask LLM: "Old: X, New: Y. Are these contradictory? If so, synthesize."
3. **Resolution:**
    - If contradictory, replace Old with Synthesis (or New).
    - If complementary, keep both or merge.

## Tasks
- [ ] Add pre-insertion vector search in `MemoryConsolidator`.
- [ ] Create `ConflictResolver` service/prompt.

