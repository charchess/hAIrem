# Sprint 4 Plan: External Brain & Creativity

**Sprint Goal:** Connecter les agents à une intelligence générative (LLM) et permettre des conversations fluides en temps réel via streaming.

## 1. Sprint Commitment
Transformer le perroquet (A2UI) en penseur.

| ID | Story Title | Status | Priority |
| --- | --- | --- | --- |
| 4.1 | Client API LLM (OpenAI-compatible) | Ready for Dev | P0 |
| 4.2 | Gestion du Streaming de réponse texte | Ready for Dev | P0 |
| 4.3 | Injection du Contexte et Prompting | Ready for Dev | P1 |

## 2. Technical Focus Areas
- **Async Streaming:** Le pipeline `LLM -> H-Core -> Redis -> WebSocket -> A2UI` doit être non-bloquant et gérer le flux token par token.
- **Provider Agnosticism:** Le client doit pouvoir parler à OpenAI, Groq, ou Ollama (local) sans changer de code, juste de config.
- **Latency minimization:** Le premier token doit arriver à l'écran < 500ms.

## 3. Risk Mitigation
- **Cost/Quota:** Gérer les limites de rate-limit des API.
- **Hallucinations:** Le prompt système doit être robuste pour empêcher l'agent de sortir de son rôle ("Tu es la Renarde...").

## 4. Definition of Done (DoD)
- [ ] Une question posée via H-Link déclenche une réponse générée par un LLM.
- [ ] Le texte s'affiche progressivement sur l'interface A2UI.
- [ ] L'agent respecte sa personnalité définie dans le YAML.

## 5. Next Steps
1.  **Story 4.1:** Implémenter le client `LlmClient` dans `h-core`.
