# 12. Use Containerization and Automated Pipeline for CI/CD

Date: 2026-01-27

## Status

Accepted

## Context

Pour garantir que hAIrem fonctionne de manière identique sur toutes les machines (dev, serveurs, cloud) et pour assurer une qualité constante, nous avons besoin d'un environnement reproductible et d'une validation systématique de chaque changement.

## Decision

1.  **Docker** : Toutes les briques (Core, Bridge, DB, Redis) sont conteneurisées.
2.  **GitHub Actions** : Utilisation de GHA pour automatiser le cycle de vie (Lint -> Test -> Build).

## Consequences

### Positives
*   **Reproductibilité** : "It works on my machine" n'existe plus grâce à Docker Compose.
*   **Sécurité** : Scan systématique des secrets (Gitleaks) en CI.
*   **Confiance** : Les tests de régression (`master_regression_v3.py`) sont obligatoires avant tout déploiement.

### Négatives
*   Temps de build initial en CI.
*   Nécessite une gestion rigoureuse des volumes pour la persistance des données.
