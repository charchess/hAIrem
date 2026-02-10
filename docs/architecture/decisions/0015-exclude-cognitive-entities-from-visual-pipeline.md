# ADR 0015 : Exclusion des Entités Cognitives du Pipeline Visuel

**Statut :** Accepté
**Date :** 28 Janvier 2026
**Auteur :** James (Dev)

## Contexte
Le système tente de bootstraper automatiquement un avatar (body/pose) pour chaque agent chargé via le `PluginLoader` s'il n'en possède pas encore. Cependant, certaines entités comme "Dieu" ou "system" sont purement fonctionnelles ou cognitives et ne doivent pas posséder de représentation physique. Tenter de générer des images pour ces entités consomme inutilement des ressources API et peut polluer l'interface.

## Décision
1.  Les agents dont le nom est "Dieu" ou "system" sont explicitement exclus du processus `bootstrap_agent_avatar` dans le `PluginLoader`.
2.  L'UI (The Stage) doit masquer les couches `body` et `face` lorsqu'un agent marqué comme `personified: false` prend la parole.
3.  Un flag `deactivatable: false` est introduit pour garantir que ces entités vitales ne peuvent pas être désactivées via le Crew Panel.

## Conséquences
- Économie de tokens sur les APIs de génération d'images.
- Meilleure clarté sémantique entre agents "incarnés" et "systèmes".
- Nécessité de maintenir une liste d'exclusion ou d'ajouter un flag `is_physical` dans les manifests.
