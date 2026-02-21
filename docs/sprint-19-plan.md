# Sprint 19 — "Fondations" · Sécurité, Tests & CI/CD

**Période :** Février 2026  
**Objectif :** Éliminer la dette critique avant toute feature. Zéro secret en clair, tests verts, pipeline automatisé.

---

## Contexte

Sprint 18 visait 47 tests GREEN — l'objectif n'est pas atteint (48 erreurs de collection persistent). Les secrets (API keys) sont en clair dans le repo. Il n'y a aucun pipeline CI/CD. Ce sprint est un pré-requis bloquant pour tout le reste.

**Règle TDD appliquée :** Pour chaque fix/feature → test d'abord (RED) → implémentation (GREEN) → refactor.

---

## Stories

### Story 19.1 — Sécurisation des secrets
**Priorité :** 🚨 CRITIQUE  
**Effort :** S

**Contexte :** `passwords.txt` est versionné en clair. Les API keys dans `.env` ne sont pas chiffrées. Le `VaultService` (Story 25.7) existe mais n'est pas utilisé comme source de vérité.

**Tests à écrire AVANT :**
```
tests/unit/test_secrets.py
- test_passwords_file_not_in_git()         # vérifie .gitignore
- test_env_example_has_no_real_keys()      # .env.example contient uniquement des placeholders
- test_vault_service_encrypt_decrypt()      # round-trip AES-256
- test_vault_service_key_not_in_plaintext() # la clé stockée n'est pas en clair dans SurrealDB
```

**Implémentation :**
1. Ajouter `passwords.txt` et `.env` à `.gitignore` (vérifier qu'ils y sont déjà sinon)
2. Purger l'historique git des secrets (git-filter-repo ou BFG)
3. Brancher `VaultService` sur la lecture des clés LLM au démarrage du `LlmClient`
4. Documenter le pattern dans `docs/architecture/coding-standards.md` (section Secrets)

**DoD :** `passwords.txt` absent du repo, test `test_secrets.py` vert, `.env.example` propre.

---

### Story 19.2 — Réparer la suite de tests (48 erreurs de collection)
**Priorité :** 🔴 HAUTE  
**Effort :** M

**Contexte :** Les tests échouent à la *collection* (avant même de tourner), probablement des imports cycliques ou des chemins cassés suite au découplage h-core/h-bridge du Sprint 18.

**Plan d'action TDD :**
1. Diagnostiquer : `pytest --collect-only 2>&1 | grep ERROR` → catégoriser les erreurs
2. Pour chaque catégorie d'erreur → écrire un test minimal qui reproduit l'import cassé
3. Fixer l'import → test vert → passer au suivant

**Fixes attendus :**
- Harmoniser les `sys.path` dans les tests (utiliser `conftest.py` central)
- Créer `apps/h-core/tests/conftest.py` robuste avec fixtures partagées (mock Redis, mock SurrealDB, mock LLM)
- Ajouter `pyproject.toml` avec `[tool.pytest.ini_options]` pour `testpaths` et `pythonpath`

**DoD :** `pytest apps/h-core/tests/` → 0 erreur de collection, ≥ 80% des tests GREEN.

---

### Story 19.3 — Pipeline CI/CD GitHub Actions
**Priorité :** 🔴 HAUTE  
**Effort :** S

**Implémentation :**
```yaml
# .github/workflows/ci.yml
jobs:
  test:
    - Lint: ruff check .
    - Type check: mypy apps/h-core/src
    - Tests unitaires: pytest apps/h-core/tests/unit/ --cov
    - Tests intégration (avec services Docker): pytest apps/h-core/tests/integration/
  docker-build:
    - docker compose build (smoke test)
```

**Tests à écrire :**
```
tests/unit/test_ci_smoke.py
- test_imports_clean()       # tous les modules s'importent sans erreur
- test_ruff_passes()         # pas de violations lint
```

**DoD :** Chaque push sur `main` déclenche le pipeline. Badge status dans README.

---

### Story 19.4 — Documentation des standards de test
**Priorité :** 🟡 MOYENNE  
**Effort :** XS

**Livrable :** `docs/architecture/testing-standards.md`
- Pattern mock Redis/SurrealDB/LLM
- Convention nommage fichiers test
- Comment écrire un test TDD pour un agent
- Fixtures partagées disponibles

---
