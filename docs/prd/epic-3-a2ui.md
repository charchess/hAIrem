# Epic 3: A2UI - The Visual Stage (Frontend)

**Goal:** Interface utilisateur réactive type Visual Novel. Le visage de hAIrem.

## User Stories

### Story 3.1: Moteur de rendu de calques
**As a** User,
**I want** to see characters composed of layers,
**So that** they can change expressions dynamically.

**Acceptance Criteria:**
- [ ] HTML/CSS/JS engine to overlay images (Background, Body, Face).
- [ ] Smooth transitions between states.

### Story 3.2: Connecteur WebSocket Redis
**As a** Frontend,
**I want** to listen to the Redis bus,
**So that** I update the UI in real-time.

**Acceptance Criteria:**
- [ ] WebSocket server in H-Core bridging to Redis.
- [ ] Frontend client connecting to WebSocket.
- [ ] Updates flow from Backend to Frontend instantly.

### Story 3.3: Gestion des états visuels
**As a** User,
**I want** the agent to look like it's thinking or listening,
**So that** the interaction feels natural.

**Acceptance Criteria:**
- [ ] Visual states defined (Idle, Thinking, Speaking).
- [ ] Trigger logic based on message events (e.g., "User speaking" -> Agent "Listening").
