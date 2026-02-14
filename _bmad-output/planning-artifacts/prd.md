---
stepsCompleted: ['step-02-discovery', 'step-03-success', 'step-04-journeys', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
inputDocuments: ['docs/brief.md']
workflowType: 'prd'
classification:
  projectType: web_app
  domain: building_automation
  complexity: high
  projectContext: brownfield
---

# Product Requirements Document - hAIrem

**Author:** Charchess  
**Date:** 2026-02-13  
**Version:** 5.0

---

## Executive Summary

hAIrem est un écosystème d'agents IA incarnés vivant dans une maison intelligente. Chaque agent (persona) possède sa propre personnalité, mémoire subjective, voix et avatar visuel. Les agents communiquent entre eux et avec les utilisateurs via une interface temps réel.

**Concept central :** Maison intelligente avec des assistants virtuels "vivants" qui :
- Ont leur propre personnalité et domaines de compétence
- Se souviennent de leurs interactions (mémoire subjective avec oubli/renforcement)
- Parlent entre eux et avec les utilisateurs
- Évoluent socialement (grille de relations dynamique)
- Sont orchestrés par un Social Arbiter qui décide QUI parle, quand, avec quelle émotion

**Différenciateur clé :** Approche mémorielle subjective unique - chaque agent a sa propre vision des faits.

---

## Success Criteria

### User Success

- Pouvoir discuter avec ses "filles" (les agents)
- Elles remplissent leurs prérogatives (domaines de compétence)
- Elles répondent aux questions
- Elles parlent entre elles
- Elles ont une mémoire avec oubli et renforcement

### Business Success

- Pas de métriques définies (projet personnel/familial)

### Technical Success

- Système fonctionnel : chat, inter-agents, mémoire, cycle nocturne

### Measurable Outcomes

- Chat avec les agents opérationnel
- Communication inter-agents fonctionnelle
- Mémoire persistante avec cycle d'oubli/renforcement
- Système de scoring/arbitrage fonctionnel

---

## Product Scope

### MVP (Phase 1)

- Remettre le chat fonctionnel
- Remettre la mémoire (SurrealDB)
- Remettre la communication inter-agents
- Reconstruire le Social Arbiter (ex-Sentinel)
- Corriger les gaps identifiés

### Growth (Phase 2)

- Voix (STT + TTS avec modulation)
- Génération visuelle (multi-providers)
- Spatial presence (pièces, localisation)
- Multi-utilisateurs avec reconnaissance vocale
- Système d'événements (proactivité)

### Vision (Phase 3)

- Écoute constante (rêve de geek)
- Évolution naturelle des personas
- Learning from feedback
- Écosystème multi-agent complet

---

## User Journeys

### Journey 1 : Utilisateur Principal

**Scène:** Tu rentres chez toi, tu dis "Bonsoir les filles"  
**Montée:** Les agents répondent, échangent, se rappellent de ta journée  
**Climax:** "Tu te souviens de ce qu'on a discuté hier ?" - Elles répondent avec des détails  
**Résolution:** Tu dis bonne nuit, elles passent en mode sommeil

### Journey 2 : Multi-utilisateurs

**Scène:** Un membre de la famille parle à l'interface  
**Montée:** Le système reconnaît QUI parle, chaque persona a sa propre mémoire de cette personne  
**Climax:** "Et toi Lisa, tu te souviens de notre conversation sur les chiens ?" - Lisa répond depuis SES souvenirs  
**Note:** La grille de relations affecte le DISCOURS, pas la QUALITÉ du service

### Journey 3 : Administration

**Scène:** Tu veux ajouter un nouvel agent ou ajuster les paramètres  
**Montée:** Tu modifies le persona, les skills, tu vérifies les coûts  
**Climax:** Tu vois la consommation de tokens par agent, tu désactives celui qui coûte trop

---

## Innovation & Differentiators

### Innovation Areas

- **Approche globale** : Écosystème d'agents incarnés unique
- **Gestion multi-persona dédiée** : Chaque agent a sa propre personnalité, mémoire, voix, avatar
- **Mémoire subjective** : Chaque agent a sa propre interprétation des faits (pas de base partagée)
- **Cycle nocturne** : Consolidation, oubli exponentiel, renforcement
- **Grille sociale dynamique** : Relations évolutives entre agents et avec les utilisateurs
- **Social Arbiter** : Décision de QUI parle, quand, avec quelle émotion

### Validation

- Tests existants en place
- Gap identifié : Ajouter tests unitaires et E2E

### Risk Mitigation

- Composants techniques = intégration de technologies existantes (LLM, Redis, SurrealDB, HA)
- Approche globale = domaine innovant

---

## Functional Requirements

### 1. Chat & Messaging

- FR1: Users can send text messages to agents via the interface
- FR2: Users can receive text responses from agents
- FR3: Agents can initiate conversations based on context and triggers
- FR4: Chat interface displays agent avatars and emotional states

### 2. Memory System

- FR5: Agents can store new memories from conversations
- FR6: Agents can retrieve relevant memories when responding
- FR7: System consolidates short-term memories to long-term storage (night cycle)
- FR8: System implements memory decay (forgetting) over time
- FR9: Memories are reinforced when recalled
- FR10: Each agent has subjective memory (different interpretation of facts)
- FR11: Memory persists across restarts
- FR12: Users can query the memory log of any agent

### 3. Inter-Agent Communication

- FR13: Agents can communicate directly (1:1)
- FR14: Agents can broadcast to multiple agents (1:many)
- FR15: Agents can send to all agents (1:all)
- FR16: System supports whisper channel for internal prompts
- FR17: Agents can subscribe to specific event channels

### 4. Social Arbiter

- FR18: System determines which agent should respond
- FR19: Arbiter considers agent interests and relevance when scoring
- FR20: Arbiter evaluates emotional context
- FR21: Named agent gets priority when explicitly mentioned
- FR22: Arbiter manages turn-taking in multi-agent conversations
- FR23: Arbiter can suppress or delay low-priority responses

### 5. Multi-User Support

- FR24: System recognizes different users by voice
- FR25: Each user has separate memory relationship with each agent
- FR26: Agents maintain distinct memories for each human
- FR27: System tracks emotional history per user (short-term context)

### 6. Social Grid

- FR28: Agents have dynamic relationships with each other
- FR29: Agents have dynamic relationships with users
- FR30: Relationship affects discourse tone but NOT service quality
- FR31: Grille evolves based on interactions and events

### 7. Administration

- FR32: Admin can view token consumption per agent
- FR33: Admin can enable/disable specific agents
- FR34: Admin can configure agent parameters and persona settings
- FR35: Admin can add new agents to the system
- FR36: Admin can configure LLM providers per agent

### 8. Voice (STT/TTS)

- FR37: Users can speak to agents via microphone
- FR38: Agents can respond with synthesized voice
- FR39: Each agent has a dedicated base voice
- FR40: Voice modulates based on context and emotion
- FR41: Voice modulation affects prosody and intonation

### 9. Visual Generation

- FR42: System generates images of agents
- FR43: Multiple image generation providers supported
- FR44: Providers can be switched without code changes
- FR45: Agents have visual avatars with customizable outfits
- FR46: Visual assets are cached for reuse

### 10. Spatial Presence

- FR47: Agents can be assigned to physical locations (rooms)
- FR48: System tracks which location each agent is present in
- FR49: Mobile clients can report their location
- FR50: Remote access (phone) has "exterior" space concept
- FR51: World state includes themes (neutral, christmas, etc.)

### 11. Proactivity & Events

- FR52: Agents can subscribe to system events
- FR53: Agents can react to hardware events (motion, door, etc.)
- FR54: Agents can react to calendar/date events
- FR55: Entropy (system) can inject stimulus ideas to agents
- FR56: Night mode suppresses loud interventions

### 12. Skills & Hotplug

- FR57: Agents have skills separate from persona
- FR58: Skills are defined in modular packages
- FR59: New agents can be added without system restart
- FR60: Skills can be independently enabled/disabled

---

## Non-Functional Requirements

### Performance

- **Approach:** Best effort - optimiser selon les contraintes
- Chat response time: depends on LLM provider
- Voice latency: depends on STT/TTS provider

### Integrations

- Integrations with Home Assistant and other systems via external skills (not native)
- Skills are modular packages that can be added/removed

### Testing

- Gap identifié: Ajouter tests unitaires et E2E pour couverture complète

---

## Project Type: Web App (SPA)

- Real-time via WebSocket
- Browser support: modern browsers (Chrome, Firefox, Safari)
- Accessibility: Voice input/output as core feature (side effect: accessible)
