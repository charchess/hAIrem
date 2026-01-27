# 11. Use Split Architecture (Core/Bridge)

Date: 2026-01-27

## Status

Accepted

## Context

Dans une architecture conversationnelle temps réel, la stabilité de la connexion utilisateur (WebSocket) est critique. Initialement, le H-Core gérait à la fois la logique cognitive et le serveur web. Un crash du Core (ex: erreur d'inférence, fuite mémoire) entraînait une déconnexion immédiate de l'interface utilisateur (A2UI).

## Decision

Nous séparons l'application en deux services distincts et indépendants :
1.  **H-Bridge** : Un service léger (FastAPI) dédié uniquement à la gestion des WebSockets et de l'interface statique.
2.  **H-Core** : Le moteur cognitif (Python Asyncio pur) qui traite la logique.

La communication entre les deux se fait exclusivement via le bus Redis.

## Consequences

### Positives
*   **Résilience** : Le Core peut redémarrer sans que l'utilisateur ne perde sa session WebSocket sur le Bridge.
*   **Scalabilité** : On peut multiplier les instances du Bridge pour supporter plus d'utilisateurs.
*   **Simplicité** : Le Core est libéré des contraintes d'un serveur Web (Uvicorn/FastAPI).

### Négatives
*   Introduit une latence réseau (minime via Redis) entre les deux services.
*   Complexité opérationnelle accrue (deux Dockerfiles à maintenir).
