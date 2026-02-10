# 5. Use Poetry for Dependency Management

Date: 2026-01-27

## Status

Accepted

## Context

La gestion des dépendances en Python peut devenir chaotique (pip freeze, requirements.txt, conflits de versions).
Nous avons besoin de :
*   Builds reproductibles.
*   Gestion des environnements virtuels simplifiée.
*   Résolution de dépendances stricte.

## Decision

Nous utilisons **Poetry**.

## Consequences

### Positives
*   **Lockfile** : `poetry.lock` garantit que tout le monde a *exactement* les mêmes versions.
*   **DX** : Commandes simples (`poetry add`, `poetry run`).
*   **Packaging** : Facilite la création de packages si besoin.

### Négatives
*   Courbe d'apprentissage légère par rapport à `pip`.
*   Parfois lent sur la résolution de dépendances complexes (bien que amélioré en v1.8+).
