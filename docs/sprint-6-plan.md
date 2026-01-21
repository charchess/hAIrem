# Sprint 6 Plan: Text Interaction Layer

**Sprint Goal:** Intégrer une interface de chat hybride à l'A2UI permettant la saisie de texte, la visualisation de l'historique et l'exécution de commandes directes.

## 1. Sprint Commitment
L'objectif est de rendre hAIrem multimodal (Texte + Voix).

| ID | Story Title | Status | Priority |
| --- | --- | --- | --- |
| 6.1 | Zone de saisie texte (Chat Input) | Draft | P0 |
| 6.2 | Historique de conversation | Draft | P0 |
| 6.3 | Slash Commands | Draft | P1 |

## 2. Technical Focus Areas
- **UI Hybridization:** Superposer proprement l'input texte sur le "Stage" sans casser l'immersion Visual Novel.
- **Bi-directional H-Link:** Valider que les messages envoyés par l'utilisateur (`sender: user`) sont correctement traités par le `BaseAgent`.
- **UI State Sync:** S'assurer que les messages envoyés en texte apparaissent instantanément dans l'historique.

## 3. Risk Mitigation
- **Visual Clutter:** Éviter que les bulles de chat ne cachent trop les avatars. Utiliser une opacité variable.
- **Command Injection:** Valider les commandes slash avant de les router vers Redis.

## 4. Definition of Done (DoD)
- [ ] L'utilisateur peut envoyer un message texte et recevoir une réponse en streaming.
- [ ] L'historique affiche les 10 derniers échanges de manière lisible.
- [ ] Les commandes `/slash` pilotent Home Assistant en direct.

## 5. Next Steps
1.  **Story 6.1:** Création de l'input HTML/CSS et branchement au WebSocket.
