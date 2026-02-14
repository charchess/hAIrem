---
title: hAIrem Product Requirements Document (PRD)
version: 4.1
status: Approved
classification:
  domain: general
  projectType: web_app
inputDocuments: []
stepsCompleted: [1]
---

# hAIrem Product Requirements Document (PRD) - V4

**Version:** 4.1
**Status:** Approved ✅
**Theme:** "Deep Cognition, True Presence & Visual Imagination"

---

## 1. Vision & Goals

**V4 (The Goal):** Transformer hAIrem en une entité capable de cognition profonde et d'expression visuelle dynamique.
*   **Deep Mind:** Mémoire subjective, hiérarchisation des stimuli et cycle de sommeil.
*   **Deep Presence:** Voix neuronales, présence visuelle cohérente et conscience de l'état physique (tenue/lieu).
*   **Deep Home:** Réactions proactives, architecture de compétences (Skills) pluggables et imagination anticipée.

---

## 2. Les Trois Piliers

### Pilier 1 : Deep Mind (Architecture Cognitive)
*   **Subjective Graph Memory (Epic 13) :** Base de données de graphe avec MDP.
*   **Cognitive Cycle (New V4) :** Cycle de consolidation nocturne. Passage de la mémoire courte vers le long terme et génération de stimuli "rêvés" pour la proactivité du lendemain.
*   **Stimuli Hierarchy (Epic 18) :** Hiérarchisation des flux gérée par le Social Arbiter.

...

## 4. Métriques de Succès
- **Latence Visuelle :** Asset prêt en < 5s (Warm cache) ou < 20s (Génération + Détourage).
- **Stabilité Système :** 100% de disponibilité des services LLM/Imaging grâce à la gestion de la file d'attente d'inférence.
- **Pertinence Cognitive :** Augmentation mesurable des références aux conversations passées suite au cycle de consolidation.
*   **Social Dynamics (Epic 18) :** 
    - **Onboarding :** Session d'initialisation des relations (entretien d'embauche virtuel).
    - **Polyphonie :** Gestion des tours de parole et conscience de l'existence des autres agents.

### Pilier 2 : Deep Presence (Corps & Sens)
*   **Sensory Layer (Epic 14) :** Transcription et synthèse vocale multi-voix. Candidats : Orpheus, Melo, RVC, OpenVoice (focus sur prosodie et intonation).
*   **Imagination Visuelle (Epic 25) :** 
    - **Visual Bible :** Pilotage scientifique (FACS/Mehrabian) et styles modulaires.
    - **Vault System :** Inventaire nommé des tenues (Garde-robe) et décors de référence.
*   **Spatial Presence (Core V4) :** 
    - **Localization :** Capacité pour les agents d'être assignés à des lieux physiques (Cuisine, Bureau).
    - **Device Hierarchy :**
        - *Fixed Stages :* Tablettes murales liées à une pièce (affichage statique du lieu).
        - *Mobile Stages :* Appareils nomades (tablettes/laptops) avec suivi de localisation.
        - *Remote Stages :* Accès extérieur (Interface "Pocket"). Alfred agit comme concierge dans un espace virtuel extérieur (Jardin/Ville), mais les agents domestiques restent accessibles via le flux narratif global (ex: Electra répondant à une question sur la domotique).
    - **Multi-Stage UI :** Support de plusieurs clients avec backgrounds locaux et bus audio global.

### Pilier 3 : Deep Home (Habitat & Skills)
*   **Architecture Persona-Skill (Epic 15) :** Découplage total entre l'identité et les capacités techniques.
*   **Proactivité Mondiale (Epic 18/25) :** 
    - **World State :** Gestion des thèmes globaux (Noël, Saisons, Météo) par Entropy (Dieu).
    - **Thematic Cascade :** Un changement de thème (ex: Noël) déclenche automatiquement la ré-imagination des décors de tous les lieux et suggère des changements de tenues aux agents.

---

## 3. Roadmap des Epics (V4)

| Epic | Titre | Statut |
| :--- | :--- | :--- |
| **13** | **Deep Cognitive Architecture** | DONE |
| **25** | **Visual Imagination (Modular)** | IN PROGRESS |
| **17** | **"The Stage" UI/UX (A2UI)** | DONE |
| **14** | **Sensory Layer (Ears & Voice)** | IN PROGRESS |
| **15** | **Living Home (Skills & Proactivity)** | IN PROGRESS |
| **18** | **Social Dynamics & Social Arbiter** | TO DO |

### Détails du Planning
*   **Epic 13 (Done) :** Le coeur cognitif est fonctionnel. La base de données stocke les souvenirs.
*   **Epic 17 (Done) :** L'interface "The Stage" est déployée avec le sélecteur d'agent (17.4) et le support mobile.
*   **Epic 25 (Focus Actuel) :** Le fournisseur d'imagination visuelle (25.1) est prêt. Prochaine étape : Asset Manager DB (25.2) pour lier les images aux lieux/personnages.
*   **Epic 14 & 15 :** En parallèle. L'intégration de la transcription et synthèse vocale (14) et l'architecture Skills (15) sont en cours de définition technique.
*   **Epic 18 :** Futur proche. C'est ici que nous gérerons le "Pocket Mode" d'Alfred et la localisation dynamique.

---

## 4. Métriques de Succès
- **Latence Visuelle :** Asset prêt en < 5s (Warm cache) ou < 20s (Génération + Détourage).
- **Consistance Visuelle :** Identité des agents et décors préservés à > 90% via le système de Vaults.
- **Réactivité Contextuelle :** 100% de succès sur les interactions liées à la "Burning Memory" (ex: réactions aux tenues).
- **Fiabilité Stimuli :** Zéro collision de stimuli critiques grâce à la hiérarchisation.

---

## 5. User Journeys

*   **UJ-01 (Cognitive Deepening) :** L'utilisateur interagit longuement. La nuit, le système consolide ces faits. Le lendemain, l'agent mentionne un détail de la veille de manière proactive.
*   **UJ-02 (Multi-Stage Presence) :** L'utilisateur passe de la cuisine (Fixed Stage) au jardin (Remote Stage). Alfred assure la transition narrative et le flux audio sans interruption.

## 6. Functional Requirements

*   **FR-01 :** Le système peut consolider les souvenirs à court terme en mémoire à long terme durant le cycle de sommeil.
*   **FR-02 :** Les agents peuvent percevoir et réagir à l'état du monde (thèmes, météo, événements).

## 7. Non-Functional Requirements

*   **NFR-01 (Performance) :** La synthèse vocale doit commencer en moins de 800ms après la fin de la transcription.
*   **NFR-02 (Disponibilité) :** Le bus audio global doit maintenir une disponibilité de 99.9%.

---
*Approuvé par John (PM) le 28 Janvier 2026.
