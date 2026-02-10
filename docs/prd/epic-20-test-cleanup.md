# Epic 20: Test Infrastructure Cleanup & Hygiène

**Status:** Done
**Theme:** Qualité & Maintenabilité
**PRD Version:** V3

## 1. Vision
Garantir que la suite de tests automatisée est un outil de confiance et non une source de confusion. L'objectif est de supprimer ou mettre à jour tous les tests obsolètes (legacy) pour atteindre un état "100% Green" sur l'ensemble de la codebase.

## 2. Objectifs Métier
- **Fiabilité de la CI/CD :** Pouvoir automatiser les déploiements en sachant que si les tests passent, le système est sain.
- **Productivité Dev :** Éviter que les développeurs perdent du temps à analyser des échecs de tests qui ne sont plus pertinents.
- **Documentation par le Test :** Faire en sorte que les tests reflètent l'état actuel de l'architecture (ex: signatures de BaseAgent et SurrealDB).

## 3. Exigences Clés
- **Requirement 20.1 (Legacy Audit) :** Identifier précisément les 13 tests en échec et décider pour chacun : mise à jour (si la logique est encore utile) ou suppression (si le test est devenu caduc).
- **Requirement 20.2 (Signature Alignment) :** Mettre à jour les mocks et les initialisations dans les tests pour correspondre aux nouveaux constructeurs (BaseAgent avec LLM, SurrealDB avec Auth).
- **Requirement 20.3 (Standardisation) :** Harmoniser l'utilisation du `PYTHONPATH` pour que les tests puissent être lancés d'une seule commande `pytest` à la racine.

## 4. Critères de Succès
- La commande `pytest apps/h-core/tests/` retourne 100% de succès.
- Aucune erreur de type `ModuleNotFoundError` ou `TypeError` liée aux signatures de classes fondamentales.

---
*Défini par John (PM) le 26 Janvier 2026.*
