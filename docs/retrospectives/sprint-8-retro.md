# Rétrospective Sprint 8 : The Archive & Intelligence

**Date :** 23 Janvier 2026
**Équipe :** Lisa (SM/Quinn), James (Dev), Bob (SM)
**Statut de l'Epic :** TERMINÉ ✅

## 🥳 Ce qui a bien fonctionné (Wins)
- **Flexibilité Totale :** Le passage à LiteLLM (Story 8.0) est un game-changer. hAIrem n'est plus lié à une seule API. Le test réussi avec **Gemini 2.5 Flash** prouve la robustesse du connecteur.
- **Mémoire Vive :** SurrealDB est en place et encaisse chaque message. La persistance est transparente et asynchrone, sans impact sur la fluidité de l'UI.
- **Expérience Utilisateur :** La restauration de l'historique (8.2) donne enfin une impression de "produit fini". On ne perd plus le fil au moindre refresh.
- **Intelligence Augmentée :** Les agents ont maintenant un outil `recall_memory`. C'est la première étape vers une véritable conscience à long terme.

## 🛠️ Les défis techniques (Friction)
- **Syntaxe SurrealDB :** La gestion des IDs avec des UUIDs a causé des erreurs de parsing. *Leçon :* Toujours utiliser les backticks (`` ` ``) pour les IDs complexes dans SurrealQL.
- **Versioning LiteLLM :** Les modèles Gemini nécessitent parfois des préfixes spécifiques (`gemini/`) pour que LiteLLM identifie correctement le provider, surtout pour les embeddings.
- **Asynchronisme :** La librairie `surrealdb` en Python a nécessité quelques ajustements (passage à `AsyncSurreal`) pour éviter de bloquer la boucle d'événements FastAPI.

## 📊 Métriques du Sprint
- **Stories Complétées :** 4 (8.0, 8.1, 8.2, 8.3)
- **Bugs Critiques Résolus :** 2 (Persistence UUID, Missing Embeddings)
- **Qualité :** 100% des stories validées par Quinn.

## 🚀 Prochaines Étapes (Action Items)
1. **Semantic Caching :** Implémenter un cache pour les embeddings afin de réduire les coûts et la latence.
2. **Privacy Filter :** Ajouter un middleware pour éviter de vectoriser des données sensibles (clés API, mots de passe).
3. **Optimisation RAG :** Affiner le prompt système des agents pour qu'ils utilisent `recall_memory` de manière plus proactive.

---
*Fin de la rétro - En route pour le Sprint 9 !* 🏃✨
