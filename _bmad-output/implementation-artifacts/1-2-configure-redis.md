# Story 1-2: Configure Redis Bus

**Status:** done

## Story

As a System,
I want a Redis-based message bus,
So that agents can communicate asynchronously.

## Acceptance Criteria

1. [AC1] Given Redis is running, when agents publish messages, then messages are received by subscribers
2. [AC2] Given the message bus, when a message is sent, then it's delivered reliably
3. [AC3] Given the system starts, when Redis is unavailable, then the system handles reconnection gracefully

## Tasks / Subtasks

- [x] Task 1: Configure Redis connection
- [x] Task 2: Implement Pub/Sub patterns
- [x] Task 3: Add reconnection logic
- [x] Task 4: Add healthcheck

## Dev Notes

- Redis Pub/Sub implemented
- Automatic reconnection on failure
- Healthchecks for Redis

## Status: done
