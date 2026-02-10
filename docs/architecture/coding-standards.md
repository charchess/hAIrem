# Coding Standards & Guidelines

## 1. Principes Généraux
*   **Isolation Stricte** : Les modules ne doivent pas avoir de dépendances circulaires ni d'imports système implicites.
*   **Asynchronicité** : Tout code effectuant des opérations I/O (réseau, base de données, fichiers) DOIT être asynchrone (`async`/`await`).
*   **Immuabilité** : Les faits bruts dans le système cognitif sont immuables.

## 2. Style de Code (Python)
*   **Linter** : Nous utilisons `ruff`.
*   **Formatage** :
    *   Longueur de ligne : **120 caractères** (configuré dans `pyproject.toml`).
    *   Respect de la PEP 8.
*   **Typage** : Les annotations de type (Type Hinting) sont **obligatoires** pour toutes les signatures de fonctions et méthodes publiques.
    *   Utiliser `mypy` pour la validation statique.

## 3. Documentation
*   **Docstrings** : Obligatoires pour les modules, classes et fonctions publiques (format Google ou NumPy).
*   **Commentaires** : Expliquer le *POURQUOI*, pas le *COMMENT*.

## 4. Tests
*   Framework : `pytest`.
*   Les tests doivent être indépendants et reproductibles.

## 5. Gestion des Erreurs
*   Utiliser des exceptions typées et explicites.
*   Ne jamais utiliser de `except Exception:` passif sans logging.
