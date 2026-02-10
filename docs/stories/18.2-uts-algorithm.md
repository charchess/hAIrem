---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories']
inputDocuments: ['docs/prd-v4.md', 'docs/architecture/4-modles-de-donnes-mmoire-subjective.md', 'docs/architecture/10-social-arbiter.md', 'docs/ux/front-end-spec.md', 'docs/THOUGHTS.md']
---

# hAIrem - Epic Breakdown (V4)

## Overview

Ce document détaille le découpage en épopées et stories pour hAIrem V4, transformant la vision de "l'équipage conscient" en tâches d'implémentation concrètes.

## Requirements Inventory

### Functional Requirements

- **FR-V4-01: Matrix Initialization** - Le système initialise les liens relationnels entre agents au démarrage.
- **FR-V4-02: Conflict Resolution** - Arbitrage entre faits contradictoires via synthèse sémantique.
- **FR-V4-03: Semantic Decay** - Érosion temporelle des faits non-renforcés dans le graphe.
- **FR-V4-04: Real-time Token Billing** - Affichage du coût ($) par agent dans le Crew Panel.
- **FR-V4-05: Invisible Agent Control** - Interface de contrôle pour les agents sans avatar (ex: Dieu/Entropy).
- **FR-V4-06: Spatial Routing Badge** - Indicateur visuel de la pièce active dans l'interface.

### NonFunctional Requirements

- **NFR-V4-01: Graph Performance** - Temps de recherche dans le graphe < 500ms.
- **NFR-V4-02: Privacy STT** - 95% du traitement audio effectué localement.
- **NFR-V4-03: Scalability** - Support de 10 agents actifs sans latence système.
- **NFR-UX-01: Perceived Reactivity** - Feedback visuel immédiat (< 200ms).

### Additional Requirements

- **Architecture :** Schéma SCHEMAFULL SurrealDB avec arêtes BELIEVES, ABOUT, CAUSED. Social Arbiter avec algorithme UTS et Social Working Memory (SWM) dans Redis.
- **UX Design :** Style "Cyber-Cozy High-Fi", Rim Lighting, focus polyphonique (scale 1.05 + halo).
- **Technical :** Migration vers des UUIDs immuables pour les entités du graphe.

### FR Coverage Map

- **FR-V4-01 :** Epic 13 (Relations) & Epic 18 (Initialisation sociale).
- **FR-V4-02 :** Epic 13 (Synthèse sémantique).
- **FR-V4-03 :** Epic 13 (Algorithme de decay).
- **FR-V4-04 :** Epic 17 (Calcul tokens/coûts).
- **FR-V4-05 :** Epic 17 (Visibilité agents invisibles).
- **FR-V4-06 :** Epic 17 (Badge Spatial).

---

## Epic List

### Epic 13: La Mémoire de l'Équipage (Deep Cognitive Memory)
Permettre aux agents de "se souvenir" de manière cohérente, subjective et évolutive.
**FRs :** FR-V4-01, FR-V4-02, FR-V4-03.

### Epic 17: Le Centre de Commande High-Fi (The Stage UI/UX)
Offrir un contrôle total et immersif sur l'équipage, les coûts et la présence spatiale.
**FRs :** FR-V4-04, FR-V4-05, FR-V4-06.

### Epic 18: La Synergie Sociale (Social Dynamics & Polyphony)
Transformer l'interaction en une discussion de groupe organique et autonome.
**FRs :** FR-V4-01, FR-V4-02.

---

## Epic 13: La Mémoire de l'Équipage

### Story 13.1: Migration vers le Schéma de Graphe Subjectif
**As a** System,
**I want** to store information as nodes and edges in a Knowledge Graph,
**So that** I can model complex relationships like `BELIEVES` and `ABOUT` with metadata.

**Acceptance Criteria:**
- **Given** une nouvelle information à stocker.
- **When** le système persiste le message.
- **Then** il crée un noeud `fact` et une arête `BELIEVES` liée à l'agent émetteur avec un score de confiance initial.
- **And** le schéma supporte les types de relations `BELIEVES`, `ABOUT` et `CAUSED`.

### Story 13.2: L'Algorithme d'Oubli (Semantic Decay)
**As an** Agent,
**I want** my memories to fade over time if they are not reinforced,
**So that** I maintain a natural and relevant cognitive load.

**Acceptance Criteria:**
- **Given** un ensemble de relations `BELIEVES` en base.
- **When** le cycle de sommeil (Sleep Cycle) est déclenché.
- **Then** la force (`strength`) de chaque arête est réduite selon la formule de decay exponentiel.
- **And** les arêtes dont la force tombe sous 0.1 sont automatiquement archivées ou supprimées.

### Story 13.3: Synthèse Dialectique des Conflits
**As a** User,
**I want** the system to detect and resolve contradictions in its memory,
**So that** my agents don't hold simultaneously opposing beliefs.

**Acceptance Criteria:**
- **Given** un nouveau fait entrant en contradiction sémantique avec un fait existant.
- **When** le `MemoryConsolidator` traite l'insertion.
- **Then** un processus d'arbitrage LLM est lancé pour choisir entre le remplacement (OVERRIDE) ou la fusion (MERGE).

---

## Epic 17: Le Centre de Commande High-Fi

### Story 17.1: Visualisation de la Conscience Spatiale
**As a** User,
**I want** to see where my agents are located in the house,
**So that** I understand the routing of audio and visuals.

**Acceptance Criteria:**
- **Given** un agent affecté à une pièce (Room ID).
- **When** j'ouvre l'interface A2UI.
- **Then** un badge "📍 Nom de la pièce" apparaît sur l'interface.
- **And** le badge se met à jour en temps réel via le bus d'événements.

### Story 17.2: Monitoring Économique (Token Billing per Persona)
**As a** User,
**I want** to see the cost of each agent in real-time,
**So that** I am informed of my system's operational footprint.

**Acceptance Criteria:**
- **Given** une session active.
- **When** j'ouvre le Crew Panel.
- **Then** chaque carte d'agent affiche son coût cumulé en $ et son nombre de jetons.
- **And** un total global de session est calculé dynamiquement.

### Story 17.3: Gestion des Agents Invisibles
**As a** User,
**I want** to see and configure background processes like "Dieu" or "Entropy",
**So that** I have full visibility over all active entities.

**Acceptance Criteria:**
- **Given** des agents chargés sans assets visuels.
- **When** j'ouvre le Crew Panel.
- **Then** ils apparaissent dans la liste avec un indicateur "Processus de fond".
- **And** je peux accéder à leurs logs et à leur configuration.

---

## Epic 18: La Synergie Sociale

### Story 18.1: Initialisation de la Matrice Relationnelle
**As a** System,
**I want** to initialize initial relationships between agents based on their bios,
**So that** they don't behave as strangers when they first meet.

**Acceptance Criteria:**
- **Given** plusieurs agents avec biographies.
- **When** le système démarre.
- **Then** il génère des arêtes `KNOWS` ou `TRUSTS` initiales dans le graphe.
- **And** ces liens influencent la priorité des échanges.

### Story 18.2: L'Arbitre Social (Algorithme UTS)
**As a** User,
**I want** the system to automatically decide which agent should speak based on the topic,
**So that** the conversation feels natural and relevant.

**Acceptance Criteria:**
- **Given** un nouveau message sur le bus.
- **When** le Social Arbiter évalue l'interaction.
- **Then** il calcule un score "Urge-to-Speak" (UTS) pour chaque agent.
- **And** l'agent ou les agents les plus pertinents (> 0.75) sont activés en cascade.

### Story 18.3: Mise en Scène de la Polyphonie (Visual Focus)
**As a** User,
**I want** to see clairement quel agent parle ou réagit,
**So that** je ne me perde pas dans une discussion multi-agents.

**Acceptance Criteria:**
- **Given** une discussion multi-agents.
- **When** un agent prend la parole.
- **Then** son avatar subit un scale de 1.05 et un halo (Arbitration Glow) apparaît.
- **And** les autres agents subissent un léger grayscale (20%).

### Story 18.4: Flux de Discussion Inter-Agents
**As a** User,
**I want** à regarder mes agents discuter entre eux sans intervenir,
**So that** la maison semble être un environnement vivant.

**Acceptance Criteria:**
- **Given** une interaction initiale.
- **When** un agent répond.
- **Then** l'Arbiter permet à un autre agent de rebondir organiquement.
- **And** le cycle s'arrête si l'intérêt tombe ou après 5 échanges.