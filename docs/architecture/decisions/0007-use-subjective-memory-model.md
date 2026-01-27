# 7. Use Subjective Memory Model (Graph)

Date: 2026-01-27

## Status

Accepted

## Context

Les IA conversationnelles classiques souffrent d'amnésie ou d'hallucinations contextuelles. Elles ne "savent" pas vraiment qui elles sont ni ce qu'elles ont vécu.
Un simple stockage de logs (Chat History) ne suffit pas pour construire une relation à long terme ou des avis divergents entre agents.

## Decision

Nous implémentons un **Modèle de Mémoire Subjective** basé sur un Graphe (SurrealDB).
Chaque fait est stocké du point de vue de l'observateur (Subjectivité).

Voir spécification détaillée : [4. Modèles de Données](../4-modles-de-donnes-mmoire-subjective.md)

## Consequences

### Positives
*   **Réalisme** : Permet à deux agents d'avoir des souvenirs contradictoires d'un même événement (conflit narratif).
*   **Profondeur** : Permet de modéliser des croyances, des rumeurs et des secrets.

### Négatives
*   **Complexité d'écriture** : Transformer du langage naturel en triplets graphe (Sujet-Verbe-Objet) demande une étape de "Consolidation" coûteuse en LLM.
