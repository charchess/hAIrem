# Sprint 22 — "Le Monde Vivant" · World State, Sleep Cycle & Spatial Complet

**Période :** Avril 2026 (semaine 1-2)  
**Objectif :** La maison est un organisme vivant. Dieu modifie le monde, les agents se souviennent automatiquement, les pièces sont des entités réelles.

---

## Stories

### Story 22.1 — Sleep Cycle Automatique
**Priorité :** 🔴 HAUTE (CONFORMITE bloquant)  
**Effort :** M

**Problème :** `MemoryConsolidator.consolidate()` existe mais n'est jamais appelé automatiquement. La mémoire ne se consolide que manuellement.

**Tests à écrire AVANT :**
```
apps/h-core/tests/test_sleep_cycle_auto.py
- test_sleep_cycle_triggers_on_inactivity()
  # Given: aucun message depuis INACTIVITY_THRESHOLD (ex: 30min)
  # When: SleepCycleScheduler tick
  # Then: consolidate() appelé une fois

- test_sleep_cycle_triggers_on_slash_command()
  # Given: commande /sleep reçue
  # When: CommandHandler traite
  # Then: cycle déclenché immédiatement

- test_sleep_cycle_does_not_trigger_during_active_conversation()
  # Given: messages < 5min
  # When: scheduler évalue
  # Then: consolidation NOT appelée

- test_sleep_cycle_broadcasts_completion_event()
  # Given: consolidation terminée
  # When: résultat
  # Then: HLink message system.log sur system_stream

- test_decay_applied_after_consolidation()
  # Given: cycle complet
  # When: consolidate() finit
  # Then: apply_decay() appelé automatiquement après
```

**Implémentation :**
- Créer `apps/h-core/src/services/sleep_scheduler.py`
- Timer asyncio : si `time_since_last_message > INACTIVITY_THRESHOLD` → `consolidator.consolidate()` puis `apply_decay()`
- Ajouter `SleepScheduler` dans `HaremOrchestrator.run()` comme tâche background
- Hooker `/sleep` dans `CommandHandler`

**Config** (`.env.example`) :
```
SLEEP_INACTIVITY_THRESHOLD_MINUTES=30
DECAY_RATE=0.9
DECAY_THRESHOLD=0.1
```

---

### Story 22.2 — World State Management (Dieu/Entropy)
**Priorité :** 🔴 HAUTE (CONFORMITE bloquant)  
**Effort :** L

**Contexte :** L'agent Dieu doit pouvoir changer le "thème du monde" (saison simulée, ambiance soirée/jour, événement spécial), et cette modification doit déclencher une cascade visuelle : régénération des décors et tenues de chaque agent.

**Tests à écrire AVANT :**
```
apps/h-core/tests/test_world_state.py
- test_world_state_persists_theme_in_surrealdb()
  # Given: theme = "soiree_halloween"
  # When: WorldStateService.set_theme("soiree_halloween")
  # Then: SurrealDB world_state record mis à jour

- test_world_state_change_triggers_cascade()
  # Given: WorldStateService
  # When: set_theme() appelé
  # Then: cascade_event publié sur system_stream

- test_visual_service_receives_cascade_event()
  # Given: cascade_event avec theme="soiree_halloween"
  # When: VisualImaginationService écoute l'événement
  # Then: regenerate_all_agents_visuals(theme) appelé

- test_dieu_processes_theme_command()
  # Given: message "passe en mode nuit d'halloween"
  # When: Dieu.process_message()
  # Then: WorldStateService.set_theme() appelé avec theme extrait

- test_world_state_read_by_all_agents_in_prompt()
  # Given: world_state = "winter_night"
  # When: agent construit son system_prompt
  # Then: le thème est injecté dans le contexte du prompt
```

**Implémentation :**
- Créer `apps/h-core/src/services/spatial/world_state.py` : `WorldStateService`
- SurrealDB table `world_state` (singleton record)
- Event `world.theme_changed` sur `system_stream`
- `VisualImaginationService` souscrit à cet event → `regenerate_backgrounds(theme)`
- `MultiLayerPromptBuilder` lit le world_state au build du prompt
- Brancher dans `agents/dieu/logic.py`

---

### Story 22.3 — Services Spatiaux Complets
**Priorité :** 🟠 MOYENNE  
**Effort :** M

**Contexte :** `SpatialRegistry`, `RoomService`, `LocationService`, `ExteriorService`, `WorldThemeService` existent structurellement. Leur logique réelle est à vérifier et compléter.

**Tests à écrire AVANT :**
```
apps/h-core/tests/test_spatial_complete.py
- test_room_service_creates_and_retrieves_room()
- test_agent_assigned_to_room_persists_in_db()
- test_location_service_updates_agent_location()
- test_spatial_badge_data_in_heartbeat()
  # Given: Lisa assignée à "salon"
  # When: heartbeat émis
  # Then: agents_stats["lisa"]["location"] = "Salon"

- test_exterior_service_returns_current_conditions()
  # (via HA sensor météo si disponible, sinon mock)

- test_world_theme_applied_to_exterior_description()
```

**Implémentation :**
- Auditer chaque fichier dans `spatial/` → compléter les méthodes manquantes
- Brancher `SpatialRegistry` dans `HaremOrchestrator._background_setup()`
- Passer `spatial_registry` aux agents via `PluginLoader`

---

### Story 22.4 — Badge Spatial dans l'UI (FR-V4-06)
**Priorité :** 🟠 MOYENNE  
**Effort :** S

**Tests :**
```
apps/h-core/tests/test_spatial_badge.py
- test_heartbeat_includes_agent_location()
- test_location_updates_in_realtime_via_redis()
```

**Implémentation :**
- Vérifier que `agents_stats[aid]["location"]` est correctement peuplé dans `status_heartbeat()`
- S'assurer que le bridge transmet cette donnée au frontend
- Documenter le format dans `docs/architecture/18-spatial-world-state.md`

---

### Story 22.5 — LRU Cleanup Media Générés
**Priorité :** 🟡 MOYENNE  
**Effort :** S

**Tests :**
```
apps/h-core/tests/test_media_cleanup.py
- test_lru_removes_oldest_files_when_limit_reached()
  # Given: dossier media/ avec 110 fichiers (limit=100)
  # When: MediaCleanupWorker.run()
  # Then: 10 fichiers les plus anciens supprimés

- test_permanent_files_not_deleted()
  # Given: fichier avec flag "permanent" dans AssetManager DB
  # When: cleanup
  # Then: fichier préservé

- test_cleanup_runs_periodically()
```

**Implémentation :**
- Créer `apps/h-core/src/services/media_cleanup.py`
- Worker asyncio périodique (toutes les 6h)
- Requête SurrealDB pour les assets par `last_accessed_at` ASC
- Ajouter à `HaremOrchestrator.run()`

---
