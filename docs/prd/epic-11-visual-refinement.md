# Epic 11: Expressive Embodiment & Visual Refinement

**Status:** Done (Retro-documented)
**Theme:** Identité Visuelle & Poses
**PRD Version:** V2.5

## 1. Vision
Transformer les placeholders génériques en avatars expressifs capables de réagir émotionnellement aux dialogues, renforçant l'immersion dans l'A2UI.

## 2. Objectifs Métier
- **Émotionnalité :** Mapper les poses des agents sur le framework émotionnel de Paul Ekman.
- **Réactivité :** Déclencher automatiquement les changements de poses via le texte narratif.
- **Présence Multiple :** Supporter l'affichage et la gestion de plusieurs agents sur le "Stage".

## 3. Exigences Clés
- **Requirement 11.1 (Expression Mapping) :** Définition du set de poses (Happy, Sad, Angry, etc.).
- **Requirement 11.2 (Pose Triggering) :** Implémentation du protocole `[pose:X]` dans le renderer.
- **Requirement 11.3 (Asset Pipeline) :** Organisation et chargement dynamique des assets PNG par agent.
