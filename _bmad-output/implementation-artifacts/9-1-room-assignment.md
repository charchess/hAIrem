# Story 9.1: Room Assignment

Status: completed

## Story

As a System,
I want agents to be assigned to physical locations,
so that I know which agent is in which room.

## Acceptance Criteria

1. [AC1] Given agents are configured, when room assignment is set, then agents are linked to rooms
2. [AC2] Given agent has room assignment, when queried, then room information is returned
3. [AC3] Given admin changes room assignment, when saved, then agent's location is updated

## Tasks / Subtasks

- [x] Task 1: Implement room data model (AC: #1)
  - [x] Subtask 1.1: Define room schema (name, type, description)
  - [x] Subtask 1.2: Add room_id to agent schema
- [x] Task 2: Implement room query (AC: #2)
  - [x] Subtask 2.1: Add room info to agent queries
  - [x] Subtask 2.2: Return room in agent details API
- [x] Task 3: Implement room assignment (AC: #3)
  - [x] Subtask 3.1: Create room assignment endpoint
  - [x] Subtask 3.2: Update agent location

## Dev Notes

### References
- PRD: _bmad-output/planning-artifacts/prd.md (FR47)
- Epic Breakdown: _bmad-output/planning-artifacts/epics.md

## Dev Agent Record

### Agent Model Used

opencode/big-pickle

### File List

- apps/h-core/src/features/home/spatial/rooms/models.py (NEW)
- apps/h-core/src/features/home/spatial/rooms/repository.py (NEW)
- apps/h-core/src/features/home/spatial/rooms/service.py (NEW)
- apps/h-core/src/features/home/spatial/rooms/__init__.py (NEW)
- apps/h-core/src/features/home/spatial/__init__.py (NEW)
- apps/h-core/src/models/agent.py (MODIFIED - added room_id field)
- apps/h-core/src/main.py (MODIFIED - added RoomService and message handlers)
- apps/h-core/src/features/admin/agent_creation/service.py (MODIFIED - added room_service dependency)
- apps/h-core/tests/test_room_assignment.py (NEW)