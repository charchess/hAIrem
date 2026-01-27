# 8. Use Social Arbiter Pattern for Orchestration

Date: 2026-01-27

## Status

Accepted

## Context

Gérer la prise de parole entre plusieurs agents (Lisa, Renarde, Dieu) est complexe.
*   Une machine à états finis (State Machine) devient vite ingérable (explosion combinatoire).
*   Le "chacun son tour" est robotique et non-naturel.

## Decision

Nous utilisons le **Pattern Social Arbiter** (Probabiliste).
Un LLM léger évalue le "désir de parler" (Urge-to-Speak Score) de chaque agent à chaque tour.

Voir spécification détaillée : [6. Orchestration Narrative](../6-orchestration-narrative.md)

## Consequences

### Positives
*   **Naturalité** : Permet des interruptions, des silences, ou des débats dynamiques.
*   **Flexibilité** : Ajouter un nouvel agent ne demande aucune reconfiguration du routeur, juste l'ajout de son profil au scoring.

### Négatives
*   **Latence** : Ajoute un appel LLM (même petit) avant chaque réponse.
*   **Non-déterministe** : Difficile à tester unitairement de manière stricte (le comportement peut varier légèrement).
