# Sprint 1 Plan: Foundation & H-Core

**Sprint Goal:** Établir l'infrastructure de base (Monorepo, Bus Redis, Plugin Loader) pour permettre la communication entre agents et l'évolutivité du système.

## 1. Sprint Commitment
Nous nous engageons sur l'intégralité de l'**Epic 1**, car ces composants sont indissociables pour obtenir un système minimal fonctionnel.

| ID | Story Title | Status | Priority |
| --- | --- | --- | --- |
| 1.1 | Initialiser le repo Monorepo | Approved | P0 |
| 1.2 | Configurer le Bus Redis | Ready for Dev | P0 |
| 1.3 | Implémenter le chargeur de plugins | Ready for Dev | P0 |

## 2. Technical Focus Areas
- **Monorepo Architecture:** Garantir une séparation nette entre le H-Core (Python) et l'A2UI (Frontend).
- **Asynchronicité:** Valider que Redis Pub/Sub fonctionne correctement en mode asynchrone avec FastAPI.
- **Dynamisme:** S'assurer que le Hot-Reload des agents est robuste.

## 3. Risk Mitigation (From QA Quinn)
- **Redis SPOF:** Implémentation d'une reconnexion automatique.
- **YAML Stability:** Validation stricte du schéma `expert.yaml` pour éviter les crashs au chargement.

## 4. Definition of Done (DoD)
- [ ] Code produit selon les Coding Standards.
- [ ] Tests unitaires et d'intégration passants (100% P0).
- [ ] Linting (Ruff) sans erreur.
- [ ] Documentation mise à jour.
- [ ] Revue par l'Architecte (Winston) et le QA (Quinn).

## 5. Next Steps
1.  **Story 1.1 Execution:** Initialisation physique du repo par le Dev.
2.  **Daily Sync:** Suivi des obstacles techniques sur Redis.
