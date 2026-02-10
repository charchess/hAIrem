# Rétrospective Sprint 17 : "The Stage" UI/UX Overhaul

**Date :** 26 Janvier 2026
**Équipe :** Lisa (SM/Quinn), James (Dev), Bob (SM)
**Statut de l'Epic :** TERMINÉ ✅

## 🥳 Ce qui a bien fonctionné (Wins)
- **Fluidité de Navigation (Story 17.1) :** Le passage à une navigation par icônes (⚙️/👥) et la gestion des modals "Click-outside-to-close" transforment l'interface en une véritable application moderne et intuitive.
- **Adressage Visuel (Story 17.4) :** Le sélecteur de destinataire simplifie drastiquement l'interaction. L'utilisateur n'a plus à mémoriser les préfixes `@Nom`, et le passage à un adressage explicite dans le payload WebSocket fiabilise le routage backend.
- **Observabilité Augmentée (Story 17.2) :** L'intégration des logs système en temps réel et des contrôles de puissance directement dans le Control Panel permet un débogage "à chaud" sans quitter l'interface.
- **Support Grok-4.1 :** L'optimisation du flux LLM pour extraire le `reasoning_content` et nettoyer les messages vides améliore la qualité des réponses pour les modèles les plus récents.

## 🛠️ Les défis techniques (Friction)
- **Placeholders JS :** Une version intermédiaire du `renderer.js` contenait des placeholders qui ont cassé la classe. 
    - *Action :* Renforcer la validation statique avant le déploiement UI.
- **Variations de Payload HA :** L'outil `call_ha_service` a dû être durci pour supporter des payloads stringifiés envoyés par certains modèles LLM.
- **Cacophonie de Broadcast :** Les agents avaient tendance à tous répondre aux messages "Tout le monde". 
    - *Action :* Implémentation d'une règle où les agents ignorent le broadcast sauf mention explicite dans le texte.

## 📊 Métriques du Sprint
- **Stories Complétées :** 4 (17.1, 17.2, 17.3, 17.4)
- **Qualité :** 100% PASS sur les QA Gates.
- **Performance :** Adressage explicite réduit le temps de parsing du router backend.

## 🚀 Prochaines Étapes (Action Items)
1. **Graph Memory (Epic 13) :** Maintenant que l'UI est stable, migrer la mémoire vers SurrealDB avec schéma de graphe.
2. **Mathematical Decay :** Implémenter l'algorithme d'oubli progressif pour la mémoire à long terme.
3. **Conflict Synthesis :** Gérer les divergences de croyances entre agents via une synthèse subjective.

---
*Fin du Sprint 17 - L'interface est maintenant digne de hAIrem !* 🏃🎉✨
