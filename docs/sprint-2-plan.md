# Sprint 2 Plan: The Agent Ecosystem

**Sprint Goal:** Donner vie aux agents en définissant leur protocole de communication, leur structure de code et en instanciant le duo initial (Renarde & Expert).

## 1. Sprint Commitment
L'objectif est de rendre le système "intelligible" pour les agents.

| ID | Story Title | Status | Priority |
| --- | --- | --- | --- |
| 2.1 | Définir le schéma H-Link et Diagrammes | Approved | P0 |
| 2.2 | Implémenter l'Agent Générique (BaseAgent) | Approved | P0 |
| 2.3 | Configurer "La Renarde" et "L'Expert" | Approved | P0 |

## 2. Technical Focus Areas
- **Protocol Strictness:** Le schéma JSON H-Link doit être la seule vérité. Aucun message hors protocole ne doit circuler.
- **Inheritance Pattern:** La classe `BaseAgent` doit être suffisamment générique pour tout type d'expert futur (LLM, RAG, Tool).
- **Context Isolation:** Garantir que chaque agent ne voit que ce qui le concerne (via son propre channel Redis).

## 3. Risk Mitigation
- **Infinite Loop:** Attention aux boucles de messages (Agent A parle à Agent B qui répond à Agent A...). Prévoir un TTL ou un compteur de hops dans les métadonnées H-Link.
- **Prompt Injection:** Sécuriser les prompts systèmes dans les fichiers YAML.

## 4. Definition of Done (DoD)
- [ ] Diagrammes de séquence Mermaid validés.
- [ ] Classe `BaseAgent` testée avec un Mock Redis.
- [ ] Agents Renarde et Expert chargés sans erreur au démarrage.
- [ ] Documentation H-Link publiée.

## 5. Next Steps
1.  **Story 2.1 Execution:** Documentation et Diagrammes.
2.  **Story 2.2 Execution:** Code Python (Core logic).
