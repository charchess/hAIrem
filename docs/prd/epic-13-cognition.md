# Epic 13: Deep Cognitive Architecture (Cognition Profonde)

**Status:** In Review
**Theme:** Pillar 1 - Deep Mind
**PRD Version:** V3

## 1. Executive Summary
Transformer la mémoire de hAIrem d'un simple stockage de documents (RAG classique) en un modèle mental structuré (Graphe de connaissances). L'objectif est de permettre aux agents d'avoir des croyances subjectives, de "ressentir" le passage du temps via l'oubli (decay) et de résoudre activement les contradictions.

## 2. Business Objectives & User Value
- **Cohérence des Personnages :** Chaque agent doit pouvoir avoir ses propres opinions (subjectivité).
- **Pertinence Cognitive :** Éviter la surcharge d'informations obsolètes via un algorithme d'érosion naturelle (oubli).
- **Évolution Mentale :** Le système doit pouvoir changer d'avis de manière logique lorsqu'un fait nouveau contredit un fait ancien (synthèse).

## 3. Scope & Key Requirements

### 3.1 Graphe de Connaissances (Graph Memory)
- **Requirement 1.1 :** Migration du stockage plat (JSON/Text) vers un schéma de Graphe dans SurrealDB.
- **Requirement 1.2 :** Distinction entre les Noeuds (Faits, Sujets, Concepts) et les Arêtes (Croyances, Relations).
- **Requirement 1.3 :** Typage strict des relations `BELIEVES`, `ABOUT`, `CAUSED`.

### 3.2 Subjectivité & Perspectives
- **Requirement 2.1 :** Un fait peut être cru par plusieurs agents avec des niveaux de confiance différents.
- **Requirement 2.2 :** Filtrage de la recherche sémantique par "Point de vue" (Agent ID + Système).

### 3.3 Érosion & Renforcement (Decay)
- **Requirement 3.1 :** Diminution automatique de la force des croyances avec le temps.
- **Requirement 3.2 :** Renforcement de la force d'un fait chaque fois qu'il est rappelé (boucle de feedback).
- **Requirement 3.3 :** Suppression automatique (ou archivage) des faits dont la force tombe sous un seuil critique.

### 3.4 Synthèse Dialectique (Conflict Resolution)
- **Requirement 4.1 :** Détection de conflits sémantiques lors de la consolidation.
- **Requirement 4.2 :** Utilisation du LLM pour arbitrer entre un fait ancien et un fait nouveau (Override vs Merge vs Ignore).

## 4. Success Metrics
- **Zéro Contradiction :** Le système ne doit pas affirmer simultanément "A" et "Non-A".
- **Spécificité des Agents :** Les agents doivent démontrer des biais différents sur des sujets subjectifs lors des tests.
- **Performance :** La recherche dans le graphe ne doit pas excéder 500ms.

---
*Défini par John (PM) le 26 Janvier 2026.*
