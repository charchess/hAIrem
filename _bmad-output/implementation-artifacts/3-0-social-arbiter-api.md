# Story 3-0: Social Arbiter API

**Status: completed**

## Story

As a System,
I want to provide Social Arbiter functionality via API,
so that agents can be selected based on relevance to user messages.

## Acceptance Criteria

### AC1: Agent Selection API (FR18)
- [x] Given POST /api/arbiter/select with message and context, when called, then selected agent returned (200)
- [x] Given message with multiple relevant agents, when selected, then single agent returned
- [x] Given message with no relevant agents, when selected, then "no match" returned

### AC2: Agent Scoring API (FR19)
- [x] Given POST /api/arbiter/score with message and agents, when called, then scores for each agent returned (200)

### AC3: Configuration API
- [x] Given GET /api/arbiter/config, when called, then arbiter configuration returned (200/404)

### AC4: Turn-Taking (FR22)
- [x] Given multiple agents could respond, when arbiter processes, then only one agent selected

### AC5: Response Suppression (FR23)
- [x] Given responses below threshold, when arbiter evaluates, then responses suppressed

## Tasks / Subtasks

### Phase 1: Arbiter Service
- [x] Task 1: Create arbiter service
  - [x] Subtask 1.1: Create `apps/h-bridge/src/services/arbiter.py`
  - [x] Subtask 1.2: Implement agent selection logic
  - [x] Subtask 1.3: Implement scoring algorithm

### Phase 2: API Endpoints
- [x] Task 2: Add Arbiter endpoints
  - [x] Subtask 2.1: POST /api/arbiter/select
  - [x] Subtask 2.2: POST /api/arbiter/score
  - [x] Subtask 2.3: GET /api/arbiter/config

### Phase3: Business Logic
- [x] Task 3: Implement interest-based scoring
- [x] Task 4: Implement emotional context evaluation
- [x] Task 5: Implement named agent priority
- [x] Task 6: Implement turn-taking
- [x] Task 7: Implement response suppression

## Dev Notes

### Required Endpoints
```
POST   /api/arbiter/select           - Select best agent for message
POST   /api/arbiter/score            - Get agent scores
GET    /api/arbiter/config           - Get arbiter config
```

### Additional Endpoints Implemented
```
GET    /api/arbiter/emotions         - Detect emotions in message
GET    /api/arbiter/topics           - Extract topics from message
GET    /api/arbiter/suppression/stats - Get suppression stats
POST   /api/arbiter/agents           - Register new agent
```

### Test Files
- tests/atdd/epic3-social-arbiter.spec.ts

### Supported Scoring Factors
- Topic relevance
- Emotional context
- Named agent priority
- Turn-taking state

## Implementation Notes

- Implemented self-contained arbiter service in `apps/h-bridge/src/services/arbiter.py`
- Default agents: Chef, Tech, Companion, Gardener
- Scoring uses weighted combination of relevance, interest match, and emotional compatibility
- Minimum threshold (0.2) for agent selection
- Named agent detection works by matching agent name in message

## Dev Agent Record

### File List
- apps/h-bridge/src/services/arbiter.py (new)
- apps/h-bridge/src/main.py (add endpoints)

### Verified Working Endpoints
```
curl -X POST http://localhost:8000/api/arbiter/select -d '{"message": "Can someone help me with dinner recipes?", "context": {}}'
curl -X POST http://localhost:8000/api/arbiter/score -d '{"message": "Help me with coding", "agents": []}'
curl http://localhost:8000/api/arbiter/config
```
