# Epic 15: Living Home (Proactive HA)

**Status:** In Definition
**Theme:** Pillar 3 - Deep Home
**PRD Version:** V3

## 1. Vision
L'agent ne se contente plus de piloter la maison sur demande ; il l'habite. Il observe les changements d'état et réagit de manière autonome si cela correspond à sa personnalité ou ses objectifs.

## 2. Objectifs Métier
- **Proactivité Réelle :** Un agent peut intervenir si une lumière reste allumée inutilement ou si la température monte (ex: "Lisa : Il commence à faire chaud, je baisse les stores ?").
- **Conscience Spatiale :** Le système sait dans quelle pièce se trouve l'utilisateur et route l'audio/visuel en conséquence.
- **Identification :** Reconnaissance des différents membres de la famille (Multi-user).

## 3. Exigences Clés
- **Requirement 15.1 (Event Subscription) :** Capacité pour un agent de "s'abonner" à un capteur HA (via `logic.py`).
- **Requirement 15.2 (Spatial Mapping) :** Table de correspondance entre les zones HA et les interfaces hAIrem.
- **Requirement 15.3 (User Discovery) :** Utilisation de la voix ou de la présence Bluetooth pour identifier *qui* parle.

---
*Défini par John (PM) le 26 Janvier 2026.*
