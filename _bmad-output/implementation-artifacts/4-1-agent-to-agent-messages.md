# Story 4-1: Agent-to-Agent Direct Messages

**Status:** done

## Story

As an Agent,
I want to send direct messages to another agent,
So that I can communicate privately.

## Acceptance Criteria

1. [AC1] Given two agents exist, when one sends a direct message, then only that agent receives it
2. [AC2] Given a direct message is sent, when received, then it's processed correctly
3. [AC3] Given the sender is invalid, when sending, then an error is returned

## Tasks / Subtasks

- [x] Task 1: Implement direct message endpoint
- [x] Task 2: Add agent targeting
- [x] Task 3: Add validation

## Dev Notes

- Direct messaging via Redis Pub/Sub
- Agent targeting via whisper channel
- Implemented in apps/h-core/src/domain/messages.py

## Status: done
