# Story 1-4: Agent Communication Protocol

**Status:** done

## Story

As an Agent,
I want a defined communication protocol,
So that I can send and receive messages reliably.

## Acceptance Criteria

1. [AC1] Given two agents, when one sends a message, then the other receives it
2. [AC2] Given a message is sent, when received, then the message format is validated
3. [AC3] Given the protocol, when implemented, then it supports different message types

## Tasks / Subtasks

- [x] Task 1: Define message format/schema
- [x] Task 2: Implement send/receive methods
- [x] Task 3: Add message type support
- [x] Task 4: Implement validation

## Dev Notes

- Message protocol defined in apps/h-core/src/domain/messages.py
- Supports text, system, event message types
- Validation implemented

## Status: done
