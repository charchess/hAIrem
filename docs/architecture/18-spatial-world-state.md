# Architecture Design: Spatial Architecture & World State

**Version:** 1.0
**Status:** In Definition
**Author:** Winston (Architect)
**Date:** 2026-01-28

---

## 1. Introduction

hAIrem supporte une existence multi-site. Les agents peuvent résider dans des lieux physiques différents (Cuisine, Bureau) tout en partageant une conscience collective et un environnement temporel commun (Saisons, Événements).

## 2. Spatial Registry (Le Registre des Lieux)

Le système maintient une table `location` dans SurrealDB pour segmenter les environnements visuels.

```surrealql
DEFINE TABLE location SCHEMAFULL;
DEFINE FIELD name ON TABLE location TYPE string; -- ex: 'Cuisine', 'Bureau'
DEFINE FIELD master_background ON TABLE location TYPE string; -- Image de référence vide
DEFINE FIELD active_background ON TABLE location TYPE string; -- Image actuellement affichée
```

### 2.1 Présence des Agents
Chaque agent a un champ `current_location` pointant vers un record `location`.
- **Note Architecturale :** La présence est visuelle. Un agent "résidant" en cuisine est affiché sur le client de la cuisine, mais son "écoute" (Redis Bus) est globale.

## 3. World State (L'État du Monde)

Un singleton `world_state` gère les variables globales injectées par Entropy (Dieu).
- **Theme :** `neutral`, `christmas`, `party`, `night_mode`.
- **Atmosphere :** `calm`, `tense`, `festive`.
- **Weather :** Synchronisé avec Home Assistant.

## 4. Le Flux de Transformation Thématique (ex: Noël)

Lorsqu'un changement de thème est amorcé par Dieu :

1. **Propagation du Contexte :** Le `world_state` est mis à jour.
2. **Ré-imagination des Lieux :** 
   - Pour chaque `location`, le `VisualImaginationService` génère une variation du `master_background` incluant le thème (ex: sapin, neige).
   - L'A2UI reçoit un message `visual.asset` avec une transition `cross-fade` pour mettre à jour le décor.
3. **Réaction des Personas :** 
   - Un stimulus narratif de niveau 2 (Whisper) est envoyé aux agents.
   - Les agents consultent leur `Character Vault` (Garde-robe) pour trouver une tenue compatible avec le thème.
   - Si trouvée, l'agent publie son changement de tenue.

## 5. Multi-Client Routing (H-Bridge)

Le H-Bridge utilise le `client_id` pour filtrer les flux :
- **Audio/Texte :** Broadcast global (tout le monde entend tout).
- **Visual (Background/Poses) :** Routage sélectif. Le client "Cuisine" ne reçoit que les mises à jour des agents présents en `location:cuisine`.

---
🏗️ Winston - Architecte hAIrem
