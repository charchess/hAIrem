# Architecture Design: Rendering Layers & GPU Concurrency

**Version:** 1.0
**Status:** In Definition
**Author:** Winston (Architect)
**Date:** 2026-01-28

---

## 1. Stratégie de Rendu Hybride

Pour éviter les incohérences spatiales (ex: un sapin sur une plaque de cuisson), le système adopte une approche hybride :

### 1.1 Le Fond Thématique (Baking)
Lors d'un changement de `World State` (ex: passage à Noël), le système ne "superpose" pas d'images. Il procède à une **Régénération Structurée** du décor :
- **Entrée :** `Master Reference` du lieu + `World State Theme`.
- **Technique :** Utilisation de **ControlNet** (Depth ou Canny) pour conserver la structure physique (murs, meubles) tout en ré-imaginant les textures et les objets décoratifs (sapins, guirlandes) de manière cohérente avec l'éclairage et la perspective.
- **Résultat :** Un nouveau `active_background` statique, utilisé comme base de rendu jusqu'au prochain changement de thème.

### 1.2 Le Layering Dynamique (Real-time)
Seuls les éléments changeant fréquemment sont gérés en calques au-dessus du `active_background` :
- **Agent Layer :** Personnages détourés via "La Découpeuse".
- **Overlay FX :** Effets atmosphériques (particules de neige, lueurs, filtres de couleur).

## 2. Intelligence Spatiale (Semantic Masks)
Pour guider la régénération, chaque `Master Reference` peut être associée à un **Masque de Décoration** (Inpainting Mask) définissant les zones "sûres" pour l'ajout d'objets proactifs (ex: le sol, les étagères) et les zones "exclues" (ex: plaques de cuisson, évier).

## 2. Orchestration de l'Inference (GPU Queue)

Le `VisualImaginationService` doit implémenter un gestionnaire de priorité pour les appels aux modèles (LLM, Stable Diffusion, Rembg).

### 2.1 Priorités de Génération
- **P0 (Interaction Live) :** Réponse immédiate d'un agent à l'utilisateur.
- **P1 (Proactivité Immédiate) :** Changement de tenue suite à un événement HA.
- **P2 (World State Update) :** Mise à jour des décors suite à un changement de thème global.
- **P3 (Background/Dreamer) :** Imagination nocturne, pré-calcul pour le lendemain.

### 2.2 Mécanisme de Verrouillage
Un `InferenceLock` (via Redis) empêche le système de lancer plus de N générations simultanées (N dépendant de la VRAM disponible), évitant les crashs `Out of Memory (OOM)`.

## 3. État d'Implémentation

| Composant | Statut | Fichier |
|-----------|--------|---------|
| **InferenceLock** (Redis) | ✅ Implémenté | `services/visual/inference_lock.py` |
| **GPUQueue** (asyncio) | ✅ Disponible | `services/visual/gpu_queue.py` |
| **ControlNet** (depth/canny) | ❌ Backlog | — Requiert modèle ControlNet local |
| **Semantic Masks / Inpainting** | ❌ Backlog | — Requiert pipeline ComfyUI/A1111 |

L'InferenceLock est actif dans `VisualImaginationService.generate_for_agent()`. Le GPUQueue est disponible comme utilitaire pour les déploiements nécessitant une file d'attente inter-processus.

---
🏗️ Winston - Architecte hAIrem
