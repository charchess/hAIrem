# Epic 14: Sensory Layer (Ears & Voice)

**Status:** In Definition
**Theme:** Pillar 2 - Deep Presence
**PRD Version:** V3

## 1. Vision
Donner un corps sonore aux agents. hAIrem doit pouvoir entendre (STT) et parler (TTS) avec une latence quasi humaine, tout en respectant la vie privée (traitement local prioritaire).

## 2. Objectifs Métier
- **Immersion Vocale :** Chaque agent possède sa propre voix unique (clonage ou synthèse spécialisée).
- **Mains Libres :** Interaction via Wakeword ("Hey Lisa") sans toucher au clavier.
- **Latence < 1s :** La fluidité de la conversation dépend de la vitesse de la boucle Audio -> Texte -> LLM -> Texte -> Audio.

## 3. Exigences Clés
- **Requirement 14.1 (Audio Ingestion) :** Capturation du flux micro via le navigateur (A2UI) ou un micro distant (ESP32-S3).
- **Requirement 14.2 (Wakeword Engine) :** Détection locale et sécurisée du mot de réveil.
- **Requirement 14.3 (Whisper Pipeline) :** Transcription locale (Faster-Whisper) avec support du contexte (mots-clés hAIrem).
- **Requirement 14.4 (Neural TTS) :** Synthèse vocale hybride (Piper pour la rapidité, ElevenLabs pour la haute fidélité émotionnelle).

## 4. Contraintes de Design
- **Privacy :** L'audio n'est jamais envoyé au cloud pour le Wakeword ou le STT standard.
- **Interruption :** Le système doit arrêter de parler si l'utilisateur l'interrompt vocalement (Barge-in).

---
*Défini par John (PM) le 26 Janvier 2026.*
