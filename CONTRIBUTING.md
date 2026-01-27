# Contributing to hAIrem

Merci de contribuer à hAIrem ! Ce document décrit les règles et processus pour participer au développement.

## Workflow de Développement

1.  **Fork & Branch** : Créez une branche pour chaque fonctionnalité ou correctif (`feat/nom-feature` ou `fix/nom-bug`).
2.  **Coding Standards** : Référez-vous impérativement à [Coding Standards](./docs/architecture/coding-standards.md).
    *   Utilisez `ruff` pour le linting.
    *   Utilisez `mypy` pour le typage.
3.  **Tests** : Ajoutez des tests unitaires (`pytest`) pour toute nouvelle logique.

## Environnement Local

Le projet utilise **Poetry** pour la gestion des dépendances.

```bash
# Installation
poetry install

# Activation de l'environnement
poetry shell

# Lancement des tests
pytest
```

## Commit Messages

Nous suivons la convention **Conventional Commits** :

*   `feat: add memory consolidation loop`
*   `fix: resolve redis connection timeout`
*   `docs: update architecture diagram`
*   `refactor: simplify agent perception pipeline`

## Pull Requests

*   Décrivez clairement les changements.
*   Assurez-vous que la CI passe (Lint + Tests).
