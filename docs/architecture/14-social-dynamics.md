# Architecture Design: Social Dynamics & Arbitration (Epic 18)

**Version:** 1.0
**Status:** In Definition
**Author:** Winston (Architect)
**Date:** 2026-01-28

---

## 1. Introduction

Ce document définit l'architecture sociale de hAIrem, transformant un groupe d'agents isolés en un "équipage" cohérent. L'objectif est de gérer la polyphonie, d'initialiser les relations inter-personnes et d'assurer une proactivité narrative contrôlée.

## 2. Le Social Arbiter
...
### 2.2 Biais Contextuel (Contextual Bias)
L'arbitre ne score pas seulement sur le message, mais sur le `World State` actuel :
- **Thème Festif :** Bonus de scoring pour les agents ayant des traits "Joyeux" ou "Social".
- **Nuit/Sommeil :** Malus pour les interventions bruyantes, sauf urgence P0.
- **Localisation :** Un agent présent dans la même `location` que l'utilisateur reçoit un bonus de proximité narrative.

## 3. Onboarding & Graphe Social

Le graphe social est stocké dans SurrealDB via des relations typées entre les records `agent`.

### Initialisation (The Interview)
Pour éviter un graphe froid, chaque nouvel agent passe par une session d'onboarding (entretien d'embauche virtuel).
- **Entrées :** Bio de l'agent, bios des agents déjà présents.
- **Sorties :** Création des edges `TRUSTS`, `KNOWS`, `LIKES` avec des poids initiaux.

### Évolution
Les relations évoluent dynamiquement en fonction des interactions (Sentiment Analysis) durant les sessions de consolidation nocturnes.

## 4. Proactivité : Le Tickler (Entropy)

Le service **Entropy (Dieu)** utilise un timer avec une composante aléatoire (RNG) pour maintenir la vie du système.

### Mécanisme de Stimulus
Plutôt que de forcer une parole, Entropy injecte un "stimulus" (un mot-clé ou une idée parasite) dans la **Burning Memory** de l'agent.
- L'agent traite ce stimulus comme une pensée propre.
- L'agent décide, selon sa personnalité, s'il l'exprime immédiatement ou s'il le garde en "réserve narrative".

## 5. Conscience Collective (Shared Context)

Le H-Core maintient une liste des agents "présents" dans la session actuelle.
- Cette liste est injectée dans le prompt système de chaque agent.
- Permet aux agents de répondre collectivement (ex: "On arrive !" ou "Les filles, on y va").

## 6. Composants Implémentés

### 6.1 RelationshipBootstrapper
`apps/h-core/src/services/relationship_bootstrapper.py`

Initialise les arêtes de graphe inter-agents (`KNOWS`, `LIKES`, `TRUSTS`) au démarrage. Vérifie l'existence des arêtes avant création pour l'idempotence.

### 6.2 Onboarding — "The Interview"
`apps/h-core/src/features/home/onboarding/service.py`

Flux guidé pour les nouveaux utilisateurs (4 questions séquentielles). Les réponses sont stockées comme `fact` dans SurrealDB. Broadcast de `system.onboarding_complete` en fin de session.

Routes : `POST /api/onboarding/start`, `POST /api/onboarding/answer`, `GET /api/onboarding/status/{user_id}`

### 6.3 Contextual Bias Arbiter (Implémenté)
`determine_responder_async(world_context={"theme": ..., "location": ...})` — bonus +0.1 pour `preferred_location`, +0.05 pour correspondance de thème.

---
🏗️ Winston - Architecte hAIrem
