# Epic 2: The Agent Ecosystem (Backend)

**Goal:** Créer les structures de données pour les agents et la communication. C'est ici que l'intelligence du système est structurée.

## User Stories

### Story 2.1: Définir le schéma H-Link
**As a** System,
**I want** a standardized JSON message format,
**So that** all agents understand each other.

**Acceptance Criteria:**
- [ ] JSON Schema defined for messages (sender, type, payload, timestamp).
- [ ] Validation logic implemented.

### Story 2.2: Implémenter l'Agent Générique
**As a** Developer,
**I want** a base Agent class,
**So that** I can instantiate specific experts easily.

**Acceptance Criteria:**
- [ ] Python class `Agent` with methods for receiving and sending messages.
- [ ] Prompt handling logic.
- [ ] Tool execution logic (stub for now).

### Story 2.3: Configurer "La Renarde" et "L'Expert"
**As a** User,
**I want** the initial duo of agents,
**So that** I can start interacting with the system.

**Acceptance Criteria:**
- [ ] `agents/renarde/expert.yaml` created.
- [ ] `agents/expert-domotique/expert.yaml` created.
- [ ] Both agents load successfully into H-Core.
