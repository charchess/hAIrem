# Story 10-1: Event Subscriptions

**Status:** backlog

## Story

As an Agent,
I want to subscribe to system events,
So that I can react to changes in the environment.

## Acceptance Criteria

1. [AC1] Given an agent subscribes to events, when matching events occur, then the agent is notified
2. [AC2] Given event subscriptions exist, when unsubscribing, then notifications stop
3. [AC3] Given multiple agents subscribe, when event triggers, then all are notified

## Tasks / Subtasks

- [ ] Task 1: Implement event subscription system
- [ ] Task 2: Add unsubscribe capability
- [ ] Task 3: Add multi-subscriber support

## Dev Notes

- To be implemented in Sprint 22
- Based on Redis Pub/Sub
- Event types: system_status, agent_state, user_activity

## File List

- apps/h-core/src/domain/events.py (to be created)

## Status: backlog
