# Architecture Design: Observabilité & Monitoring (L'Observatoire — Sprint 23)

**Version:** 1.0
**Status:** Implémenté
**Author:** Winston (Architect)
**Date:** 2026-02-22

---

## 1. Introduction

Le Sprint 23 "L'Observatoire" rend l'activité interne du système visible et monitorable en production. Cinq composants ont été implémentés : collecte de métriques, signal de parole agent, log handler async-safe, interruption barge-in, et budget de discussion.

---

## 2. MetricsCollector

**Fichier :** `src/services/metrics.py`

Collecteur de métriques léger sans dépendance externe. Exposé comme singleton global.

```python
from src.services.metrics import get_metrics

metrics = get_metrics()
metrics.increment("messages_processed")
metrics.observe("tts_latency_seconds", 0.42)
```

### 2.1 Interface

| Méthode | Description |
|---------|-------------|
| `increment(name, value=1)` | Incrémente un compteur |
| `get(name) → float` | Lit la valeur courante d'un compteur |
| `observe(name, value)` | Enregistre une observation dans un histogramme |
| `get_avg(name) → float` | Moyenne des observations pour un histogramme |
| `to_prometheus_text() → str` | Export au format texte Prometheus |

### 2.2 Format d'export Prometheus

```
messages_processed 42
llm_calls 17
tts_latency_seconds_avg 0.385
tts_latency_seconds_count 17
```

Le format est compatible avec un scraping Prometheus standard. Un endpoint `/metrics` FastAPI peut être branché sur `to_prometheus_text()` sans modification supplémentaire.

### 2.3 Singleton

```python
def get_metrics() -> MetricsCollector:
```

Retourne toujours la même instance — les compteurs sont partagés entre tous les modules du processus.

---

## 3. Signal agent.speaking

**Fichier :** `src/domain/agent.py` — méthode `generate_response()`

Avant chaque appel LLM, `BaseAgent` publie un signal sur `system_stream` indiquant que l'agent est en train de "parler" (i.e., de préparer une réponse).

```json
{
  "type": "agent.speaking",
  "sender": {"agent_id": "lisa", "role": "guide"},
  "payload": {"content": {"speaking": true}}
}
```

Ce signal permet au Bridge et à l'A2UI de :
- Afficher une animation de lèvres sur l'avatar de l'agent
- Afficher un indicateur "en train de répondre…"
- Désactiver temporairement la détection wakeword pour éviter la boucle

Le signal est émis en `try/except` silencieux pour ne pas bloquer la génération de réponse en cas d'erreur Redis.

---

## 4. RedisLogHandler Async-Safe

**Fichier :** `src/main.py`

Le `RedisLogHandler` diffuse les logs Python vers Redis pour visibilité depuis l'UI. Le handler original utilisait `asyncio.create_task()` qui lève `RuntimeError` lorsqu'aucune boucle événements n'est en cours.

**Correction appliquée :**

```python
try:
    loop = asyncio.get_running_loop()
    loop.create_task(self.redis.publish_event("system_stream", data))
except RuntimeError:
    pass
```

`asyncio.get_running_loop()` retourne la boucle courante si elle existe, ou lève `RuntimeError` si aucune boucle n'est active. Le `except RuntimeError` garantit que le handler ne crashe jamais hors contexte async (ex. : démarrage synchrone, tests unitaires).

Pour activer le handler en production, décommenter dans `HaremOrchestrator.start()` :

```python
log_handler = RedisLogHandler(self.redis)
logging.getLogger().addHandler(log_handler)
```

---

## 5. Barge-in Detection

**Fichier :** `src/services/audio/speech_queue.py`

Lorsque l'utilisateur parle pendant qu'un agent TTS est actif, le système doit interrompre immédiatement la lecture audio en cours.

```python
def interrupt(self) -> None:
    self.is_interrupted = True
    while not self._queue.empty():
        try:
            self._queue.get_nowait()
        except asyncio.QueueEmpty:
            break
```

Comportement :
1. `is_interrupted` est posé à `True`
2. Toutes les requêtes TTS en attente sont supprimées
3. Le flag est réinitialisé automatiquement au prochain `enqueue()`

Le composant TTS Orchestrator consulte `is_interrupted` avant de commencer la synthèse d'une nouvelle requête.

---

## 6. Budget de Discussion (Polyphonie)

**Fichier :** `src/features/home/social_arbiter/arbiter.py`

Le Social Arbiter peut décider d'arrêter une discussion multi-agents après un nombre de tours défini, pour éviter que les agents ne monopolisent le canal.

```python
self.discussion_turn: int = 0
self.max_discussion_turns: int = 20

def should_stop_discussion(self) -> bool:
    return self.discussion_turn >= self.max_discussion_turns
```

Le compteur `discussion_turn` est incrémenté à chaque appel à `update_agent_stats()`, c'est-à-dire à chaque réponse émise par un agent. Quand `should_stop_discussion()` retourne `True`, l'arbitre peut inhiber les réponses spontanées et redonner la main à l'utilisateur.

`max_discussion_turns` est configurable par instance — la valeur par défaut de 20 est adaptée à une conversation naturelle de durée raisonnable.

---

## 7. Tests

**Fichier :** `apps/h-core/tests/test_sprint23_observatoire.py`

20 tests couvrant les 5 composants :

| Classe de test | Composant | Tests |
|----------------|-----------|-------|
| `TestMetricsCollector` | MetricsCollector | 7 |
| `TestAgentSpeakingSignal` | agent.speaking | 2 |
| `TestRedisLogHandlerAsyncSafe` | RedisLogHandler | 2 |
| `TestSpeechQueueInterrupt` | SpeechQueue.interrupt() | 4 |
| `TestDiscussionBudgetStop` | SocialArbiter budget | 5 |

---

## 8. Pistes d'Extension

| Extension | Effort | Priorité |
|-----------|--------|----------|
| Endpoint FastAPI `/metrics` exposant `to_prometheus_text()` | S | Moyenne |
| Dashboard Grafana avec scraping Prometheus | M | Basse |
| Signal `agent.done_speaking` après fin TTS | S | Haute |
| Métriques LLM (latence, tokens) auto-instrumentées dans `generate_response()` | S | Haute |
| Alerting sur `discussion_turn > max` via `system_stream` | S | Basse |
