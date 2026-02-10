# Epic 15: Living Home (Skills & Proactivity)

**Version:** 2.0
**Status:** In Progress
**Theme:** Pillar 3 - Deep Home
**PRD Version:** V4

---

## 1. Vision
L'agent habite la maison et son environnement numérique de manière proactive. Cette Epic introduit l'architecture de **Skills Pluggables**, découplant les capacités techniques des identités des agents.

## 2. Objectifs Métier
- **Architecture Persona-Skill :** Permettre à n'importe quel agent de "souscrire" à une compétence (HA, Kanban, Discord) via son `persona.yaml`.
- **Proactivité Réelle :** Réactions autonomes aux événements (ex: "Lisa : Il commence à faire chaud, je baisse les stores ?").
- **Optimisation du Quotidien :** Skills utilitaires comme le "Shopping Night-Scraper" pour la gestion de listes de courses.

## 3. Requirements

### 3.1 Functional Requirements (FR)
- **FR15.1 (Skill Mapping) :** Système de chargement dynamique des outils basé sur la liste `skills` du `persona.yaml`.
- **FR15.2 (Home Assistant Skill) :** Module autonome permettant le pilotage et l'observation de la domotique.
- **FR15.3 (Event Subscription) :** Capacité d'un agent à s'abonner à un bus d'événements HA pour déclencher des réactions.
- **FR15.4 (UI Plugin System) :** Support dans le Dashboard d'onglets spécifiques aux skills (ex: onglet Kanban si Renarde est active).
- **FR15.5 (Shopping Skill) :** Scraper asynchrone pour la comparaison de prix et l'optimisation des listes de courses.

### 3.2 Non-Functional Requirements (NFR)
- **NFR15.1 (Isolation) :** Une erreur dans une skill ne doit pas faire crash l'agent.
- **NFR15.2 (Privacy) :** Les tokens d'accès aux skills (HA_TOKEN, etc.) sont isolés et gérés par le Config Panel.

---
*Mis à jour par John (PM) le 28 Janvier 2026.*