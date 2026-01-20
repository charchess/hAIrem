# Project Brief: hAIrem Framework

**Version:** 1.0  
**Status:** Finalized (Interactive Session)  
**Date:** Mardi 20 Janvier 2026  

---

## 1. Résumé Analytique (Executive Summary)

**Concept du Produit :**
hAIrem est un framework pionnier de "Maison Vivante" fusionnant la collaboration agentique spécialisée et l'incarnation narrative. Il se positionne à l'intersection inédite des frameworks techniques (type CrewAI), du roleplay immersif (type SillyTavern) et de la domotique (Home Assistant), créant un écosystème d'experts incarnés en un "équipage" cohérent.

**Problème Principal :**
Les IA actuelles sont soit des outils transactionnels "froids" sans âme, soit des entités de divertissement sans utilité concrète ni contexte environnemental. Il n'existe pas de solution offrant une collaboration proactive et autonome au sein d'un écosystème incarné et persistant qui interagit avec le monde physique.

**Proposition de Valeur Clé :**
Au-delà du simple assistant, hAIrem introduit la **Cognition Temporelle** (cycles veille/sommeil analytique) et un **Directeur Narratif** qui garantit l'évolution et la cohérence de l'écosystème. Cela transforme une suite d'outils en un équipage proactif, capable de gérer des tâches complexes (numériques et domotiques) tout en tissant un lien émotionnel fort avec l'utilisateur via l'interface A2UI.

---

## 2. Énoncé du Problème (Problem Statement)

**État Actuel et Points de Douleur :**
Aujourd'hui, l'interaction avec l'IA est soit purement transactionnelle (ChatGPT), soit purement ludique (Character.ai). Les utilisateurs de domotique (Home Assistant) jonglent avec des assistants vocaux limités et "froids" qui ne comprennent pas leur contexte de vie global.

**Impact du Problème :**
*   **L'effet de lassitude :** Sans personnalité ni évolution, l'intérêt pour l'IA s'émousse rapidement.
*   **Fragmentation Cognitive :** L'utilisateur doit coordonner ses différents outils, créant une charge mentale.
*   **Manque de Confiance :** L'absence d'interface "humaine" et de mémoire persistante empêche la délégation de tâches critiques.

---

## 3. Solution Proposée (Proposed Solution)

**Concept Central :**
hAIrem propose un framework où l'IA n'est plus un outil que l'on appelle, mais un **"Équipage Virtuel"** qui habite l'interface.

**Piliers de la Solution :**
1.  **L'A2UI (Agent-to-User Interface) :** Un moteur de rendu type Visual Novel utilisant des calques dynamiques (poses/émotions).
2.  **L'Inter-agentivité Native :** Un protocole de communication (Bus Redis) permettant aux agents de collaborer de manière asynchrone.
3.  **La Cognition Temporelle & le Director "Éveillable" :**
    *   **Cycles Veille/Sommeil :** Consolidation des données et synthèse mémorielle pendant l'inactivité.
    *   **Directeur Narratif Stateful :** Un agent méta intermittent qui garantit la cohérence globale et introduit des éléments de "vie".

---

## 4. Utilisateurs Cibles (Target Users)

*   **Segment Primaire : L'Orchestrateur Domotique**
    *   Utilisateur technophile (Home Assistant) cherchant à déléguer la gestion quotidienne à un équipage autonome et proactif.
*   **Segment Secondaire : Le Développeur Créatif / Amateur de RP**
    *   Passionné de LLM et de design narratif cherchant un framework modulaire pour créer des scénarios d'interaction complexes.
*   **Cas d'Usage "Social Good" : L'Assistant de Présence**
    *   Pour les personnes isolées, offrant une présence bienveillante et une sécurité proactive sans intrusion.

---

## 5. Objectifs et Métriques de Succès (Goals & Metrics)

**Le "Noyau Dur" des Métriques MVP :**
1.  **Taux d'Incarnation Quotidienne (DAE) :** L'utilisateur ouvre-t-il l'interface A2UI au moins une fois par jour ?
2.  **Taux de Validation de la Proactivité :** Les suggestions de l'agent sont-elles acceptées par l'utilisateur ?
3.  **Coût Opérationnel de la "Vie" :** Le coût en tokens/calcul pour maintenir l'agent "éveillé" est-il soutenable ?

---

## 6. Périmètre du MVP (MVP Scope)

**Fonctions Noyau (Framework) :**
*   **Interface A2UI "Lightweight" :** Affichage calques images/texte, faible consommation.
*   **Architecture de Déportation :** Appels API/Webhook pour les ressources lourdes (LLM, ComfyUI).
*   **Moteur d'Expertise Modulaire :** Plugins experts (YAML + Python) chargés dynamiquement.
*   **Bus de Communication (Redis) :** Cœur réactif pour les échanges inter-agents.
*   **Le Duo Initial :** La Renarde (Coordinatrice) et l'Expert Domotique.

**Hors Périmètre MVP :**
*   Gestion budgétaire (module futur).
*   Génération d'images locale (déportée).
*   Animation fluide (reste en style VN).

---

## 7. Vision Post-MVP

*   **Soul Transfer :** Changer l'enveloppe visuelle en gardant la mémoire.
*   **Économie Inter-Agentive :** Budget de tokens pour les agents.
*   **Vie Autonome Visible :** Les agents interagissent entre eux dans l'interface sans solliciter l'utilisateur.
