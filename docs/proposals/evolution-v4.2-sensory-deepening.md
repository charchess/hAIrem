# Proposition d'Évolution v4.2 : Approfondissement Sensoriel

**Auteur :** hAIrem Core Agent
**Date :** 16 Février 2026
**Objet :** Intégration de la reconnaissance d'émotions vocales et de l'identification du locuteur.

## 1. Objectif
Passer d'une interface de "transcription textuelle" à une interface de "perception sensorielle". L'objectif est de permettre aux agents de savoir **qui** parle et **dans quel état émotionnel**, afin d'ajuster dynamiquement leur comportement, leur voix (ElevenLabs) et leurs visuels.

## 2. Architecture Technique Suggérée

L'idée est d'enrichir le pipeline audio actuel dans le container `h-bridge` en ajoutant deux moteurs d'analyse en parallèle de Whisper.

### A. Reconnaissance d'Émotions (SER) via Wav2Vec 2.0
*   **Moteur :** Modèle Wav2Vec 2.0 (fine-tuned sur RAVDESS/ESD).
*   **Fonctionnement :** Analyse les caractéristiques acoustiques (prosodie, fréquence, intensité) pour classifier l'audio.
*   **Sortie :** Vecteur de probabilités sur 5-7 émotions (Joy, Anger, Sadness, Fear, Surprise, Neutral).
*   **Avantage :** 100% local, très rapide sur CPU, déjà compatible avec les dépendances PyTorch du Bridge.

### B. Identification du Locuteur (SID) via ECAPA-TDNN
*   **Moteur :** ECAPA-TDNN (via la librairie SpeechBrain).
*   **Fonctionnement :** Génère un "Voiceprint" (embedding de 192 dimensions) unique à chaque individu.
*   **Processus d'Enrôlement :** Une phase unique de 5 secondes ("Bonjour Lisa") suffit pour créer l'empreinte.
*   **Stockage :** Empreinte stockée sous forme de vecteur dans SurrealDB (table `subject`).
*   **Avantage :** Modèle ultra-léger (~80 Mo), haute précision, souveraineté totale.

## 3. Flux de Données (Data Flow)

1.  **Audio Buffer :** Le flux microphone est capturé.
2.  **Analyse Triple (Parallèle) :**
    *   **Whisper :** Audio ⮕ Texte ("Qu'est-ce qui est dit ?").
    *   **Wav2Vec :** Audio ⮕ Emotion Metadata ("Comment c'est dit ?").
    *   **ECAPA-TDNN :** Audio ⮕ Speaker Embedding ("Qui parle ?").
3.  **Enrichissement H-Link :** Les trois résultats sont fusionnés dans un `MessageType.USER_MESSAGE` enrichi :
    ```json
    {
      "type": "user_message",
      "payload": {
        "content": "Bonjour Lisa",
        "sensory": {
          "emotion": {"label": "joy", "score": 0.92},
          "speaker_id": "user_master",
          "is_recognized": true
        }
      }
    }
    ```
4.  **Réaction Cognitive :** L'agent utilise ces métadonnées pour pondérer son `ScoringEngine` et ajuster son ton TTS.

## 4. Impact sur les Epics existants

*   **Epic 26 (Advanced NPC) :** Devient le pilier de l'interaction personnalisée (ex: "Lisa est plus timide avec les inconnus identifiés par ECAPA").
*   **Epic 14 (Voice) :** La modulation ElevenLabs utilise directement le label d'émotion Wav2Vec pour choisir le style de voix.
*   **Sécurité (Epic 7) :** Permet de restreindre des commandes domotiques sensibles au "Voice ID" du propriétaire.

## 5. Prochaines Étapes BMAD
1.  **Draft PRD 4.2 :** Spécification détaillée des critères d'acceptation (AC) pour l'enrôlement vocal.
2.  **Phase Dev :** Ajout des librairies `speechbrain` et `transformers` au Dockerfile du Bridge.
3.  **Phase QA :** Validation de la précision du Speaker ID dans des environnements bruyants.

---
*Ce document sert de base de discussion pour le prochain cycle de développement.*
