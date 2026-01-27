# Source Tree Organization

Ce document décrit la structure des dossiers du projet `hAIrem` et la responsabilité de chaque module.

## Arborescence Principale

### `/agents`
Contient les définitions et logiques spécifiques aux agents IA.
*   `electra/`, `entropy/`, `lisa/`, `renarde/` : Dossiers individuels pour chaque persona d'agent.

### `/apps`
Applications principales et services exécutables.
*   `h-core/` : Le cœur du système (Kernel), gestion de la mémoire, orchestration.
*   `h-bridge/` : Passerelle de communication (API, liaisons externes).

### `/config`
Fichiers de configuration globaux (YAML, JSON).
*   `prompts.yaml`, `system.yaml` : Configurations du système et des prompts IA.

### `/docs`
Documentation du projet.
*   `architecture/` : Documents d'architecture technique (ADR, standards, diagrammes).
*   `prd/` : Product Requirements Documents (spécifications fonctionnelles).
*   `references/` : Sources de vérité créatives (Lore, Personas, Matrices de relations, Image prompts).

## Fichiers à la racine
*   `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md` : Standards de gestion de projet.
*   `pyproject.toml` : Configuration du projet Python.
*   `PROMPTS.md` : Artefact temporaire de génération d'assets (Image Prompts).
*   `rattrapage.md` : Suivi de la dette technique et de processus (Dette BMad).
