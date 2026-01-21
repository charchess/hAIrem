# hAIrem Project Documentation

**Version:** 1.0 (Initial Setup)
**Date:** 20 Janvier 2026
**Status:** Greenfield / Epic 1 Started

## 1. Introduction

hAIrem is a framework for an ecosystem of specialized, embodied, and inter-agentive AI agents. It functions as a "Living House" where agents interact proactively.

### Core Architecture: Thin Orchestrator
The system is designed as a **Thin Orchestrator** (H-Core) that delegates heavy lifting (LLM inference, image generation) to external services. The core focuses on state management, message routing, and agent coordination.

## 2. Repository Structure (Planned)

The project follows a Monorepo structure to keep backend and frontend tightly coupled in configuration while decoupled in execution.

```text
hAIrem/
├── apps/
│   ├── h-core/        # Backend: Python 3.11+ (FastAPI + Async)
│   │   ├── src/       # Application source code
│   │   ├── tests/     # Pytest suite
│   │   └── Dockerfile
│   └── a2ui/          # Frontend: Lightweight Web Interface (Visual Novel style)
├── agents/            # Plugins: Specialized Agents configurations & scripts
│   ├── renarde/       # Example Agent 1
│   └── expert/        # Example Agent 2
├── packages/          # Shared code (Schemas, Types)
├── docs/              # Documentation (PRD, Architecture, Stories)
└── docker-compose.yml # Local development orchestration
```

## 3. Technology Stack

### Backend (H-Core)
- **Language:** Python 3.11+
- **Framework:** FastAPI (for API) + Asyncio (for internal loop)
- **Communication:** Redis (Pub/Sub) using `redis-py` (async)
- **Dependency Management:** Poetry

### Frontend (A2UI) - V2 Omnichannel
- **Type:** Web Application (SPA)
- **Views:**
    - **The Stage:** Visual Novel interface (existing).
    - **Chat Overlay:** Transparent overlay for text input and scrollable history.
    - **Agent Dashboard:** Administrative view for crew status and logs.
- **Communication:** WebSocket (bidirectional).
- **Rendering:** HTML5/CSS3 (Obsidian style) + Transitions.

### Infrastructure & Data
- **Message Bus:** Redis 7.x (Alpine)
- **Persistence:** SurrealDB (Hot) / SQL (Cold - TBD)
- **Containerization:** Docker & Docker Compose

## 4. Key Concepts & Patterns

### H-Link Protocol (v1.1 Standard)
Agents and Users communicate via the Redis bus.

**V2 Update:** The User is now a formal participant in the bus.
- **User Text Input:** Published as `type: narrative.text` with `sender.agent_id: "user"`.
- **Slash Commands:** Published as `type: expert.command` directly to the target agent.

**Message Envelope Schema (JSON):**
```json
{
  "id": "uuid-v4",
  "timestamp": "2026-01-21T10:00:00Z",
  "type": "narrative.text|narrative.chunk|expert.command|system.log",
  "sender": {
    "agent_id": "renarde|user",
    "role": "coordinator|user"
  },
  "recipient": {
    "target": "broadcast|expert-domotique"
  },
  "payload": {
    "content": "Message content or data object",
    "format": "text|json",
    "emotion": "neutral",
    "is_final": true 
  },
  "metadata": {
    "priority": "normal",
    "correlation_id": "uuid-of-parent-msg",
    "ttl": 5
  }
}
```

## 5. Persistent Memory (V2 Addition)
The system will now implement a persistence layer to archive all `narrative.text` messages.
- **Hot Storage:** Redis (current session).
- **Cold Storage:** SurrealDB or SQL (history).
- **Indexing:** By timestamp and agent_id.

## 6. Development Workflow

1.  **Story Driven:** All work starts with a User Story in `docs/stories/`.
2.  **Test First/Driven:** QA designs tests (`docs/qa/assessments/`) before implementation.
3.  **Linting:** Mandatory use of `ruff` for Python linting and formatting.
4.  **Doc Updates:** Documentation must be updated with code changes.

## 6. Current Technical Debt / Known Constraints

- **Greenfield:** No legacy code exists.
- **Dependency:** Heavily reliant on external APIs for intelligence (LLM). The system is "dumb" without connectivity.
- **Constraint:** CPU usage for H-Core must remain minimal to allow running on modest hardware (alongside Home Assistant).

## 7. Useful Commands

```bash
# Start the full stack (once implemented)
docker-compose up -d

# Run Python tests (in h-core)
poetry run pytest

# Lint code
poetry run ruff check .
```
