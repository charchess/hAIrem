# Sprint 23 — "L'Observatoire" · Monitoring, Polyphonie & Polish Final

**Période :** Avril 2026 (semaine 3-4)  
**Objectif :** Le système est observable, la polyphonie visuelle est complète, les derniers gaps UX sont fermés.

---

## Stories

### Story 23.1 — Monitoring Prometheus/Grafana
**Priorité :** 🟠 MOYENNE (NFR-V4-01)  
**Effort :** M

**Métriques cibles :**
- Latence graphe SurrealDB < 500ms (NFR-V4-01)
- Latence TTS < 800ms (NFR audio)
- Tokens consommés par agent (déjà en heartbeat → exporter)
- Temps de réponse par agent

**Tests à écrire AVANT :**
```
apps/h-core/tests/test_metrics.py
- test_graph_query_latency_recorded()
  # Given: query SurrealDB instrumentée
  # When: query exécutée
  # Then: MetricsCollector enregistre la durée

- test_tts_latency_recorded()
- test_token_counter_increments_correctly()
- test_metrics_endpoint_returns_prometheus_format()
  # Given: GET /metrics sur h-bridge
  # When: request
  # Then: format text/plain Prometheus valide
```

**Implémentation :**
- Ajouter `prometheus_client` aux dépendances
- Instrumenter : `SurrealDbClient._call()`, `TtsOrchestrator.synthesize()`, `LlmClient.get_completion()`
- Exposer `/metrics` dans h-bridge (FastAPI endpoint)
- `docker-compose.yml` : services `prometheus` + `grafana` avec dashboards pré-configurés
- Dashboard Grafana : latences, tokens/heure, agents actifs

---

### Story 23.2 — Polyphonie Visuelle (Arbitration Glow)
**Priorité :** 🟠 MOYENNE (Story 18.3)  
**Effort :** M

**Contexte :** Quand un agent parle, son avatar doit scale à 1.05 + halo lumineux. Les autres passent à 20% grayscale. Ce signal doit venir du backend.

**Tests à écrire AVANT :**
```
apps/h-core/tests/test_polyphony_signal.py
- test_speaking_agent_signal_published_on_bus()
  # Given: agent Lisa en train de générer sa réponse
  # When: BaseAgent.process_message() démarre
  # Then: HLink message type=agent.speaking { agent_id: "lisa", state: "speaking" } publié

- test_speaking_signal_cleared_on_response_end()
  # Given: Lisa a fini de parler
  # When: réponse complète publiée
  # Then: HLink message type=agent.speaking { state: "idle" } publié

- test_only_one_agent_speaking_at_a_time()
  # Given: Lisa et Renarde toutes deux en train de répondre
  # When: signaux publiés
  # Then: un seul agent en état "speaking" à tout moment (le premier)
```

**Implémentation :**
- Ajouter `MessageType.AGENT_SPEAKING` dans `hlink.py`
- Publier ce signal dans `BaseAgent` au début et à la fin de `process_message()`
- Le bridge transmet au frontend (déjà fait par le stream_worker)
- **Frontend (h-bridge/static)** : écouter `agent.speaking` → CSS scale + glow

---

### Story 23.3 — Flux de Discussion Inter-Agents (Story 18.4 complétion)
**Priorité :** 🟠 MOYENNE  
**Effort :** S

**Contexte :** `discussion_budget = 5` existe dans l'orchestrateur mais le budget n'est pas réinitialisé intelligemment et le stop sur "intérêt qui tombe" n'est pas implémenté.

**Tests :**
```
apps/h-core/tests/test_inter_agent_discussion.py
- test_discussion_stops_after_budget_exhausted()
  # Given: discussion_budget = 3
  # When: 3 échanges inter-agents
  # Then: 4ème message inter-agent ignoré

- test_discussion_budget_reset_on_user_message()
  # Given: budget épuisé
  # When: nouveau message utilisateur
  # Then: budget = MAX (5)

- test_arbiter_low_score_stops_cascade()
  # Given: réponse inter-agent avec UTS score < 0.3 pour tous
  # When: arbiter évalue
  # Then: None retourné, discussion s'arrête naturellement
```

---

### Story 23.4 — Détection du Barge-in
**Priorité :** 🟡 FAIBLE  
**Effort :** M

**Contexte :** Permettre à l'utilisateur d'interrompre un agent en cours de parole.

**Tests :**
```
apps/h-core/tests/test_barge_in.py
- test_barge_in_detected_during_tts()
  # Given: TTS en cours pour Lisa
  # When: input audio détecté (wakeword ou VAD)
  # Then: SpeechQueue.interrupt() appelé, TTS arrêté

- test_interrupted_agent_acknowledges()
  # Given: Lisa interrompue
  # When: barge-in
  # Then: Lisa publie courte réponse d'accusé
```

**Implémentation :**
- `SpeechQueue.interrupt()` : cancelle la tâche TTS courante
- `WakewordService` émet event `audio.barge_in` si audio détecté pendant TTS
- `HaremOrchestrator` souscrit à cet event

---

### Story 23.5 — HA Discovery Automatique
**Priorité :** 🟡 FAIBLE  
**Effort :** S

**Tests :**
```
apps/h-core/tests/test_ha_discovery.py
- test_ha_entities_fetched_on_startup()
- test_entity_list_cached_in_surrealdb()
- test_agent_tools_list_entities_from_cache()
```

**Implémentation :**
- `HaClient.get_all_entities()` → cache dans SurrealDB table `ha_entities`
- Appelé au démarrage dans `_background_setup()`

---

### Story 23.6 — Multi-room Audio Routing
**Priorité :** 🟡 FAIBLE  
**Effort :** L

**Tests :**
```
apps/h-core/tests/test_multiroom.py
- test_audio_routed_to_agent_room()
  # Given: Lisa dans "salon", Renarde dans "chambre"
  # When: Lisa parle
  # Then: audio broadcast uniquement vers speakers du "salon"

- test_user_location_determines_target_room()
  # Given: utilisateur détecté dans "cuisine"
  # When: message envoyé
  # Then: agents de la cuisine prioritaires dans arbiter
```

**Implémentation :**
- `LocationService.get_user_room()` via HA (présence BT/WiFi/RFID)
- Filtrage dans `SpeechQueue` par room_id
- HA target: `media_player.salon`, `media_player.chambre`

---

### Story 23.7 — RedisLogHandler (réparer la récursion)
**Priorité :** 🟡 FAIBLE  
**Effort :** S

**Contexte :** Le `RedisLogHandler` a été désactivé (commenté) pour éviter une boucle infinie. Les logs ne sont plus visibles dans l'UI.

**Tests :**
```
apps/h-core/tests/test_redis_log_handler.py
- test_log_handler_does_not_recurse()
  # Given: RedisLogHandler actif
  # When: une erreur se produit pendant publish()
  # Then: pas de récursion infinie (timeout 1s)

- test_log_handler_publishes_to_system_stream()
```

**Implémentation :** Le `_is_emitting` guard existe déjà. Le bug vient probablement de l'usage de `asyncio.create_task()` dans un handler synchrone. Fix : utiliser `loop.call_soon_threadsafe()` ou une queue asyncio dédiée.

---
