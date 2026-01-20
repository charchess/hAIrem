# Rétrospective Sprint 1 : Foundation

**Date :** 20 Janvier 2026
**Participants :** Bob (SM), James (Dev), Quinn (QA), Winston (Arch), Lisa (User)

## 1. Vue d'ensemble
Ce sprint a permis de passer d'un concept abstrait à une infrastructure fonctionnelle. Le "Cœur" (H-Core) bat et peut charger des greffons (Agents).

**Statut :** SUCCÈS (Toutes les stories P0 sont terminées).

## 2. Feedback de l'Équipe Virtuelle

### 👍 Ce qui a bien fonctionné (Keep)
*   **Le Processus QA-First :** Avoir Quinn qui définit les risques (SPOF Redis) et les tests *avant* que James ne code a été décisif. Le code produit était robuste immédiatement (reconnexion automatique incluse dès la V1).
*   **L'Architecture Modulaire :** La séparation nette entre `infrastructure/` et `models/` dans le code Python rend le projet très propre pour la suite.
*   **Les "Dev Notes" :** Les stories enrichies avec des références précises (chemins de fichiers, libs) ont permis à James de coder sans hésitation.

### 👎 Ce qui a frotté (Drop/Fix)
*   **Le Flou sur H-Link :** James a dû attendre que Winston (Arch) précise le schéma JSON *pendant* le sprint. Idéalement, cela aurait dû être prêt avant.
*   **L'Environnement CLI :** L'impossibilité de lancer Docker ou Poetry "pour de vrai" a limité la validation à de l'analyse statique. C'est un risque latent pour l'intégration réelle.

### 💡 Idées pour le Sprint 2 (Start)
*   **Diagrammes de Séquence :** Pour l'Epic 2 (Agents), Winston devrait fournir un diagramme des échanges Redis attendus.
*   **Mocks plus poussés :** Puisqu'on ne peut pas lancer Docker, James devrait créer des scripts de "mock" pour simuler le comportement de Redis lors des tests locaux.

## 3. Plan d'Action (Action Items)

| Action | Propriétaire | Échéance |
| --- | --- | --- |
| Définir les diagrammes de séquence pour Epic 2 | Winston (Arch) | Début Sprint 2 |
| Créer un script de Mock pour le bus d'événements | James (Dev) | Story 2.1 |
| Valider le schéma H-Link avec le Frontend (A2UI) | Lisa (PO) | Sprint 2 |

## 4. Conclusion
Le socle est solide. L'équipe a trouvé son rythme de croisière : **Spec -> Risk -> Design -> Code -> Review**. Nous sommes prêts pour l'Epic 2.
