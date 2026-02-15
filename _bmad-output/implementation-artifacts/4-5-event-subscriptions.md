# Story 4-5: Event Subscriptions

**Status:** done

## Story

As an Agent,
I want to subscribe to events,
So that I can react to system events automatically.

## Acceptance Criteria

1. [AC1] Given an agent subscribes to events, when matching events occur, then the agent is notified
2. [AC2] Given event subscriptions exist, when agent unsubscribes, then notifications stop
3. [AC3] Given multiple agents subscribe to the same event, when triggered, then all are notified

## Tasks / Subtasks

- [x] Task 1: Implement event subscription
- [x] Task 2: Add unsubscribe capability
- [x] Task 3: Add multi-subscriber support

## Dev Notes

- Event subscription via Redis Pub/Sub
- Unsubscribe via channel leave
- Multiple subscribers supported

## Status: done
