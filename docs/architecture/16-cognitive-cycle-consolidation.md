# Architecture Design: Cognitive Cycle & Consolidation

**Version:** 1.0
**Status:** In Definition
**Author:** Winston (Architect)
**Date:** 2026-01-28

---

## 1. Introduction

hAIrem ne se contente pas de réagir ; il traite l'information de manière cyclique. Ce document définit les états de conscience des agents et le processus de transfert de données de la mémoire volatile (Redis/Context) vers la mémoire permanente (SurrealDB).

## 2. Le Cycle de Vie Quotidien

### 2.1 État : Veille (Active)
- **Mémoire de Travail :** Historique récent (fenêtre de 20 messages) maintenu dans le contexte LLM.
- **Burning Memory :** Registre d'état immédiat (tenue, lieu, météo actuelle).
- **Interactions :** Réponse immédiate aux stimuli de niveau 0 (HA) et 1 (Narratif).

### 2.2 État : Sommeil (Maintenance)
Déclenché par une inactivité prolongée ou une commande spécifique ("Bonne nuit").
- **Le Dreamer (Entropy) :** Génération de stimuli subconscients (idées parasites) pour préparer les interactions du lendemain.
- **Imagination Nocturne :** Génération proactive des décors (Backgrounds) pour le prochain cycle météo via le `VisualImaginationService`.

## 3. Mécanisme de Consolidation (L'Oubli et le Souvenir)

La consolidation est une tâche de fond qui nettoie la base de données et renforce les connexions sémantiques.

### 3.1 Passage au Graphe Long Terme
1. **Extraction :** Le Core analyse les logs de conversation de la journée.
2. **Synthèse :** Un LLM (micro) extrait les faits saillants, les préférences utilisateur et les changements de relations.
3. **Persistance :** Création/Mise à jour des records dans SurrealDB :
   - Table `fact` : Données objectives.
   - Table `interpretation` : Vision subjective de l'agent.
   - Edges `TRUSTS/LIKES` : Mise à jour des poids des relations sociales.

### 3.2 Purge & LRU Cache
- **Fichiers :** Le Garbage Collector scanne `/media/generated` et supprime les fichiers les plus anciens (Last Recently Used) si le quota (2Go) est atteint.
- **Index DB :** L'indexation sémantique (Embeddings) est conservée même si le fichier physique est supprimé, permettant une régénération à l'identique si nécessaire.

---
🏗️ Winston - Architecte hAIrem
