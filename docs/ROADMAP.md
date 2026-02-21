# hAIrem — Roadmap d'Implémentation V4

> Généré le 21 Février 2026, basé sur le delta théorie/pratique.  
> Point de départ : Sprint 18 terminé (partiellement).

---

## Vue d'ensemble

| Sprint | Nom | Thème | Durée | Priorité |
|--------|-----|-------|-------|----------|
| **19** | Fondations | Sécurité, Tests, CI/CD | 2 sem | 🚨 BLOQUANT |
| **20** | Le Cerveau des Agents | Skills, Logiques custom | 2 sem | 🔴 HAUTE |
| **21** | La Voix | STT, TTS, Wakeword | 2 sem | 🔴 HAUTE |
| **22** | Le Monde Vivant | World State, Sleep Cycle, Spatial | 2 sem | 🟠 MOYENNE |
| **23** | L'Observatoire | Monitoring, Polyphonie, Polish | 2 sem | 🟡 BASSE |

---

## Gaps Couverts par Sprint

### Sprint 19 — Fondations
- ❌ `passwords.txt` en clair → ✅ Vault + .gitignore
- ❌ 48 erreurs de collection de tests → ✅ Suite verte
- ❌ Aucun CI/CD → ✅ GitHub Actions

### Sprint 20 — Le Cerveau des Agents
- ❌ Skill auto-loading (CONFORMITE critique) → ✅ `skills/registry.py` + PluginLoader
- 🟡 logic.py vides pour tous les agents → ✅ Logiques custom Lisa, Renarde, Entropy, Electra, Dieu

### Sprint 21 — La Voix
- ❌ Whisper STT absent → ✅ `stt_service.py` avec faster-whisper
- ❌ MeloTTS absent → ✅ `melotts_provider.py` + Docker service
- ❌ ElevenLabs absent → ✅ `elevenlabs_provider.py` (fallback)
- 🟡 Wakeword stub → ✅ Wakeword complet (Vosk/openWakeWord)
- 🟡 Speech Queue → ✅ File FIFO avec priorités et barge-in

### Sprint 22 — Le Monde Vivant
- ❌ Sleep Cycle non déclenché auto → ✅ `SleepScheduler` (inactivité + /sleep)
- ❌ World State (Entropy/Dieu) → ✅ `WorldStateService` + cascade visuelle
- 🟡 Services spatiaux incomplets → ✅ Spatial complet + badge UI
- ❌ LRU cleanup media → ✅ `MediaCleanupWorker`

### Sprint 23 — L'Observatoire
- ❌ Prometheus/Grafana → ✅ Metrics + dashboards
- ❌ Arbitration Glow (signal backend) → ✅ `agent.speaking` HLink event
- 🟡 Discussion inter-agents (budget) → ✅ Stop sur score bas
- ❌ Barge-in → ✅ `SpeechQueue.interrupt()`
- 🟡 RedisLogHandler récursion → ✅ Fix async-safe

---

## Architecture TDD

**Règle universelle :** Chaque story suit le cycle RED → GREEN → REFACTOR.

```
1. Écrire les tests (ils échouent — RED)
2. Implémenter le minimum pour les faire passer (GREEN)
3. Refactorer sans casser les tests
4. Valider CI/CD vert avant merge
```

**Structure des tests :**
```
apps/h-core/tests/
├── unit/           # Tests purs, sans I/O (mock tout)
├── integration/    # Tests avec Redis/SurrealDB réels (docker-compose)
└── test_*.py       # Tests par story (nomenclature: test_{story_id}_{feature}.py)
```

**Fixtures partagées (conftest.py) :**
- `mock_redis` : AsyncMock du RedisClient
- `mock_surreal` : AsyncMock du SurrealDbClient  
- `mock_llm` : LlmClient retournant réponses fixtures
- `test_agent_config` : AgentConfig minimal
- `test_hlink_message` : HLinkMessage de test

---

## Documentation à produire

| Document | Sprint | Statut |
|----------|--------|--------|
| `docs/architecture/testing-standards.md` | 19 | ❌ À créer |
| `docs/architecture/coding-standards.md` section Secrets | 19 | ❌ À compléter |
| `docs/architecture/22-skills-persona-dissociation.md` (update) | 20 | 🟡 À compléter |
| `docs/architecture/23-audio-pipeline.md` | 21 | ❌ À créer |
| `docs/architecture/18-spatial-world-state.md` (update) | 22 | 🟡 À compléter |
| `docs/architecture/24-world-state-management.md` | 22 | ❌ À créer |
| `docs/architecture/25-observability.md` | 23 | ❌ À créer |

---

## Métriques de Succès (DoD Global)

| Métrique | Cible |
|----------|-------|
| Tests GREEN | 100% (0 erreur collection) |
| Couverture de code | ≥ 80% sur h-core/src |
| Pipeline CI | Vert sur chaque push main |
| Latence graphe SurrealDB | < 500ms (p95) |
| Latence TTS | < 800ms (p95) |
| Secrets en clair | 0 dans le repo |
| Agents avec logique custom | 5/5 (Lisa, Renarde, Electra, Entropy, Dieu) |
| Skills auto-chargés | Oui (depuis persona.yaml) |
| Audio end-to-end | Wakeword → STT → Agent → TTS fonctionnel |

---

## Dépendances Externes à Ajouter

```toml
# pyproject.toml (à ajouter)
faster-whisper      # STT local
prometheus-client   # Métriques
vosk               # Wakeword (alternatif openWakeWord)
# ou : openwakeword

# Docker services à ajouter dans docker-compose.yml
melotts            # TTS local (image communautaire)
prometheus         # Collecte métriques
grafana            # Dashboards
whisper-server     # Alternative: service Whisper séparé
```

---

*Plan généré depuis le rapport delta théorie/pratique du 21 Février 2026.*
