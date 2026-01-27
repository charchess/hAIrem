# Epic 23: H-Core Refactoring (HLinkBridge & Resilience)

**Status:** Done
**Theme:** Infrastructure & Résilience
**PRD Version:** V3

## 1. Vision
Passer d'une architecture monolithique (où le backend gère tout dans un seul fichier) à une architecture de micro-services découplés par le bus Redis. L'objectif est de séparer l'interface (WebSocket) de l'intelligence (Agents/Orchestrateur) pour garantir une résilience maximale.

## 2. Objectifs Métier
- **Résilience Interface :** Si un agent ou le moteur cognitif crashe, l'interface utilisateur (WebSocket) doit rester connectée et fonctionnelle.
- **Scalabilité :** Permettre le déploiement de plusieurs instances du Bridge pour supporter plus de clients sans multiplier les instances d'agents.
- **Maintenance Facilitée :** Isoler le code de transport (WebSocket/JSON) du code métier (IA/Cognition).

## 3. Exigences Clés (Requirements)
- **Requirement 23.1 (HLinkBridge Standalone) :** Créer un nouveau service dédié uniquement à la gestion des WebSockets et à la livraison des fichiers statiques A2UI.
- **Requirement 23.2 (Redis Handshake) :** Le Bridge doit agir comme un traducteur pur : WebSocket JSON -> H-Link Redis et vice-versa.
- **Requirement 23.3 (Core Extraction) :** Le H-Core ne doit plus avoir de dépendances FastAPI/Uvicorn. Il devient un daemon Python pur qui écoute le bus Redis.
- **Requirement 23.4 (Heartbeat) :** Implémenter un système de pulsation (heartbeat) pour que l'A2UI sache en temps réel si le Core est vivant, indépendamment de la connexion WebSocket.

## 4. Métriques de Succès
- Crash simulé du service H-Core -> L'A2UI affiche "Core Offline" mais ne se déconnecte pas.
- Redémarrage du H-Core -> La communication reprend instantanément sans rafraîchir la page (F5).

---
*Défini par John (PM) le 26 Janvier 2026.*
