# Sprint 21 — "La Voix" · STT, TTS & Wakeword Complet

**Période :** Mars 2026 (semaine 3-4)  
**Objectif :** Les agents entendent et parlent. Pipeline audio end-to-end fonctionnel.

---

## Contexte

Le pipeline audio est actuellement inexistant dans h-core. `VoiceModulator` génère du SSML textuel mais rien n'est branché sur un vrai moteur TTS. Whisper (STT) n'est pas intégré. Le `WakewordService` existe mais est probablement un stub.

**Architecture cible :**
```
Mic → Wakeword → Whisper (STT) → Message HLink → Agents → TTS (MeloTTS/ElevenLabs) → Speaker
```

---

## Stories

### Story 21.1 — Wakeword Engine (complétion Story 14.2)
**Priorité :** 🔴 HAUTE  
**Effort :** M

**Tests à écrire AVANT :**
```
apps/h-core/tests/test_wakeword_complete.py
- test_wakeword_detector_initializes_without_crash()
- test_wakeword_detects_agent_name()
  # Given: buffer audio contenant "Lisa, allume la lumière"
  # When: WakewordDetector.process_audio(buffer)
  # Then: event wakeword déclenché avec target="lisa"

- test_wakeword_ignores_non_wakeword_audio()
- test_wakeword_publishes_to_redis_on_detection()
  # Given: wakeword détecté
  # When: handler appelé
  # Then: message HLink publié sur conversation_stream avec target correct

- test_wakeword_service_lifecycle_start_stop()
```

**Implémentation :**
- Compléter `WakewordDetector.process_audio()` avec Vosk ou openWakeWord (léger, local)
- Brancher `WakewordService` dans le démarrage de h-core (actuellement non démarré)
- Ajouter à `docker-compose.yml` : service audio (accès `/dev/snd` ou stream réseau)

**Doc :** Mettre à jour `docs/stories/14.2-wakeword-engine.md` avec décisions d'implémentation.

---

### Story 21.2 — Pipeline STT (Whisper)
**Priorité :** 🔴 HAUTE  
**Effort :** M

**Tests à écrire AVANT :**
```
apps/h-core/tests/test_stt_pipeline.py
- test_whisper_transcribes_audio_chunk()
  # Given: fichier WAV de test (fixture)
  # When: WhisperService.transcribe(audio_bytes)
  # Then: retourne string non-vide

- test_whisper_returns_empty_on_silence()
- test_stt_pipeline_publishes_hlink_on_transcription()
  # Given: transcription réussie
  # When: pipeline complet
  # Then: HLinkMessage type=USER_MESSAGE sur conversation_stream

- test_stt_handles_timeout_gracefully()
- test_stt_privacy_filter_applied()
  # Given: transcription contenant un mot-clé secret
  # When: PrivacyFilter appliqué
  # Then: contenu filtré avant publication Redis
```

**Implémentation :**
- Créer `apps/h-core/src/services/audio/stt_service.py`
- Wrapper autour de `faster-whisper` (pip, inference locale GPU/CPU)
- Brancher sur le pipeline après wakeword
- `docker-compose.yml` : volume pour le modèle Whisper

---

### Story 21.3 — Pipeline TTS (MeloTTS primary, ElevenLabs fallback)
**Priorité :** 🔴 HAUTE  
**Effort :** L

**Tests à écrire AVANT :**
```
apps/h-core/tests/test_tts_pipeline.py
- test_melotts_synthesizes_text()
  # Given: texte "Bonjour, comment puis-je aider ?"
  # When: MeloTtsProvider.synthesize(text, voice_id)
  # Then: retourne bytes audio non-vide

- test_tts_applies_ssml_modulation()
  # Given: texte + émotion "joy"
  # When: VoiceModulator.apply_emotion() + TTS
  # Then: audio généré avec params prosodiques corrects

- test_elevenlabs_fallback_on_melotts_timeout()
  # Given: MeloTTS timeout > 800ms
  # When: TtsOrchestrator.synthesize()
  # Then: bascule automatique sur ElevenLabs

- test_speech_queue_serializes_concurrent_requests()
  # Given: 3 agents veulent parler en même temps
  # When: SpeechQueue reçoit les 3 requêtes
  # Then: elles sont jouées dans l'ordre (FIFO avec priorité user > agent)

- test_audio_chunk_broadcast_via_redis()
  # Given: synthèse terminée
  # When: audio prêt
  # Then: publié en chunks base64 sur system_stream pour le bridge
```

**Implémentation :**
- `apps/h-core/src/services/audio/tts_orchestrator.py` : abstraction TTS avec fallback
- `apps/h-core/src/services/audio/melotts_provider.py` : wrapper MeloTTS HTTP (Docker container)
- `apps/h-core/src/services/audio/elevenlabs_provider.py` : REST API ElevenLabs
- `apps/h-core/src/services/audio/speech_queue.py` : file FIFO avec priorités
- Ajouter service `melotts` dans `docker-compose.yml`

**NFR :** TTS latence < 800ms pour phrase courte (< 20 mots). Monitorer dans heartbeat.

---

### Story 21.4 — Neural Voice Assignment par agent
**Priorité :** 🟠 MOYENNE  
**Effort :** S

**Contexte :** `neural_voice_assignment.py` existe dans h-bridge mais n'est pas branché sur les agents au chargement.

**Tests :**
```
apps/h-core/tests/test_neural_voice.py
- test_each_agent_has_assigned_voice()
  # Given: Lisa, Renarde, Electra chargées
  # When: NeuralVoiceAssignment.get_voice(agent_id)
  # Then: voix distincte pour chaque agent

- test_voice_persists_between_sessions()
  # Given: voix assignée à Lisa en DB
  # When: redémarrage du système
  # Then: même voix récupérée
```

**Implémentation :** Lire `voice_id` depuis `manifest.yaml` ou SurrealDB. Brancher dans `BaseAgent.__init__`.

---

### Story 21.5 — Reconnaissance vocale par utilisateur
**Priorité :** 🟡 MOYENNE  
**Effort :** M

**Contexte :** `voice_recognition/` existe (embedding, matcher, models, repository) mais n'est pas branché dans le pipeline STT.

**Tests :**
```
apps/h-core/tests/test_voice_recognition_pipeline.py
- test_voice_embedding_identifies_registered_user()
- test_unknown_voice_defaults_to_anonymous()
- test_user_id_injected_in_hlink_message()
  # Given: voix reconnue comme "user_123"
  # When: HLink message créé
  # Then: payload.user_id = "user_123"
```

---

### Story 21.6 — Documentation Audio
**Livrable :** `docs/architecture/23-audio-pipeline.md`
- Schéma flux : Mic → Wakeword → STT → PrivacyFilter → Bus → Agents → TTS → Queue → Speaker
- Config Docker pour les services audio
- Variables d'environnement : `WHISPER_MODEL`, `MELOTTS_URL`, `ELEVENLABS_API_KEY`

---
