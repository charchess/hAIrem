# 14. Bootstrap Avatar & Système d'Outfits (Epic 25)

**Date :** 27 Janvier 2026
**Agent :** James (Developer)
**Contexte :** Story 25.1 - Interface GenericProvider & Client NanoBanana

## 1. Description de la Dérive
1. **Bootstrap Avatar :** Génération automatique de `character_sheet_neutral.png` si absente au chargement.
2. **Système d'Outfits :** Capacité du moteur à changer les vêtements d'un agent tout en préservant son identité visuelle via l'image de référence.
3. **Commande `/outfit` :** Ajout d'une commande slash pour déclencher manuellement un changement de tenue. Inclus désormais dans le heartbeat pour l'autocomplétion UI.
4. **Routage Multimodal :** Mise à jour du Bridge et du H-Core pour supporter l'interception des commandes envoyées sous forme de `EXPERT_COMMAND` ou de texte narratif, garantissant la compatibilité avec toutes les versions de l'interface.
5. **Correction Frontend :** Synchronisation de `network.js` pour inclure `outfit` dans les commandes globales, évitant ainsi les erreurs de parsing côté client.

## 2. Justification
La boucle de diagnostic a révélé des désynchronisations majeures entre le frontend et le backend, ainsi que des instabilités dans les souscriptions Redis. La centralisation du routage dans le H-Core et la mise à jour du client JS étaient nécessaires pour rendre le système d'imagination réellement utilisable.

## 3. Conclusion
Le système est désormais stable et validé par Playwright. L'avatar de Lisa a été restauré et le changement de tenue est fonctionnel.

---
*Cette note fait office d'avenant technique final à l'Epic 25.*
