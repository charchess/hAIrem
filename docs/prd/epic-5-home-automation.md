# Epic 5: Home Automation Bridge

**Goal:** Ancrage dans le réel via Home Assistant.

## User Stories

### Story 5.1: Client Home Assistant
**As a** System,
**I want** to connect to Home Assistant,
**So that** I can read sensor data.

**Acceptance Criteria:**
- [ ] WebSocket client for HA API.
- [ ] Authentication via Long-Lived Access Token.

### Story 5.3: Actions Domotiques
**As a** User,
**I want** the Expert agent to control my home,
**So that** I can delegate tasks.

**Acceptance Criteria:**
- [ ] "Expert Domotique" has a tool to call HA services (e.g., `light.turn_on`).
- [ ] Successful execution feedback loop.
