---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
workflowType: 'architecture'
lastStep: 8
status: 'complete'
completedAt: '2026-02-10'
updatedAt: '2026-02-13'
inputDocuments: ['docs/prd.md', 'docs/architecture.md', 'docs/a2ui-spec-v2.md', 'docs/epic-breakdown-v4.md', 'docs/design-assets-standards.md', '_bmad-output/planning-artifacts/prd.md', '_bmad-output/planning-artifacts/epics.md']
project_name: 'hairem'
user_name: 'Charchess'
date: '2026-02-13'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
Le projet hAIrem V4 se concentre sur trois piliers : Deep Mind (mémoire graphe subjective, cycle cognitif), Deep Presence (sens, présence spatiale, polyphonie) et Deep Home (proactivité, architecture persona-skill). L'architecture doit supporter un graphe de connaissances dynamique, un bus d'événements temps-réel et une interface distribuée multi-clients.

**Non-Functional Requirements:**
- Performance : Synthèse vocale < 800ms, latence visuelle < 5s (chaud) / 20s (froid).
- Disponibilité : Bus audio 99.9%, services LLM/Imaging 100%.
- Cohérence : Identité visuelle préservée à > 90% via le système de Vaults.

**Scale & Complexity:**
Le projet présente une complexité élevée due à l'orchestration multi-agents, la gestion de mémoire sémantique persistante et le rendu visuel dynamique détouré en temps réel.

- Primary domain: AI Agent Ecosystem / Smart Home
- Complexity level: High
- Estimated architectural components: 8-10 (Core, Redis, SurrealDB, LiteLLM, Imaging, UI Stages, Skills Engine, etc.)

### Technical Constraints & Dependencies

- Utilisation de SurrealDB pour la mémoire unifiée.
- Bus de communication Redis.
- Pipeline d'imagerie NanoBanana/rembg.
- Infrastructure Kubernetes mentionnée dans l'architecture actuelle.

### Cross-Cutting Concerns Identified

- Latence de bout en bout (STT -> LLM -> TTS -> Visual).
- Synchronisation d'état entre stages (Localisation, Focus).
- Gestion de la charge GPU/Inférence.

## Starter Template Evaluation

### Primary Technology Domain

AI Agent Ecosystem / Smart Home based on project requirements analysis.

### Starter Options Considered

L'analyse s'est concentrée sur l'évolution de la base de code existante (**h-core**) plutôt que sur un nouveau starter, afin de préserver l'investissement déjà réalisé tout en corrigeant la 'corruption' par une mise à jour systématique des dépendances et des schémas.

### Selected Starter: Custom h-core Evolution (Python/FastAPI)

**Rationale for Selection:**
L'architecture actuelle repose sur une stack Python/FastAPI/Redis/SurrealDB cohérente avec les besoins de flexibilité et d'asynchronisme. La mise à jour vers les versions stables de Février 2026 garantit la sécurité et l'accès aux dernières optimisations de performance (notamment pour SurrealDB 2.7 et Redis 8.6).

**Initialization Command:**

```bash
# Mise à jour de l'environnement existant
poetry add fastapi@latest redis@latest surrealdb@latest litellm@latest
poetry add python@^3.14
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
Python 3.14.3 avec exécution asynchrone (FastAPI/Uvicorn).

**Styling Solution:**
Tailwind CSS + Framer Motion (côté UI Stages) pour le style 'Cyber-Cozy High-Fi'.

**Build Tooling:**
Poetry pour la gestion des dépendances et Docker/Kubernetes pour le déploiement.

**Testing Framework:**
Pytest pour les tests unitaires et d'intégration.

**Code Organization:**
Architecture modulaire Persona-Skill permettant le hotplugging d'agents.

**Development Experience:**
Auto-rechargement, typage strict via Pydantic v2, et observabilité via le broadcast des prompts.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Adoption de SurrealDB 2.7 en mode SCHEMAFULL.
- Utilisation de Redis 8.6 avec Streams pour les données persistantes.
- Authentification via JWT.

**Important Decisions (Shape Architecture):**
- Validation systématique via Pydantic v2.
- Bus audio global synchronisé via Redis.

### Data Architecture
- **SurrealDB 2.7 (SCHEMAFULL) :** Migration des modèles de données vers des définitions de tables strictes. Utilisation des capacités de graphe pour la MDP (Mémoire Dynamique Pondérée).
- **Validation :** Couche de validation Pydantic v2 intégrée au H-Core.

### Authentication & Security
- **FastAPI Security (JWT) :** Gestion des sessions agents/utilisateurs via tokens cryptographiques. Support de la hiérarchie des périphériques (Fixed/Mobile/Remote).

### API & Communication Patterns
- **Redis 8.6 :** Emploi des Streams pour la file d'attente d'inférence et les souvenirs subjectifs. Pub/Sub pour le broadcast des états visuels et de la polyphonie.

### Decision Impact Analysis
**Implementation Sequence:**
1. Mise à jour des dépendances (Poetry).
2. Définition des schémas SCHEMAFULL SurrealDB.
3. Implémentation du middleware JWT.
4. Refactorisation du bus de communication vers Redis Streams.

## Implementation Patterns & Consistency Rules

### Naming Patterns
- **Database (SurrealDB) :** Tables et champs en \`snake_case\`. Pluriel pour les tables (ex: \`agents\`, \`facts\`).
- **API (FastAPI) :** Endpoints en \`kebab-case\` (ex: \`/agent-deep-dive\`). Paramètres en \`snake_case\`.
- **Code (Python) :** Strict respect de la PEP8. Modèles Pydantic en \`snake_case\` pour correspondre à la DB.

### Structure Patterns
- **Organisation :** Architecture orientée 'Features'. Chaque pilier (Mind, Presence, Home) possède son sous-dossier avec ses modèles, services et tests.
- **Tests :** Co-localisation des tests unitaires dans un dossier \`tests/\` au sein de chaque feature.

### Format Patterns
- **API Response :** Format unifié \`{"status": "success", "data": {...}}\` ou \`{"status": "error", "message": "..."}\`.
- **Dates :** Toujours au format ISO 8601 (UTC).

### Communication Patterns
- **Redis Events :** Pattern \`domaine.action\` (ex: \`memory.fact_stored\`, \`presence.stage_updated\`).
- **Payloads :** Toujours inclure un \`timestamp\` et l'ID de l'agent émetteur.

### Enforcement Guidelines
**Tous les agents DOIVENT :**
- Valider les données via les modèles Pydantic avant toute écriture en DB.
- Utiliser le bus Redis Streams pour toute modification d'état global.
- Documenter chaque nouvel endpoint via les docstrings FastAPI (OpenAPI).

## Project Structure & Boundaries

### Complete Project Directory Structure

\`\`\`
hairem/
├── apps/
│   ├── h-core/                 # Cœur Python/FastAPI
│   │   ├── src/
│   │   │   ├── core/           # Bus Redis, Auth JWT, Orchestration
│   │   │   ├── features/
│   │   │   │   ├── mind/       # Epic 13: SurrealDB MDP, Cognitive Cycle
│   │   │   │   ├── presence/   # Epic 14 & 25: Sensory, Visual Bible, Vaults
│   │   │   │   └── home/       # Epic 15 & 18: Skills, Social Arbiter, World State
│   │   │   ├── shared/         # Modèles Pydantic communs, Utils
│   │   │   └── main.py
│   │   ├── tests/              # Tests d'intégration et unitaires par feature
│   │   └── pyproject.toml      # Dépendances Poetry (v3.14)
├── agents/                     # Définitions des Personas (persona.yaml, logic.py)
├── config/                     # Configuration globale (visual, system)
├── docs/                       # Documentation (PRD, Architecture, UJs)
├── shared_assets/              # Vaults (Tenues, Décors de référence)
└── docker-compose.yml          # Orchestration Redis, SurrealDB, H-Core
\`\`\`

### Architectural Boundaries
- **API Boundaries :** Endpoints FastAPI typés sous \`/api/v4/\`. Accès via \`Authorization: Bearer <JWT>\`.
- **Service Boundaries :** Isolation par feature. Un service 'Mind' ne peut pas écrire directement dans le dossier 'Presence'.
- **Data Boundaries :** Schémas SCHEMAFULL SurrealDB imposés par feature.

### Requirements to Structure Mapping
- **Deep Mind (E13) :** \`src/features/mind/\`. Gère les noeuds 'fact' et les arêtes 'BELIEVES'.
- **Sensory & Visual (E14/25) :** \`src/features/presence/\`. Intégration TTS/STT (Candidats: Orpheus, Melo, RVC, OpenVoice) et Asset Manager.
- **Social & Proactivity (E15/18) :** \`src/features/home/\`. Moteur de Skills et Social Arbiter.

### Integration Points
- **Internal :** Bus Redis 8.6 (Streams pour la cognition, Pub/Sub pour l'UI).
- **External :** LiteLLM pour l'abstraction des modèles d'IA.

## Architecture Validation Results

### Coherence Validation ✅
Les versions logicielles de Février 2026 sont validées. L'approche hybride Redis (Streams + Pub/Sub) résout les problèmes de perte de stimuli identifiés lors de l'audit initial.

### Requirements Coverage Validation ✅
- **Cognition :** Supportée par SurrealDB 2.7 et le cycle de consolidation nocturne asynchrone.
- **Polyphonie :** Gérée par le Social Arbiter via Redis Streams.
- **Multi-Stage :** Sécurisé par JWT et routage via FastAPI.

### Implementation Readiness Validation ✅
L'architecture orientée 'Features' et les schémas strictes garantissent que les agents de développement produiront un code modulaire et robuste.

### Architecture Completeness Checklist
- [x] Analyse du contexte projet terminée
- [x] Stack technologique spécifiée (Python 3.14, FastAPI, Redis 8.6, SurrealDB 2.7)
- [x] Patterns de nommage et de structure établis
- [x] Frontières de services et API définies
- [x] Traçabilité avec le PRD V4.1 assurée

### Architecture Readiness Assessment
**Overall Status:** READY FOR IMPLEMENTATION
**Confidence Level:** High

### Implementation Handoff
Les agents de développement doivent prioriser la migration des schémas SurrealDB en mode SCHEMAFULL pour stabiliser la base de données avant d'implémenter les nouvelles fonctionnalités de l'Epic 25.

---

## Architecture Updates (2026-02-13)

### Nouveaux Documents Créés

| Document | Description | Équivalent Epic |
|----------|-------------|-----------------|
| `20-multi-user-social-grid.md` | Support multi-utilisateurs, reconnaissance vocale, grille sociale | Epic 6 |
| `21-admin-ui-dashboard.md` | Interface d'administration, gestion des agents, providers | Epic 7 |

### Gaps Identifiés et Actions

| Gap | Status | Action |
|-----|--------|--------|
| Multi-user | ✅ Complété | Doc 20 créé |
| Admin UI | ✅ Complété | Doc 21 créé |
| Social Arbiter (code) | ❌ PERDU | A reconstruire (Epic 3) |
| Multi-provider images | ⚠️ Partiel | Spec exists, code à implémenter |

### Architecture Completeness (Updated)

- [x] Analyse du contexte projet terminée
- [x] Stack technologique spécifiée (Python 3.14, FastAPI, Redis 8.6, SurrealDB 2.7)
- [x] Patterns de nommage et de structure établis
- [x] Frontières de services et API définies
- [x] Traçabilité avec le PRD V5 assurée
- [x] Support multi-utilisateurs documenté
- [x] Admin UI documentée

### Architecture Readiness Assessment (Updated)

**Overall Status:** READY FOR IMPLEMENTATION  
**Confidence Level:** High  
**Updated:** 2026-02-13