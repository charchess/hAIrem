# 4. Use FastAPI for Core Services

Date: 2026-01-27

## Status

Accepted

## Context

Nous développons des services backend en Python (`h-core`, `h-bridge`).
Les contraintes sont :
*   **Asynchrone (I/O Bound)** : Beaucoup d'appels LLM, DB, Redis en attente.
*   **Typage** : Besoin de robustesse et d'autocomplétion.
*   **Performance**.

## Decision

Nous utilisons **FastAPI**.

## Consequences

### Positives
*   **Async natif** : Parfait pour orchestrer des appels LLM/DB non bloquants.
*   **Pydantic** : Validation des données (entrées/sorties) robuste et intégrée.
*   **Doc auto** : Swagger/OpenAPI généré automatiquement pour le `h-bridge`.

### Négatives
*   Nécessite une bonne compréhension de l'event loop Python (`asyncio`).
