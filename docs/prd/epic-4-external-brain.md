# Epic 4: External Brain & Creativity

**Goal:** Connecteurs vers les services d'intelligence déportés. Le cerveau de hAIrem.

## User Stories

### Story 4.1: Client API LLM
**As a** System,
**I want** to call an OpenAI-compatible API,
**So that** agents can generate text.

**Acceptance Criteria:**
- [ ] Generic API client implemented.
- [ ] Configurable endpoint (URL, Key).
- [ ] Error handling for timeouts/failures.

### Story 4.3: Gestion du Streaming
**As a** User,
**I want** to see the text appear as it's generated,
**So that** latency feels lower.

**Acceptance Criteria:**
- [ ] Backend supports streaming responses from LLM.
- [ ] Frontend displays text character-by-character (typewriter effect).
