# hAIrem Test Framework

Initialisé via le module BMad TEA (Test Architect).

## Architecture
- **Framework** : Playwright (TypeScript)
- **Structure** :
  - `tests/e2e/` : Tests de bout en bout et d'intégration
  - `tests/support/fixtures/` : Fixtures composables
  - `tests/support/helpers/` : Utilitaires et clients API

## Commandes
- `npm run test:e2e` : Lancer tous les tests en mode headless
- `npx playwright test --headed` : Lancer les tests en mode graphique
- `npx playwright test --debug` : Lancer le debugger Playwright

## Bonnes Pratiques
- Utiliser les sélecteurs `data-testid`.
- Maintenir l'isolation des tests (pas de partage d'état global).
- Chaque test doit être déterministe (pas de waits arbitraires).
