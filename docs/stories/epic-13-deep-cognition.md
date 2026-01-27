# Epic 13: Deep Cognitive Architecture (The True Memory)

**Status:** Planned
**Goal:** Transform the simple RAG/Vector storage into a true "Subjective Dynamic Memory" (MDP) using Graph Theory.

## Stories

### 13.1: Graph Schema Implementation
**Goal:** Define the Nodes (`Fact`, `Subject`) and Edges (`BELIEVES`, `OBSERVED`) in SurrealDB.
**Key Tech:** SurrealDB `RELATE` statements.

### 13.2: The Decay Algorithm
**Goal:** Implement a background process that reduces the weight/confidence of facts over time unless reinforced.
**Key Tech:** Scheduled task, mathematical decay function.

### 13.3: Subjective Retrieval
**Goal:** Update `recall_memory` to fetch facts based on the *Agent's* perspective (edges starting from `agent:{id}`).
**Key Tech:** Graph traversal queries (`SELECT ->BELIEVES->fact FROM agent:lisa`).

### 13.4: Conflict Synthesis
**Goal:** When consolidating memory, detect contradictory facts and trigger a "Conflict Resolution" LLM prompt to synthesize or discard them.
**Key Tech:** LLM Logic, Advanced Prompting.

