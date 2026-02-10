# Rétrospective Sprint 4 : External Brain

**Date :** 20 Janvier 2026
**Participants :** Bob (SM), James (Dev), Quinn (QA)

## 1. Vue d'ensemble
Le Sprint 4 a transformé un automate scripté en une entité conversationnelle. L'intégration du LLM avec streaming est une réussite technique majeure qui valide l'UX "Visual Novel temps réel".

**Statut :** SUCCÈS.

## 2. Feedback de l'Équipe Virtuelle

### 👍 Ce qui a bien fonctionné (Keep)
*   **Architecture Streaming :** Le pipeline `AsyncGenerator -> Redis -> WebSocket` fonctionne sans blocage. L'utilisateur voit le texte s'afficher immédiatement.
*   **Provider Agnosticism :** L'utilisation de variables d'environnement (`LLM_BASE_URL`) permet de basculer instantanément entre OpenAI et Ollama.
*   **Prompting Contextuel :** L'injection du `system_prompt` depuis le YAML donne bien une personnalité distincte à chaque agent.

### 👎 Ce qui a frotté (Drop/Fix)
*   **Gestion du Contexte :** La fenêtre glissante de 10 messages est une heuristique fragile. Un utilisateur bavard peut faire sortir les instructions système du contexte si la limite de tokens est basse.
*   **Manque de Function Calling :** Pour l'instant, l'agent ne peut que parler. Il ne sait pas encore qu'il peut *agir* (ce sera l'objet de l'Epic 5).

### 💡 Idées pour le Sprint 5 (Home Automation)
*   **Function Calling Natif :** Utiliser les capacités de "Tools" de l'API OpenAI pour exposer les services Home Assistant directement au LLM, plutôt que de parser du texte.
*   **Safety First :** Mettre un filtre (Gatekeeper) avant d'exécuter une action réelle sur la maison.

## 3. Plan d'Action (Action Items)

| Action | Propriétaire | Échéance |
| --- | --- | --- |
| Implémenter le comptage de tokens (tiktoken) | James (Dev) | Backlog Tech |
| Définir le schéma JSON des outils Home Assistant | Winston (Arch) | Début Sprint 5 |
| Tester le modèle avec des commandes domotiques | Quinn (QA) | Story 5.2 |

## 4. Conclusion
hAIrem pense et parle. Maintenant, il doit agir. L'Epic 5 sera le test ultime de l'utilité du système.
