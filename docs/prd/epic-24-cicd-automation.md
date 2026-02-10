# Epic 24: CI/CD Pipeline & Automated Security

**Status:** Approved
**Theme:** Automatisation & Sécurité Proactive
**PRD Version:** V3

## 1. Vision
Mettre en place une "Usine Logicielle" qui valide automatiquement chaque changement. Personne ne peut plus casser hAIrem sans que le pipeline ne l'identifie immédiatement. On veut un flux : Code -> Scan -> Test -> Deploy.

## 2. Objectifs Métier
- **Confiance Totale :** Supprimer la peur de casser le backend lors d'une mise à jour.
- **Sécurité Garantie :** Scanner chaque commit pour empêcher les fuites de secrets (GitGuardian style).
- **Déploiement en 1 clic :** Automatiser la mise à jour des containers Docker.

## 3. Exigences Clés (Requirements)
- **Requirement 24.1 (Secret Scanning) :** Intégrer un outil (ex: Gitleaks) qui bloque le pipeline si une clé API est détectée en clair.
- **Requirement 24.2 (Quality Entonnoir) :** Lancer automatiquement `pytest` (47 tests) et le `master_regression_v3.py` à chaque modification.
- **Requirement 24.3 (Docker Build Check) :** Vérifier que les images `h-bridge` et `h-core` se compilent correctement.
- **Requirement 24.4 (Auto-Deploy MVP) :** Créer un script de déploiement qui met à jour les containers sur l'environnement de test/production Docker.

## 4. Critères de Succès
- Un commit avec une erreur de syntaxe est rejeté par la CI.
- Une tentative de commit d'une clé API factice est bloquée.
- Le temps total de validation ne doit pas excéder 5 minutes.

---
*Défini par John (PM) le 26 Janvier 2026.*
