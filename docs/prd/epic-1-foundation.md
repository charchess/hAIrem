# Epic 1: Foundation & H-Core Architecture

**Goal:** Mettre en place le bus Redis, le conteneur principal et le squelette de l'orchestrateur. Cette étape est cruciale pour établir la communication asynchrone qui est le cœur de hAIrem.

## User Stories

### Story 1.1: Initialiser le repo Monorepo
**As a** Developer,
**I want** a structured monorepo with Python Backend and light Frontend,
**So that** I can manage the codebase efficiently.

**Acceptance Criteria:**
- [ ] Repo structure created (`apps/h-core`, `apps/a2ui`, `agents/`).
- [ ] Docker Compose file for local development (Redis + H-Core).
- [ ] Basic CI/CD pipeline (linting).

### Story 1.2: Configurer le Bus Redis
**As a** System,
**I want** a robust message bus,
**So that** agents can communicate asynchronously.

**Acceptance Criteria:**
- [ ] Redis service running in Docker.
- [ ] Python Redis client implemented in H-Core.
- [ ] Basic Pub/Sub mechanism operational (Test publisher/subscriber).

### Story 1.3: Implémenter le chargeur de plugins
**As a** Developer,
**I want** the system to load `expert.yaml` files dynamically,
**So that** I can add agents without restarting the core.

**Acceptance Criteria:**
- [ ] File watcher on `agents/` directory.
- [ ] Parser for `expert.yaml` files.
- [ ] Registration of agents in the memory/registry upon detection.
