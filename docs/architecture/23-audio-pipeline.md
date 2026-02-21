# Architecture Design: Pipeline Audio Complet (La Voix — Sprint 21)

**Version:** 1.0
**Status:** Implémenté
**Author:** Winston (Architect)
**Date:** 2026-02-22

---

## 1. Introduction

Le Sprint 21 "La Voix" introduit l'interaction vocale bidirectionnelle dans hAIrem. L'objectif est de transformer la voix de l'utilisateur en stimulus traité par les agents, et les réponses des agents en audio synthétisé restitué à l'utilisateur.

Le pipeline complet couvre : détection du wakeword → transcription (STT) → reconnaissance du locuteur → publication H-Link → traitement agent → synthèse vocale (TTS) → file de lecture audio.

---

## 2. Architecture — Vue d'Ensemble

```mermaid
flowchart LR
    MIC[Microphone] --> WW[WakewordDetector]
    WW -->|wakeword détecté| STT[STT Service\nfaster-whisper]
    STT -->|texte transcrit| VR[VoiceRecognition\nidentification locuteur]
    VR -->|HLink USER_MESSAGE\nuser_id injecté| RS[(Redis\nconversation_stream)]
    RS --> AGT[Agents\nLisa / Renarde / …]
    AGT -->|NARRATIVE_TEXT| TTS[TTS Orchestrator]
    TTS --> SQ[SpeechQueue\nPriorityQueue]
    SQ -->|audio base64| SS[(Redis\nsystem_stream)]
    SS --> UI[A2UI / Bridge]
```

Les deux canaux Redis clés :
- `conversation_stream` — bus principal des messages H-Link (USER_MESSAGE, NARRATIVE_TEXT)
- `system_stream` — événements système et broadcast audio vers l'interface

---

## 3. Wakeword Detector

**Fichier :** `src/features/home/wakeword/wakeword.py`

Surveille en continu le flux audio et déclenche le pipeline STT lorsqu'un wakeword est détecté.

| Propriété | Valeur |
|-----------|--------|
| Moteur | `openwakeword` (optionnel, graceful degradation) |
| Période de grâce | 5 secondes après détection |
| Paramètre Redis | `redis_client=None` (optionnel) |

Méthode centrale :

```python
def process_audio(self, buffer: bytes) -> Optional[str]:
```

À la détection, publie sur `conversation_stream` :

```python
HLinkMessage(type=MessageType.USER_MESSAGE, ...)
```

En l'absence d'`openwakeword`, le détecteur se désactive silencieusement sans bloquer le démarrage.

---

## 4. STT Service

**Fichier :** `src/services/audio/stt_service.py`

Wrapper autour de `faster-whisper` pour la transcription audio-vers-texte.

```python
async def transcribe(self, audio_bytes: bytes) -> str: ...
async def transcribe_and_publish(self, audio_bytes: bytes) -> None: ...
```

`transcribe_and_publish()` transcrit puis publie un `HLinkMessage(USER_MESSAGE)` sur `conversation_stream`.

**Graceful degradation :** si `faster-whisper` n'est pas installé, `transcribe()` retourne une chaîne vide et logue un avertissement.

---

## 5. Voice Recognition

**Répertoire :** `src/features/home/voice_recognition/`

Identifie le locuteur à partir de l'empreinte vocale et enrichit le message H-Link avec `user_id` et `user_name`.

- Si le locuteur est reconnu : `user_id` injecté dans le `Payload`
- Si non identifié : fallback `user_id = "anonymous"`
- `FallbackBehavior` : gestion des sessions non identifiées avec tentative de ré-identification différée

---

## 6. TTS Orchestrator

**Fichier :** `src/services/audio/tts_orchestrator.py`

Orchestre la synthèse vocale avec un mécanisme de fallback entre providers.

```
Provider primaire : MeloTTS (instance Docker locale)
Provider secondaire : ElevenLabs (REST API)
```

Comportement :
1. Tente le provider primaire
2. Si échec ou indisponible → bascule sur le provider secondaire
3. Broadcast du résultat audio (base64) sur `system_stream`

### 6.1 MeloTTSProvider

**Fichier :** `src/services/audio/melotts_provider.py`

Appel HTTP POST vers le conteneur MeloTTS local. Retourne les octets audio.

### 6.2 ElevenLabsProvider

**Fichier :** `src/services/audio/elevenlabs_provider.py`

Appel REST API ElevenLabs. Nécessite `ELEVENLABS_API_KEY` dans les variables d'environnement.

---

## 7. SpeechQueue

**Fichier :** `src/services/audio/speech_queue.py`

File de priorité FIFO pour ordonner les requêtes de synthèse.

| Priorité | Usage |
|----------|-------|
| `0` | Messages urgents (réponse directe utilisateur) |
| `1` | Réponses normales des agents |

```python
@dataclass
class SpeechRequest:
    text: str
    agent_id: str
    priority: int = 1
    voice_id: Optional[str] = None
```

### 7.1 Barge-in (Interruption)

```python
def interrupt(self) -> None:
```

Vide la queue et pose `is_interrupted = True`. Le flag est réinitialisé automatiquement au prochain `enqueue()`. Permet l'interruption de la parole d'un agent quand l'utilisateur prend la parole.

---

## 8. Neural Voice

**Fichier :** `src/services/audio/neural_voice.py`

Chaque agent peut avoir une voix distincte définie dans sa configuration.

```python
# src/models/agent.py
class AgentConfig(BaseModel):
    voice_id: Optional[str] = None
```

La voix est transmise à la `SpeechRequest` et acheminée au provider TTS. Override possible via `persona.yaml`.

---

## 9. Audio Pipeline Orchestrateur

**Fichier :** `src/services/audio/audio_pipeline.py`

Composant chapeau qui orchestre la séquence STT → VoiceRecognition → publication H-Link.

- Injecte le `user_id` résolu dans le message H-Link
- Fallback `"anonymous"` si la reconnaissance vocale échoue
- Point d'entrée unique pour le traitement d'un buffer audio entrant

---

## 10. Dépendances & Graceful Degradation

| Dépendance | Usage | Comportement si absente |
|------------|-------|------------------------|
| `openwakeword` | Wakeword detection | Détecteur désactivé silencieusement |
| `faster-whisper` | STT transcription | `transcribe()` retourne `""` |
| `pyaudio` | Capture micro | Capture désactivée |
| `httpx` | Appels MeloTTS / ElevenLabs | Providers TTS indisponibles |
| MeloTTS Docker | Provider TTS primaire | Fallback ElevenLabs |
| ElevenLabs API | Provider TTS secondaire | Pas de TTS |

Toutes les dépendances optionnelles sont importées en `try/except ImportError` pour ne pas bloquer le démarrage du Core.
