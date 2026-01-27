# Pipeline Visuel : Poses & Assets

L'interface A2UI de hAIrem est pilotée par un système de métadonnées visuelles injectées dans les flux narratifs.

## 1. Protocole de Poses
Les agents peuvent exprimer des émotions via des tags de pose insérés dans leur texte.
- **Format :** `[pose:nom_de_la_pose]`
- **Heuristique :** Le `Renderer` (JS) extrait ces tags via regex, les supprime du texte affiché et déclenche un changement d'image.

### Mapping des Poses
Le `Renderer` utilise un `poseMap` pour mapper les émotions LLM (souvent variées) vers un set d'assets fixes :
- `thinking`, `pensive` → `thinking`
- `happy`, `smile`, `joy` → `happy`
- `shy`, `blush`, `seductive` → `shy`
- `glitch`, `error` → `glitch`

## 2. Structure des Assets
Les assets sont organisés par agent dans `/public/assets/agents/{agent_id}/`.
- Convention de nommage : `{agent_id}_{pose}_{variante}.png`
- Exemple : `lisa_happy_01.png`

## 3. États Visuels (V3)
À terme, le système doit migrer vers un champ `visual_state` dédié dans le payload `HLinkMessage` pour éviter de polluer le texte avec des tags techniques.

### Gestion du Focus
L'A2UI gère dynamiquement l'opacité et la mise en avant des agents sur le "Stage" en fonction de qui est l'émetteur du dernier message `narrative.text`.

---
