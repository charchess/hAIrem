# Brainstorming Session Results: hAIrem Framework

**Date :** Mardi 20 Janvier 2026
**Participants :** Lisa (User) & Mary (Analyst)

---

## 1. Vision & Concept
*   **Maison Vivante :** Transformer l'assistant IA en un "équipage" qui habite la maison.
*   **Inspiration Visual Novel :** Utiliser des codes esthétiques de VN (poses, expressions, calques) pour l'incarnation.
*   **Vocal-First :** L'interaction doit être fluide à la voix (enceintes connectées), l'image est un bonus d'incarnation émotionnelle.

## 2. Décisions Architecturales (Pivots)
*   **Thin Orchestrator :** Le framework est léger. Il délègue l'inférence LLM (Ollama/OpenAI) et la génération d'images (ComfyUI) à des serveurs déportés pour ne pas saturer le CPU/GPU local.
*   **H-Core (Bus Redis) :** Utilisation de Redis (Pub/Sub) pour une communication asynchrone entre agents. Un agent peut "écouter" sans être sollicité.
*   **Hot-Reload :** Chargement dynamique des experts via `expert.yaml` sans redémarrage.
*   **Mémoire Subjective :** Base de données centrale avec indexation par agent.

## 3. Le Narrative Director (ND)
*   **Rôle :** "Jardinier Narratif".
*   **Fonctionnement :** Intermittent (pas un LLM 24/7). S'éveille la nuit ou sur triggers pour synthétiser les logs, assurer la cohérence et injecter du "chaos" (micro-incidents de personnalité).

## 4. Expérience Utilisateur (A2UI)
*   **Réactivité :** Utilisation du streaming LLM.
*   **État "Pensif" :** Dès que l'utilisateur parle, l'agent change de pose pour montrer qu'il écoute/réfléchit (réduction de la perception de latence).
*   **Équipage de lancement :**
    *   **La Renarde :** Coordinatrice sociale, visage du système.
    *   **L'Expert Domotique :** Traducteur technique pour Home Assistant.

## 5. Scénarios d'Échec identifiés (Prévention)
*   **Interruption vs Incarnation :** Éviter que l'IA ne devienne un "Clippy" envahissant. L'incarnation doit pouvoir être passive.
*   **Le Syndrome du Tamagotchi Mort :** S'assurer que l'utilisateur ne se sente pas exclu si les agents "vivent" trop de choses pendant son absence.
*   **Coût des tokens :** L'architecture doit être optimisée pour être économiquement viable pour un particulier.

---
**Statut :** Clos - Utilisé comme base pour le Project Brief v1.0.
