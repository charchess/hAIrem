# Synthèse des Choix Techniques et Décisions (hAIrem)

Ce document résume les points clés extraits des fragments de discussion récupérés lors de la phase de restauration de février 2026.

## 1. Transition vers l'Architecture V4
*   **Objectif :** Passer d'un système réactif à un "Équipage Virtuel" conscient et proactif.
*   **Décision :** Adoption d'un style de documentation "workflow-driven" avec des artefacts générés automatiquement dans `_bmad-output`.
*   **Raison :** Centraliser la vérité technique et éviter la dérive entre les intentions (Epics) et l'implémentation (Stories).

## 2. Modèle de Mémoire et Cognition (Epic 13)
*   **Choix :** Migration vers un schéma de **Graphe Subjectif** dans SurrealDB.
*   **Détails :** Utilisation d'arêtes `BELIEVES`, `ABOUT`, et `CAUSED`.
*   **Raison :** Permettre aux agents d'avoir des croyances individuelles et des biais propres (Subjective Retrieval), tout en partageant des faits universels liés à l'agent `system`.
*   **Algorithmes :** Implémentation du **Semantic Decay** (érosion temporelle des souvenirs non renforcés) pour simuler l'oubli.

## 3. Évolution Audio et TTS (Epic 14)
*   **Choix :** Passage de Piper à **Qwen3-TTS 0.6B GGUF** via `llama.cpp`.
*   **Raison :** Support des **Dynamic LoRAs** pour permettre à chaque agent d'avoir une voix neuronale distincte et de haute qualité avec une faible latence.
*   **Audio Bridge :** Utilisation de WebSockets pour l'ingestion audio binaire en temps réel (`h-bridge`), avec une file d'attente (`audio_queue`) pour gérer la concurrence voix/texte.

## 4. Interface et UX (A2UI - Epic 17)
*   **Vision :** "The Living Stage" (Scène Vivante).
*   **Composants :** Navigation **Dual Panel**, intégration de **Modales UX**, et un **Crew Panel** affichant le statut et le coût (tokens) en temps réel.
*   **Highlighting :** Ajout de propriétés CSS `scale(1.05)` et "Arbitration Glow" pour identifier visuellement l'agent qui parle (Active Speaker).

## 5. Sécurité et Contexte (Epic 19)
*   **Problème :** Blocage de l'API `getUserMedia` (microphone) lors de l'accès via IP locale (contexte non sécurisé).
*   **Solution :** Recommandation de l'utilisation de **tunnels SSH** ou HTTPS pour garantir un "Secure Context" nécessaire aux fonctionnalités audio.
*   **Filtrage :** Implémentation de filtres de confidentialité (Privacy Filter) et de sanitisation des messages en sortie.

## 6. Normes de Développement
*   **Tests :** Priorité aux tests d'intégration avec **Pytest** pour les nouvelles fonctionnalités de graphe (tables Schemefull : `fact`, `subject`, `concept`).
*   **Logging :** Migration complète des `print()` vers le module `logging` standard pour une meilleure observabilité en production (Story 5.3).
*   **Conventions :** Standardisation des titres de stories au format `X-Y-titre` pour une meilleure traçabilité.
