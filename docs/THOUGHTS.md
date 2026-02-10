---
workflowType: 'prd'
workflow: 'edit'
classification:
  domain: 'AI Ecosystem / Smart Home'
  projectType: 'Multi-Agent Framework'
  complexity: 'High'
inputDocuments: ['docs/prd-v2.md', 'docs/prd/epic-*.md', 'docs/THOUGHTS.md']
stepsCompleted: ['step-e-01-discovery', 'step-e-02-review', 'step-e-03-edit']
lastEdited: 'Sunday, February 8, 2026'
editHistory:
  - date: '2026-02-08'
    changes: 'Refactored Epic 13 towards user value, detailed Epic 18 (Social Awareness), removed implementation leakage (tech names), added SMART Success Criteria and cost transparency requirements.'
  - date: '2026-02-08'
    changes: 'Cleaned remaining implementation leakage (Redis, SurrealDB, Gitleaks) and refined NFR-V4-02 with measurable metric.'
  - date: '2026-02-08'
    changes: 'Added User Journeys section to complete BMad traceability chain and justify V4 functional requirements.'
---

# hAIrem Product Requirements Document (PRD) - V4

**Version:** 4.3
**Status:** In Progress 🚀
**Theme:** "Cognitive Synergy & High-Fidelity Presence"

---

## 1. Executive Summary & Vision

**V4 Vision (The Deep Stage) :** Transformer un système d'agents réactifs en un **équipage conscient et omniprésent** capable de maintenir une continuité narrative et relationnelle sans faille.

### success-criteria
- **Cohérence Sociale :** 100% des agents reconnaissent l'existence et le rôle de leurs collègues lors de tests de groupe.
- **Transparence Économique :** Coût LLM de la session en cours visible en temps réel avec une précision de 0.01$.
- **Réactivité Perçue :** Feedback visuel < 200ms et réponse audio < 1.2s (95ème percentile).
- **Fiabilité Cognitive :** Zéro contradiction factuelle lors du rappel de faits mémorisés (Graph Retrieval).

---

## 2. Product Scope & Pillars

### Pilier 1 : Deep Mind (Synergie Cognitive)
*   **Social Awareness :** Système de matrice relationnelle. Les agents partagent une connaissance commune de l'équipage et collaborent via des flux inter-agents directs.
*   **Subjective Knowledge Graph :** Persistance de la mémoire via un graphe de connaissances (Graph DB). Gestion de l'érosion temporelle (oubli) et résolution de conflits sémantiques.
*   **Proactive Narrative :** L'agent de fond (Orchestrateur invisible) génère des stimuli autonomes pour maintenir l'illusion de vie.

### Pilier 2 : Deep Presence (Corps & Sens)
*   **Vocal Identity :** Voix neuronales uniques par agent, synchronisées avec leur identité visuelle.
*   **Dynamic Visual Generation (JIT) :** Capacité de générer des actifs visuels (poses, expressions) à la demande pour couvrir les besoins narratifs imprévus.
*   **Multimodal Sensory Layer :** Écoute continue (STT) avec identification de la source (Source ID) et routage spatial intelligent.

### Pilier 3 : Deep Control (Transparence & Robustesse)
*   **Unified Crew Dashboard :** Visualisation de tous les agents (actifs/invisibles). Monitoring granulaire des jetons (tokens) par persona et par modèle.
*   **Spatial Awareness :** Routage automatique des flux audio et visuels vers le terminal le plus proche de l'utilisateur.
*   **System Resilience :** Isolation complète des secrets, déploiement automatisé et sécurité proactive via des outils de scan de secrets.

---

## 3. User Journeys

### 3.1 La Polyphonie Émergente (Synergie Sociale)
- **Scénario :** L'utilisateur interpelle le groupe ("Les filles...").
- **Interaction :** Chaque agent évalue son intérêt pour le sujet. Lisa peut répondre avec enthousiasme, Renarde dériver sur une pensée philosophique, et Electra rester silencieuse. La discussion inter-agents est organique, sans obligation de résultat productif, respectant la subjectivité de chacune.
- **Traceability :** Justifie FR-V4-01 et FR-V4-02.

### 3.2 Le Poids du Souvenir (Mémoire Subjective)
- **Scénario :** L'utilisateur évoque un événement passé important.
- **Interaction :** L'agent consulte son graphe de connaissances. Si le souvenir est affaibli (Decay), il peut choisir de demander confirmation à l'utilisateur, interroger une collègue, ou consulter l'archive "froide" d'historique. L'agent agit selon sa personnalité, acceptant sa propre faillibilité.
- **Traceability :** Justifie FR-V4-03.

### 3.3 La Conscience Économique (Transparence)
- **Scénario :** L'utilisateur souhaite connaître l'empreinte opérationnelle de sa maison.
- **Interaction :** Il ouvre le Crew Panel et prend connaissance de la consommation exacte ($) de chaque membre de l'équipage, y compris les processus invisibles (Dieu). Cette consultation informe sans imposer d'ajustement technique immédiat.
- **Traceability :** Justifie FR-V4-04 et FR-V4-05.

---

## 4. Roadmap des Epics (V4 Priority)

| Epic | Titre | Statut | Valeur Utilisateur |
| :--- | :--- | :--- | :--- |
| **13** | **Deep Cognitive Memory** | **IN PROGRESS** | Permettre aux agents de "se souvenir" de manière cohérente et d'évoluer avec l'utilisateur. |
| **17** | **The High-Fi Stage** | **IN PROGRESS** | Offrir un contrôle total sur l'équipage et les coûts sans briser l'immersion. |
| **18** | **Social Dynamics** | **PLANNED** | Transformer la discussion "IA-User" en une interaction sociale riche entre agents. |
| **14** | **Sensory Presence** | **PLANNED** | Entendre et parler avec le naturel d'une présence humaine. |
| **15** | **Visual Imagination** | **PLANNED** | Visualiser instantanément n'importe quelle situation ou émotion décrite. |

---

## 5. Functional Requirements (V4 Specific)

### 5.1 Intelligence & Mémoire
- **FR-V4-01 Matrix Initialization :** Le système initialise les liens relationnels initiaux entre agents au démarrage.
- **FR-V4-02 Conflict Resolution :** Le système arbitre entre deux faits contradictoires via un processus de synthèse.
- **FR-V4-03 Semantic Decay :** Les faits non-renforcés perdent en force de rappel avec le temps.

### 5.2 Interaction & UI
- **FR-V4-04 Real-time Token Billing :** Affichage du coût en dollars par agent dans le Crew Panel.
- **FR-V4-05 Invisible Agent Control :** Capacité d'interagir et de configurer les agents sans avatar (ex: Dieu/Entropy).
- **FR-V4-06 Spatial Routing Badge :** Indicateur visuel de la pièce active dans l'interface.

---

## 6. Non-Functional Requirements

- **NFR-V4-01 Performance (Graph) :** Temps de recherche dans le graphe de connaissances < 500ms.
- **NFR-V4-02 Privacy (STT) :** Traitement local (95% des requêtes effectuées localement) pour l'écoute continue et le mot de réveil.
- **NFR-V4-03 Scalability :** Support de 10 agents actifs simultanés sans dégradation de la latence du bus d'événements.

---
*Dernière mise à jour par John (PM) le 08 Février 2026.*