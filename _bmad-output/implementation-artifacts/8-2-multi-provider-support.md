# Story 8-2: Multi-Provider Support

**Status:** done

## Story

As a System,
I want to support multiple image providers,
So that we can switch providers without code changes.

## Acceptance Criteria

1. [AC1] Given multiple providers exist, when configured, then they're all available
2. [AC2] Given a provider is selected, when generating, then that provider is used
3. [AC3] Given a provider fails, when attempted, then fallback to another provider

## Tasks / Subtasks

- [x] Task 1: Implement provider abstraction
- [x] Task 2: Add provider configuration
- [x] Task 3: Add fallback logic

## Dev Notes

- Provider abstraction in VisualConfigService
- Supports nanobanana, google, imagen-v2
- Fallback on provider failure

## Status: done
