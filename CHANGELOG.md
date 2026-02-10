# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-01-28

### Added (Architecture V4.4 & PRD V4.1)
- **Architecture Persona-Skill :** Découplage total identité/compétence via `persona.yaml`.
- **Social Arbiter & Hiérarchie :** Priorisation des stimuli (0-3) et gestion de la polyphonie.
- **Mémoire Brûlante :** Injection de l'état visuel (tenue/lieu) dans le contexte court terme.
- **Vault System :** Gestion des inventaires nommés pour les tenues et les décors de référence.
- **Onboarding :** Nouveau workflow d'initialisation des relations inter-agents.
- **Modular Visual Bible :** Découplage styles/poses (FACS)/attitudes (Mehrabian) via `config/visual/`.
- **Pipeline de Détourage :** Intégration de `rembg` (La Découpeuse).
- **Observabilité :** Broadcast des `RAW_PROMPT` vers l'UI pour audit.
- **Cache Visuel :** Indexation et réutilisation sémantique (K-NN) dans SurrealDB.

### Added (Initial)
- Initialisation de la documentation standard (`README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`).
- Refonte de la documentation d'architecture (`tech-stack.md`, `coding-standards.md`, `source-tree.md`).

### Changed
- Nettoyage des doublons dans `docs/architecture/`.
