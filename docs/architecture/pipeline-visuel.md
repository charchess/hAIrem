# Pipeline Visuel : Poses & Assets

L'interface A2UI de hAIrem est pilotée par un système de métadonnées visuelles injectées dans les flux narratifs et alimentée par l'imagination proactive (Epic 25).

## 1. Protocole de Poses & Expressions (V4)
Les agents expriment des émotions via une combinaison de bibles visuelles et de tags dynamiques.
- **Bibles Visuelles (`config/visual/`) :**
    - **POSES.yaml :** Basé sur le système FACS (Facial Action Coding System) pour une précision anatomique.
    - **ATTITUDES.yaml :** Basé sur les travaux de Mehrabian pour la kinesthésie et l'orientation corporelle.
- **Format de Message :** Migration vers le type `visual.asset` dans H-Link, incluant l'URL de l'asset détouré (via La Découpeuse).

## 2. Structure des Assets & Imagination
Les assets ne sont plus seulement statiques mais générés dynamiquement ou récupérés du cache sémantique.
- **Volume Partagé :** `/media/generated/` accessible par H-Bridge et A2UI.
- **Détourage :** Tous les personnages (`asset_type: pose`) subissent un détourage automatique via le pipeline `rembg`.

## 3. États Visuels & "The Stage"
L'A2UI (Epic 17) gère dynamiquement l'opacité, le placement et les transitions :
- **Transitions :** Cross-fade matériel pour les fonds (`background`).
- **Overlays :** Assets narratifs temporaires affichés par-dessus la scène.
- **Focus Dynamique :** Mise en avant automatique de l'agent qui "parle" via le message `narrative.text`.

---
