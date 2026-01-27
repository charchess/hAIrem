# 9. Standardize Agent Bundle Structure (Hotplug)

Date: 2026-01-27

## Status

Accepted

## Context

L'architecture hAIrem traite chaque agent comme un module "Hotplug" (chargeable à chaud). Pour que le `PluginLoader` du Core puisse automatiser la découverte, l'instanciation et la gestion du cycle de vie des agents, il est impératif d'avoir une structure de fichiers standardisée et prévisible.

Actuellement, les termes `agent.yaml`, `expert.yaml` et `persona.yaml` sont utilisés de manière interchangeable dans la documentation, ce qui crée une confusion pour le développement.

## Decision

Nous adoptons une structure de "Bundle" stricte pour chaque agent dans le répertoire `/agents/{agent_id}/` :

1.  **`manifest.yaml`** (OBLIGATOIRE) : Contient les métadonnées techniques (ID, version, type d'agent, dépendances). C'est le point d'entrée du `PluginLoader`.
2.  **`persona.yaml`** (OPTIONNEL) : Contient les instructions narratives (Prompt système, voix TTS, traits de personnalité, émotions). Séparé du manifest pour permettre des changements de "personnalité" sans changer la logique technique.
3.  **`logic.py`** (OPTIONNEL) : Code Python surchargeant la classe `BaseAgent`. Doit impérativement exposer une classe nommée `Agent`.
4.  **`requirements.txt`** (OPTIONNEL) : Liste les dépendances Python spécifiques à l'agent (ex: drivers domotiques).

## Consequences

### Positives
*   **Découverte Automatisée** : Le Core n'a besoin que de scanner la présence de `manifest.yaml`.
*   **Séparation des préoccupations** : La configuration technique (`manifest`), narrative (`persona`) et logique (`logic.py`) est isolée.
*   **Modularité** : Permet de créer des agents "purement narratifs" (sans code) ou des agents "purement techniques" (sans persona).

### Négatives
*   Impose une structure plus rigide aux développeurs d'agents.
*   Nécessite une mise à jour de la documentation technique (Spécification 7).
