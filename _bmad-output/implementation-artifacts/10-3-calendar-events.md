# Story 10-3: Calendar Events

**Status:** done

## Story

As an Agent,
I want to know about calendar events,
So that I can remind users or prepare for upcoming events.

## Acceptance Criteria

1. [AC1] Given calendar integration exists, when events are fetched, then they're available to agents
2. [AC2] Given an event is upcoming, when threshold is reached, then the agent is notified
3. [AC3] Given calendar access fails, when attempted, then graceful error handling occurs

## Tasks / Subtasks

- [x] Task 1: Implement calendar events API endpoints
- [x] Task 2: Add event listing
- [x] Task 3: Add upcoming events endpoint

## Dev Notes

- Calendar events API implemented in apps/h-bridge/src/main.py
- In-memory storage (can integrate with Google Calendar, CalDAV)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/calendar/events` | GET | List calendar events |
| `/api/calendar/events` | POST | Create event |
| `/api/calendar/events/upcoming` | GET | Get upcoming events |

## File List

- apps/h-bridge/src/main.py (calendar endpoints)

## Status: done
