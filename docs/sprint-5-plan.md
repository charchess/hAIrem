# Sprint 5 Plan: Home Automation Bridge

**Sprint Goal:** Connecter hAIrem à Home Assistant pour permettre aux agents de lire l'état de la maison et d'exécuter des actions concrètes (lumières, interrupteurs, etc.).

## 1. Sprint Commitment
Donner des "mains" à nos agents.

| ID | Story Title | Status | Priority |
| --- | --- | --- | --- |
| 5.1 | Client WebSocket/REST Home Assistant | Ready for Dev | P0 |
| 5.2 | Exposition des outils HA au LLM (Function Calling) | Ready for Dev | P0 |
| 5.3 | Boucle d'action réelle (Command -> HA -> Response) | Ready for Dev | P0 |

## 2. Technical Focus Areas
- **Reliable Connectivity:** Gérer l'authentification (Long-Lived Access Token) et la reconnexion au bus de Home Assistant.
- **Tool Discovery:** Comment mapper automatiquement les entités HA en "Tools" compréhensibles par le LLM.
- **Safety:** S'assurer que seules les commandes validées par l'Expert sont exécutées.

## 3. Risk Mitigation
- **Security:** Ne jamais stocker le token HA en dur (Variables d'environnement uniquement).
- **Latency:** Les appels HA ne doivent pas bloquer la boucle de dialogue.
- **Unintended Actions:** L'agent doit confirmer les actions critiques (ex: ouvrir la porte).

## 4. Definition of Done (DoD)
- [ ] Le H-Core est connecté à une instance Home Assistant.
- [ ] L'Expert-Domotique peut rapporter l'état d'une lampe.
- [ ] Une commande vocale/texte ("Allume le salon") est exécutée physiquement sur HA.
- [ ] Le résultat de l'action est renvoyé à la Renarde pour confirmation narrative.

## 5. Next Steps
1. **Story 5.1:** Mise en place du client technique HA.
