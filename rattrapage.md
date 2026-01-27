# Liste de Rattrapage (Dette de Processus)

Ce document liste les actions nécessaires pour remettre le projet en conformité avec le flux de travail BMad™.

## 🏗️ À adresser par l'Architecte (Winston)
- [x] **Documenter la Mémoire Subjective :** Compléter `docs/architecture/4-modles-de-donnes-mmoire-subjective.md`. 
- [x] **Mettre à jour la Tech Stack :** Vérifier que `docs/architecture/3-tech-stack.md`.
- [x] **Développer l'Architecture de Haut Niveau :** Compléter `docs/architecture/2-architecture-de-haut-niveau.md`.
- [x] **Documenter l'Orchestration Narrative :** Étendre `docs/architecture/6-orchestration-narrative.md`.
- [x] **Spécifier le Système de Plugins :** Détailler `docs/architecture/7-systme-hotplug-plugins.md`.
- [x] **Infrastructure Cognitive :** Documenter le **Semantic Caching** et le **Privacy Filter** (Epic 9).
- [x] **Pipeline Visuel :** Documenter le fonctionnement des Poses et de la génération d'assets (Epic 11).
- [x] **Spécifier le "Social Arbiter" (Polyphonie V3) :** Créer un document dédié sur l'arbitrage des tours de parole via micro-modèle local (Llama-1B).
    - *Fait :* Nouveau document `docs/architecture/10-social-arbiter.md`.
- [x] **Refactoring H-Core :** Définir le plan de découplage du Bridge WebSocket vers un service dédié (`HLinkBridge`).
    - *Fait :* Documenté dans `docs/architecture/8-rsilience-dploiement.md`.

## 🚩 ALERTES CRITIQUES (Dette Technique & Bugs)
- [x] **SÉCURITÉ :** Brancher le `PrivacyFilter` dans `main.py` pour caviarder les logs/DB.
    - *Fait :* Intégré dans Story 19.1.
- [x] **AUTOMATION :** Activer le cycle de sommeil dans le H-Core (instanciation du `MemoryConsolidator`).
    - *Fait :* Activé dans Story 19.2.
- [x] **DOUBLONS :** Supprimer les tags `[pose:X]` du texte final une fois que le payload supporte `visual_state`.
    - *Fait :* Nettoyage UI implémenté dans Story 19.3.

## 📋 À adresser par le Product Manager (John)
- [x] **Régularisation PRD (Epic 9, 10, 11, 12, 17) :** Rétro-documenter les besoins métier pour ces epics déjà codés.
- [x] **Shard "Social Dynamics" :** Définir les règles de savoir-vivre et l'expérience utilisateur de la polyphonie (qui peut couper qui ?).
    - *Fait :* Nouveau document `docs/prd/epic-18-social-dynamics.md`.
- [x] **Epic 14 (Sensory Layer) :** Créer `docs/prd/epic-14-sensory-layer.md`.
- [x] **Epic 15 (Living Home) :** Créer `docs/prd/epic-15-living-home.md`.
- [x] **Audit PRD V3 :** Finaliser le brouillon de `docs/prd.md`.
    - *Fait :* `docs/prd.md` mis à jour et passé en statut "Approved".

## 🏃 À adresser par le Scrum Master (Bob)
- [x] **Rétrospective Epic 13 (Graph Memory) :** Animer et enregistrer le bilan.
    - *Fait :* `docs/retrospectives/sprint-13-retro.md` créé.
- [x] **Découpage Stories "Stabilisation V3" :** Transformer les alertes critiques de Winston en stories actionnables par James.
    - *Fait :* Stories 19.1, 19.2 et 19.3 créées dans `docs/stories/19-stabilization-v3.md`.
- [x] **Cleanup Backlog :** Marquer les stories 13.x comme "Done".
    - *Fait :* Statuts mis à jour dans les fichiers de stories.

## ✅ À adresser par la QA (Quinn)

- [x] **Validation Finale Epic 13 :** Signer les QA Gates 13.2, 13.3, 13.4.

    - *Fait :* Gates signées et statuts mis à jour.

- [x] **Audit de Non-Régression :** Vérifier la Home Automation (Epic 5) après le refactoring UI du Sprint 17.

    - *Fait :* Simulation réussie, routage expert fonctionnel.

- [x] **Validation Epic 19 :** Vérifier l'intégration du Privacy Filter et du cycle de sommeil.

    - *Fait :* Tests d'intégration passés avec succès. Statut PASS.

- [x] **Test Cleanup Sprint :** Mettre à jour ou supprimer les 13 tests unitaires "legacy" qui échouent.

    - *Fait :* Suite de tests 100% Green (47/47) validée par Quinn.

- [x] **CI/CD Integration :** Intégrer `scripts/master_regression_v3.py` dans le pipeline de validation automatisé.
    - *Fait :* Stratégie documentée (Doc 8) incluant le Secret Scanning et la compatibilité Kubernetes. Ready pour l'implémentation.






