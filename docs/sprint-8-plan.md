# Sprint 8 Plan: Visual DNA & Identity Consistency

**Sprint Goal:** Garantir une identité visuelle stable pour tous les agents grâce à l'implémentation du pipeline de prompt multicouche (Visual DNA) et automatiser le partage des assets générés.

## 1. Sprint Commitment
Passer d'une génération "aléatoire" à une matérialisation fidèle des personnages.

| ID | Story Title | Status | Priority |
| --- | --- | --- | --- |
| 11.8 | Multi-Layer Prompt Construction (Visual DNA) | Draft | P0 |
| 11.9 | Shared Asset Volume (H-Core <-> H-Bridge) | Draft | P1 |
| 11.11 | Visual State Protocol Migration (Payload Cleanup) | Draft | P1 |
| 11.13 | Visual Variety & Randomization | Draft | P2 |
| 11.14 | Infrastructure & Docker Refresh (Reproducibility) | Draft | P0 |

## 2. Technical Focus Areas
- **Identity Enforcement:** Utilisation du champ `visual_dna` et des `loras` du manifest.
- **Protocol Cleanup:** Migration des tags techniques vers un champ `visual_state` structuré.
- **Environment Stability:** Fix des Dockerfiles et dépendances pour un setup "one-shot".

## 3. Risk Mitigation
- **Prompt Bloating:** Surveiller la longueur des prompts générés pour éviter de dépasser les limites de l'API Imagen.
- **File System Permissions:** S'assurer que `h-core` a les droits d'écriture dans le dossier statique du `h-bridge`.
- **LoRA Weight Balance:** Ajuster les poids par défaut pour ne pas "brûler" l'image ou casser l'anatomie.

## 4. Definition of Done (DoD)
- [ ] Le prompt envoyé à Imagen combine Style Global + ADN Agent + Pose + Négatif.
- [ ] Les LoRAs définis dans le manifest sont transmis et appliqués par l'API.
- [ ] Une image générée par `h-core` est immédiatement visible dans le dossier `/static/assets/agents/` sans action manuelle.
- [ ] Le test de validation `tests/validate_imagen_api.py` reste au vert.

## 5. Next Steps
1. **Story 11.8:** James commence le refactoring de `prompts.py`.
2. **Story 11.9:** Winston définit la structure du volume partagé dans `docker-compose.yml`.
