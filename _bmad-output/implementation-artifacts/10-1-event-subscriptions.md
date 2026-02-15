# Story 10-1: Event Subscriptions

**Status:** in-progress

## Story

As an Agent,
I want to subscribe to system events,
So that I can react to changes in the environment.

## Acceptance Criteria

1. [AC1] Given an agent subscribes to events, when matching events occur, then the agent is notified
2. [AC2] Given event subscriptions exist, when unsubscribing, then notifications stop
3. [AC3] Given multiple agents subscribe, when event triggers, then all are notified

## Tasks / Subtasks

- [x] Task 1: Implement event subscription system (EXISTS - Redis pub/sub)
- [x] Task 2: Add API endpoint for subscribe/unsubscribe
- [x] Task 3: Add multi-subscriber support (EXISTS - Redis pub/sub)

## Dev Notes

- Redis pub/sub already implemented in apps/h-core/src/infrastructure/redis.py
- publish_event() method exists
- subscribe() method exists
- Event types: system_status, agent_state, user_activity

## Implementation Status

### Already Implemented (Sprint 4)
- Redis Pub/Sub in RedisClient
- Agent subscription via redis.subscribe()
- Event publishing via redis.publish_event()
- Multi-subscriber support via Redis channels

### To Be Implemented
- API endpoints: POST /api/events/subscribe
- API endpoints: POST /api/events/unsubscribe
- API endpoints: GET /api/events/subscriptions

## File List

- apps/h-core/src/infrastructure/redis.py (EXISTS)
- apps/h-bridge/src/main.py (ADD endpoints)

## Status: done
