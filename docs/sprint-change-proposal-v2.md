# Sprint Change Proposal: hAIrem V2 - Omnichannel Expansion

**Date:** 21 Janvier 2026
**Status:** Approved by User
**Initiator:** John (PM)

## 1. Analysis Summary

### Issue Identified
The current hAIrem MVP is strictly "Vocal-First" and lacks an interface for text-based interaction and administrative control. Users need to be able to whisper (text) to their agents and visualize the state of the "Living House" through a dashboard.

### Impact Analysis
- **Epics:** Epic 1-5 (MVP) remain valid and serve as the foundation. No rollback required.
- **Architecture:** The H-Core and Redis bus are compatible. The A2UI (Frontend) requires significant expansion to handle multimodal inputs and multiple views (Stage vs. Dashboard).
- **Scope:** Expansion from "Vocal-Only" to "Omnichannel Companion".

## 2. Recommended Path Forward
**Option:** Direct Integration (V2 Phase).
We will add three new Epics to the project to deliver these features iteratively.

## 3. Specific Artifact Updates

### PRD (docs/prd.md)
Add a "V2 Roadmap" section defining:
- **Epic 6: Text Interaction Layer**
- **Epic 7: Agent Dashboard**
- **Epic 8: Persistent Memory**

### Project Documentation (docs/project-documentation.md)
Update the A2UI section to include:
- **Chat Overlay:** A transparent text input/history area on top of the "Stage".
- **Dashboard View:** A dedicated administrative area accessible via navigation.

## 4. Success Criteria for the Change
- The user can type a message and receive a streamed narrative response.
- The user can see a list of loaded agents and their current "mood" (emotion).
- History is preserved between sessions (Epic 8).

## 5. Next Steps
1.  **PM (John):** Update `docs/prd.md` with V2 Roadmap.
2.  **Architect (Winston):** Update `docs/project-documentation.md` with A2UI redesign notes.
3.  **SM (Bob):** Draft Story 6.1 (Chat Input UI).
