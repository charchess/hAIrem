# Story 8-4: Customizable Outfits

**Status:** done

## Story

As a User,
I want to customize agent outfits,
So that agents can wear different clothing.

## Acceptance Criteria

1. [AC1] Given outfit customization, when requested, then outfit options are shown
2. [AC2] Given an outfit is selected, when applied, then the agent displays it
3. [AC3] Given outfit is changed, when applied, then previous outfit is replaced

## Tasks / Subtasks

- [x] Task 1: Implement outfit selection UI
- [x] Task 2: Add outfit application logic
- [x] Task 3: Add outfit persistence

## Dev Notes

- Outfit customization via /api/visual/outfit endpoint
- Outfit stored in SurrealDB via WEARS relation
- Automatic invalidation of previous outfit

## Status: done
