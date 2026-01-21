# Epic 6: Text Interaction Layer

**Goal:** Offrir une alternative textuelle à la voix et permettre un suivi historique.

## User Stories

### Story 6.1: Zone de saisie texte (Chat Input)
**As a** User,
**I want** to type my requests,
**So that** I can interact silently or more precisely.

**Acceptance Criteria:**
- [ ] Input field overlay on A2UI.
- [ ] Send button or "Enter" triggers H-Link message.
- [ ] Message is published to Redis.

### Story 6.2: Historique de conversation
**As a** User,
**I want** to see previous exchanges,
**So that** I don't lose context.

**Acceptance Criteria:**
- [ ] Scrollable message bubbles.
- [ ] Support for both User and Agent messages.

### Story 6.3: Slash Commands
**As a** Power User,
**I want** to bypass the LLM for direct actions,
**So that** I can execute commands faster.

**Acceptance Criteria:**
- [ ] Detection of "/" prefix.
- [ ] Routing direct to Expert agents via expert.command.
