# 3. Use Redis for Event Bus

Date: 2026-01-27

## Status

Accepted

## Context

L'architecture est composée de multiples services (`h-core`, `h-bridge`, agents potentiellement distribués) qui doivent communiquer de manière :
*   Asynchrone.
*   Découplée (Le producteur ne connait pas le consommateur).
*   Rapide (Faible latence pour la conversation).

## Decision

Nous utilisons **Redis** (version 7.x) comme bus d'événements Pub/Sub.

## Consequences

### Positives
*   **Simplicité** : Le mécanisme Pub/Sub de Redis est trivial à implémenter.
*   **Performance** : Latence sub-milliseconde.
*   **Ubiquité** : Déjà présent pour le caching si besoin.

### Négatives
*   **Persistance (Pub/Sub)** : Par défaut, le Pub/Sub Redis est "fire and forget". Si un service est down, il rate le message (contrairement à Redis Streams ou RabbitMQ).
    *   *Mitigation* : Pour l'instant acceptable pour du chat éphémère. Pour des tâches critiques, on devra passer à Redis Streams.
