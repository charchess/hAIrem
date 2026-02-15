# Sprint 13 Plan: Deep Cognitive Memory (Epic 13)

**Date:** Janvier 2026  
**Durée:** 2 semaines  
**Objectif:** Implémenter la mémoire cognitive avec graphe, decay et synthèse

---

## 📋 Stories

| Story | Description | Points |
|-------|-------------|--------|
| 13.1 | Graph Schema Implementation | 8 |
| 13.2 | Semantic Decay (L'Oubli) | 8 |
| 13.3 | Subjective Retrieval | 5 |
| 13.4 | Conflict Synthesis | 8 |
| 13.5 | Sleep Orchestration | 5 |
| 13.6 | Transient State Management | 5 |

---

## 🎯 Objectifs

1. **Graphe de Connaissance** - Nodes (fact, subject, concept) + Edges (BELIEVES, ABOUT, CAUSED)
2. **Mémoire Subjective** - Chaque agent a ses propres croyances
3. **Oubli Naturel** - Algorithme de decay exponentiel
4. **Résolution de Conflits** - Synthèse dialectique (Thèse/Antithèse/Synthèse)

---

## Défis Techniques (de la Rétro)

- Complexité des requêtes SurrealDB
- Réglage fin du prompt de consolidation
- Performance des traversées de graphe

---

## Définition of Done

- [ ] Code implémenté
- [ ] Tests unitaires graph-memory GREEN
- [ ] Tests de decay GREEN
- [ ] Utilisation de SCHEMAFULL sur les relations

---

## Métriques Cibles

- Graph Performance: < 500ms
- Tests: 100% passage
- Intégrité: SCHEMAFULL sur BELIEVES

---

*Plan reconstruit depuis la rétro Epic 13*
