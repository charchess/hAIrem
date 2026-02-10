# hAIrem Product Requirements Document (PRD)

**Version:** 1.0
**Status:** Approved
**Source:** Derived from Project Brief 1.0 & Architecture 4.2

---

## 1. Introduction & Vision

**hAIrem** est un framework d'écosystème d'agents spécialisés, incarnés et inter-agentifs. Il transforme l'assistant personnel classique en une **"Maison Vivante"** habitée par un équipage virtuel proactif.

### 1.1 Core Concept
L'intersection entre :
1.  **Frameworks Agentiques** (Collaboration technique type CrewAI).
2.  **Roleplay Immersif** (Interface Visual Novel type SillyTavern).
3.  **Domotique** (Contrôle physique type Home Assistant).

### 1.2 Value Proposition
- **Incarnation :** Interface A2UI (Agent-to-User Interface) pour un lien émotionnel.
- **Cognition Temporelle :** Cycles de sommeil analytique pour la consolidation mémorielle.
- **Inter-agentivité :** Les agents discutent et collaborent entre eux via un bus d'événements.

---

## 2. Target Audience

1.  **Primary: The Smart Home Orchestrator**
    - Utilisateurs Home Assistant cherchant à déléguer la gestion complexe via une interface naturelle et proactive.
2.  **Secondary: Creative Developers**
    - Créateurs de scénarios et de personnalités d'agents (Plugin Devs).
3.  **Use Case: Presence Assistant**
    - Personnes isolées nécessitant une présence bienveillante et une sécurité passive.

---

## 3. Functional Requirements (MVP)

### 3.1 Core System (H-Core)
- **FR-01 Event Bus:** Communication asynchrone totale via Redis (Pub/Sub ou Streams).
- **FR-02 Thin Orchestrator:** Le noyau Python gère le flux mais délègue l'inférence (LLM) et la génération (ComfyUI) à des services externes.
- **FR-03 Hot-Reload:** Chargement dynamique des configurations d'agents (`expert.yaml`) sans redémarrage du conteneur.

### 3.2 Agent System
- **FR-04 Specialized Agents:** Support d'agents définis par leur Rôle, Prompt, et Outils.
    - *MVP Agents:* "La Renarde" (Coordination/Social) et "L'Expert Domotique" (Technique).
- **FR-05 Narrative Director (ND):** Processus intermittent (cron/trigger) analysant l'historique pour injecter de la cohérence ou des événements narratifs.
- **FR-06 Memory:** Stockage centralisé avec indexation par agent.

### 3.3 User Interface (A2UI)
- **FR-07 Visual Novel Engine:** Interface Web légère affichant les avatars (layers: BG, Body, Expression).
- **FR-08 Vocal-First:** Conception prioritaire pour l'interaction vocale, le visuel étant un support d'incarnation.
- **FR-09 Streaming Responses:** Affichage/Synthèse en temps réel avec états d'attente visuels ("Pensive").

### 3.4 Integrations
- **FR-10 Home Assistant:** Connecteurs bidirectionnels (Lecture états / Action services) via WebSocket ou API.

---

## 4. Non-Functional Requirements

- **NFR-01 Latency:** Feedback visuel immédiat (< 200ms) lors d'une interaction vocale (changement de pose avant réponse).
- **NFR-02 Resource Efficiency:** CPU/RAM du noyau H-Core minimes (< 500MB RAM hors services déportés).
- **NFR-03 Modularity:** Architecture plugin stricte pour les agents.
- **NFR-04 Resilience:** Tolérance aux pannes des services externes (LLM/ComfyUI) sans crash du noyau.

---

## 5. Epics & User Stories (MVP)

### Epic 1: Foundation & H-Core Architecture
**Goal:** Mettre en place le bus Redis, le conteneur principal et le squelette de l'orchestrateur.
- **Story 1.1:** Initialiser le repo Monorepo (Python Backend + Frontend léger).
- **Story 1.2:** Configurer le Bus Redis et les clients Pub/Sub Python.
- **Story 1.3:** Implémenter le chargeur de plugins `expert.yaml` (Hot-reload).

### Epic 2: The Agent Ecosystem (Backend)
**Goal:** Créer les structures de données pour les agents et la communication.
- **Story 2.1:** Définir le schéma des messages H-Link (JSON sur Redis).
- **Story 2.2:** Implémenter l'Agent Générique (Classe de base gérant Prompts & Outils).
- **Story 2.3:** Créer les configs pour "La Renarde" et "L'Expert".

### Epic 3: A2UI - The Visual Stage (Frontend)
**Goal:** Interface utilisateur réactive type Visual Novel.
- **Story 3.1:** Moteur de rendu de calques (Layers composition).
- **Story 3.2:** Connecteur WebSocket au Bus Redis pour mises à jour temps réel.
- **Story 3.3:** Gestion des états visuels (Idle, Listening, Thinking, Speaking).

### Epic 4: External Brain & Creativity
**Goal:** Connecteurs vers les services d'intelligence déportés.
- **Story 4.1:** Client API générique (OpenAI-compatible) pour LLM.
- **Story 4.2:** Connecteur pour génération d'images (ComfyUI - optionnel MVP mais structurellement prêt).
- **Story 4.3:** Gestion du Streaming de réponse texte.

### Epic 5: Home Automation Bridge
**Goal:** Ancrage dans le réel.
- **Story 5.1:** Client WebSocket Home Assistant.
- **Story 5.2:** Mapping d'entités HA vers le contexte des agents.
- **Story 5.3:** Exécution d'actions domotiques simples par l'Expert.

---

---

## 7. V2 Roadmap: Omnichannel Expansion

### Epic 6: Text Interaction Layer
**Goal:** Offrir une alternative textuelle à la voix et permettre un suivi historique.
- **Story 6.1:** Implémenter une zone de saisie texte (Chat Input) superposée à l'A2UI.
- **Story 6.2:** Afficher l'historique de la conversation actuelle (Message Bubbles).
- **Story 6.3:** Support des commandes "Slash" (ex: /expert-domotique turn_on light.salon).

### Epic 7: Agent Dashboard & Control
**Goal:** Visualiser et gérer l'équipage hAIrem.
- **Story 7.1:** Vue liste des agents chargés avec leur statut (Idle/Thinking) et émotion.
- **Story 7.2:** Visualisation des logs système en temps réel dans l'UI.
- **Story 7.3:** Interface de configuration simplifiée pour les nouveaux agents.

### Epic 8: Persistent Memory (The Archive)

**Goal:** Sauvegarder les interactions pour une continuité à long terme.

- **Story 8.1:** Intégrer une base de données de persistance (SQL ou SurrealDB).

- **Story 8.2:** Chargement de l'historique au démarrage de la session.

- **Story 8.3:** Recherche sémantique dans les souvenirs (RAG local).



### Epic 9: Cognitive Consolidation & Optimization

**Goal:** Améliorer l'intelligence et la performance du système.

- **Story 9.1:** Semantic Caching pour réduire la latence et les coûts.

- **Story 9.2:** Privacy Filter Middleware pour sécuriser les données sensibles.

- **Story 9.3:** The Sleep Cycle (Analytic Background Process) pour l'apprentissage.



### Epic 10: Narrative Orchestration & Proactivity

**Goal:** Incarner une "Maison Vivante" capable d'initiatives.

- **Story 10.1:** Sleep Automation & Scheduling.

- **Story 10.2:** The Entropy Agent (Dieu) pour briser le silence.

- Story 10.3: Cross-Agent Collaboration (Internal Coordination).

### Epic 12: Stabilization & UI Polish
**Goal:** Finaliser la v2 avec une expérience utilisateur fluide et une infrastructure robuste.
- **Story 12.1:** Gestion de la cacophonie - File d'attente (Queue) de parole.
- **Story 12.2:** UI Feedback - États de réflexion, boutons de chargement et indicateur de readiness.
- **Story 12.3:** Dashboard Fixes - Correction de la navigation et toggle d'activation des agents.
- **Story 12.4:** Backend Flexibility - Configuration LLM par agent et persistance SurrealDB (Volumes).

---

## 8. Backlog & Future Concepts (Pending Investigation)

### 8.1 Advanced Persona Management
- **Persona Card Standard:** Définir un format de fichier strict contenant le profil, les outils et les métadonnées.
- **Automated Import Pipeline:** Système d'import de persona avec détourage automatique des assets et stockage local optimisé.
- **Dynamic Asset Expansion:** Capacité à générer des expressions manquantes à partir d'une simple description ou d'une image de base.

### 8.2 Visual & Creative Consistency
- **Outfit Coherence:** Utilisation de LoRA ou de techniques de Prompt Engineering avancées pour garantir que les agents gardent la même tenue sur tous les assets générés.

### 8.3 Interaction Design
- **Omnichannel UI:** Étendre l'interface pour supporter des modes de visualisation alternatifs (Mobile, AR/VR).

