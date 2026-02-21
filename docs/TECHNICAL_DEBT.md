# hAIrem Technical Debt Log

This document tracks identified technical debt, architectural shortcuts, and security considerations that need addressing in future iterations.

## Security & Auth
- **API Key Storage (Cleartext)**: LLM API keys and provider credentials are currently stored in cleartext within the `config` table in SurrealDB.
  - *Mitigation Plan*: Implement a vault service with AES encryption for sensitive configuration fields.
- **WebSocket Security**: The `/ws` endpoint does not require authentication.
  - *Mitigation Plan*: Implement JWT-based handshake for WebSocket connections.

## Configuration & Performance
- **Arbitre Social Isolation**: The Social Arbiter is currently locked to system-level defaults (from environment variables) to ensure "brain" stability. It is not granularly configurable via the UI.
  - *Mitigation Plan*: Add an "Expert/Brain" tab in the Admin UI to manage the arbiter's LLM parameters independently.
- **Config Refresh Overhead**: Updating a global config triggers a reconstruction of LLM clients for all agents. While acceptable for <10 agents, this should be optimized for larger crews.

## Observability
- **Redis Logging Loop Risk**: Log recursion is prevented by disabling Redis logging in `h-core`.
  - *Mitigation Plan*: Implement a separate, non-looping logging pipeline (e.g. specialized stream) for core system messages.
