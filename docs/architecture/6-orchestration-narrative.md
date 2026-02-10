# 6. Orchestration Narrative & Autonomie

L'orchestration narrative définit comment les agents interagissent entre eux et avec l'environnement pour créer une expérience cohérente et vivante.

## 6.1 Cycle de Sommeil (Consolidation Cognitive)
Le système ne reste pas statique. Il simule un cycle circadien via le **MemoryConsolidator**.
- **Trigger :** Déclenché par l'inactivité ou une commande système.
- **Processus :**
    1. Analyse des messages récents non traités.
    2. Extraction de faits atomiques (LLM).
    3. Résolution de conflits (Dialectique).
    4. Migration vers le Graphe de connaissance.
- **Résultat :** Le système "apprend" et stabilise ses connaissances pendant ses phases de repos.

## 6.2 Proactivité & Chaos (Dieu/Entropy)
hAIrem n'attend pas toujours une commande utilisateur.
- **Entropy Agent :** Un agent spécial ("Dieu") peut injecter des "Whispers" (pensées internes) aux autres agents.
- **Triggers Proactifs :** Basés sur des événements Home Assistant (ex: "Il fait nuit") ou le passage du temps.
- **Whisper Protocol :** Message de type `system.whisper` envoyé sur le channel privé d'un agent pour influencer son prochain comportement sans que l'utilisateur ne le voie.

## 6.3 Collaboration Inter-Agents (Internal Notes)
Les agents peuvent communiquer entre eux "en coulisses" via des **Internal Notes**.
- **Usage :** Lisa demande à l'Expert Domotique l'état d'une lampe avant de répondre à l'utilisateur.
- **Type :** `AGENT_INTERNAL_NOTE`.
- **Visibilité :** Ces notes sont injectées dans le contexte LLM des agents concernés mais ne sont jamais affichées sur l'A2UI.

## 6.5 La Polyphonie Émergente (Social Arbiter)
Pour permettre une interaction naturelle entre plusieurs agents sans chaos, hAIrem utilise un modèle d'arbitrage social.

### Le Mécanisme "Urge-to-Speak"
Au lieu d'un routage statique, chaque message (utilisateur ou agent) déclenche une micro-inférence locale via le **Social Arbiter**.
1. **Scoring :** Un modèle LLM ultra-léger (1B) évalue l'intérêt de chaque agent en fonction du message et de son "Persona Summary".
2. **Table d'Intérêt :** L'Arbiter produit une liste de scores (0.0 à 1.0).
3. **Activation :** Seuls les agents dépassant un seuil (ex: 0.75) entrent dans la file d'attente de réponse.
4. **Priorisation :** L'agent au score le plus élevé prend la parole en premier.

### Interaction Inter-Agents (La Dispute)
Après chaque intervention d'un agent, le cycle de scoring est relancé.
- Un agent peut réagir à ce qu'un autre vient de dire si son score d'intérêt bondit (ex: contradiction technique ou insulte narrative).
- **Repetition Penalty :** Un agent ayant déjà parlé subit un malus de -0.5 sur son score pour le tour suivant afin de favoriser la diversité.

### Limites de Conversation (Budget de Parole)
Pour éviter les boucles infinies et la consommation excessive de tokens :
- Chaque interaction utilisateur ouvre une "Session Narrative" limitée à **5 échanges inter-agents**.
- Un agent "Animateur" (ex: Lisa) force la synthèse finale une fois le budget épuisé.

---
