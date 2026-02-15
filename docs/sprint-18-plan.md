# Sprint 18 Plan: "La Grande Purification" - Major Cleanup

**Date:** Janvier 2026  
**Durée:** 2 semaines  
**Objectif:** Purification du système et clôture des epics techniques

---

## 📋 Epics Couvertes

| Epic | Description | Stories |
|------|-------------|---------|
| 19 | Privacy & Security | 19.1, 19.2, 19.3 |
| 20 | Test Cleanup | 20.1, 20.2, 20.3 |
| 23 | H-Core/H-Bridge Decoupling | 23.1, 23.2, 23.3, 23.4, 23.5, 23.6 |
| 13 | (Finalisation) | 13.5, 13.6 |

---

## 🎯 Objectifs

1. **Découplage H-Bridge / H-Core** - Séparation physique interface et cerveau
2. **Privacy Filter** - Aucun secret dans la mémoire à long terme
3. **Test Cleanup** - Passage de 13 tests échoués à 47 GREEN
4. **Stabilité** - Heartbeat système à 10s

---

## Défis Techniques (de la Rétro)

- Ghost Worker du Core: Worker de config oublié dans asyncio.gather
- Complexité SurrealQL: Itérations multiples sur le schéma

---

## Définition of Done

- [ ] Code implémenté
- [ ] Tests: 47 GREEN (100%)
- [ ] Code review passé

---

## Métriques Cibles

- Tests Unitaires: 47 (100% Pass)
- Stabilité: Heartbeat actif

---

*Plan reconstruit depuis la rétro Sprint 18*
