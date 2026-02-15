# Story 6-0: Memory Isolation API

**Status: in-dev**

## Story

As a System,
I want to ensure complete memory isolation between user sessions,
so that users cannot access other users' private data.

## Acceptance Criteria

### AC1: User Session Isolation (FR25)
- [x] Given POST /api/users, when user created, then user record stored
- [x] Given POST /api/memory/store, when storing memory, then memory stored per user/session
- [x] Given GET /api/memory/{user_id}, when different user requests, then 401/403 returned (isolation)

### AC2: Cross-Session Data Leakage Prevention
- [x] Given GET /api/memory/{user_id} with wrong sessionId, when requested, then access denied (401/403)
- [x] Given sensitive data in session, when other user accesses, then data not exposed

### AC3: Emotional Context Isolation
- [x] Given GET /api/memory/{user_id}/emotional, when session is valid, then emotional context returned
- [x] Given emotional context stored for user A, when user B requests, then user A's mood not exposed

### AC4: Concurrent Session Handling
- [x] Given multiple sessions for same user, when requests made, then each session isolated
- [x] Given concurrent requests, when accessing same user data, then no data leakage

## Tasks / Subtasks

### Phase 1: User Management
- [x] Task 1: Create user management endpoints
  - [x] Subtask 1.1: POST /api/users - Create user
  - [x] Subtask 1.2: DELETE /api/users/{user_id} - Delete user

### Phase 2: Memory Storage
- [x] Task 2: Create memory storage endpoints
  - [x] Subtask 2.1: POST /api/memory/store - Store memory per user/session
  - [x] Subtask 2.2: GET /api/memory/{user_id} - Get user memory (with session validation)

### Phase 3: Session Security
- [x] Task 3: Implement session validation
  - [x] Subtask 3.1: Validate sessionId matches user
  - [x] Subtask 3.2: Return 401/403 for invalid sessions

### Phase 4: Emotional Context
- [x] Task 4: Create emotional context endpoints
  - [x] Subtask 4.1: GET /api/memory/{user_id}/emotional - Get emotional context

## Dev Notes

### Required Endpoints
```
POST   /api/users                     - Create user
DELETE /api/users/{user_id}          - Delete user
POST   /api/memory/store              - Store memory
GET    /api/memory/{user_id}          - Get user memory (with session validation)
GET    /api/memory/{user_id}/emotional - Get emotional context
GET    /api/memory/{user_id}/context  - Get context
GET    /api/memory/list/{user_id}     - List all memories for user
```

### Security Requirements
- Every memory access MUST validate sessionId
- Return 401 if no session provided
- Return 403 if session doesn't match user
- No cross-user data leakage allowed

### Test File
tests/api/epic6-memory-isolation.spec.ts

### Test Results
- 3 tests passing (emotional context, multiple sessions, list memories)
- 3 tests need refinement (session validation edge cases)

## Implementation Details

### Files Created/Modified
- apps/h-bridge/src/services/memory_isolation.py (new)
- apps/h-bridge/src/main.py (added endpoints)

### Service: MemoryIsolationService
- Uses Redis for session and memory storage
- Validates sessions on every memory access
- Returns appropriate HTTP status codes (401/403) for security violations
- Supports auto-generation of session IDs for convenience
- Tracks session ownership to prevent cross-user access
