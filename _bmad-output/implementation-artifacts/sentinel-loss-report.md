# Rapport de Perte Technique : Sentinel Engine

## État des Lieux
Lors de la migration et de l'audit technique du 12 février 2026, le service `sentinel-engine` a été identifié comme "orphelin" et techniquement défaillant. 

## Fonctions Perdues
Le moteur **Sentinel** assurait les fonctions cognitives avancées suivantes :
1.  **Attention Scoring** : Calcul de pertinence pour déterminer quel persona doit répondre à un message global.
2.  **Auto-RAG** : Injection automatique de souvenirs pertinents (récupérés via SurrealDB) dans le prompt des agents.
3.  **Contextualisation** : Enrichissement des requêtes LLM avec des données temps réel et historiques.

## Causes de la Défaillance
- **Rupture de liens** : Les chemins de montage Docker pointaient vers une ancienne structure de fichiers (`/home/charchess/openclaw/...`).
- **Obsolescence** : Utilisation d'Ollama local (Qwen 2.5) dont la communication avec le nouveau protocole H-Link n'était plus assurée.

## Mesures de Sauvegarde
- **Assets récupérés** : Les sprites et character sheets de Lisa et Electra ont été extraits des volumes Docker orphelins et réintégrés dans `/agents`.
- **Modèles sauvés** : Les poids du modèle SDXL (Imagination) et Qwen 2.5 sont conservés dans les volumes `hairem_sentinel_models` et `electra-models`.
- **Code source** : La logique de mémoire (SurrealDB) est présente dans `apps/h-core/src/infrastructure/surrealdb.py` mais n'est plus pilotée par un chef d'orchestre automatique.

## Recommandation QA
Ne pas tenter de relancer le conteneur original. Une ré-implémentation de la logique de scoring et d'auto-RAG directement dans le module `HaremOrchestrator` est préconisée pour assurer la compatibilité avec le bus de données `system_stream`.
