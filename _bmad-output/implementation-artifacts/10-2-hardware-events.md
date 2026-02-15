# Story 10-2: Hardware Events

**Status:** done

## Story

As a System,
I want to detect hardware events,
So that agents can react to physical changes in the environment.

## Acceptance Criteria

1. [AC1] Given hardware events occur, when detected, then they're published to the system
2. [AC2] Given hardware events are published, when agents subscribe, then they react accordingly
3. [AC3] Given hardware is unavailable, when event occurs, then graceful degradation occurs

## Tasks / Subtasks

- [x] Task 1: Implement hardware event endpoint (POST /api/hardware/events)
- [x] Task 2: Add event listing endpoint (GET /api/hardware/events)
- [x] Task 3: Add device listing endpoint (GET /api/hardware/devices)

## Dev Notes

- Hardware events API implemented in apps/h-bridge/src/main.py
- Events stored in-memory (can be moved to Redis/database)
- Events published to Redis channel for agent subscription

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/hardware/events` | GET | List recent hardware events |
| `/api/hardware/events` | POST | Receive a hardware event |
| `/api/hardware/devices` | GET | List all known devices |
| `/api/hardware/events/{device_id}` | GET | Get events for a specific device |

## File List

- apps/h-bridge/src/main.py (hardware events endpoints)

## Status: done
