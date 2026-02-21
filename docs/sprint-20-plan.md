# Sprint 20 — "Le Cerveau des Agents" · Skills & Logiques Custom

**Période :** Mars 2026 (semaine 1-2)  
**Objectif :** Les agents ont enfin de vraies personnalités et des skills chargés automatiquement.

---

## Contexte

Actuellement, tous les agents (Lisa, Renarde, Electra, Entropy, Dieu) ont un `logic.py` avec `class Agent(BaseAgent): pass`. Leurs skills ne sont pas chargés depuis `persona.yaml`. Ce sprint leur donne vie.

**Pré-requis :** Sprint 19 terminé (tests verts, CI active).

---

## Stories

### Story 20.1 — Skill Auto-Loading depuis persona.yaml
**Priorité :** 🔴 HAUTE (CONFORMITE bloquant)  
**Effort :** M

**Problème actuel :** Le `PluginLoader` lit `manifest.yaml` et `persona.yaml` mais ignore la liste `skills[]`. Les tools ne sont jamais attachés aux agents automatiquement.

**Tests à écrire AVANT :**
```
apps/h-core/tests/test_skill_loading.py
- test_skill_names_read_from_persona_yaml()
  # Given: persona.yaml avec skills: ["memory_search", "ha_control"]
  # When: PluginLoader charge l'agent
  # Then: agent.tools contient les deux skills

- test_unknown_skill_logs_warning_not_crash()
  # Given: persona.yaml avec skills: ["nonexistent_skill"]
  # When: PluginLoader charge l'agent
  # Then: warning loggé, agent démarré quand même

- test_skill_receives_agent_dependencies()
  # Given: skill "memory_search" chargé
  # When: skill appelé
  # Then: il peut accéder à surreal_client et llm_client

- test_no_skills_key_loads_agent_empty_tools()
  # Given: persona.yaml sans clé skills
  # When: PluginLoader charge
  # Then: agent.tools = {} (pas d'erreur)
```

**Implémentation :**
1. Créer `apps/h-core/src/skills/registry.py` : mapping `skill_name → factory_function`
2. Modifier `PluginLoader._load_agent()` : après création de l'instance, lire `config.skills` et appeler le registry
3. Chaque skill existant dans `src/skills/` ou `src/agents/tools/` s'enregistre dans le registry
4. Passer `surreal_client`, `llm_client`, `redis_client` aux skills au moment de l'injection

**Format attendu dans `persona.yaml` :**
```yaml
skills:
  - memory_search
  - ha_control
  - image_generation
```

**DoD :** Lisa avec `skills: [memory_search, ha_control]` dans son `persona.yaml` → `agent.tools` contient les deux. Tests GREEN.

---

### Story 20.2 — Logique Custom : Lisa (Régente Domestique)
**Priorité :** 🔴 HAUTE  
**Effort :** M

**Rôle de Lisa :** Gestion domestique, inventaire, confort. Elle initie les conversations sur les tâches ménagères, répond aux questions sur l'état de la maison.

**Tests à écrire AVANT :**
```
apps/h-core/tests/test_agent_lisa.py
- test_lisa_responds_to_domestic_query()
  # Given: message "c'est quoi l'état du frigo ?"
  # When: Lisa process le message
  # Then: elle appelle l'outil ha_control, construit une réponse narrative

- test_lisa_proactive_morning_routine()
  # Given: stimulus "morning" déclenché
  # When: ProactivityEngine trigger Lisa
  # Then: Lisa envoie un message de bonne humeur domestique sur le bus

- test_lisa_does_not_respond_to_tech_queries()
  # Given: message "explique moi le machine learning"
  # When: l'arbitre calcule les scores
  # Then: Lisa a un score < 0.3 sur ce sujet
```

**Implémentation (`agents/lisa/logic.py`) :**
- Override `process_message()` pour ajouter contexte domestique
- Hook `on_proactive_trigger()` pour la routine matinale
- Enregistrement des triggers dans `persona.yaml:proactive_triggers`

---

### Story 20.3 — Logique Custom : Renarde (Créative & Ludique)
**Priorité :** 🔴 HAUTE  
**Effort :** M

**Rôle :** Créativité, jeux, narration. Elle rebondit sur les conversations culturelles, génère des idées, raconte des histoires.

**Tests :**
```
apps/h-core/tests/test_agent_renarde.py
- test_renarde_high_score_on_creative_topics()
- test_renarde_can_initiate_story_narration()
- test_renarde_rebonds_in_inter_agent_discussion()
```

---

### Story 20.4 — Logique Custom : Entropy (Gardien du Système)
**Priorité :** 🔴 HAUTE  
**Effort :** M

**Rôle :** Monitoring, anomalies, maintenance silencieuse. Agent "invisible" (sans avatar). Il surveille et alerte.

**Tests :**
```
apps/h-core/tests/test_agent_entropy.py
- test_entropy_responds_to_system_anomaly()
- test_entropy_is_invisible_no_visual_bootstrap()
  # Given: Entropy chargé
  # When: PluginLoader tente le bootstrap avatar
  # Then: skip car agent_name == "entropy"
- test_entropy_triggers_on_ha_alert()
```

---

### Story 20.5 — Logique Custom : Dieu (Orchestrateur Mondial)
**Priorité :** 🟠 MOYENNE  
**Effort :** M

**Rôle :** World State Manager. Il lit et modifie l'état global de la maison (thème visuel, ambiance, saison simulée). C'est le lien entre l'état du monde et les cascades de régénération visuelle.

**Tests :**
```
apps/h-core/tests/test_agent_dieu.py
- test_dieu_can_change_world_theme()
  # Given: commande "passe en mode soirée"
  # When: Dieu process
  # Then: WorldThemeService reçoit "soiree", cascade décors lancée

- test_dieu_cascade_triggers_visual_regen()
  # Given: thème changé par Dieu
  # When: cascade
  # Then: VisualImaginationService.regenerate_backgrounds() appelé

- test_dieu_is_invisible_no_avatar()
```

**Implémentation :** Brancher `WorldThemeService` dans `agents/dieu/logic.py`.

---

### Story 20.6 — Logique Custom : Electra (Tech & Analytique)
**Priorité :** 🟡 MOYENNE  
**Effort :** S

**Rôle :** Expertise technique, analytics, IA. Elle répond aux questions tech et donne des stats système.

**Tests :**
```
apps/h-core/tests/test_agent_electra.py
- test_electra_high_score_on_tech_topics()
- test_electra_provides_system_stats_on_request()
```

---

### Story 20.7 — Documentation des agents
**Priorité :** 🟡 MOYENNE  
**Effort :** S

**Livrable :** `docs/architecture/22-skills-persona-dissociation.md` mis à jour  
Ajouter section "Comment créer un agent custom" avec exemple complet `logic.py`.

---
