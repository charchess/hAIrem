# Architecture Design: Observability & Debug (Transparent Mind)

**Version:** 1.0
**Status:** In Definition
**Author:** Winston (Architect)
**Date:** 2026-01-28

---

## 1. Introduction

James (Dev) et Quinn (QA) ont besoin d'outils pour auditer le comportement des agents. Contrairement à un logiciel classique, hAIrem est probabiliste. L'observabilité doit donc capturer le "cheminement de pensée".

## 2. Le Flux "Transparent Mind"

Chaque étape de la cognition d'un agent doit être diffusée sur un canal Redis dédié (`hairem:debug:mind`).

### 2.1 Événements Audités
- **Stimulus Interception :** Quel stimulus a été reçu ? (Niveau 0-3).
- **Arbiter Scoring :** Pourquoi cet agent a-t-il été choisi ? (Scores de pertinence).
- **Raw Prompts :** Le prompt exact envoyé au LLM (incluant le contexte injecté).
- **Internal Monologue :** Si l'agent utilise une étape de "Chain of Thought" (CoT) avant de répondre.
- **Visual Decisions :** Pourquoi telle tenue ou tel background a été choisi ?

## 3. Interfaces de Debug

### 3.1 La Console A2UI (Hidden Layer)
Une vue "Developer" dans l'A2UI permet d'afficher en temps réel :
- Le log `visual.raw_prompt`.
- Les scores du Social Arbiter sous forme de graphique à barres.
- Le statut des bourses de mémoire (Burning vs Long Term).

### 3.2 Master Regression Suite
Pour Quinn, le script `master_regression_v3.py` doit être capable de :
1. **Injecter des stimuli** contrôlés.
2. **Vérifier les sorties** non seulement sur le texte, mais sur les métadonnées (ex: l'agent X doit répondre avec une émotion "Angry" si on lui vole son asset).

## 4. Tracing des Assets

...

## 5. Le "Cognition Playground" (Shadow Mode)

Pour permettre à James et Quinn de tester des scénarios complexes (ex: le passage au thème de Noël) sans corrompre la "Burning Memory" ou les relations réelles des agents :

- **Shadow Context :** Possibilité de lancer une session avec un flag `--shadow`. 
- **Isolation :** Dans ce mode, les interactions sont traitées normalement par le LLM et les services d'imagerie, mais les résultats ne sont **pas persistés** dans la table long-terme de SurrealDB.
- **Theme Injection :** Permet d'injecter un `world_state` arbitraire pour vérifier la cohérence des prompts et des tenues générées avant un déploiement "live".
