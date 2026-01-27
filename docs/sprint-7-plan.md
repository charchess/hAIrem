# Sprint 7 Plan: Intelligence & Embodiment

**Sprint Goal:** Rendre hAIrem réellement "pluggable" en permettant des scripts Python par agent, activer le contrôle réel de Home Assistant pour l'Expert, et finaliser l'identité visuelle de la flotte.

## 1. Sprint Commitment
Passer du chatbot à l'OS de maison intelligent et incarné.

| ID | Story Title | Status | Priority |
| --- | --- | --- | --- |
| 5.4 | Custom Python Logic Loader (Pluggability) | Approved | P0 |
| 5.5 | Expert-Domotique HA Integration | Draft | P0 |
| 11.5 | Multi-Agent Presence (Assets & Non-Personified) | Draft | P1 |
| 11.6 | Real-time Asset Generation Tool (Research) | Draft | P2 |

## 2. Technical Focus Areas
- **Dynamic Importing:** Sécuriser et fiabiliser le chargement des classes `logic.py` par le `PluginLoader`.
- **Action Loop Validation:** S'assurer que les outils HA rapportent correctement les erreurs en langage naturel.
- **Visual Consistency:** Harmoniser les styles de Lisa et de l'Expert avec celui de la Renarde.

## 3. Risk Mitigation
- **Module Collisions:** Utiliser des espaces de noms uniques lors du chargement dynamique des scripts Python.
- **HA Latency:** Gérer les timeouts si Home Assistant ne répond pas assez vite.
- **Asset Quality:** Vérifier que le pipeline `rembg` ne dégrade pas les nouveaux assets générés.

## 4. Definition of Done (DoD)
- [ ] N'importe quel agent peut porter un script `logic.py` chargé dynamiquement.
- [ ] L'Expert-Domotique peut allumer une lampe ou lire un capteur via HA.
- [ ] Dieu ne génère plus d'erreurs 404 (non-personnifié).
- [ ] Lisa et l'Expert ont leurs 10 expressions fonctionnelles.

## 5. Next Steps
1. **Story 5.4:** Développement du chargeur de logique Python.
