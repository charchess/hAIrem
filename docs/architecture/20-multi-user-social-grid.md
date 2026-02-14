# Architecture Design: Multi-User Support & Social Grid

**Version:** 1.0
**Status:** To Be Defined
**Author:** Charchess / PM Agent
**Date:** 2026-02-13

---

## 1. Introduction

Ce document définit l'architecture pour le support multi-utilisateurs et la grille sociale dynamique de hAIrem. Chaque utilisateur humain interagit avec les agents de manière unique, avec une mémoire et une relation distinctes par agent.

## 2. User Identity & Recognition

### 2.1 Voice Recognition

**FR24: System recognizes different users by voice**

#### Architecture
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Microphone │────▶│  Whisper STT │────▶│  Voice ID  │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │  User Repo  │
                                         │ (SurrealDB)│
                                         └─────────────┘
```

#### Composants
- **Voice Enrollment**: Lors de la première interaction, l'utilisateur enregistre un sample vocal (10s minimum)
- **Voice Matching**: Embedding vocaux stockés et comparés via similarité cosinus
- **Fallback**: Si non reconnu, demander le nom ou utiliser "guest"

#### Schema SurrealDB
```surql
DEFINE TABLE user SCHEMAFULL;
DEFINE FIELD name ON user TYPE string;
DEFINE FIELD voice_embedding ON user TYPE array;
DEFINE FIELD created_at ON user TYPE datetime;
DEFINE FIELD last_seen ON user TYPE datetime;
DEFINE FIELD default_agent ON user TYPE option<string>;
```

### 2.2 User Context Injection

Chaque requête utilisateur doit inclure le `user_id` pour permettre :
- Récupération de la mémoire utilisateur-agent
- Tracking de l'historique émotionnel
- Personnalisation du ton de réponse

## 3. Per-User Memory

**FR25: Each user has separate memory relationship with each agent**

### 3.1 Memory Partition

Chaque agent maintient une mémoire **par utilisateur** :

```python
# Exemple de structure en mémoire
agent_memory = {
    "user:alice": {
        "facts": [...],  # Faits sur Alice vus par cet agent
        "relationship_score": 0.7,
        "last_interaction": "2026-02-13T10:30:00Z"
    },
    "user:bob": {
        "facts": [...],  # Faits sur Bob vus par cet agent
        "relationship_score": 0.3,
        "last_interaction": "2026-02-12T15:00:00Z"
    }
}
```

### 3.2 Query Flow

```
User Query → [Identify User] → [Get Agent's Memory for User] 
    → [Inject in Prompt] → LLM → Response
```

### 3.3 Schema SurrealDB

```surql
-- Mémoire partitionnée par agent et utilisateur
DEFINE TABLE user_agent_memory SCHEMAFULL;
DEFINE FIELD agent ON user_agent_memory TYPE record(agent);
DEFINE FIELD user ON user_agent_memory TYPE record(user);
DEFINE FIELD facts ON user_agent_memory TYPE array;
DEFINE FIELD relationship_score ON user_agent_memory TYPE float DEFAULT 0.5;
DEFINE FIELD last_interaction ON user_agent_memory TYPE datetime;

DEFINE INDEX agent_user_idx ON user_agent_memory COLUMNS agent, user UNIQUE;
```

## 4. Emotional History

**FR27: System tracks emotional history per user (short-term context)**

### 4.1 Emotion Detection

L'émotion est détectée via :
- **Analyse vocale** (prosodie, rythme) si audio
- **Analyse textuelle** (NLP) si texte
- **Historique** (si l'utilisateur était énervé les 3 dernières interactions)

### 4.2 Short-Term Context

```python
# Conservation des 5 dernières interactions
emotional_context = {
    "user_id": "alice",
    "history": [
        {"emotion": "annoyed", "timestamp": "2026-02-13T10:25:00Z"},
        {"emotion": "neutral", "timestamp": "2026-02-13T10:20:00Z"},
        {"emotion": "happy", "timestamp": "2026-02-13T10:15:00Z"},
    ]
}
```

### 4.3 Impact sur le scoring

Si `emotional_context[-3:]` contient ≥ 2 émotions négatives :
- Bonus de compréhension (+0.1)
- Réponses plus courtes
- Le ton peut être interpreté différemment ("merci" peut être sarcastique)

## 5. Social Grid (Grille Sociale)

**FR28-FR31: Dynamic relationships between agents and users**

### 5.1 Types de Relations

| Relation | Direction | Description |
|----------|-----------|-------------|
| `TRUSTS` | Agent ↔ Agent | Confiance entre agents |
| `LIKES` | Agent ↔ Agent | Affection entre agents |
| `KNOWS` | Agent ↔ Agent | Connaissance |
| `TRUSTS_USER` | Agent → User | Confiance envers l'utilisateur |
| `LIKES_USER` | Agent → User | Affection envers l'utilisateur |

### 5.2 Évolution des Relations

Les relations évoluent via :
- **Interactions positives** : +0.05 par interaction réussie
- **Interactions négatives** : -0.05
- **Temps** : -0.01 par jour sans interaction
- **Événements** : Score défini par le LLM lors de moments clés

### 5.3 Tone vs Quality

**RÈGLE CRITICAL** : La relation affecte le **TON**, jamais la **QUALITÉ** du service.

| Relation Score | Ton | Service |
|---------------|-----|---------|
| 0.8-1.0 | Chaleureux, personnel | ✅ Normal |
| 0.5-0.8 | Professionnel | ✅ Normal |
| 0.2-0.5 | Neutre/distant | ✅ Normal |
| < 0.2 | Froid mais poli | ✅ Normal |

### 5.4 Schema SurrealDB

```surql
-- Graphe social
DEFINE TABLE agent_relationship SCHEMAFULL;
DEFINE FIELD from_agent ON agent_relationship TYPE record(agent);
DEFINE FIELD to_agent ON agent_relationship TYPE record(agent);
DEFINE FIELD relationship_type ON agent_relationship TYPE string; -- TRUSTS, LIKES, KNOWS
DEFINE FIELD score ON agent_relationship TYPE float DEFAULT 0.5;
DEFINE FIELD last_updated ON agent_relationship TYPE datetime;

DEFINE TABLE user_relationship SCHEMAFULL;
DEFINE FIELD agent ON user_relationship TYPE record(agent);
DEFINE FIELD user ON user_relationship TYPE record(user);
DEFINE FIELD relationship_type ON user_relationship TYPE string; -- TRUSTS_USER, LIKES_USER
DEFINE FIELD score ON user_relationship TYPE float DEFAULT 0.5;
DEFINE FIELD last_updated ON user_relationship TYPE datetime;

DEFINE INDEX rel_idx ON agent_relationship COLUMNS from_agent, to_agent, relationship_type UNIQUE;
DEFINE INDEX user_rel_idx ON user_relationship COLUMNS agent, user, relationship_type UNIQUE;
```

## 6. Onboarding (FR28)

### 6.1 Interview d'Onboarding

Quando un nouvel utilisateur arrive :
1. **Enregistrement vocal** : Capture 10s de parole
2. **Création du profil** : Nom, préférences
3. **Introduction aux agents** : Chaque agent reçoit une "note de présentation"

### 6.2 Introduction aux Agents

```python
# Prompt d'introduction pour chaque agent
onboarding_prompt = f"""
Nouvel utilisateur : {user_name}
Âge: {user_age}  # optionnel
Intérêts: {user_interests}

{krij} une première impression de cet utilisateur.
"""
```

## 7. API Endpoints

### 7.1 User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/users` | Create new user |
| GET | `/api/v1/users` | List all users |
| GET | `/api/v1/users/{user_id}` | Get user details |
| PUT | `/api/v1/users/{user_id}/voice` | Enroll voice |
| DELETE | `/api/v1/users/{user_id}` | Delete user |

### 7.2 Relationship Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/agents/{agent_id}/relationships` | Get agent's relationships |
| GET | `/api/v1/users/{user_id}/relationships` | Get user's relationships |
| PUT | `/api/v1/relationships/{id}/score` | Update relationship score |

### 7.3 Emotional Context

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/{user_id}/emotional-context` | Get short-term emotional history |
| POST | `/api/v1/emotions/analyze` | Analyze text/audio emotion |

## 8. Integration Points

### 8.1 With Social Arbiter
- L'Arbiter reçoit le `user_id` avec chaque message
- Le score de relation est injecté dans le prompt de l'agent
- Le ton est modulé selon la relation

### 8.2 With Memory System
- Les faits sont taggués avec `user_id`
- Chaque agent a sa propre vue des faits par utilisateur
- La consolidation nocturne inclut les relations

---

🏗️ PM Agent - hAIrem Architecture
