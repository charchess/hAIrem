# Architecture Design: Sensory Pipeline (Epic 14)

**Version:** 1.0
**Status:** Implémenté
**Author:** Winston (Architect)
**Date:** 2026-01-28

---

## 1. Introduction

Ce document définit l'architecture des flux sensoriels (audition et parole) de hAIrem. L'objectif est de permettre une interaction vocale fluide, à faible latence, intégrée au protocole H-Link.

## 2. Flux d'Audition (Ears : ASR)

Le pipeline d'audition transforme la voix de l'utilisateur en texte traité comme un stimulus par le Core.

### 2.1 Capture & Streaming
1. **A2UI :** Capture l'audio via l'API Web MediaRecorder (format Opus/WebM).
2. **H-Bridge :** Reçoit les chunks audio par WebSocket et les accumule dans un buffer mémoire.
3. **Transcription (Whisper) :** 
   - Utilisation d'une instance **Faster-Whisper** (locale ou containerisée).
   - Le Bridge envoie le buffer au service de transcription une fois le silence détecté (VAD - Voice Activity Detection).
4. **H-Link :** Le texte transcrit est publié sur Redis avec le type `system.whisper`.

## 3. Flux de Parole (Voice : TTS & Modulation)

Le système doit être agnostique vis-à-vis des moteurs de synthèse pour permettre l'utilisation de voix ultra-réalistes ou clonées (Luxa, ElevenLabs, Piper).

### 3.1 Abstraction Provider
1. **TTS Service :** Interface générique `VoiceProvider`.
2. **Voice Profiles :** Chaque agent définit dans son `persona.yaml` :
   - `provider` : Le moteur à utiliser (ex: `luxa`).
   - `voice_id` : L'identifiant de la voix de référence.
   - `modulation_params` : Paramètres de ton, de vitesse et d'émotion (injectables dynamiquement selon le sentiment de la réponse).

### 3.2 Clonage & Imitation (Luxa/Advanced)
- Pour les agents nécessitant une identité vocale forte, le pipeline supporte le **Zero-Shot Voice Cloning**. 
- Un échantillon de 10s de la voix de référence est stocké dans `agents/{id}/media/voice_ref.wav`.
- Le provider utilise cette référence pour générer chaque réponse, garantissant une signature vocale unique.

### 3.2 Rendu
1. **A2UI :** Reçoit l'URL, précharge l'audio et déclenche la lecture en synchronisation avec l'affichage du texte (si possible avec des marqueurs de synchronisation labiale / visèmes).

## 4. Latence et Optimisation

- **Local Inference :** Utilisation de modèles quantifiés (Piper GMS, Whisper Tiny/Base) pour garantir une réponse en < 1s.
- **Caching :** Les réponses TTS courantes ("Bonjour", "D'accord") sont cachées par hash SHA-256 dans Redis pour éviter la régénération.

---
🏗️ Winston - Architecte hAIrem
