# Architecture Design: Skills & Persona Dissociation

**Version:** 1.0
**Status:** Defined
**Author:** Charchess
**Date:** 2026-02-13

---

## 1. Principe de Dissociation

Un **Persona** et ses **Skills** sont **COMPLÈTEMENT SÉPARÉS** :

```
persona-lisa/           # Lea persona N'EST PAS dans le même dossier que les skills
├── persona.yaml       # Personality, prompts, bio, voice
├── scope.yaml         # Interests, domains
└── media/             # Voice samples, images
    └── voice_ref.wav

skills/
├── home_assistant/    # Skill "indépendant" - peut être utilisé par N'IMPORTE quel persona
│   ├── manifest.yaml
│   ├── logic.py
│   └── requirements.txt
├── cooking/
│   ├── manifest.yaml
│   ├── logic.py
│   └── recipes/
└── calendar/
    ├── manifest.yaml
    └── logic.py
```

---

## 2. Pourquoi cette dissociation ?

| Benefit | Description |
|---------|-------------|
| **Réutilisabilité** | Un skill peut être utilisé par plusieurs personas |
| **Indépendance** | Le skill évolue indépendamment du persona |
| **Hotplug** | On ajoute/enlève des skills sans modifier le persona |
| **Teamwork** | Un persona "demande" un skill |

---

## 3. Comment ça marche ?

### 3.1 Le Persona "demande" un skill

```yaml
# persona.yaml
persona:
  name: "Lisa"
  skills_needed:
    - home_assistant
    - cooking
```

### 3.2 Le Skill est chargé séparément

```python
# core/agent.py
class BaseAgent:
    def __init__(self, config, ...):
        self.skills = {}
        
    def load_skills(self, skill_names: list[str]):
        for skill_name in skill_names:
            skill = SkillRegistry.load(skill_name)
            self.skills[skill_name] = skill
            
    def call_skill(self, skill_name: str, *args, **kwargs):
        if skill_name in self.skills:
            return self.skills[skill_name].execute(*args, **kwargs)
```

### 3.3 Communication Persona ↔ Skill

```python
# Le skill peut appeler le LLM du persona
class BaseSkill:
    def __init__(self, agent: BaseAgent):
        self.agent = agent  # Accès au LLM, mémoire, etc.
        
    def execute(self, *args, **kwargs):
        # Peut utiliser self.agent.llm pour des décisions
        # Peut utiliser self.agent.memory pour stocker des faits
        pass
```

---

## 4. Structure d'un Skill

```yaml
# skills/{skill_name}/manifest.yaml
skill:
  name: "home_assistant"
  version: "1.0.0"
  description: "Contrôle de la maison via Home Assistant"
  dependencies:
    - home_assistant_api
  triggers:
    - event:motion
    - event:door
    - command:turn_on
  persona_required: []  # Optional - si skill nécessite une personnalité spécifique
```

```python
# skills/{skill_name}/logic.py
class Skill(BaseSkill):
    async def execute(self, action: str, **kwargs):
        if action == "turn_on":
            return await self.turn_on_light(kwargs["entity_id"])
        elif action == "get_state":
            return await self.get_entity_state(kwargs["entity_id"])
    
    async def turn_on_light(self, entity_id: str):
        # Logique HA
        pass
```

---

## 5. Skill Registry

```python
class SkillRegistry:
    _skills: dict[str, type[BaseSkill]] = {}
    
    @classmethod
    def load(cls, skill_name: str) -> BaseSkill:
        if skill_name not in cls._skills:
            # Import dynamique
            module = importlib.import_module(f"skills.{skill_name}.logic")
            cls._skills[skill_name] = module.Skill
        return cls._skills[skill_name](agent)
    
    @classmethod
    def list_available(cls) -> list[str]:
        # Liste les skills dans le dossier skills/
        return os.listdir("skills/")
```

---

## 6. Différences Clés

| Aspect | Ancien (V4) | Nouveau (V5) |
|--------|-------------|--------------|
| **Emplacement** | `agents/lisa/logic.py` | `skills/{skill}/logic.py` |
| **Dossier agent** | `agents/lisa/` | `persona-lisa/` (seulement données) |
| **Code** | Dans le bundle agent | Séparé |
| **Drivers** | `lib/drivers/` dans agent | Dans le skill |

---

## 7. Migration

### Avant (V4)
```
agents/lisa/
├── manifest.yaml
├── persona.yaml
├── logic.py          # <-- Tout le code
└── lib/
    └── drivers/
        └── ha_driver.py
```

### Après (V5)
```
persona-lisa/
├── persona.yaml
├── scope.yaml
└── media/

skills/
├── home_assistant/
│   ├── manifest.yaml
│   └── logic.py
└── ha_driver/  # Le driver est un skill
    ├── manifest.yaml
    └── logic.py
```

---

## 8. Points Clarifiés

### A/ Skills Additionnels

HA, Google Calendar, Gmail sont des **skills additionnels** (usecases).
- `home_assistant` est déjà implémenté mais reste un "usecase"
- De nouveaux skills peuvent être ajoutés (calendar, email, etc.)

### B/ Isolation venv par skill
**À ÉTUDIER**

| Pro | Con |
|-----|-----|
| Pas de conflits de dépendances | Complexité de gestion |
| Sécurité (isolation) | Déploiement plus lourd |
| Versions indépendantes | Temps de chargement |

### C/ Gestion des Secrets

Les secrets sont gérés par le **Dashboard/UI** :

```yaml
# persona.yaml
skill: home_assistant
required_secrets:
  - TOKEN_HA  # Référence le nom du secret

# Configuration (Dashboard)
secrets:
  TOKEN_HA: "sk_live_xxxxx"  # Configuré dans l'UI, stocké chiffré
```

```python
# core/secret_manager.py
class SecretManager:
    def get(self, name: str) -> str:
        # Récupère le secret chiffré depuis la DB
        return self.db.get_secret(name)
    
    # La skill appelle:
    ha_token = SecretManager.get("TOKEN_HA")
```

**Avantages:**
- Pas de secrets en dur dans le code
- Dashboard pour gérer les tokens
- Rotation des secrets possible
- Audit des accès

---

🏗️ Architecture Defined - 2026-02-13
