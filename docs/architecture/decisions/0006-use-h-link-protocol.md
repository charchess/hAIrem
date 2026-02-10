# 6. Use H-Link Protocol for Inter-Agent Communication

Date: 2026-01-27

## Status

Accepted

## Context

Dans une architecture multi-agents hétérogène, les composants doivent s'échanger des messages complexes (texte, émotion, commandes domotiques, méta-données système).
L'utilisation d'appels API REST synchrones crée un couplage fort et une latence additive inacceptable pour une conversation fluide.

## Decision

Nous définissons et utilisons le **Protocole H-Link**.
Il s'agit d'un standard de message JSON strict circulant sur le bus Redis.

Voir spécification détaillée : [5. Protocole H-Link](../5-protocole-h-link.md)

## Consequences

### Positives
*   **Découplage total** : Un agent peut être redémarré sans casser les autres.
*   **Introspection** : Facile à débugger (il suffit d'écouter le bus Redis).
*   **Extensibilité** : On peut ajouter de nouveaux types de messages (`type`) sans changer le core.

### Négatives
*   Nécessite une validation stricte (Schema) à l'entrée/sortie pour éviter le "schema drift".
