# Architecture: Skill Access Model & Wardrobe

**Version:** 1.0
**Status:** Implemented
**Extends:** doc-22 (Skills & Persona Dissociation)
**Date:** 2026-02-22

---

## 1. Wardrobe (renommage)

Le service `VaultService` dans `services/visual/` est renommé **`WardrobeService`** (`wardrobe.py`).

Rationale: le terme "vault" est réservé exclusivement à la sécurité/credentials (`services/vault/credentials.py`).
Le wardrobe stocke les **assets graphiques persistants** des personas : tenues, décors, poses.

| Service | Fichier | Rôle |
|---------|---------|------|
| `CredentialVaultService` | `services/vault/credentials.py` | Clés API, secrets chiffrés (Fernet) |
| `WardrobeService` | `services/visual/wardrobe.py` | Assets visuels (tenues, décors) par persona |

---

## 2. Modèle d'accès aux Skills

Chaque skill déclare son mode d'accès dans `skill.yaml` :

```yaml
name: cooking
version: "1.0.0"
access: unique        # unique | multiple
description: ...
```

| Valeur | Signification |
|--------|--------------|
| `unique` | Un seul persona actif à la fois (ressource avec état, ex: session HA dédiée) |
| `multiple` | N personas peuvent l'utiliser simultanément (stateless ou multi-tenant) |

Par défaut (si absent) : `multiple`.

---

## 3. Système de Grants (activation runtime)

Le `persona.yaml` déclare les skills **souhaités** (`skills_needed`).
Le **SkillGrantService** contrôle lesquels sont **actifs** au runtime.

```
persona.yaml[skills_needed]  →  SkillGrantService  →  BaseAgent.tools
     (ce que le persona veut)     (ce qui est accordé)    (ce qui est utilisable)
```

Un `SkillGrant` est un enregistrement SurrealDB :

```
{
  persona_id: "Lisa",
  skill_name: "cooking",
  active: true,
  granted_at: datetime,
  access_mode: "unique"   # copie du skill.yaml au moment du grant
}
```

**Comportement :**
- Si aucun grant n'existe pour un skill → il est actif par défaut (rétrocompatibilité)
- Un grant `active: false` désactive le skill sans le supprimer
- Un skill `unique` ne peut être `active: true` que pour **un seul persona** à la fois

---

## 4. Crew Manager API (admin)

`SkillManagementService` expose via Redis/admin :

| Méthode | Description |
|---------|-------------|
| `list_skills()` | Tous les skills disponibles avec metadata + grants actifs |
| `grant(persona_id, skill_name)` | Active un skill pour un persona |
| `revoke(persona_id, skill_name)` | Désactive un skill pour un persona |
| `list_persona_skills(persona_id)` | Skills actifs d'un persona |

**Format badge crew manager :**
```json
{
  "skill_name": "cooking",
  "version": "1.0.0",
  "access": "unique",
  "description": "...",
  "active_for": ["Moka"],
  "available": true
}
```

---

## 5. Alignement MCP

Les skills hAIrem sont structurellement compatibles avec MCP (Model Context Protocol) :

| MCP | hAIrem |
|-----|--------|
| MCP Server | Skill plugin (`skills/<name>/`) |
| Server manifest | `skill.yaml` |
| Tool definition | Fonction publique dans `__init__.py` |
| MCP Host | hAIrem core (PluginLoader + SkillGrantService) |
| Client capability | `persona.yaml[skills_needed]` |

Les skills sont aujourd'hui **in-process** (modules Python). La migration vers MCP out-of-process
(stdio/HTTP) est possible sans changer les interfaces : il suffit de wrapper chaque skill dans un
MCP server et d'adapter `SkillRegistry.load()`.

---

## 6. Flux complet

```
Boot:
  PluginLoader._load_agent(manifest)
    → lit persona.yaml[skills_needed]
    → pour chaque skill:
        SkillGrantService.is_active(persona, skill) ?
          oui → SkillRegistry.load(skill) → agent.tools[fn_name] = fn
          non → skill ignoré (placeholder si skill déclaré dans skills[])

Runtime admin:
  SkillManagementService.revoke("Lisa", "cooking")
    → SkillGrant.active = false en DB
    → Redis event SKILL_REVOKED
    → agent retire le tool de agent.tools (si reload supporté)

Crew Manager UI:
  GET /admin/skills → liste badges
  POST /admin/skills/{skill}/grant/{persona}
  POST /admin/skills/{skill}/revoke/{persona}
```
