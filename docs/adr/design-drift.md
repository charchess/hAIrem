# Design Drift / Architecture Decisions

Ce documenttrack les décisions de conception prises pendant le développement et qui dévient ou complètent les stories originales.

---

## ADR-001: Priorité de Configuration LLM

**Date:** 2026-02-14
**Contexte:** Le système avait une hiérarchie de configuration confuse où la DB écrasait les variables d'environnement sans possibilité de gestion UI.

### Décision

La hiérarchie de configuration devient (du plus prioritaire au moins prioritaire):

```
1. Admin UI Override (SurrealDB)     → Runtime, plus haut priorité
2. Manifest YAML (llm_config)        → Préférence du persona  
3. Environment Variables             → Fallback / Dev
```

### Implémentation Requise

- Modifier `agent_config_service.py` pour que les vars d'environnement soient le fallback
- La config DB doit exister mais être vide par défaut
- L'UI doit permettre de voir quelle source est active

### Statut: Planifié (Story 7.5)

---

## ADR-002: Stockage des API Keys

**Date:** 2026-02-14
**Contexte:** Les API keys ne doivent pas être stockées en clair dans la DB.

### Option A: Variables d'Environnement
- Avantage: Simple, sécurisé par défaut
- Inconvénient: Nécessite redémarrage des containers

### Option B: Vault/Chiffrement
- Avantage: Gestion dynamique via UI
- Inconvénient: Plus complexe à implémenter

### Décision
Utiliser les variables d'environnement comme stockage principal pour les secrets, avec override optionnel via vault chiffré dans une future iteration.

**Statut:** Planifié

---

## ADR-003: Modèle LLM par Defaut

**Date:** 2026-02-14
**Contexte:** Le modèle par défaut était "gemini-2.0-flash" en dur quelque part, causant des échecs.

### Décision
- **Ollama** devient le provider par défaut recommandé pour le POC
- Modèle: `llama2` (plus réactif que mistral sur notre setup)
- La configuration explicite dans les manifests est obligatoire

### Fichiers Modifiés
- `agents/*/manifest.yaml` - Ajout explicite `llm_config`

**Statut:** Implémenté

---

## ADR-004: Docker Compose - SurrealDB Healthcheck

**Date:** 2026-02-14
**Contexte:** Le healthcheck de SurrealDB utilisait une commande invalide.

### Avant
```yaml
healthcheck:
  test: ["/surreal", "is-ready"]
```

### Après
```yaml
healthcheck:
  test: ["CMD", "wget", "--spider", "-q", "http://localhost:8000/health"]
```

**Statut:** Implémenté

---

## ADR-005: Container Ollama sans Healthcheck

**Date:** 2026-02-14
**Contexte:** Le healthcheck d'Ollama échouait avec curl non disponible dans le container.

### Décision
- Retirer le healthcheck temporairement
- Ollama sera considéré comme "started" pas "healthy"

**Statut:** Implémenté (workaround)

---

## ADR-006: Modèles Ollama

**Date:** 2026-02-14
**Contexte:** Quel modèle utiliser pour hAIrem ?

### Models Installés
- `mistral:latest` - 4.4GB, bon en français
- `llama2:latest` - 3.8GB, plus rapide

### Décision
`llama2` est utilisé par défaut pour sa rapidité. `mistral` peut être meilleur en français.

### Notes
- Les modèles sont dans un volume Docker (`ollama_data`) - persistants
- Premier appel est lent (chargement du modèle en mémoire)

**Statut:** Implémenté

---

## ADR-007: Structure des Tests E2E

**Date:** 2026-02-14
**Contexte:** Les tests de chat échouaient à cause d'un mauvais sélecteur.

### Problème
Le test cherchait `.message, .agent-message, [data-testid*="message"]` mais les messages utilisent `.message-bubble`.

### Solution
Correcteur le sélecteur dans `chat-engine.spec.ts`.

**Statut:** Implémenté ✅

---

## ADR-008: Fix Priorité Configuration

**Date:** 2026-02-14
**Contexte:** Les configs DB écrasaient les configs YAML/manifest sans discrimination.

### Implémentation

**Fichier:** `apps/h-core/src/features/admin/agent_config/service.py`
- `_apply_config_to_agent()`: N'applique que les valeurs NON-None

**Fichier:** `apps/h-core/src/features/admin/agent_config/models.py`
- `DEFAULT_PARAMETERS`: `model=None`

**Fichier:** `apps/h-core/src/features/admin/agent_config/repository.py`
- `get_or_default()`: Retourne `AgentParameters()` vide

### Résultat
- Manifest YAML respecté ✅
- Env vars comme fallback ✅
- UI peut surcharger (Story 7.5)

**Statut:** Implémenté ✅

---

## ADR-009: UI Configuration LLM (Story 7.5)

**Date:** 2026-02-14
**Contexte:** Besoin d'une UI pour configurer les providers LLM.

### Implémentation

**Backend:**
- `ProviderConfigService.test_connection()`: Teste la connectivité LLM
- Message `admin.llm.test_connection`: API pour tester
- Message `admin.agent.config`: Sauvegarde config per-agent

**Frontend:**
- Section "LLM Configuration" dans admin panel
- Liste des providers (Ollama, OpenAI, Anthropic, Google)
- Test de connexion avec feedback
- Override per-agent

**Fichiers Modifiés:**
- `apps/h-core/src/features/admin/provider_config/service.py`
- `apps/h-core/src/main.py`
- `apps/h-bridge/static/index.html`
- `apps/h-bridge/static/style.css`
- `apps/h-bridge/static/js/renderer.js`
- `apps/h-bridge/static/js/network.js`

**Statut:** Partiellement implémenté (UI de base) ✅

---

## Prochaines Questions en Suspens

1. **Vault System:** Quand implémenter le stockage sécurisé des clés API ?
2. **Hot Reload:** Les changements de config doivent-ils nécessiter un restart ?
3. **Multi-tenant:** Comment gérer les configs pour plusieurs utilisateurs ?

---

*Ce document est vivant - mettre à jour au fur et à mesure des décisions de design.*
