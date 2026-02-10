# 10. Le Social Arbiter (Moteur d'Arbitrage Narratif)

Le Social Arbiter est le composant responsable de la fluidité et de la cohérence de la polyphonie au sein de hAIrem. Il remplace le routage statique par une orchestration basée sur l'intérêt.

## 10.1 Concept : L'Urge-to-Speak (UTS)
Chaque interaction déclenche une évaluation de l'intérêt pour chaque agent via un micro-modèle local (ex: Llama-3.2-1B).

### Le Prompt d'Arbitrage
L'Arbiter reçoit :
- Le dernier message (User ou Agent).
- Le contexte court de la conversation (3 derniers messages).
- Les résumés de persona des agents actifs.

Il doit retourner un score UTS (0.0 à 1.0) par agent.

## 10.2 Workflow d'Arbitrage
1. **Input Interception** : Le message arrive sur le bus Redis.
2. **Scoring Cycle** : L'Arbiter calcule la table d'intérêt.
3. **Selection** : 
    - Si un agent est explicitement nommé : UTS = 1.0.
    - Si plusieurs agents > 0.75 : File d'attente séquentielle (Cascade).
    - Sinon : Seul le score le plus haut parle.
4. **Token de Parole** : Le H-Core envoie une commande d'activation à l'agent choisi.

## 10.3 Gestion de la Polyphonie (Surenchère)
Pour permettre des échanges riches (négociation, dispute) :
- **Re-Scoring** : Après chaque réponse d'agent, l'Arbiter ré-évalue la table.
- **Dynamic Context** : La réponse de l'Agent A est immédiatement disponible pour l'Agent B via le `SocialContext` (Redis).
- **Inhibition** : Un agent ayant parlé reçoit un malus de -0.5 sur son UTS pour le tour suivant (sauf si interpellé).

## 10.4 Optimisations Techniques
- **Modèle Local** : Inférence sur CPU/GPU local pour garantir < 500ms de décision.
- **Agent Summaries** : Stockage en cache Redis des descriptions courtes des agents pour minimiser le contexte de l'Arbiter.

---
*Spécifié par Winston (Architect) le 26 Janvier 2026.*
