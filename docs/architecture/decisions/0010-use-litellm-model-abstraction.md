# 10. Use LiteLLM for Model Abstraction

Date: 2026-01-27

## Status

Accepted

## Context

Le projet hAIrem doit être capable de basculer dynamiquement entre différents fournisseurs de LLM (OpenRouter, Google Gemini, modèles locaux via Ollama, etc.) selon le coût, la latence ou les capacités spécifiques du modèle. Câbler directement les SDK propriétaires (ex: `google-generativeai`) créerait un couplage fort et rendrait le système rigide.

## Decision

Nous utilisons **LiteLLM** comme couche d'abstraction unique pour toutes les interactions avec les modèles de langage.

## Consequences

### Positives
*   **Standardisation** : Toutes les réponses (streaming ou non) suivent le format standard OpenAI, quel que soit le provider.
*   **Agilité** : Permet de changer de modèle ou de provider en modifiant une simple variable d'environnement, sans toucher au code.
*   **Observabilité** : Facilite le tracking des coûts et des tokens de manière centralisée.

### Négatives
*   Dépendance supplémentaire à une bibliothèque tierce.
*   Certaines fonctionnalités très spécifiques à un provider (ex: Gemini System Instructions complexes) peuvent nécessiter des ajustements de mapping.
