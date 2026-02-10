# Liste de Rattrapage (Dette de Processus)

Ce document liste les actions nécessaires pour remettre le projet en conformité avec le flux de travail BMad™.

## 🏗️ À adresser par l'Architecte (Winston)
- [x] **Modularité Visuelle (Epic 25) :** Découplage du service visuel via des bibles YAML (`POSES`, `ATTITUDES`, `STYLE_GLOBAL`).
- [x] **Système Pluggable :** Chaque agent porte désormais ses propres métadonnées visuelles via `persona.yaml`.
- [x] **Détourage Automatique :** Pipeline intégré via `rembg` (La Découpeuse).
- [x] **Observabilité :** Broadcast des prompts bruts (`RAW_PROMPT`) vers l'UI pour audit.

## 🚩 ALERTES CRITIQUES (Dette Technique & Bugs)

- [x] **SÉCURITÉ/CI :** Nettoyer les secrets détectés par Gitleaks.

- [x] **SYNTAXE :** Résolution des erreurs de blocs `try/except` mal fermés dans `VisualImaginationService`.

- [x] **COMPATIBILITÉ :** Correction des embeddings Gemini via LiteLLM (passage en mode v1beta fallback).

- [x] **INFRA :** Mise à jour du Dockerfile `h-core` pour les dépendances binaires ONNX et Mesa.



## 📋 À adresser par le Product Manager (John)

- [x] **Régularisation Epic 25 :** Définir les besoins de la Story 25.2 (Asset Manager DB).

- [x] **Bible Visuelle :** Valider la conformité scientifique des poses (FACS) et attitudes (Mehrabian).

- [x] **Mise à jour PRD :** Passage à la PRD V4.1 (incluant Vaults, Skills et Social Arbiter).



## 🏃 À adresser par le Scrum Master (Bob)

- [x] **Mise à jour du Backlog :** Structuration de `THOUGHTS.md` et alignement Roadmap.

- [x] **Documentation des Dérives :** Création des ADR pour la modularité visuelle.



## ✅ À adresser par la QA (Quinn)

- [x] **Validation UI Finale :** Vérifier le rendu des poses transparentes sur différents fonds.

- [x] **Test de Charge Logs :** S'assurer que le broadcast des prompts volumineux ne sature pas le WebSocket.



---



## Historique des sessions de rattrapage



### 01 Février 2026 - Intégration Graphique & Qualité

- **Architecture Visuelle :**
    - Migration du provider par défaut vers `ImagenV2Provider` (SDXL/Pony via API interne).
    - Endpoint cible : `http://192.168.199.119:8009` (GPU Serveur dédié).
    - Intégration d'un **Negative Prompt** global dans `STYLE_GLOBAL.yaml` pour réduire les artefacts (anatomie, texte).
- **Processus :**
    - Validation du pipeline `/outfit` avec timestamp pour contournement de cache.
    - Identification de l'absence de `rembg` (La Découpeuse) sur l'environnement actuel (fallback gracieux actif).

### 28 Janvier 2026 - Stabilisation de l'Epic 25 & Alignement V4

- **Secrets :** Nettoyage complet des secrets dans `.env`, tests et logs détectés par Gitleaks.
- **Correction h-bridge :** Modification du endpoint `/generate` pour respecter le token d'autorisation envoyé par le Core ou utiliser `NANOBANANA_API_KEY`. Résolution de l'erreur 429 (quota exhausted) due à l'usage de la clé gratuite par défaut.
- **Modèle d'Embedding :** Migration par défaut vers `gemini/text-embedding-004` (plus stable sur LiteLLM v1beta que `embedding-001`).
- **Bootstrap Visuel :** Implémentation de `bootstrap_agent_avatar` dans `VisualImaginationService`. Correction du crash au chargement des agents (Entropy).
- **Entités non-physiques :** Exclusion de "Dieu" et "system" du processus de génération d'avatars dans le `PluginLoader`.
- **Résilience UI :** Ajout d'un flag `deactivatable: false` pour verrouiller l'état "Actif" des composants système dans le Crew Panel.
- **Documentation :** Passage à l'Architecture V4.4 et PRD V4.1. Consolidation des ADR 13 et 14.
- **Epic 25 :** Réouverture de l'Epic 25 (Status: IN PROGRESS) pour intégrer les Vaults et la Burning Memory.
- **Backlog :** Réorganisation de `THOUGHTS.md` en format Kanban (Fait/Prévu/Idée) avec traçabilité.
- **Vision :** Validation du système de Skills pluggables et de la hiérarchie des stimuli.
