# Architecture Design: Admin UI & Dashboard

**Version:** 1.0
**Status:** To Be Defined
**Author:** Charchess / PM Agent
**Date:** 2026-02-13

---

## 1. Introduction

Ce document définit l'architecture de l'interface d'administration pour hAIrem. L'Admin UI permet de gérer les agents, surveiller les performances, configurer les providers, et gérer les utilisateurs.

## 2. Overview

### 2.1 Features Required (from PRD V5)

| FR | Feature | Description |
|----|---------|-------------|
| FR32 | Token Consumption | View token usage per agent |
| FR33 | Enable/Disable Agents | Toggle agent active state |
| FR34 | Configure Agent Parameters | Modify persona settings |
| FR35 | Add New Agents | Create new agents |
| FR36 | Configure LLM Providers | Per-agent provider config |

### 2.2 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Admin UI (SPA)                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ Dashboard│ │ Agents  │ │ Users   │ │Settings │          │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘          │
└───────┼──────────┼──────────┼──────────┼─────────────────┘
        │          │          │          │
        └──────────┴──────────┴──────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                  H-Core Admin API                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │Agent Manager │ │User Manager  │ │Config Manager│       │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘       │
└─────────┼────────────────┼────────────────┼────────────────┘
          │                │                │
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Redis   │    │SurrealDB │    │  Config  │
    │  Streams │    │   DB     │    │  Files   │
    └──────────┘    └──────────┘    └──────────┘
```

## 3. Dashboard

### 3.1 Overview Page

**Métriques affichées :**

| Metric | Source | Update Frequency |
|--------|--------|------------------|
| **Active Agents** | Redis | Real-time |
| **Messages/min** | Redis counter | 1 min |
| **Token Usage Today** | LLM client | 5 min |
| **System Health** | Health checks | 30 sec |
| **Error Rate** | Logs | 5 min |

### 3.2 Token Consumption (FR32)

```python
# Exemple de tracking
class TokenTracker:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def record(self, agent_id: str, tokens: int):
        # Incrément journalier
        key = f"tokens:{agent_id}:{date.today()}"
        self.redis.incrby(key, tokens)
    
    def get_daily_usage(self, agent_id: str) -> int:
        key = f"tokens:{agent_id}:{date.today()}"
        return int(self.redis.get(key) or 0)
    
    def get_cost_estimate(self, agent_id: str) -> float:
        # Prix par token selon provider
        tokens = self.get_daily_usage(agent_id)
        rate = self.get_provider_rate(agent_id)
        return tokens * rate
```

**UI Display:**
```
┌─────────────────────────────────────────┐
│  Agent      │ Tokens Today │ Est. Cost │
├─────────────────────────────────────────┤
│  Lisa       │   45,230    │  $0.18    │
│  Electra    │   32,100    │  $0.13    │
│  System     │   12,500    │  $0.05    │
└─────────────────────────────────────────┘
```

### 3.3 Agent Status

| Status | Description |
|--------|-------------|
| 🟢 Active | Agent loaded and responding |
| 🟡 Idle | Agent loaded but no recent activity |
| 🔴 Error | Agent has errors |
| ⚪ Disabled | Agent disabled by admin |

## 4. Agent Management

### 4.1 Agent List

**FR33: Enable/Disable Agents**

```
┌──────────────────────────────────────────────────────────────┐
│ Agents                                    [+ Add New Agent] │
├──────────────────────────────────────────────────────────────┤
│ ┌──────────┐ Lisa           🟢 Active  [Edit] [Disable]  │
│ │  Avatar  │ Electra         🟢 Active  [Edit] [Disable]  │
│ └──────────┘ TestBot        ⚪ Disabled [Edit] [Enable]   │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Agent Configuration (FR34)

Editable parameters:
- **Persona**: Name, description, prompt
- **Skills**: List of enabled skills
- **LLM Provider**: Provider selection
- **Voice**: TTS voice selection
- **Visual**: Default outfit, visual preferences

```yaml
# Agent Config Example
agent:
  name: "Lisa"
  enabled: true
  llm_provider: "openrouter"
  llm_model: "google/gemma-3-27b-it:free"
  tts_voice: "fr-FR-RemyNeural"
  skills:
    - home_assistant
    - cooking
  memory:
    retention_days: 30
    decay_rate: 0.9
```

### 4.3 Add New Agent (FR35)

Wizard en 3 étapes :
1. **Basic Info**: Name, description, avatar
2. **Configuration**: Provider, skills, voice
3. **Review & Create**

## 5. Provider Configuration (FR36)

### 5.1 Multi-Provider Support

```python
# Configuration des providers
providers = {
    "openrouter": {
        "type": "llm",
        "api_key": "sk-...",
        "models": ["google/gemma-3-27b-it:free", "openai/gpt-4o"],
        "fallback": "ollama"
    },
    "ollama": {
        "type": "llm",
        "endpoint": "http://192.168.1.100:11434",
        "models": ["qwen2.5", "llama3"]
    },
    "nanobanana": {
        "type": "image",
        "endpoint": "http://192.168.1.101:8000"
    },
    "imagen": {
        "type": "image", 
        "endpoint": "http://192.168.1.119:8009"
    }
}
```

### 5.2 Per-Agent Provider

```python
# Chaque agent peut avoir son provider
agent_config = {
    "lisa": {
        "llm_provider": "openrouter",
        "llm_model": "google/gemma-3-27b-it:free",
        "image_provider": "nanobanana"
    },
    "electra": {
        "llm_provider": "ollama",
        "llm_model": "qwen2.5",
        "image_provider": "imagen"
    }
}
```

### 5.3 Fallback Logic

```python
async def call_with_fallback(agent_id: str, prompt: str):
    provider = get_agent_provider(agent_id)
    
    try:
        return await provider.complete(prompt)
    except ProviderError as e:
        if provider.fallback:
            logger.warning(f"Provider {provider.name} failed, trying fallback")
            fallback = get_provider(provider.fallback)
            return await fallback.complete(prompt)
        raise
```

## 6. User Management

### 6.1 User List

| User | Voice Enrolled | Last Seen | Relationships |
|------|----------------|-----------|---------------|
| Alice | ✅ | 2 min ago | View |
| Bob | ❌ | 1 hour ago | View |

### 6.2 User Details

- Voice enrollment status
- Relationship scores with each agent
- Memory query access
- Delete user option

## 7. API Endpoints

### 7.1 Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/dashboard/stats` | Get overview stats |
| GET | `/api/v1/admin/dashboard/health` | System health |

### 7.2 Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/agents` | List all agents |
| POST | `/api/v1/admin/agents` | Create new agent |
| GET | `/api/v1/admin/agents/{id}` | Get agent details |
| PUT | `/api/v1/admin/agents/{id}` | Update agent |
| DELETE | `/api/v1/admin/agents/{id}` | Delete agent |
| POST | `/api/v1/admin/agents/{id}/enable` | Enable agent |
| POST | `/api/v1/admin/agents/{id}/disable` | Disable agent |

### 7.3 Providers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/providers` | List providers |
| PUT | `/api/v1/admin/providers/{id}` | Update provider config |
| GET | `/api/v1/admin/agents/{id}/provider` | Get agent's provider |
| PUT | `/api/v1/admin/agents/{id}/provider` | Set agent's provider |

### 7.4 Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/users` | List users |
| GET | `/api/v1/admin/users/{id}` | Get user details |
| DELETE | `/api/v1/admin/users/{id}` | Delete user |
| POST | `/api/v1/admin/users/{id}/enroll-voice` | Enroll voice |

### 7.5 Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/monitoring/tokens` | Token usage |
| GET | `/api/v1/admin/monitoring/errors` | Error logs |
| GET | `/api/v1/admin/monitoring/performance` | Performance metrics |

## 8. Security

### 8.1 Authentication

- JWT token required for all admin endpoints
- Separate admin user table with role-based access
- Session timeout: 24 hours

### 8.2 Authorization

| Role | Dashboard | Agents | Users | Settings |
|------|-----------|--------|-------|----------|
| Viewer | Read | Read | Read | Read |
| Admin | Full | Full | Full | Full |

## 9. Tech Stack

- **Frontend**: React + TypeScript + Tailwind CSS
- **State**: React Query pour data fetching
- **Charts**: Recharts pour les métriques
- **Forms**: React Hook Form + Zod

---

🏗️ PM Agent - hAIrem Architecture
