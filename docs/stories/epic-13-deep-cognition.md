# Epic 13: Deep Cognitive Architecture (The True Memory)

**Status:** Done
**Goal:** Transform the simple RAG/Vector storage into a true "Subjective Dynamic Memory" (MDP) using Graph Theory.

## Stories

### 13.1: Graph Schema Implementation [DONE]
**Goal:** Define the Nodes (`Fact`, `Subject`) and Edges (`BELIEVES`, `OBSERVED`) in SurrealDB.

### 13.2: The Decay Algorithm [DONE]
**Goal:** Implement a background process that reduces the weight/confidence of facts over time unless reinforced.

### 13.3: Subjective Retrieval [DONE]
**Goal:** Update `recall_memory` to fetch facts based on the *Agent's* perspective.

### 13.4: Conflict Synthesis [DONE]
**Goal:** Detect contradictory facts and trigger synthesis.

### 13.5: Restore Sleep & Cognition Orchestration [DONE]
**Goal:** Re-implement the background worker for consolidation and decay.

### 13.6: Transient State Management (Self-Awareness) [DONE]
**Goal:** Manage agents' outfits and locations as objective facts in the graph.

