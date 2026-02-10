# Sprint 9 Plan: Deep Cognition & Living Stage

**Sprint Goal:** Transformer hAIrem en une entité "vivante" par l'injection proactive de mémoire et une interface tactile "High-Fi".

## 1. Sprint Commitment

| ID | Story Title | Status | Priority |
| --- | --- | --- | --- |
| 15.4 | Spatial Zone Registry & Routing Logic | Done ✅ | P0 |
| 14.5 | Neural Voice Assignment (Piper) | Done ✅ | P1 |
| 13.5 | Automatic Context Enrichment | Ready for Dev ✅ | P0 |
| 17.5 | Agent Detail View (Deep Dive UI) | Ready for Dev ✅ | P1 |
| 18.1 | Social Referee (Arbitrage LLM local) | Draft 📝 | P1 |

## 2. Technical Focus Areas
- **Cognitive Intuition (13.5):** Injection automatique des faits SurrealDB dans le prompt `system`.
- **Tactile UI (17.5):** Implémentation du design "Cyber-Cozy" et visualisation de la force des croyances.
- **Social Arbitration (18.1):** Utilisation d'un LLM local ultra-rapide pour gérer la polyphonie.

## 2. Technical Focus Areas
- **Spatial Awareness:** Mapper les containers hAIrem aux zones physiques de Home Assistant.
- **Vocal Identity:** Associer des voix synthétiques uniques à l'ADN visuel de chaque agent.
- **Contextual Recall:** S'assurer que les faits stockés en mémoire SurrealDB influencent réellement le prompt LLM.

## 3. Risk Mitigation
- **Routing Loop:** Éviter qu'un message ne soit diffusé sur trop de terminaux simultanément (Bruit).
- **TTS Latency:** Optimiser le temps de génération de la voix pour rester sous les 1.2s.
- **Memory Noise:** Filtrer les faits non-pertinents lors de l'injection dans le contexte LLM.

## 4. Definition of Done (DoD)
- [ ] Le système peut identifier dans quelle pièce se trouve l'utilisateur (via un capteur de présence simulé ou réel).
- [ ] Un message peut être adressé à une pièce spécifique dans le payload `Recipient`.
- [ ] Lisa, Electra et Renarde ont chacune une voix distincte et fonctionnelle.
- [ ] L'agent utilise au moins un fait passé lors d'une conversation de test.

## 5. Next Steps
1. **Story 15.4:** Développement du registre de zones spatiales.
2. **Story 14.5:** Configuration du client TTS unifié.
