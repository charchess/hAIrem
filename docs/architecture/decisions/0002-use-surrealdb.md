# 2. Use SurrealDB for Cognitive Memory

Date: 2026-01-27

## Status

Accepted

## Context

Le projet hAIrem nécessite un stockage de "mémoire subjective" complexe pour les agents.
Les besoins incluent :
*   Relations complexes entre entités (Qui connait qui ? Qui a fait quoi ?).
*   Structure de données flexible (Schémas évolutifs).
*   Temps réel (Live queries pour la réactivité).
*   Besoin de stocker des vecteurs (pour le RAG/Embeddings à terme).

Les bases SQL traditionnelles (Postgres) demandent trop de "joins" rigides. Les bases NoSQL pures (Mongo) manquent de relations fortes.

## Decision

Nous utilisons **SurrealDB**.

*   **Mode** : Single node (via Docker) pour le dev/MVP.
*   **Utilisation** : Graph database + Document store.

## Consequences

### Positives
*   **Modélisation cognitive** : Les relations "graph" (edges) correspondent parfaitement à la mémoire associative d'une IA.
*   **Performance** : Moins de joins coûteux au niveau applicatif.
*   **Simplification** : Une seule DB pour le structuré, le non-structuré et (potentiellement) les vecteurs.

### Négatives
*   **Maturité** : SurrealDB est plus récent que Postgres, communauté plus petite.
*   **Tooling** : Moins d'outils d'ORM matures en Python (on utilise souvent le driver raw ou des wrappers légers).
