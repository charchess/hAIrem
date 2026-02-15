# Story 24-1: E2E Epic 3 - Social Arbiter UI Tests

**Status:** backlog

## Story

As a QA Engineer,
I want end-to-end tests for Epic 3 Social Arbiter,
So that the core conversation routing works reliably in UI.

## Acceptance Criteria

1. [AC1] Given multiple agents, when user sends message, then correct agent responds
2. [AC2] Given agent speaks, when UI updates, then avatar animates and text appears
3. [AC3] Given turn-taking, when agents respond, then no overlapping speech
4. [AC4] Given low-priority responses, when suppressed, then UI shows no response

## Tasks / Subtasks

- [ ] Task 1: Create Playwright E2E tests for social arbiter
- [ ] Task 2: Test multi-agent conversation flow
- [ ] Task 3: Test suppression logic in UI
- [ ] Task 4: Add video recording for failures

## Dev Notes

- Use Playwright for browser automation
- Test real conversation flow
- ~8 tests estimated

## File List

- tests/e2e/epic3-social-arbiter.spec.ts

## Status: backlog