# hAIrem

> **H**ome **A**utomation **I**ntelligence & **R**esident **E**ntity **M**anagement

**hAIrem** est une architecture cognitive modulaire conçue pour orchestrer un écosystème d'agents IA vivants et persistants au sein de votre domicile. Plus qu'un simple chatbot, c'est un "Sanctuaire Numérique" où cohabitent des personnalités artificielles dotées d'une mémoire subjective, d'émotions et d'une capacité d'action sur le monde réel.

Le système repose sur un noyau central (`h-core`) et une passerelle de communication (`h-bridge`), utilisant SurrealDB pour le stockage de graphes (Mémoire) et Redis pour le bus d'événements (Nerfs).

## Développement & Crédits

hAIrem est un projet de vie dont la réalisation technique est propulsée par l'Intelligence Artificielle, transformant une vision créative en un système complexe et fonctionnel.

*   **Moteur de Développement** : Le code est généré et orchestré par des agents IA (**Gemini 2.0 Flash/Pro** & **Claude 3.5 Sonnet**) via le framework [**BMad** (Breakthrough Method of Agile AI Driven Development)](https://github.com/bmad-code-org/BMAD-METHOD). Cette approche permet de franchir les barrières techniques pour se concentrer sur l'innovation et l'expérience utilisateur.
*   **Assets Visuels** : L'univers graphique (avatars, décors) est généré par **Nano Banana** (IA générative graphique de Google/Gemini).
*   **Gouvernance** : L'architecture est maintenue par l'agent **Architect** (Winston) pour garantir la rigueur, la pérennité et la cohérence de l'écosystème.

---

## Documentation

La documentation technique complète se trouve dans le dossier [`docs/`](./docs/architecture/index.md).

*   [Architecture de Haut Niveau](./docs/architecture/2-architecture-de-haut-niveau.md)
*   [Tech Stack](./docs/architecture/tech-stack.md)
*   [Coding Standards](./docs/architecture/coding-standards.md)

## Démarrage Rapide

### Prérequis

*   Python 3.11+
*   Poetry
*   Docker & Docker Compose

### Installation

1.  Cloner le dépôt :
    ```bash
    git clone <repository_url>
    cd hAIrem
    ```

2.  Installer les dépendances :
    ```bash
    poetry install
    ```

3.  Lancer l'infrastructure (Redis, SurrealDB) :
    ```bash
    docker-compose up -d
    ```

4.  Lancer le Core :
    ```bash
    poetry run python -m apps.h-core.main
    ```

## Structure

*   `apps/` : Applications principales (Core, Bridge).
*   `agents/` : Logique spécifique des agents (Personas).
*   `packages/` : Bibliothèques partagées.
